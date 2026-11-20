#!/usr/bin/env python3
"""
retrain.py — Phase D5. Continual learning on a laptop CPU: no LLM, no server, seconds to minutes.

Recipe (model card §2, Phase C): per head, multinomial logistic regression on [768-d embedding | role one-hot |
position one-hot]; C from the parent manifest; sample weight = balanced n/(k*n_c) x teacher weight_<head>,
mean 1; corrections weighted x2. Temperatures re-fitted on gold-calib (balanced and prior-corrected modes);
class prior = teacher-weighted class share of the pool; per-head modes copied from the parent.

Gate (all must pass to promote):
  1. no drop in strict macro-F1 on gold-dev for any head (vs the promoted model);
  2. no class F1 on gold-dev drops by more than 0.03;
  3. better accuracy than the promoted model on the held-out 20% of corrections.
Deviations from the SRS / handover (logged): gold-test is not used (it is spent); gold-dev is used for the gate
ONLY, not for training, so the gate is not measured on training data.

    python scripts\\retrain.py --reproduce                  # sanity check: no corrections -> must match model_v1
    python scripts\\retrain.py --corrections my_corrections.csv [--promote]
Corrections CSV: email_uid, head, label, user_id, recipient_role, recipient_position and either input_text
(embedded here on CPU) or --corr-emb <prefix> with <prefix>_emb.npy / _uids.txt.
Writes model_vN\\ (heads.npz + manifest.json) only with --promote and a passing gate; always writes
runs\\<date>-retrain\\{report.md, gate.json}. promoted.json points the service at the promoted model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import student as S  # noqa: E402

HEADS = ("type", "urgency", "sentiment")
SEED = 42


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def gold_label_col(df: pd.DataFrame, h: str) -> str:
    """The primary gold label column (`type`, `urgency`, `sentiment`). Gold-dev and gold-calib are all
    single-labelled, so primary = strict there (Phase C handover). `<head>_strict` is not a label column."""
    return h


def load_split(name: str, manifest: dict) -> tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_csv(ROOT / "Data" / "gold_final" / f"{name}.csv", dtype=str, keep_default_na=False)
    E, uids = S.load_embeddings(ROOT / "Data" / "emb" / name)
    return df, S.align(E, uids, df["email_uid"].tolist(), name)


def features(E, roles, positions, manifest):
    X, _ = S.build_features(E, list(roles), list(positions), manifest["roles"], manifest["positions"])
    return X


def balanced_weights(y: np.ndarray, base: np.ndarray, classes: list[str]) -> np.ndarray:
    n, k = len(y), len(classes)
    counts = {c: max(int((y == c).sum()), 1) for c in classes}
    w = np.array([n / (k * counts[c]) for c in y]) * base
    return w / w.mean()


def fit_temperature(z: np.ndarray, y_idx: np.ndarray) -> float:
    from scipy.optimize import minimize_scalar

    y_idx = np.asarray(y_idx, dtype=int)
    if len(y_idx) == 0:
        raise ValueError("no calibration rows with a valid label for this head")

    def nll(T):
        p = S.softmax(z / T)
        return -np.log(np.clip(p[np.arange(len(y_idx)), y_idx], 1e-12, None)).mean()
    return float(minimize_scalar(nll, bounds=(0.05, 20.0), method="bounded").x)


def train(parent: dict, pool: pd.DataFrame, E_pool: np.ndarray, corr: pd.DataFrame | None, E_corr: np.ndarray | None,
          calib: pd.DataFrame, E_calib: np.ndarray, corr_weight: float) -> tuple[dict, dict]:
    from sklearn.linear_model import LogisticRegression
    X_pool = features(E_pool, pool["recipient_role"], pool["recipient_position"], parent)
    X_cal = features(E_calib, calib["recipient_role"], calib["recipient_position"], parent)
    heads, man = {}, json.loads(json.dumps(parent))
    man["temperatures"], man["temperatures_prior"], man["class_prior"] = {}, {}, {}
    for h in HEADS:
        classes = parent["classes"][h]
        wcol = f"weight_{h}" if f"weight_{h}" in pool.columns else "weight"
        base = pd.to_numeric(pool[wcol], errors="coerce").fillna(0).to_numpy()
        keep = (pool[h].isin(classes).to_numpy()) & (base > 0)
        X, y, b = X_pool[keep], pool[h].to_numpy()[keep], base[keep]
        prior = np.array([b[y == c].sum() for c in classes]) / b.sum()
        is_corr = np.zeros(len(y), bool)
        if corr is not None and len(corr):
            ch = corr[corr["head"] == h]
            if len(ch):
                idx = ch.index.to_numpy()
                X = np.vstack([X, features(E_corr[idx], ch["recipient_role"], ch["recipient_position"], parent)])
                y = np.concatenate([y, ch["label"].to_numpy()])
                b = np.concatenate([b, np.ones(len(ch))])
                is_corr = np.concatenate([is_corr, np.ones(len(ch), bool)])
        w = balanced_weights(y, b, classes)
        w[is_corr] *= corr_weight
        w = w / w.mean()
        clf = LogisticRegression(C=float(parent["C"][h]), max_iter=3000, random_state=SEED)
        clf.fit(X, y, sample_weight=w)
        order = [list(clf.classes_).index(c) for c in classes]       # sklearn sorts classes; restore manifest order
        W, bias = clf.coef_[order], clf.intercept_[order]
        heads[h] = (W, bias)
        # temperatures on gold-calib
        col = gold_label_col(calib, h)
        m = calib[col].isin(classes).to_numpy()
        z = S.logits(X_cal[m], W, bias)
        yi = np.array([classes.index(c) for c in calib[col].to_numpy()[m]])
        man["temperatures"][h] = fit_temperature(z, yi)
        man["temperatures_prior"][h] = fit_temperature(z + np.log(prior), yi)
        man["class_prior"][h] = prior.tolist()
    return heads, man


def predict(man: dict, heads: dict, X: np.ndarray) -> dict:
    return S.predict_proba(man, heads, X, "mixed" if man.get("head_mode") else man.get("default_mode", "balanced"))


def f1_report(y_true, y_pred, classes) -> dict:
    from sklearn.metrics import f1_score
    present = [c for c in classes if c in set(y_true)]
    per = f1_score(y_true, y_pred, labels=present, average=None, zero_division=0)
    return {"macro": float(np.mean(per)) if len(per) else 0.0, "per_class": dict(zip(present, map(float, per)))}


def evaluate_dev(man, heads, dev, X_dev) -> dict:
    P = predict(man, heads, X_dev)
    out = {}
    for h in HEADS:
        cl = man["classes"][h]
        col = gold_label_col(dev, h)
        m = dev[col].isin(cl).to_numpy()
        pred = np.array(cl)[P[h].argmax(1)]
        out[h] = f1_report(dev[col].to_numpy()[m], pred[m], cl)
    return out


def corrections_accuracy(man, heads, corr, E_corr) -> float | None:
    if corr is None or not len(corr):
        return None
    X = features(E_corr[corr.index.to_numpy()], corr["recipient_role"], corr["recipient_position"], man)
    P = predict(man, heads, X)
    hits = [man["classes"][r.head][int(P[r.head][i].argmax())] == r.label for i, r in enumerate(corr.itertuples())]
    return float(np.mean(hits))


def split_corrections(corr: pd.DataFrame, holdout: float, user_cap: float) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    info = {"rows_in": len(corr), "users": int(corr["user_id"].nunique())}
    if info["users"] >= 4:                                   # cap any one user at 25% of corrections
        cap = math.ceil(user_cap * len(corr))
        parts = []
        for _, g in corr.groupby("user_id", sort=True):
            parts.append(g if len(g) <= cap else g.sample(cap, random_state=SEED))
        corr = pd.concat(parts)
        info["user_cap"] = cap
    else:
        info["user_cap"] = "not applied (fewer than 4 users)"
    hold = []
    for _, g in corr.groupby("head", sort=True):             # stratified by head
        n = int(round(holdout * len(g))) if len(g) >= 2 else 0
        hold += list(rng.choice(g.index.to_numpy(), size=n, replace=False)) if n else []
    hold_set = set(hold)
    tr = corr[~corr.index.isin(hold_set)]
    ho = corr[corr.index.isin(hold_set)]
    info.update({"rows_after_cap": len(corr), "train": len(tr), "holdout": len(ho)})
    return tr, ho, info


def gate(cur_dev, cand_dev, cur_acc, cand_acc, tol: float, class_drop: float) -> dict:
    checks = {"macro_f1_no_drop": {}, "class_f1_drop_le_0.03": {}, "better_on_heldout_corrections": None}
    ok = True
    for h in HEADS:
        d = cand_dev[h]["macro"] - cur_dev[h]["macro"]
        checks["macro_f1_no_drop"][h] = {"promoted": cur_dev[h]["macro"], "candidate": cand_dev[h]["macro"],
                                         "delta": d, "pass": d >= -tol}
        ok &= d >= -tol
        worst = min((cand_dev[h]["per_class"].get(c, 0) - v for c, v in cur_dev[h]["per_class"].items()), default=0)
        checks["class_f1_drop_le_0.03"][h] = {"worst_class_delta": worst, "pass": worst >= -class_drop}
        ok &= worst >= -class_drop
    if cand_acc is None:
        checks["better_on_heldout_corrections"] = {"pass": None, "note": "no held-out corrections"}
        ok = False
    else:
        better = cand_acc > cur_acc
        checks["better_on_heldout_corrections"] = {"promoted": cur_acc, "candidate": cand_acc, "pass": better}
        ok &= better
    checks["pass"] = bool(ok)
    return checks


def next_version(root: Path) -> int:
    ns = [int(p.name.split("_v")[1]) for p in root.glob("model_v*") if p.name.split("_v")[1].isdigit()]
    return max(ns, default=1) + 1


def load_pool(parent: dict) -> tuple[pd.DataFrame, np.ndarray]:
    pool = pd.read_csv(ROOT / parent["inputs"]["train"]["path"].replace("\\", "/"), dtype=str, keep_default_na=False)
    E, uids = S.load_embeddings(ROOT / "Data" / "emb" / "pool")
    return pool, S.align(E, uids, pool["email_uid"].tolist(), "pool")


def run(parent_dir: Path, corr: pd.DataFrame | None, E_corr: np.ndarray | None, out_run: Path, corr_weight: float,
        holdout: float, user_cap: float, tol: float, promote: bool, model_out: Path | None = None) -> dict:
    from secep_ml.triage import promoted_model_dir
    parent, parent_heads = S.load_model(parent_dir)
    pool, E_pool = load_pool(parent)
    calib, E_calib = load_split("gold_calib", parent)
    dev, E_dev = load_split("gold_dev", parent)
    X_dev = features(E_dev, dev["recipient_role"], dev["recipient_position"], parent)
    tr = ho = None
    split_info = None
    if corr is not None:
        corr = corr.reset_index(drop=True)
        tr, ho, split_info = split_corrections(corr, holdout, user_cap)
    heads, man = train(parent, pool, E_pool, tr, E_corr, calib, E_calib, corr_weight)
    cur_dev = evaluate_dev(parent, parent_heads, dev, X_dev)
    cand_dev = evaluate_dev(man, heads, dev, X_dev)
    cur_acc = corrections_accuracy(parent, parent_heads, ho, E_corr)
    cand_acc = corrections_accuracy(man, heads, ho, E_corr)
    g = gate(cur_dev, cand_dev, cur_acc, cand_acc, tol, 0.03)
    Pp, Pc = predict(parent, parent_heads, X_dev), predict(man, heads, X_dev)
    agree = {h: float((Pp[h].argmax(1) == Pc[h].argmax(1)).mean()) for h in HEADS}
    maxdiff = {h: float(np.abs(Pp[h] - Pc[h]).max()) for h in HEADS}
    result = {"created": datetime.now().isoformat(timespec="seconds"), "parent": parent.get("model", parent_dir.name),
              "parent_dir": str(parent_dir.name), "corrections": split_info, "corr_weight": corr_weight,
              "gate": g, "dev_label_agreement_vs_parent": agree, "dev_max_prob_diff_vs_parent": maxdiff,
              "temperatures": man["temperatures"], "temperatures_prior": man["temperatures_prior"],
              "promoted": False}
    man.update({"created": result["created"], "parent": result["parent"], "retrain": {
        "corrections": split_info, "corr_weight": corr_weight, "gate": g,
        "data_sha256": {"pool": parent["inputs"]["train"]["sha256"],
                        "calib": sha256(ROOT / "Data" / "gold_final" / "gold_calib.csv"),
                        "dev_gate": sha256(ROOT / "Data" / "gold_final" / "gold_dev.csv")}}})
    out_run.mkdir(parents=True, exist_ok=True)
    if model_out is not None:                                     # demo / inspection: save without promoting
        man["model"] = model_out.name
        S.save_model(model_out, heads, man)
        result["model_dir"] = str(model_out)
    if promote and g["pass"]:
        cur_promoted = promoted_model_dir(ROOT)
        v = next_version(ROOT)
        d = ROOT / f"model_v{v}"
        man["model"] = d.name
        S.save_model(d, heads, man)
        (ROOT / "promoted.json").write_text(json.dumps({"model_dir": d.name, "promoted_at": result["created"],
                                                        "previous": cur_promoted.name, "gate": "pass"}, indent=2),
                                            encoding="utf-8")
        result.update({"promoted": True, "model_dir": d.name})
    (out_run / "gate.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    L = [f"# Retrain — {result['created']}", "", f"Parent `{result['parent']}`; corrections: {split_info}; "
         f"weight x{corr_weight}.", "", "| head | gold-dev macro-F1 promoted | candidate | Δ | worst class Δ | pass |",
         "|---|---|---|---|---|---|"]
    for h in HEADS:
        a_, b_ = g["macro_f1_no_drop"][h], g["class_f1_drop_le_0.03"][h]
        L.append(f"| {h} | {a_['promoted']:.3f} | {a_['candidate']:.3f} | {a_['delta']:+.3f} | "
                 f"{b_['worst_class_delta']:+.3f} | {'✓' if a_['pass'] and b_['pass'] else '✗'} |")
    hc = g["better_on_heldout_corrections"]
    L += ["", f"Held-out corrections accuracy: promoted {hc.get('promoted')}, candidate {hc.get('candidate')} "
          f"→ {'✓' if hc.get('pass') else '✗'}", "",
          f"Label agreement with parent on gold-dev: {agree}; max prob diff {maxdiff}", "",
          (f"**Gate: {'PASS' if g['pass'] else 'FAIL'}** — "
           + ("promoted to " + result["model_dir"] if result["promoted"] else "not promoted"))
          if corr is not None else "**Reproduction check only** (no corrections): gate not applicable, nothing saved."]
    (out_run / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return result


def embed_texts(texts: list[str]) -> np.ndarray:
    from secep_ml import triage as TR
    t = TR.load(ROOT / "model_v1")
    return t.embed(texts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parent", type=Path, help="default: the promoted model (promoted.json) or model_v1")
    ap.add_argument("--corrections", type=Path)
    ap.add_argument("--corr-emb", type=Path, help="prefix of <prefix>_emb.npy / _uids.txt for the corrections")
    ap.add_argument("--corr-weight", type=float, default=2.0)
    ap.add_argument("--holdout", type=float, default=0.2)
    ap.add_argument("--user-cap", type=float, default=0.25)
    ap.add_argument("--tolerance", type=float, default=0.0, help="allowed macro-F1 drop (default 0: no drop)")
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--reproduce", action="store_true", help="no corrections: check this recipe reproduces the parent")
    a = ap.parse_args()
    from secep_ml.triage import promoted_model_dir
    parent = a.parent or promoted_model_dir(ROOT)
    out = ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-retrain{'-reproduce' if a.reproduce else ''}"
    if a.reproduce:
        r = run(parent, None, None, out, a.corr_weight, a.holdout, a.user_cap, a.tolerance, False)
        worst = min(r["dev_label_agreement_vs_parent"].values())
        print(f"\nREPRODUCTION: worst-head label agreement with {parent.name} on gold-dev = {worst:.1%} "
              f"({'OK' if worst >= 0.97 else 'DIFFERS: this recipe does not match Phase C training closely enough'})")
        return
    if not a.corrections:
        sys.exit("ERROR: --corrections is required (or use --reproduce)")
    corr = pd.read_csv(a.corrections, dtype=str, keep_default_na=False)
    need = {"email_uid", "head", "label", "user_id", "recipient_role", "recipient_position"}
    if need - set(corr.columns):
        sys.exit(f"ERROR: corrections CSV missing {sorted(need - set(corr.columns))}")
    parent_man = json.loads((parent / "manifest.json").read_text(encoding="utf-8"))
    bad = corr[~corr.apply(lambda r: r["head"] in HEADS and r["label"] in parent_man["classes"].get(r["head"], []), axis=1)]
    if len(bad):
        sys.exit(f"ERROR: {len(bad)} corrections have an unknown head or label, e.g. {bad.head(3).to_dict('records')}")
    if a.corr_emb:
        E, uids = S.load_embeddings(a.corr_emb)
        E_corr = S.align(E, uids, corr["email_uid"].tolist(), "corrections")
    elif "input_text" in corr.columns:
        E_corr = embed_texts(corr["input_text"].tolist())
    else:
        sys.exit("ERROR: corrections need input_text or --corr-emb")
    run(parent, corr, E_corr, out, a.corr_weight, a.holdout, a.user_cap, a.tolerance, a.promote)


if __name__ == "__main__":
    main()
