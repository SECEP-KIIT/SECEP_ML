#!/usr/bin/env python3
"""
infer.py — Phase D1, step 3. Raw email file(s) + recipient role/position -> triage.v1.1 JSON lines.

Run from ML_Training:
    # one file or a folder (every file inside, recursively), same role/position for all
    python scripts\\infer.py --file Data\\raw\\maildir\\wolfe-j\\06_saved\\82 --role ClientFacing --position To
    python scripts\\infer.py --folder Data\\raw\\maildir\\wolfe-j\\06_saved --role ClientFacing --position To --out x.jsonl

    # the D1 acceptance run: N pool emails (seed 42), role/position taken from the pool row
    python scripts\\infer.py --pool-sample 20

Pool mode also checks:
  * schema validity of every output (the package validates; failures are counted, not hidden);
  * train/serve text parity: re-processing the raw file must give the pool's stored input_text exactly;
  * determinism: every email is classified --repeats times; all outputs must be identical;
  * latency of classify() (process + embed + heads + validation) after load and 3 warm-ups: median, p95 (target <= 350 ms).
Writes runs\\<date>-d1-infer\\{predictions.jsonl, config.json, metrics.json, report.md}.
Never reads gold-test: sealed / gold_test paths are refused, and pool mode reads only the pool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from secep_ml import triage as TR  # noqa: E402

PINNED_TS = "2026-01-01T00:00:00.000Z"      # used only for the determinism comparison


def refuse_locked(p: Path) -> None:
    parts = [x.lower() for x in p.resolve().parts]
    if "sealed" in parts or any("gold_test" in x for x in parts):
        sys.exit(f"ERROR: {p} is gold-test / sealed data; inference refuses to read it")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stub_embed(texts):  # tests only (--stub-encoder)
    out = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:8], "little")
        v = np.random.default_rng(seed).standard_normal(768)
        out.append(v / np.linalg.norm(v))
    return np.asarray(out, dtype=np.float32)


def first_diff(a: str, b: str, ctx: int = 60) -> str:
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"at char {i}: pool={a[max(0, i - 10):i + ctx]!r} vs now={b[max(0, i - 10):i + ctx]!r}"


def run_files(tri, files, role, position, out_path):
    n_ok = n_err = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for p in files:
            try:
                r = tri.classify(p.read_bytes(), role, position)
                f.write(json.dumps({"source": str(p), "triage": r}) + "\n")
                n_ok += 1
            except Exception as e:  # one bad file never stops the batch
                f.write(json.dumps({"source": str(p), "error": f"{type(e).__name__}: {e}"}) + "\n")
                n_err += 1
    print(f"{n_ok} classified, {n_err} errors -> {out_path}")
    return n_err == 0


def run_pool(tri, a, run_dir: Path) -> bool:
    import pandas as pd
    pool = pd.read_parquet(a.pool, columns=["pool_uid", "slice", "source_path", "recipient_role",
                                            "recipient_position", "input_text"])
    rows = pool.sample(a.pool_sample, random_state=42).reset_index(drop=True)

    records, times, problems = [], [], []
    text_mismatch, nondet, invalid = [], [], 0
    loaded = []
    for r in rows.itertuples(index=False):
        path = Path(a.raw_root, *re.split(r"[\\/]", r.source_path))
        try:
            refuse_locked(path)
            loaded.append((r, path.read_bytes()))
        except (OSError, SystemExit) as e:
            problems.append({"pool_uid": r.pool_uid, "path": str(path), "error": str(e)})

    for r, raw in loaded[:3]:                                   # warm-up, not timed
        tri.classify(raw, r.recipient_role, r.recipient_position)

    for r, raw in loaded:
        outs = []
        for _ in range(a.repeats):
            t = time.perf_counter()
            try:
                res = tri.classify(raw, r.recipient_role, r.recipient_position, processed_at=PINNED_TS)
            except Exception as e:                                # includes jsonschema.ValidationError
                invalid += 1
                problems.append({"pool_uid": r.pool_uid, "error": f"{type(e).__name__}: {str(e)[:300]}"})
                break
            times.append((time.perf_counter() - t) * 1000)
            outs.append(res)
        if not outs:
            continue
        if any(o != outs[0] for o in outs[1:]):
            nondet.append(r.pool_uid)
        now_text = TR.Triage.prepare(raw)["input_text"]
        if now_text != r.input_text:
            text_mismatch.append({"pool_uid": r.pool_uid, "diff": first_diff(r.input_text, now_text)})
        res = outs[0]
        records.append({"pool_uid": r.pool_uid, "slice": r.slice, "source_path": r.source_path,
                        "role": r.recipient_role, "position": r.recipient_position, "triage": res})

    with open(run_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    ms = np.array(times) if times else np.array([np.nan])
    lat = {"n_timings": len(times), "median_ms": float(np.median(ms)), "p95_ms": float(np.percentile(ms, 95)),
           "max_ms": float(np.max(ms)), "target_p95_ms": 350,
           "cpu": platform.processor() or platform.machine(), "threads": os.cpu_count()}
    heads = ("type", "urgency", "sentiment")
    review = {h: float(np.mean([h in x["triage"]["review_heads"] for x in records])) if records else None
              for h in heads}
    gates = {
        "all_classified_valid": len(records) == a.pool_sample and invalid == 0 and not problems,
        "deterministic": not nondet,
        "text_parity": not text_mismatch,
        "p95_le_350ms": bool(lat["p95_ms"] <= 350),
    }
    metrics = {"requested": a.pool_sample, "classified": len(records), "invalid": invalid, "problems": problems,
               "nondeterministic": nondet, "text_mismatch": text_mismatch, "latency": lat,
               "review_rate": review, "review_rate_any_head": float(np.mean([x["triage"]["needs_review"]
                                                                              for x in records])) if records else None,
               "unseen": [x["triage"].get("unseen") for x in records if x["triage"].get("unseen")],
               "gates": gates, "pass": all(gates.values())}
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    L = [f"# D1 inference on pool sample — {datetime.now().isoformat(timespec='seconds')}", "",
         f"Model `{tri.model_version}` (manifest `{tri.manifest_sha256[:12]}…`), text recipe {tri.text_version}, "
         f"{a.pool_sample} pool emails (seed 42), {a.repeats} runs each.", "",
         "| check | result | pass |", "|---|---|---|",
         f"| classified + schema-valid | {len(records)}/{a.pool_sample}, invalid {invalid}, problems {len(problems)} "
         f"| {'✓' if gates['all_classified_valid'] else '✗'} |",
         f"| deterministic across {a.repeats} runs | {len(nondet)} differ | {'✓' if gates['deterministic'] else '✗'} |",
         f"| text parity with pool input_text | {len(text_mismatch)} mismatch | {'✓' if gates['text_parity'] else '✗'} |",
         f"| latency (classify, after load) | median {lat['median_ms']:.0f} ms, p95 {lat['p95_ms']:.0f} ms, "
         f"max {lat['max_ms']:.0f} ms over {lat['n_timings']} | {'✓' if gates['p95_le_350ms'] else '✗'} |", "",
         f"Model load {a._load_s:.1f} s. Review rate: " + ", ".join(f"{h} {v:.0%}" for h, v in review.items()
                                                                     if v is not None)
         + (f", any head {metrics['review_rate_any_head']:.0%}" if records else ""), "",
         f"**D1 pool run: {'PASS' if metrics['pass'] else 'FAIL'}**"]
    for t in text_mismatch[:5]:
        L.append(f"- text mismatch {t['pool_uid']}: {t['diff']}")
    for p in problems[:5]:
        L.append(f"- problem: {p}")
    if a.stub_encoder:
        L += ["", "_Stub encoder: test run, labels and latency are meaningless._"]
    (run_dir / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return metrics["pass"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "model_v1")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", type=Path)
    g.add_argument("--folder", type=Path)
    g.add_argument("--pool-sample", type=int, metavar="N")
    ap.add_argument("--role", help="recipient role (I1 or DB spelling) for --file/--folder")
    ap.add_argument("--position", help="To | Cc | Bcc (any case) for --file/--folder")
    ap.add_argument("--out", type=Path, help="JSON-lines output for --file/--folder (default: stdout for --file)")
    ap.add_argument("--pool", type=Path, default=ROOT / "Data" / "pool" / "pool.parquet")
    ap.add_argument("--raw-root", type=Path, default=ROOT / "Data" / "raw" / "maildir")
    ap.add_argument("--repeats", type=int, default=3, help="pool mode: runs per email (determinism + timing)")
    ap.add_argument("--run-dir", type=Path, default=ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-d1-infer")
    ap.add_argument("--stub-encoder", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    t0 = time.perf_counter()
    tri = TR.load(a.model, embed_fn=stub_embed if a.stub_encoder else None)
    a._load_s = time.perf_counter() - t0

    if a.pool_sample:
        refuse_locked(a.pool)
        a.run_dir.mkdir(parents=True, exist_ok=True)
        cfg = {"created": datetime.now().isoformat(timespec="seconds"), "script": "scripts/infer.py",
               "model": str(a.model), "model_version": tri.model_version, "manifest_sha256": tri.manifest_sha256,
               "mode": tri.mode, "head_modes": tri.head_modes, "threshold": tri.threshold,
               "text_version": tri.text_version, "seed": 42, "pool_sample": a.pool_sample, "repeats": a.repeats,
               "model_load_s": round(a._load_s, 1), "stub_encoder": bool(a.stub_encoder),
               "inputs_sha256": {"pool": sha256(a.pool)}}
        (a.run_dir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        ok = run_pool(tri, a, a.run_dir)
        print(f"\nwrote {a.run_dir}")
        sys.exit(0 if ok else 1)

    if not (a.role and a.position):
        sys.exit("ERROR: --role and --position are required with --file/--folder")
    if a.file:
        refuse_locked(a.file)
        if not a.out:
            print(json.dumps(tri.classify(a.file.read_bytes(), a.role, a.position), indent=1))
            return
        files = [a.file]
    else:
        refuse_locked(a.folder)
        files = sorted(p for p in a.folder.rglob("*") if p.is_file())
    out = a.out or (a.run_dir / "predictions.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if run_files(tri, files, a.role, a.position, out) else 1)


if __name__ == "__main__":
    main()
