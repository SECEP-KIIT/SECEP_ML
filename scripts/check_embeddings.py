#!/usr/bin/env python3
"""
check_embeddings.py — Phase C2, step 3 (local). Verifies the embeddings downloaded from Kaggle.

Run from ML_Training (after extracting emb.zip so the files sit in Data\\emb\\):
    python scripts\\check_embeddings.py                 # structure checks only
    python scripts\\check_embeddings.py --parity 20     # + re-embed 20 gold_dev emails on this CPU

Checks, per file in Data\\emb_inputs\\:
    - the input CSV hash matches what Kaggle embedded (same text went in)
    - uids file == CSV uid order; .npy shape (rows, 768), float32, finite, unit norm
    - --parity N: GPU vectors vs local CPU vectors, cosine >= 0.999 (the live system embeds on CPU)
Writes runs\\<date>-embed-check\\embed_check.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from embed import MAX_TOKENS, MODEL, SEED, sha256  # noqa: E402

IN, EMB = ROOT / "Data" / "emb_inputs", ROOT / "Data" / "emb"
PARITY_MIN_COS = 0.999


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parity", type=int, default=0, metavar="N")
    a = ap.parse_args()
    report, ok = {"files": {}}, True

    for csv in sorted(IN.glob("*.csv")):
        name = csv.stem
        r = {}
        try:
            meta = json.loads((EMB / f"{name}_emb.json").read_text())
            E = np.load(EMB / f"{name}_emb.npy")
            uids = (EMB / f"{name}_uids.txt").read_text(encoding="utf-8").splitlines()
            df = pd.read_csv(csv, dtype=str, keep_default_na=False)
            norms = np.linalg.norm(E, axis=1)
            r = {"rows": len(df), "shape": list(E.shape), "dtype": str(E.dtype),
                 "same_input": meta["input_sha256"] == sha256(csv),
                 "uid_order_ok": uids == df["uid"].tolist(),
                 "finite": bool(np.isfinite(E).all()),
                 "max_norm_err": float(np.abs(norms - 1).max()),
                 "model_ok": meta["model"] == MODEL and meta["max_seq_length"] == MAX_TOKENS,
                 "truncated_rows": meta["truncated_rows"], "device": meta.get("gpu") or meta["device"]}
            r["pass"] = (r["same_input"] and r["uid_order_ok"] and r["finite"] and r["model_ok"]
                         and r["shape"] == [len(df), 768] and r["dtype"] == "float32" and r["max_norm_err"] < 1e-3)
        except FileNotFoundError as e:
            r = {"pass": False, "error": f"missing {Path(e.filename).name}"}
        ok &= r["pass"]
        report["files"][name] = r
        print(f"{name:<11} {'PASS' if r['pass'] else 'FAIL'}  " +
              ("  ".join(f"{k}={v}" for k, v in r.items() if k != "pass")))

    if a.parity:
        from embed import encode, load_model
        df = pd.read_csv(IN / "gold_dev.csv", dtype=str, keep_default_na=False)
        idx = np.random.default_rng(SEED).choice(len(df), min(a.parity, len(df)), replace=False)
        model, dev = load_model("cpu")
        local = encode(model, df["input_text"].iloc[idx].tolist(), batch=8, progress=False)
        cos = (np.load(EMB / "gold_dev_emb.npy")[idx] * local).sum(axis=1)
        p = {"n": len(idx), "min_cos": float(cos.min()), "mean_cos": float(cos.mean()),
             "pass": bool(cos.min() >= PARITY_MIN_COS)}
        ok &= p["pass"]
        report["cpu_parity"] = p
        print(f"CPU parity  {'PASS' if p['pass'] else 'FAIL'}  n={p['n']} min cos={p['min_cos']:.6f} "
              f"(need >= {PARITY_MIN_COS})")

    out = ROOT / "runs" / f"{date.today()}-embed-check"
    out.mkdir(parents=True, exist_ok=True)
    report["all_pass"] = bool(ok)
    (out / "embed_check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n{'ALL PASS' if ok else 'SOMETHING FAILED'} -> {out / 'embed_check.json'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
