#!/usr/bin/env python3
"""
predict.py — Phase C4. Model folder + CSV (with C2 embeddings) -> predictions.csv (I4).

Run from ML_Training:
    python scripts\\predict.py --csv Data\\gold_final\\gold_dev.csv --emb Data\\emb\\gold_dev --mode balanced --out runs\\<date>-predict-dev\\balanced
    python scripts\\predict.py --csv Data\\gold_final\\gold_dev.csv --emb Data\\emb\\gold_dev --mode prior    --out runs\\<date>-predict-dev\\prior
    python scripts\\predict.py --latency 50          # CPU latency of predict_one (embed + heads), median / p95

The heads run in numpy only (common/student.py). numpy == scikit-learn parity is proven at
training time (train_heads.py, <= 1e-6) and recorded in the run's metrics.json.
Writes <out>/predictions.csv (email_uid, pred_<head>, prob_<head>_<Class>) and <out>/predict.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import student as S  # noqa: E402


def batch_predict(model_dir: Path, csv: Path, emb_prefix: Path, mode: str, out: Path) -> None:
    manifest, heads = S.load_model(model_dir)
    mode = mode or manifest.get("default_mode", "balanced")
    df = pd.read_csv(csv, dtype=str, keep_default_na=False)
    for c in ("email_uid", "recipient_role", "recipient_position"):
        if c not in df.columns:
            sys.exit(f"ERROR: {csv} has no column {c}")
    E, uids = S.load_embeddings(emb_prefix)
    E = S.align(E, uids, df["email_uid"].tolist(), str(csv))
    X, unseen = S.build_features(E, df["recipient_role"], df["recipient_position"],
                                 manifest["roles"], manifest["positions"])
    if unseen["role"] or unseen["position"]:
        print(f"note: unseen categories mapped to fallback: {unseen}")
    P = S.predict_proba(manifest, heads, X, mode)

    pred = pd.DataFrame({"email_uid": df["email_uid"]})
    for h, classes in manifest["classes"].items():
        pred[f"pred_{h}"] = [classes[j] for j in P[h].argmax(1)]
        for j, c in enumerate(classes):
            pred[f"prob_{h}_{c}"] = P[h][:, j]
    out.mkdir(parents=True, exist_ok=True)
    pred.to_csv(out / "predictions.csv", index=False, float_format="%.8f")
    conf = np.vstack([P[h].max(1) for h in manifest["classes"]])
    thr = manifest.get("review_threshold", 0.60)
    info = {"created": datetime.now().isoformat(timespec="seconds"), "model": str(model_dir), "mode": mode,
            "head_modes": S.head_modes(manifest, mode),
            "csv": str(csv), "rows": len(df), "unseen": unseen,
            "review_rate": {h: float((P[h].max(1) < thr).mean()) for h in manifest["classes"]},
            "review_rate_any_head": float((conf < thr).any(0).mean()),
            "pred_counts": {h: pred[f"pred_{h}"].value_counts().to_dict() for h in manifest["classes"]}}
    (out / "predict.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"{mode}: {len(df)} rows -> {out / 'predictions.csv'}")
    print("  review rate " + "  ".join(f"{h} {v:.0%}" for h, v in info["review_rate"].items())
          + f"  any-head {info['review_rate_any_head']:.0%}")
    for h, vc in info["pred_counts"].items():
        print(f"  predicted {h}: {vc}")


def latency(model_dir: Path, csv: Path, n: int, mode: str) -> None:
    import os
    import platform
    df = pd.read_csv(csv, dtype=str, keep_default_na=False).sample(n, random_state=42)
    t0 = time.perf_counter()
    st = S.Student(model_dir, mode=mode, device="cpu")
    load_s = time.perf_counter() - t0
    rows = list(df[["input_text", "recipient_role", "recipient_position"]].itertuples(index=False))
    for r in rows[:3]:                                   # warm-up, not timed
        st.predict_one(*r)
    ms = []
    for r in rows:
        t = time.perf_counter()
        res = st.predict_one(*r)
        ms.append((time.perf_counter() - t) * 1000)
    ms = np.array(ms)
    out = {"n": n, "median_ms": float(np.median(ms)), "p95_ms": float(np.percentile(ms, 95)),
           "max_ms": float(ms.max()), "model_load_s": round(load_s, 1), "target_ms": 350,
           "cpu": platform.processor() or platform.machine(), "threads": os.cpu_count(), "example": res}
    print(f"predict_one on CPU over {n} emails: median {out['median_ms']:.0f} ms, p95 {out['p95_ms']:.0f} ms, "
          f"max {out['max_ms']:.0f} ms (target < 350 ms); model load {load_s:.1f}s")
    print("example output:", json.dumps(res, indent=1)[:600])
    run = ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-latency"
    run.mkdir(parents=True, exist_ok=True)
    (run / "latency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {run / 'latency.json'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "model_v1")
    ap.add_argument("--csv", type=Path, default=ROOT / "Data" / "gold_final" / "gold_dev.csv")
    ap.add_argument("--emb", type=Path, default=ROOT / "Data" / "emb" / "gold_dev")
    ap.add_argument("--mode", choices=S.MODES, default=None,
                    help="balanced | prior | mixed (default: the model's default_mode from manifest.json)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--latency", type=int, metavar="N", help="time predict_one on N emails from --csv instead")
    a = ap.parse_args()
    if "gold_test" in a.csv.name:
        sys.exit("ERROR: gold_test is sealed until C5 (use the C5 procedure)")
    if a.latency:
        latency(a.model, a.csv, a.latency, a.mode)
    else:
        if not a.out:
            sys.exit("ERROR: --out is required")
        batch_predict(a.model, a.csv, a.emb, a.mode, a.out)


if __name__ == "__main__":
    main()
