#!/usr/bin/env python3
"""
check_triage_parity.py — Phase D1, step 2. Does secep_ml.triage give the same answers as Phase C?

Part A (the D1 gate): stored gold-dev embeddings -> secep_ml.triage heads path, compared with
    scripts/predict.py's predictions.csv for the same model and mode. Pass = max |diff| <= 1e-6, labels 100% equal.
Part B (report only): re-embed gold-dev on this CPU with the package's encoder and compare against the stored
    Kaggle (GPU) embeddings: cosine, label agreement, probability drift. GPU and CPU floats differ in the last
    digits, so this is not held to 1e-6; it shows whether serving on a laptop changes decisions.

Run from ML_Training:
    python scripts\\check_triage_parity.py                 # A + B (B loads mpnet: ~25 s load + ~1 min embed)
    python scripts\\check_triage_parity.py --no-reembed    # A only, seconds

Writes runs\\<date>-d1-parity\\{config.json, metrics.json, report.md} and reference\\predictions.csv.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
from secep_ml import triage as TR  # noqa: E402

TOL = 1e-6


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_predict_module():
    spec = importlib.util.spec_from_file_location("phase_c_predict", ROOT / "scripts" / "predict.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stub_embed(texts):  # test-only stand-in for mpnet (used with --stub-encoder)
    out = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:8], "little")
        v = np.random.default_rng(seed).standard_normal(768)
        out.append(v / np.linalg.norm(v))
    return np.asarray(out, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "model_v1")
    ap.add_argument("--csv", type=Path, default=ROOT / "Data" / "gold_final" / "gold_dev.csv")
    ap.add_argument("--emb", type=Path, default=ROOT / "Data" / "emb" / "gold_dev")
    ap.add_argument("--emb-inputs", type=Path, default=ROOT / "Data" / "emb_inputs" / "gold_dev.csv",
                    help="the exact CSV that was embedded on Kaggle (its input_text is re-embedded in part B)")
    ap.add_argument("--no-reembed", action="store_true", help="skip part B (no encoder load)")
    ap.add_argument("--stub-encoder", action="store_true", help=argparse.SUPPRESS)  # tests only
    ap.add_argument("--out", type=Path, default=ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-d1-parity")
    a = ap.parse_args()

    for p in (a.csv, a.emb_inputs):
        if "gold_test" in p.name.lower() or "sealed" in [x.lower() for x in p.parts]:
            sys.exit("ERROR: gold-test is locked; parity runs on gold-dev only")
    a.out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(a.csv, dtype=str, keep_default_na=False)
    E_all, emb_uids = S.load_embeddings(a.emb)
    E = S.align(E_all, emb_uids, df["email_uid"].tolist(), str(a.csv))
    roles, positions = df["recipient_role"].tolist(), df["recipient_position"].tolist()

    # ---------------- Part A: package heads vs predict.py
    pred_mod = load_predict_module()
    ref_dir = a.out / "reference"
    pred_mod.batch_predict(a.model, a.csv, a.emb, None, ref_dir)       # mode None -> manifest default (mixed)
    ref = pd.read_csv(ref_dir / "predictions.csv", dtype={"email_uid": str})
    if ref["email_uid"].tolist() != df["email_uid"].tolist():
        sys.exit("ERROR: predict.py output order differs from the CSV")

    tri = TR.load(a.model, embed_fn=stub_embed if (a.stub_encoder or a.no_reembed) else None)
    P, unseen = tri.probs_from_embeddings(E, roles, positions)
    manifest, heads = S.load_model(a.model)
    X, _ = S.build_features(E, roles, positions, manifest["roles"], manifest["positions"])
    Q = S.predict_proba(manifest, heads, X, tri.mode)                 # same call predict.py makes, unrounded

    part_a = {"rows": len(df), "mode": tri.mode, "head_modes": tri.head_modes, "unseen": unseen, "heads": {}}
    ok_a = True
    for h, classes in manifest["classes"].items():
        R = ref[[f"prob_{h}_{c}" for c in classes]].to_numpy(float)
        d_csv = float(np.abs(P[h] - R).max())                         # vs predictions.csv (8-decimal file)
        d_mem = float(np.abs(P[h] - Q[h]).max())                      # vs predict.py's code path in memory
        lab = float((np.array(classes)[P[h].argmax(1)] == ref[f"pred_{h}"].to_numpy()).mean())
        passed = d_csv <= TOL and d_mem <= TOL and lab == 1.0
        ok_a &= passed
        part_a["heads"][h] = {"max_abs_diff_vs_csv": d_csv, "max_abs_diff_vs_code": d_mem,
                              "label_agreement": lab, "pass": passed}
    part_a["pass"] = ok_a

    # ---------------- Part B: CPU re-embedding vs stored Kaggle embeddings
    part_b = None
    if not a.no_reembed:
        src = a.emb_inputs if a.emb_inputs.exists() else a.csv
        tx = pd.read_csv(src, dtype=str, keep_default_na=False)
        if "input_text" not in tx.columns or "email_uid" not in tx.columns:
            src, tx = a.csv, df
        tx = tx.set_index("email_uid").loc[df["email_uid"]]
        t0 = time.perf_counter()
        E_cpu = tri.embed(tx["input_text"].tolist())
        embed_s = time.perf_counter() - t0
        cos = (E_cpu.astype(np.float64) * E.astype(np.float64)).sum(1) / (
            np.linalg.norm(E_cpu, axis=1) * np.linalg.norm(E, axis=1))
        P_cpu, _ = tri.probs_from_embeddings(E_cpu, roles, positions)
        part_b = {"text_source": str(src.relative_to(ROOT) if src.is_relative_to(ROOT) else src),
                  "embed_seconds": round(embed_s, 1),
                  "cosine": {"min": float(cos.min()), "median": float(np.median(cos)),
                             "rows_below_0.999": int((cos < 0.999).sum())},
                  "max_abs_emb_diff": float(np.abs(E_cpu - E).max()), "heads": {}}
        for h, classes in manifest["classes"].items():
            same = P_cpu[h].argmax(1) == P[h].argmax(1)
            thr = tri.threshold
            flip_review = (P_cpu[h].max(1) < thr) != (P[h].max(1) < thr)
            part_b["heads"][h] = {"label_agreement": float(same.mean()), "labels_changed": int((~same).sum()),
                                  "review_flag_changed": int(flip_review.sum()),
                                  "max_prob_diff": float(np.abs(P_cpu[h] - P[h]).max())}
        worst = min(v["label_agreement"] for v in part_b["heads"].values())
        part_b["verdict"] = ("ok" if part_b["cosine"]["min"] >= 0.999 and worst >= 0.98 else
                             "investigate: CPU embeddings drift from the stored ones (check text source / settings)")

    # ---------------- write run
    metrics = {"part_a_gate": part_a, "part_b_reembed": part_b}
    config = {"created": datetime.now().isoformat(timespec="seconds"), "script": "scripts/check_triage_parity.py",
              "tolerance": TOL, "model": str(a.model), "model_version": tri.model_version,
              "manifest_sha256": tri.manifest_sha256, "text_version": tri.text_version, "seed": 42,
              "stub_encoder": bool(a.stub_encoder),
              "inputs_sha256": {"csv": sha256(a.csv), "emb_npy": sha256(Path(f"{a.emb}_emb.npy")),
                                "emb_uids": sha256(Path(f"{a.emb}_uids.txt"))}}
    (a.out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (a.out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    lines = [f"# D1 parity — {config['created']}", "",
             f"Model `{tri.model_version}` (manifest `{tri.manifest_sha256[:12]}…`), mode `{tri.mode}` "
             f"{tri.head_modes}, gold-dev {len(df)} rows.", "",
             "## A. Package vs predict.py (gate: max |diff| ≤ 1e-6, labels 100%)", "",
             "| head | max diff vs predictions.csv | max diff vs code | label agreement | pass |", "|---|---|---|---|---|"]
    for h, v in part_a["heads"].items():
        lines.append(f"| {h} | {v['max_abs_diff_vs_csv']:.2e} | {v['max_abs_diff_vs_code']:.2e} | "
                     f"{v['label_agreement']:.1%} | {'✓' if v['pass'] else '✗'} |")
    lines += ["", f"**Part A: {'PASS' if ok_a else 'FAIL'}**", ""]
    if part_b:
        c = part_b["cosine"]
        lines += ["## B. CPU re-embedding vs stored Kaggle embeddings (report only)", "",
                  f"Text from `{part_b['text_source']}`; embedded in {part_b['embed_seconds']} s. "
                  f"Cosine min {c['min']:.6f}, median {c['median']:.6f}, rows < 0.999: {c['rows_below_0.999']}. "
                  f"Max element diff {part_b['max_abs_emb_diff']:.2e}.", "",
                  "| head | label agreement | labels changed | review flag changed | max prob diff |",
                  "|---|---|---|---|---|"]
        for h, v in part_b["heads"].items():
            lines.append(f"| {h} | {v['label_agreement']:.1%} | {v['labels_changed']} | "
                         f"{v['review_flag_changed']} | {v['max_prob_diff']:.2e} |")
        lines += ["", f"Verdict: **{part_b['verdict']}**"]
    if a.stub_encoder:
        lines += ["", "_Stub encoder: test run, part B numbers are meaningless._"]
    (a.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nwrote {a.out}")
    sys.exit(0 if ok_a else 1)


if __name__ == "__main__":
    main()
