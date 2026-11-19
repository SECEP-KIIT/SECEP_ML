#!/usr/bin/env python3
"""
ablate.py — ablation table for the model card (SRS NFR-ML-007). Gold-dev only.

Run from ML_Training, after set_head_modes.py (uses model_v1's per-head C and head_mode):
    python scripts\\ablate.py

Each variant switches one thing off, retrains the three heads on the full teacher pool with the
SAME C as model_v1 (no new grid search, so differences come from the switch alone), refits the
temperature on gold-calib, and scores on gold-dev:
    full               the shipped recipe, re-run (should reproduce the C4 gold-dev numbers)
    embedding_only     no role / position one-hots
    no_class_balance   class weight 1 (teacher weight kept). Prior correction does not apply
                       (nothing to undo), so every head uses plain softmax(logits / T)
    no_teacher_weight  teacher weight 1 for every labelled row (class balance kept)
    no_temperature     the full model with T = 1 everywhere (no retrain)
Writes runs\\<date>-ablation\\ablation.json + ablation.md.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import metrics as M  # noqa: E402
from common import student as S  # noqa: E402
from train_heads import balanced_weights, fit_lr, fit_temperature  # noqa: E402

D = ROOT / "Data"
VARIANTS = ["full", "embedding_only", "no_class_balance", "no_teacher_weight", "no_temperature"]


def main() -> None:
    t_all = time.time()
    manifest, _ = S.load_model(ROOT / "model_v1")
    head_mode = S.head_modes(manifest, manifest.get("default_mode", "balanced"))
    C = manifest["C"]
    roles, positions = manifest["roles"], manifest["positions"]
    thr = manifest.get("review_threshold", 0.60)

    tr = pd.read_csv(D / "pseudo" / "pseudo_train.csv", dtype=str, keep_default_na=False)
    cal = pd.read_csv(D / "gold_final" / "gold_calib.csv", dtype=str, keep_default_na=False)
    dev = pd.read_csv(D / "gold_final" / "gold_dev.csv", dtype=str, keep_default_na=False)

    def feats(df, prefix):
        E, u = S.load_embeddings(D / "emb" / prefix)
        E = S.align(E, u, df["email_uid"].tolist(), prefix)
        X, _ = S.build_features(E, df["recipient_role"], df["recipient_position"], roles, positions)
        return X

    X_tr, X_cal, X_dev = feats(tr, "pool"), feats(cal, "gold_calib"), feats(dev, "gold_dev")
    n_emb = S.EMB_DIM

    results = {}
    for v in VARIANTS:
        t0 = time.time()
        cols = slice(0, n_emb) if v == "embedding_only" else slice(None)
        preds, conf = {}, {}
        for h, classes in M.HEADS.items():
            w_t = pd.to_numeric(tr[f"weight_{h}"], errors="coerce").fillna(0).to_numpy()
            keep = (tr[h] != "").to_numpy() & (w_t > 0)
            y = tr.loc[keep, h].to_numpy()
            tw = np.ones(keep.sum()) if v == "no_teacher_weight" else w_t[keep]
            if v == "no_class_balance":
                w = tw.copy()
            else:
                cw = balanced_weights(y, classes)
                w = np.array([cw[c] for c in y]) * tw
            w = w / w.mean()

            if v == "no_temperature":       # reuse the full model's W, b
                W = np.load(ROOT / "model_v1" / "heads.npz")[f"W_{h}"]
                b = np.load(ROOT / "model_v1" / "heads.npz")[f"b_{h}"]
            else:
                clf = fit_lr(X_tr[keep][:, cols], y, w, C[h])
                order = [list(clf.classes_).index(c) for c in classes]
                W, b = clf.coef_[order], clf.intercept_[order]

            mode = "balanced" if v == "no_class_balance" else head_mode[h]
            prior = np.array([w_t[keep][y == c].sum() for c in classes])
            prior = prior / prior.sum()
            shift = np.log(prior) if mode == "prior" else 0.0

            cs = ((cal[f"{h}_strict"].str.lower() == "true") & (cal[h] != "")).to_numpy()
            yc_idx = np.array([classes.index(x) for x in cal.loc[cs, h]])
            zc = S.logits(X_cal[cs][:, cols], W, b) + shift
            T = 1.0 if v == "no_temperature" else fit_temperature(zc, yc_idx)[0]

            P = S.softmax((S.logits(X_dev[:, cols], W, b) + shift) / T)
            preds[h] = [classes[j] for j in P.argmax(1)]
            conf[h] = P.max(1)

        row = {"seconds": round(time.time() - t0, 1)}
        for h, classes in M.HEADS.items():
            s = ((dev[f"{h}_strict"].str.lower() == "true") & (dev[h] != "")).to_numpy()
            yt = dev.loc[s, h].tolist()
            yp = [p for p, k in zip(preds[h], s) if k]
            row[h] = M.macro_f1(yt, yp, classes)
            correct = [a == b_ for a, b_ in zip(yp, yt)]
            row[f"ece_{h}"] = M.ece(conf[h][s], correct, 10, "width")[0]
            row[f"review_{h}"] = M.review_rate(conf[h])
            for view, (vh, _, vcls) in M.VIEWS.items():
                if vh == h:
                    row[view] = M.macro_f1(M.to_view(yt, view), M.to_view(yp, view), vcls)
        row["review_any"] = float((np.vstack([conf[h] for h in M.HEADS]) < thr).any(0).mean())
        results[v] = row
        print(f"{v:<18} type {row['type']:.3f}  urgency {row['urgency']:.3f}  sentiment {row['sentiment']:.3f}  "
              f"ECE {row['ece_type']:.3f}/{row['ece_urgency']:.3f}/{row['ece_sentiment']:.3f}  "
              f"review any {row['review_any']:.0%}  ({row['seconds']:.0f}s)")

    run = ROOT / "runs" / f"{date.today()}-ablation"
    run.mkdir(parents=True, exist_ok=True)
    out = {"created": datetime.now().isoformat(timespec="seconds"), "split": "gold_dev (indicative)",
           "head_mode": head_mode, "C": C, "results": results}
    (run / "ablation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    f = results["full"]
    L = ["# Ablation (gold-dev, strict macro-F1; indicative)", "",
         f"Each row switches one thing off and retrains with the shipped C per head; Δ is against `full`. "
         f"Head modes: {head_mode}.", "",
         "| Variant | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 | ECE type | ECE urg. | ECE sent. | Review (any head) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for v, r in results.items():
        def c(k):
            d = "" if v == "full" else f" ({r[k] - f[k]:+.3f})"
            return f"{r[k]:.3f}{d}"
        L.append(f"| {v} | {c('type')} | {c('urgency')} | {c('sentiment')} | {c('type_action')} | {c('urgency_2')} | "
                 f"{c('sentiment_2')} | {r['ece_type']:.3f} | {r['ece_urgency']:.3f} | {r['ece_sentiment']:.3f} | "
                 f"{r['review_any']:.0%} |")
    L += ["", "gold-dev has 184 emails; differences under ~0.05 are within bootstrap noise (C4 CIs are ±0.1)."]
    (run / "ablation.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\nwrote {run / 'ablation.md'} ({time.time() - t_all:.0f}s total)")


if __name__ == "__main__":
    main()
