"""Scoring functions shared by score.py, the student sanity checks (C4) and retrain.py (D).

Pure functions only: label lists / arrays in, numbers out. No file I/O.

Conventions (fixed; see README_scorer.md and decision_log.md):
- Macro-F1 is computed exactly like scripts/human_baseline.py, so the gate compares like
  with like: a class is left out of the average only when neither truth nor prediction
  ever uses it (tp+fp+fn == 0). A class that is predicted but absent from the truth stays
  in with F1 = 0. Equivalent to sklearn f1_score(labels=<union of used classes>,
  average="macro", zero_division=0).
- Lenient truth: if the prediction equals the primary label or the alt label, the truth is
  the label it matched; otherwise the truth is the primary label.
- ECE: top-label, 10 bins. Headline = equal-width; secondary = equal-count.
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

SEED = 42
REVIEW_THRESHOLD = 0.60

HEADS: dict[str, list[str]] = {
    "type": ["Task", "Info", "Credentials", "Meeting", "Approval"],
    "urgency": ["Critical", "High", "Medium", "Low"],
    "sentiment": ["Positive", "Neutral", "Negative", "Frustrated"],
}


def _type_action(v: str) -> str:
    return "Info" if v == "Info" else "Needs something"


def _urgency_2(v: str) -> str:
    return "Act soon" if v in ("Critical", "High") else "Can wait"


def _sentiment_2(v: str) -> str:
    return "Neutral" if v == "Neutral" else "Not neutral"


# view -> (head, mapping, classes). Names and labels identical to human_baseline.py MERGES.
VIEWS: dict[str, tuple[str, Callable[[str], str], list[str]]] = {
    "type_action": ("type", _type_action, ["Needs something", "Info"]),
    "urgency_2": ("urgency", _urgency_2, ["Act soon", "Can wait"]),
    "sentiment_2": ("sentiment", _sentiment_2, ["Neutral", "Not neutral"]),
}


# ------------------------------------------------------------------ core counts
def _codes(labels: Sequence[str], classes: Sequence[str]) -> np.ndarray:
    idx = {c: i for i, c in enumerate(classes)}
    try:
        return np.fromiter((idx[v] for v in labels), dtype=np.int64, count=len(labels))
    except KeyError as e:
        raise ValueError(f"label {e.args[0]!r} not in classes {list(classes)}") from None


def confusion(y_true: Sequence[str], y_pred: Sequence[str], classes: Sequence[str]) -> np.ndarray:
    """k x k counts; rows = truth, columns = prediction, in `classes` order."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred differ in length")
    k = len(classes)
    t, p = _codes(y_true, classes), _codes(y_pred, classes)
    return np.bincount(t * k + p, minlength=k * k).reshape(k, k)


def _f1_from_cm(cm: np.ndarray) -> np.ndarray:
    """Per-class F1 from a confusion matrix; NaN where the class is unused (tp+fp+fn == 0)."""
    tp = np.diag(cm).astype(float)
    fp = cm.sum(axis=0) - tp
    fn = cm.sum(axis=1) - tp
    denom = 2 * tp + fp + fn
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(denom > 0, 2 * tp / denom, np.nan)


def _macro_from_cm(cm: np.ndarray) -> float:
    f = _f1_from_cm(cm)
    return float(np.nanmean(f)) if np.any(~np.isnan(f)) else float("nan")


# ------------------------------------------------------------------ public metrics
def per_class(y_true: Sequence[str], y_pred: Sequence[str], classes: Sequence[str]) -> dict:
    """{class: {precision, recall, f1, support}}. f1 is None for a class neither side used."""
    cm = confusion(y_true, y_pred, classes)
    tp = np.diag(cm)
    pred_n, true_n = cm.sum(axis=0), cm.sum(axis=1)
    f1 = _f1_from_cm(cm)
    out = {}
    for i, c in enumerate(classes):
        used = not np.isnan(f1[i])
        out[c] = {
            "precision": (float(tp[i] / pred_n[i]) if pred_n[i] else 0.0) if used else None,
            "recall": (float(tp[i] / true_n[i]) if true_n[i] else 0.0) if used else None,
            "f1": float(f1[i]) if used else None,
            "support": int(true_n[i]),
            "predicted": int(pred_n[i]),
        }
    return out


def macro_f1(y_true: Sequence[str], y_pred: Sequence[str], classes: Sequence[str]) -> float:
    return _macro_from_cm(confusion(y_true, y_pred, classes))


def accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if not len(y_true):
        return float("nan")
    return float(np.mean([a == b for a, b in zip(y_true, y_pred)]))


def lenient_truth(y_true: Sequence[str], y_alt: Sequence[str], y_pred: Sequence[str]) -> list[str]:
    """Truth to score against when either labeller's answer is acceptable.

    Correct (matches primary or a non-blank alt) -> the matched label.
    Wrong -> the primary label.
    """
    return [p if (p == t or (a and p == a)) else t for t, a, p in zip(y_true, y_alt, y_pred)]


def bootstrap_macro_f1_ci(y_true: Sequence[str], y_pred: Sequence[str], classes: Sequence[str],
                          n_boot: int = 2000, seed: int = SEED) -> tuple[float, float]:
    """95% percentile CI over resampled emails. Each resample uses the same absent-class rule;
    NaN resamples (nothing scored) are dropped."""
    n = len(y_true)
    if n == 0:
        return float("nan"), float("nan")
    k = len(classes)
    t, p = _codes(y_true, classes), _codes(y_pred, classes)
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        i = rng.integers(0, n, n)
        cm = np.bincount(t[i] * k + p[i], minlength=k * k).reshape(k, k)
        vals[b] = _macro_from_cm(cm)
    vals = vals[~np.isnan(vals)]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def to_view(labels: Sequence[str], view: str) -> list[str]:
    _, f, _ = VIEWS[view]
    return [f(v) for v in labels]


# ------------------------------------------------------------------ calibration
def ece(confidence: Sequence[float], correct: Sequence[bool], n_bins: int = 10,
        strategy: str = "width") -> tuple[float, list[dict]]:
    """Top-label expected calibration error.

    strategy="width": bins (0,0.1], (0.1,0.2], ... ; "count": n_bins groups of ~equal size
    after sorting by confidence. Returns (ece, bins) where each bin is
    {lo, hi, n, mean_conf, accuracy}; empty bins are listed with n=0.
    """
    conf = np.asarray(confidence, dtype=float)
    corr = np.asarray(correct, dtype=float)
    n = len(conf)
    if n == 0:
        return float("nan"), []
    if strategy == "width":
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        ids = np.clip(np.digitize(conf, edges[1:-1], right=True), 0, n_bins - 1)
    elif strategy == "count":
        order = np.argsort(conf, kind="stable")
        ids = np.empty(n, dtype=int)
        ids[order] = np.arange(n) * n_bins // n
        edges = None
    else:
        raise ValueError("strategy must be 'width' or 'count'")
    total, bins = 0.0, []
    for b in range(n_bins):
        m = ids == b
        nb = int(m.sum())
        if edges is not None:
            lo, hi = float(edges[b]), float(edges[b + 1])
        else:
            lo = float(conf[m].min()) if nb else float("nan")
            hi = float(conf[m].max()) if nb else float("nan")
        if nb:
            mc, acc = float(conf[m].mean()), float(corr[m].mean())
            total += nb / n * abs(acc - mc)
        else:
            mc = acc = None
        bins.append({"lo": lo, "hi": hi, "n": nb, "mean_conf": mc, "accuracy": acc})
    return float(total), bins


def review_rate(confidence: Sequence[float], threshold: float = REVIEW_THRESHOLD) -> float:
    """Share of rows whose top probability is below the second-opinion threshold."""
    conf = np.asarray(confidence, dtype=float)
    return float(np.mean(conf < threshold)) if len(conf) else float("nan")
