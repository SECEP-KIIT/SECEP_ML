#!/usr/bin/env python3
"""
score.py — Phase C1. Scores a predictions file (I4) against a gold file.

Run from ML_Training:
    python scripts\\score.py --gold Data\\gold_final\\gold_dev.csv --pred runs\\x\\predictions.csv ^
        --out runs\\<date>-<name>\\ [--baseline Data\\gold_final\\human_baseline.json] ^
        [--exclude-uids file.txt] [--n-boot 2000]

Writes <out>/metrics.json (every number + config + input fingerprints) and <out>/report.md,
and prints a short summary. All maths lives in common/metrics.py; this file is I/O only.

Bad input fails loudly (non-zero exit): unknown class names, blank predictions, duplicate
uids, gold uids missing from the predictions, partial or non-numeric probability columns,
or probabilities whose per-head sum is off by more than 1e-3. Sums within 1e-3 are
silently renormalised. Prediction rows for uids not in the gold file are ignored (counted).
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

from common import metrics as M  # noqa: E402

PROB_TOL = 1e-3


def fail(msg: str) -> None:
    sys.exit(f"ERROR: {msg}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text_csv(path: Path) -> pd.DataFrame:
    # Everything as text: blank cells stay "" (pandas would turn an all-blank *_alt into float NaN).
    return pd.read_csv(path, dtype=str, keep_default_na=False)


# ------------------------------------------------------------------ validation
def validate_gold(gold: pd.DataFrame) -> None:
    need = ["email_uid"] + [f"{h}{s}" for h in M.HEADS for s in ("", "_alt", "_strict")]
    miss = [c for c in need if c not in gold.columns]
    if miss:
        fail(f"gold file is missing columns {miss}")
    if gold["email_uid"].duplicated().any():
        fail(f"gold has duplicate email_uid: {gold.loc[gold.email_uid.duplicated(), 'email_uid'].tolist()[:5]}")
    for h, classes in M.HEADS.items():
        for col in (h, f"{h}_alt"):
            bad = sorted(set(gold[col]) - set(classes) - {""})
            if bad:
                fail(f"gold column {col!r} has unknown labels {bad}")
        bad = sorted(set(gold[f"{h}_strict"].str.lower()) - {"true", "false"})
        if bad:
            fail(f"gold column {h}_strict has non-boolean values {bad}")


def validate_pred(pred: pd.DataFrame, gold_uids: set[str]) -> tuple[pd.DataFrame, dict, int]:
    """Returns (pred indexed by uid restricted to gold, {head: prob matrix or None}, n_extra)."""
    need = ["email_uid"] + [f"pred_{h}" for h in M.HEADS]
    miss = [c for c in need if c not in pred.columns]
    if miss:
        fail(f"predictions file is missing columns {miss}")
    if pred["email_uid"].duplicated().any():
        fail(f"predictions have duplicate email_uid: "
             f"{pred.loc[pred.email_uid.duplicated(), 'email_uid'].tolist()[:5]}")
    missing = sorted(gold_uids - set(pred["email_uid"]))
    if missing:
        fail(f"{len(missing)} gold uids have no prediction, e.g. {missing[:5]}")
    n_extra = int((~pred["email_uid"].isin(gold_uids)).sum())
    pred = pred[pred["email_uid"].isin(gold_uids)].set_index("email_uid")

    known_prob_cols = {f"prob_{h}_{c}" for h, cs in M.HEADS.items() for c in cs}
    stray = sorted(c for c in pred.columns if c.startswith("prob_") and c not in known_prob_cols)
    if stray:
        fail(f"unknown probability columns {stray} (expected prob_<head>_<Class>)")

    probs = {}
    for h, classes in M.HEADS.items():
        bad = sorted(set(pred[f"pred_{h}"]) - set(classes))
        if bad:
            fail(f"pred_{h} has unknown or blank labels {bad}; allowed {classes}")
        cols = [f"prob_{h}_{c}" for c in classes]
        present = [c for c in cols if c in pred.columns]
        if not present:
            probs[h] = None
            continue
        if len(present) != len(cols):
            fail(f"head {h}: partial probability columns; have {present}, need all of {cols}")
        try:
            P = pred[cols].apply(pd.to_numeric, errors="raise").to_numpy(dtype=float)
        except (ValueError, TypeError) as e:
            fail(f"head {h}: non-numeric probability ({e})")
        if np.isnan(P).any() or (P < 0).any():
            fail(f"head {h}: blank or negative probabilities")
        s = P.sum(axis=1)
        off = np.abs(s - 1) > PROB_TOL
        if off.any():
            i = int(np.argmax(off))
            fail(f"head {h}: {int(off.sum())} rows whose probabilities do not sum to 1 "
                 f"(e.g. uid {pred.index[i]} sums to {s[i]:.4f}; tolerance {PROB_TOL})")
        probs[h] = P / s[:, None]
    return pred, probs, n_extra


# ------------------------------------------------------------------ scoring
def block(y_true: list[str], y_pred: list[str], classes: list[str], n_boot: int,
          with_detail: bool = True) -> dict:
    out = {"n": len(y_true),
           "macro_f1": M.macro_f1(y_true, y_pred, classes) if y_true else float("nan"),
           "macro_f1_ci": list(M.bootstrap_macro_f1_ci(y_true, y_pred, classes, n_boot)),
           "accuracy": M.accuracy(y_true, y_pred)}
    if with_detail:
        out["per_class"] = M.per_class(y_true, y_pred, classes) if y_true else {}
        out["confusion"] = {"classes": classes,
                            "rows_truth_cols_pred": M.confusion(y_true, y_pred, classes).tolist()}
    return out


def score_head(gold: pd.DataFrame, pred: pd.DataFrame, h: str, n_boot: int) -> dict:
    classes = M.HEADS[h]
    lab = gold[h].tolist()
    alt = gold[f"{h}_alt"].tolist()
    strict = (gold[f"{h}_strict"].str.lower() == "true").tolist()
    yp = pred.loc[gold["email_uid"], f"pred_{h}"].tolist()

    s_idx = [i for i in range(len(lab)) if strict[i] and lab[i]]
    l_idx = [i for i in range(len(lab)) if lab[i]]
    yt_s, yp_s = [lab[i] for i in s_idx], [yp[i] for i in s_idx]
    yp_l = [yp[i] for i in l_idx]
    yt_l = M.lenient_truth([lab[i] for i in l_idx], [alt[i] for i in l_idx], yp_l)

    res = {
        "rows": {"total": len(lab), "blank_label": len(lab) - len(l_idx),
                 "strict": len(s_idx), "non_strict_labelled": len(l_idx) - len(s_idx),
                 "with_alt": sum(1 for i in l_idx if alt[i])},
        "strict": block(yt_s, yp_s, classes, n_boot),
        "lenient": block(yt_l, yp_l, classes, n_boot, with_detail=False),
        "_strict_idx": s_idx,
    }
    return res


def score_view(head_res: dict, gold: pd.DataFrame, pred: pd.DataFrame, view: str, n_boot: int) -> dict:
    h, _, classes = M.VIEWS[view]
    idx = head_res["_strict_idx"]
    lab = gold[h].tolist()
    yp = pred.loc[gold["email_uid"], f"pred_{h}"].tolist()
    yt = M.to_view([lab[i] for i in idx], view)
    pv = M.to_view([yp[i] for i in idx], view)
    return {"head": h, "strict": block(yt, pv, classes, n_boot)}


def calibration(gold: pd.DataFrame, pred: pd.DataFrame, P: np.ndarray, h: str, strict_idx: list[int]) -> dict:
    classes = M.HEADS[h]
    rows = pred.index.get_indexer(gold["email_uid"])
    P = P[rows]
    conf_all = P.max(axis=1)
    argmax = [classes[j] for j in P.argmax(axis=1)]
    yp = pred.loc[gold["email_uid"], f"pred_{h}"].tolist()
    lab = gold[h].tolist()
    conf_s = conf_all[strict_idx]
    correct_s = [yp[i] == lab[i] for i in strict_idx]
    e_w, bins_w = M.ece(conf_s, correct_s, 10, "width")
    e_c, bins_c = M.ece(conf_s, correct_s, 10, "count")
    return {"n_ece": len(strict_idx), "ece_width10": e_w, "ece_count10": e_c,
            "bins_width10": bins_w, "bins_count10": bins_c,
            "review_rate": M.review_rate(conf_all), "review_threshold": M.REVIEW_THRESHOLD,
            "n_review_rows": len(conf_all), "_conf_all": conf_all,
            "pred_differs_from_argmax": int(sum(a != b for a, b in zip(argmax, yp)))}


# ------------------------------------------------------------------ report
def f3(x) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def ci(c) -> str:
    return f"{f3(c[0])}–{f3(c[1])}"


def build_report(m: dict) -> str:
    L = [f"# Score report — {m['config']['created']}", "",
         f"- gold: `{m['inputs']['gold']['path']}` (sha256 {m['inputs']['gold']['sha256'][:16]}…)",
         f"- pred: `{m['inputs']['pred']['path']}` (sha256 {m['inputs']['pred']['sha256'][:16]}…)",
         f"- rows scored: {m['n_rows']} (excluded {m['n_excluded']}; prediction rows ignored as not in gold: "
         f"{m['n_pred_extra']})", f"- bootstrap: {m['config']['n_boot']} resamples, seed {M.SEED}", ""]

    names = list(M.HEADS) + list(M.VIEWS)
    L += ["## Summary (strict macro-F1)", "",
          "| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |",
          "|---|---|---|---|---|---|---|---|"]
    for k in names:
        r = m["heads"][k] if k in M.HEADS else m["views"][k]
        s = r["strict"]
        len_ = f3(r["lenient"]["macro_f1"]) if "lenient" in r else "–"
        g = m.get("gate", {}).get(k)
        gate_s, res_s = (f3(g["gate"]), "**PASS**" if g["pass"] else "FAIL") if g else ("–", "–")
        L.append(f"| {k} | {s['n']} | **{f3(s['macro_f1'])}** | {ci(s['macro_f1_ci'])} | {len_} | "
                 f"{f3(s['accuracy'])} | {gate_s} | {res_s} |")
    L.append("")

    for h in M.HEADS:
        r = m["heads"][h]
        L += [f"## {h}", "",
              f"Rows: {r['rows']['strict']} strict, {r['rows']['non_strict_labelled']} non-strict labelled, "
              f"{r['rows']['blank_label']} blank, {r['rows']['with_alt']} with an alt label.", "",
              "| Class | Precision | Recall | F1 | Support | Predicted |", "|---|---|---|---|---|---|"]
        for c, v in r["strict"]["per_class"].items():
            L.append(f"| {c} | {f3(v['precision'])} | {f3(v['recall'])} | {f3(v['f1'])} | "
                     f"{v['support']} | {v['predicted']} |")
        cm = r["strict"]["confusion"]
        L += ["", "Confusion (rows = gold, columns = predicted):", "",
              "| gold \\ pred | " + " | ".join(cm["classes"]) + " |",
              "|---" * (len(cm["classes"]) + 1) + "|"]
        for c, row in zip(cm["classes"], cm["rows_truth_cols_pred"]):
            L.append(f"| {c} | " + " | ".join(str(x) for x in row) + " |")
        cal = m.get("calibration", {}).get(h)
        if cal:
            L += ["", f"**Calibration** (strict rows, n={cal['n_ece']}): ECE equal-width-10 = "
                      f"**{f3(cal['ece_width10'])}**, equal-count-10 = {f3(cal['ece_count10'])}. "
                      f"Review rate (top prob < {cal['review_threshold']}) = {cal['review_rate']:.1%} "
                      f"of {cal['n_review_rows']} rows. Pred ≠ argmax on {cal['pred_differs_from_argmax']} rows.",
                  "", "| Bin | n | Mean conf | Accuracy |", "|---|---|---|---|"]
            for b in cal["bins_width10"]:
                L.append(f"| {b['lo']:.1f}–{b['hi']:.1f} | {b['n']} | {f3(b['mean_conf'])} | {f3(b['accuracy'])} |")
        L.append("")
    if "review_rate_any_head" in m:
        L += [f"**Any-head review rate** (an email is reviewed if any head is below "
              f"{M.REVIEW_THRESHOLD}): {m['review_rate_any_head']:.1%}", ""]
    return "\n".join(L) + "\n"


def jsonable(o):
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, float) and math.isnan(o):
        return None
    if isinstance(o, (np.floating, np.integer)):
        return jsonable(o.item())
    return o


# ------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", required=True, type=Path)
    ap.add_argument("--pred", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--exclude-uids", type=Path, help="text file, one email_uid per line ('#' comments ok)")
    ap.add_argument("--n-boot", type=int, default=2000)
    a = ap.parse_args(argv)

    gold = read_text_csv(a.gold)
    validate_gold(gold)
    n_excluded = 0
    if a.exclude_uids:
        ex = {ln.strip() for ln in a.exclude_uids.read_text(encoding="utf-8").splitlines()
              if ln.strip() and not ln.strip().startswith("#")}
        unknown = ex - set(gold["email_uid"])
        if unknown:
            print(f"note: {len(unknown)} excluded uids are not in this gold file (ignored)")
        n_excluded = int(gold["email_uid"].isin(ex).sum())
        gold = gold[~gold["email_uid"].isin(ex)].reset_index(drop=True)
    if gold.empty:
        fail("no gold rows left to score")

    pred, probs, n_extra = validate_pred(read_text_csv(a.pred), set(gold["email_uid"]))

    inputs = {"gold": {"path": str(a.gold), "sha256": sha256(a.gold)},
              "pred": {"path": str(a.pred), "sha256": sha256(a.pred)}}
    if a.baseline:
        inputs["baseline"] = {"path": str(a.baseline), "sha256": sha256(a.baseline)}
    if a.exclude_uids:
        inputs["exclude_uids"] = {"path": str(a.exclude_uids), "sha256": sha256(a.exclude_uids)}

    m = {"config": {"created": datetime.now().isoformat(timespec="seconds"), "n_boot": a.n_boot,
                    "seed": M.SEED, "prob_tolerance": PROB_TOL, "argv": sys.argv[1:] if argv is None else argv},
         "inputs": inputs, "n_rows": len(gold), "n_excluded": n_excluded, "n_pred_extra": n_extra,
         "heads": {}, "views": {}}
    for h in M.HEADS:
        m["heads"][h] = score_head(gold, pred, h, a.n_boot)
    for v in M.VIEWS:
        m["views"][v] = score_view(m["heads"][M.VIEWS[v][0]], gold, pred, v, a.n_boot)

    if any(P is not None for P in probs.values()):
        m["calibration"] = {h: calibration(gold, pred, P, h, m["heads"][h]["_strict_idx"])
                            for h, P in probs.items() if P is not None}
        if all(P is not None for P in probs.values()):
            conf = np.vstack([m["calibration"][h]["_conf_all"] for h in M.HEADS])
            m["review_rate_any_head"] = float(np.mean((conf < M.REVIEW_THRESHOLD).any(axis=0)))

    if a.baseline:
        base = json.loads(a.baseline.read_text(encoding="utf-8"))
        gates, human = base["teacher_gate_macro_f1"], base["results"]
        m["gate"] = {}
        for k, g in gates.items():
            r = m["heads"][k] if k in M.HEADS else m["views"][k]
            v = r["strict"]["macro_f1"]
            m["gate"][k] = {"gate": g, "human_macro_f1": human[k]["macro_f1"], "model": v,
                            "pass": bool(v == v and v >= g)}

    a.out.mkdir(parents=True, exist_ok=True)
    clean = jsonable(m)
    (a.out / "metrics.json").write_text(json.dumps(clean, indent=2), encoding="utf-8")
    (a.out / "report.md").write_text(build_report(clean), encoding="utf-8")

    print(f"scored {len(gold)} rows ({n_excluded} excluded, {n_extra} extra prediction rows ignored)")
    for k in list(M.HEADS) + list(M.VIEWS):
        r = clean["heads"][k] if k in M.HEADS else clean["views"][k]
        s = r["strict"]
        line = f"  {k:<12} strict {f3(s['macro_f1'])} [{ci(s['macro_f1_ci'])}] n={s['n']}"
        if "lenient" in r:
            line += f"  lenient {f3(r['lenient']['macro_f1'])}"
        if "gate" in clean:
            g = clean["gate"][k]
            line += f"  gate {f3(g['gate'])} {'PASS' if g['pass'] else 'FAIL'}"
        if k in clean.get("calibration", {}):
            c = clean["calibration"][k]
            line += f"  ECE {f3(c['ece_width10'])} review {c['review_rate']:.0%}"
        print(line)
    print(f"wrote {a.out / 'metrics.json'} and {a.out / 'report.md'}")
    return clean


if __name__ == "__main__":
    main()
