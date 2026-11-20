#!/usr/bin/env python3
"""
decoder_smoke.py — Phase D2, step 2. Live end-to-end check on a few POOL emails (never gold):
raw file -> secep_ml.triage (student) -> secep_ml.decoder (Gemini by default) -> summary, actions, adjudication.

It answers practical questions before any evaluation: does the key work, does the model accept our JSON
schema and settings, are responses schema-valid first time, what are latency and tokens per email.

Run from ML_Training (needs GEMINI_API_KEY and SECEP_DECODER_MODEL in the environment):
    python scripts\\decoder_smoke.py                      # 5 pool emails
    python scripts\\decoder_smoke.py --n 3 --temperature none
    python scripts\\decoder_smoke.py --nullable-enum-style type_array   # only if the schema is rejected (400)

Writes runs\\<date>-d2-smoke\\{results.jsonl, config.json, metrics.json, report.md}. Responses are cached in
runs\\decoder_cache, so re-running the same emails with the same settings spends no quota.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from secep_ml import decoder as D  # noqa: E402
from secep_ml import triage as TR  # noqa: E402


class _MockLLM:  # tests only (--mock-llm): a valid answer for whatever heads the schema asks for
    name, model, endpoint = "mock", "mock-1", "mock://"

    def generate(self, system, user, schema):
        adj = schema.get("properties", {}).get("adjudication", {}).get("properties", {})
        obj = {"summary_one_line": "Mock summary.", "summary_short": "Mock short summary.",
               "actions": [{"type": "none", "title": None, "description": None, "priority": None,
                            "due_date": None, "start": None, "end": None, "attendees": None}],
               "adjudication": {h: v["enum"][0] for h, v in adj.items()}}
        return D.LLMResult(text=json.dumps(obj), prompt_tokens=1000, output_tokens=80, latency_ms=5.0)


def _stub_embed(texts):
    out = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:8], "little")
        v = np.random.default_rng(seed).standard_normal(768)
        out.append(v / np.linalg.norm(v))
    return np.asarray(out, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model-dir", type=Path, default=ROOT / "model_v1")
    ap.add_argument("--pool", type=Path, default=ROOT / "Data" / "pool" / "pool.parquet")
    ap.add_argument("--raw-root", type=Path, default=ROOT / "Data" / "raw" / "maildir")
    ap.add_argument("--cache", type=Path, default=ROOT / "runs" / "decoder_cache")
    ap.add_argument("--temperature", help="override, e.g. 0.2 or none")
    ap.add_argument("--nullable-enum-style", choices=["anyOf", "type_array"])
    ap.add_argument("--reasoning-effort", help="override, e.g. low | medium | high | none")
    ap.add_argument("--run-dir", type=Path, default=ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-d2-smoke")
    ap.add_argument("--stub-encoder", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--mock-llm", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    if any(x in str(a.pool).lower() for x in ("gold", "sealed")):
        sys.exit("ERROR: the smoke test runs on pool emails only")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpx2", "google_genai", "sentence_transformers", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    over = {"cache_dir": str(a.cache)}
    if a.temperature is not None:
        over["temperature"] = None if a.temperature.lower() in ("none", "off") else float(a.temperature)
    if a.reasoning_effort:
        over["reasoning_effort"] = None if a.reasoning_effort.lower() == "none" else a.reasoning_effort
    if a.nullable_enum_style:
        over["nullable_enum_style"] = a.nullable_enum_style
    cfg = D.DecoderConfig.from_env(**over)
    dec = D.Decoder(cfg, backend=_MockLLM() if a.mock_llm else None)
    tri = TR.load(a.model_dir, embed_fn=_stub_embed if a.stub_encoder else None)

    pool = pd.read_parquet(a.pool, columns=["pool_uid", "source_path", "recipient_role", "recipient_position"])
    rows = pool.sample(a.n, random_state=a.seed).reset_index(drop=True)
    a.run_dir.mkdir(parents=True, exist_ok=True)
    cfg_out = {"created": datetime.now().isoformat(timespec="seconds"), "script": "scripts/decoder_smoke.py",
               "backend": dec.backend.name, "model": dec.backend.model, "prompt_version": D.PROMPT_VERSION,
               "temperature": cfg.temperature, "reasoning_effort": cfg.reasoning_effort, "strict": cfg.strict,
               "nullable_enum_style": cfg.nullable_enum_style, "rpm": cfg.rpm,
               "triage_model": tri.model_version, "manifest_sha256": tri.manifest_sha256, "n": a.n,
               "seed": a.seed, "schema_sha256": hashlib.sha256(
                   (D.SCHEMA_DIR / "enrich.v1.1.json").read_bytes()).hexdigest(),
               "mock_llm": a.mock_llm, "stub_encoder": a.stub_encoder}
    (a.run_dir / "config.json").write_text(json.dumps(cfg_out, indent=2), encoding="utf-8")

    results, lines = [], []
    for r in rows.itertuples(index=False):
        raw = Path(a.raw_root, *re.split(r"[\\/]", r.source_path)).read_bytes()
        t = tri.classify(raw, r.recipient_role, r.recipient_position)
        t0 = time.perf_counter()
        try:
            e = dec.enrich(raw, t, role=r.recipient_role, position=r.recipient_position)
            err = None
        except Exception as ex:                    # e.g. 400 schema/settings rejected: report, keep going
            e, err = None, f"{type(ex).__name__}: {str(ex)[:400]}"
        wall = (time.perf_counter() - t0) * 1000
        results.append({"pool_uid": r.pool_uid, "role": r.recipient_role, "position": r.recipient_position,
                        "triage": t, "enrich_result": e, "error": err, "wall_ms": wall})
        if err:
            lines.append(f"### {r.pool_uid} — ERROR\n`{err}`\n")
            if "400" in err or "INVALID_ARGUMENT" in err:
                break                              # a settings problem fails every email: stop spending quota
            continue
        student = {h: t[TR.OUT_KEY[h]]["label"] for h in TR.HEADS}
        moved = ", ".join(f"{h} {student[h]}→{e['final_labels'][h]}" for h in e["flagged_heads"]) or "none flagged"
        acts = ", ".join(x["type"] for x in (e["enrich"] or {}).get("actions", [])) or "—"
        m = e["meta"]
        lines.append(f"### {r.pool_uid} ({r.recipient_role}, {r.recipient_position}) — {e['status']}\n"
                     f"- adjudication: {moved}\n"
                     f"- summary: {(e['enrich'] or {}).get('summary_one_line', '—')}\n"
                     f"- actions: {acts}; violations: {[v['rule'] for v in e['violations']] or 'none'}\n"
                     f"- requests {m['requests']}, attempts {m['http_attempts']}, tokens {m['prompt_tokens']}→"
                     f"{m['output_tokens']}, latency {m['latency_ms']:.0f} ms, cache {m['cache_hit']}\n")

    with open(a.run_dir / "results.jsonl", "w", encoding="utf-8") as f:
        for x in results:
            f.write(json.dumps(x) + "\n")
    ok = [x["enrich_result"] for x in results if x["enrich_result"]]
    live = [x for x in ok if not x["meta"]["cache_hit"] and x["status"] == "enriched"]
    lat = [x["meta"]["latency_ms"] for x in live]
    metrics = {"emails": len(results), "errors": sum(1 for x in results if x["error"]),
               "status": {s: sum(1 for x in ok if x["status"] == s) for s in ("enriched", "enrich_failed",
                                                                              "enrich_pending")},
               "valid_first_attempt": sum(1 for x in live if x["meta"]["requests"] == 1),
               "requests_total": sum(x["meta"]["requests"] for x in ok),
               "latency_ms": {"median": float(np.median(lat)) if lat else None,
                              "p95": float(np.percentile(lat, 95)) if lat else None},
               "tokens_mean": {"in": float(np.mean([x["meta"]["prompt_tokens"] for x in live])) if live else None,
                               "out": float(np.mean([x["meta"]["output_tokens"] for x in live])) if live else None},
               "flagged_heads": sum(len(x["flagged_heads"]) for x in ok),
               "labels_changed": sum(1 for x, r in zip(ok, results) for h in x["flagged_heads"]
                                     if x["final_labels"][h] != r["triage"][TR.OUT_KEY[h]]["label"])}
    (a.run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    head = [f"# D2 smoke test — {cfg_out['created']}", "",
            f"Backend `{cfg_out['backend']}`, model `{cfg_out['model']}`, prompt `{D.PROMPT_VERSION}`, "
            f"temperature {cfg.temperature}, reasoning {cfg.reasoning_effort}, strict {cfg.strict}, "
            f"nullable enums `{cfg.nullable_enum_style}`.", "",
            f"**{metrics['status']['enriched']}/{metrics['emails']} enriched**, valid first attempt "
            f"{metrics['valid_first_attempt']}, errors {metrics['errors']}, requests {metrics['requests_total']}. "
            f"Latency median {metrics['latency_ms']['median'] or 0:.0f} ms, p95 {metrics['latency_ms']['p95'] or 0:.0f} ms. "
            f"Tokens/email in {metrics['tokens_mean']['in'] or 0:.0f}, out {metrics['tokens_mean']['out'] or 0:.0f}. "
            f"Flagged heads {metrics['flagged_heads']}, changed by the decoder {metrics['labels_changed']}.", ""]
    if a.mock_llm or a.stub_encoder:
        head += ["_Mock LLM / stub encoder: test run only._", ""]
    report = "\n".join(head + lines)
    (a.run_dir / "report.md").write_text(report + "\n", encoding="utf-8")
    print("\n" + report)
    print(f"wrote {a.run_dir}")
    sys.exit(0 if metrics["errors"] == 0 and metrics["status"]["enriched"] == len(results) else 1)


if __name__ == "__main__":
    main()
