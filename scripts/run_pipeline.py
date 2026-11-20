#!/usr/bin/env python3
"""
run_pipeline.py — Phase D4 manual run: secep_ml.pipeline on N pool emails (never gold) with the real decoder;
reports statuses and end-to-end latency (student + decoder, including network).

    python scripts\\run_pipeline.py --n 5
Writes runs\\<date>-d4-pipeline\\{results.jsonl, report.md}.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from secep_ml import decoder as D  # noqa: E402
from secep_ml import triage as TR  # noqa: E402
from secep_ml.pipeline import Pipeline  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no-decoder", action="store_true", help="triage only (no API calls)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    pipe = Pipeline(TR.load_promoted(ROOT),
                    None if a.no_decoder else D.Decoder(D.DecoderConfig.from_env(
                        cache_dir=str(ROOT / "runs" / "decoder_cache"))))
    pool = pd.read_parquet(ROOT / "Data" / "pool" / "pool.parquet",
                           columns=["pool_uid", "source_path", "recipient_role", "recipient_position"])
    rows = pool.sample(a.n, random_state=a.seed)
    run = ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-d4-pipeline"
    run.mkdir(parents=True, exist_ok=True)
    out, lat = [], []
    for r in rows.itertuples(index=False):
        raw = Path(ROOT / "Data" / "raw" / "maildir", *re.split(r"[\\/]", r.source_path)).read_bytes()
        res = pipe.process_email(raw, r.recipient_role, r.recipient_position)
        out.append({"pool_uid": r.pool_uid, **res})
        cached = bool(res["enrich"] and res["enrich"]["meta"]["cache_hit"])
        if not cached:
            lat.append(res["latency_ms"]["total"])
        print(f"  {r.pool_uid}: {res['status']}, labels {res['final_labels']}, sources {res['sources']}, "
              f"{res['latency_ms']['total']:.0f} ms{' (cached)' if cached else ''}")
    with open(run / "results.jsonl", "w", encoding="utf-8") as f:
        for x in out:
            f.write(json.dumps(x) + "\n")
    st = {s: sum(1 for x in out if x["status"] == s) for s in {x["status"] for x in out}}
    line = (f"End-to-end (student + decoder) over {len(lat)} uncached emails: median {np.median(lat):.0f} ms, "
            f"p95 {np.percentile(lat, 95):.0f} ms." if lat else "All decoder answers came from the cache.")
    rep = f"# D4 pipeline run — {datetime.now().isoformat(timespec='seconds')}\n\nModel `{pipe.triage.model_version}`; " \
          f"statuses {st}.\n\n{line}\n"
    (run / "report.md").write_text(rep, encoding="utf-8")
    print("\n" + rep)


if __name__ == "__main__":
    main()
