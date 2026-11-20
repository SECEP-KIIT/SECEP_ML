#!/usr/bin/env python3
"""
live_lock.py — the D3 gold-test freeze (decision log: D3, option a).

    python scripts\\live_lock.py declare     # freeze config + verify the sealed gold-test hash -> runs\\live_eval.lock.json
    python scripts\\live_lock.py status      # show the lock and whether the current config still matches it

After `declare`, `python scripts\\decoder_eval.py --split test` is the ONE run. It refuses to start if the lock is
missing, already spent, or if backend / model / prompt / schema / student model / threshold / temperature differ.
It sets the lock to "running" on start (resumable across days and API keys) and "spent" when scored.
Never edit or delete the lock by hand; a change after declaring must be logged in decision_log.md.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LOCK = ROOT / "runs" / "live_eval.lock.json"
SEALED_HASH_FILE = ROOT / "Data" / "gold_final" / "gold_test.sha256"
CANDIDATES = [ROOT / "Data" / "sealed" / "gold_test.csv", ROOT / "Data" / "sealed" / "gold_test.parquet"]
RUN_DIR = "runs/d3-live-gold-test"
FROZEN_KEYS = ("backend", "model", "prompt_version", "prompt_files_sha256", "schema_sha256", "manifest_sha256",
               "review_threshold", "temperature", "text_version", "code_sha256")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def current_config() -> dict:
    from secep_ml import decoder as D
    from secep_ml import triage as TR
    from common import text as T
    cfg = D.DecoderConfig.from_env()
    man = ROOT / "model_v1" / "manifest.json"
    prompt_files = sorted(D.PROMPT_DIR.glob("*"))
    return {"backend": cfg.backend, "model": cfg.model, "prompt_version": D.PROMPT_VERSION,
            "prompt_files_sha256": {p.name: sha256(p) for p in prompt_files},
            "schema_sha256": sha256(D.SCHEMA_DIR / "enrich.v1.1.json"), "manifest_sha256": sha256(man),
            "review_threshold": json.loads(man.read_text(encoding="utf-8")).get("review_threshold", 0.6),
            "temperature": cfg.temperature, "text_version": T.TEXT_VERSION,
            "code_sha256": {**{f"secep_ml/{f}": sha256(ROOT / "secep_ml" / f)
                               for f in ("decoder.py", "triage.py", "pipeline.py")},
                            **{f"common/{f}": sha256(ROOT / "common" / f) for f in ("text.py", "student.py")}}}


def verified_test_file() -> tuple[Path, str]:
    """The sealed gold-test file whose SHA-256 appears in gold_test.sha256 (C1/C5 seal)."""
    if not SEALED_HASH_FILE.exists():
        sys.exit(f"ERROR: {SEALED_HASH_FILE} not found")
    sealed = set(re.findall(r"\b[0-9a-fA-F]{64}\b", SEALED_HASH_FILE.read_text(encoding="utf-8", errors="replace")))
    sealed = {s.lower() for s in sealed}
    seen = {}
    for p in CANDIDATES:
        if p.exists():
            h = sha256(p)
            seen[str(p.relative_to(ROOT))] = h
            if h in sealed:
                return p, h
    sys.exit(f"ERROR: no sealed gold-test file matches {SEALED_HASH_FILE.name}.\n  sealed: {sorted(sealed)}\n"
             f"  found:  {seen}\nDo not proceed; report this.")


def load_lock() -> dict | None:
    return json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else None


def save_lock(lock: dict) -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(lock, indent=2), encoding="utf-8")


def mismatches(lock: dict) -> list[str]:
    cur = current_config()
    return [f"{k}: locked {lock['frozen'][k]!r} != now {cur[k]!r}" for k in FROZEN_KEYS if lock["frozen"].get(k) != cur[k]]


def declare() -> None:
    if LOCK.exists():
        sys.exit(f"ERROR: {LOCK} already exists (status {load_lock().get('status')}). It is declared once.")
    cur = current_config()
    if not cur["model"]:
        sys.exit("ERROR: SECEP_DECODER_MODEL is not set")
    p, h = verified_test_file()
    lock = {"status": "declared", "declared_at": datetime.now().isoformat(timespec="seconds"),
            "decision": "decision_log.md, D3 (option a): one pre-declared live-hybrid run on gold-test",
            "frozen": cur, "gold_test_file": str(p.relative_to(ROOT)), "gold_test_sha256": h,
            "run_dir": RUN_DIR, "faithfulness_sample": {"n": 100, "seed": 42}, "history": []}
    save_lock(lock)
    print(f"DECLARED -> {LOCK}\n  model {cur['backend']}/{cur['model']}, prompt {cur['prompt_version']}, "
          f"temperature {cur['temperature']}\n  gold-test {p.name} sha256 {h[:12]}… (matches the seal)\n"
          f"Next: python scripts\\decoder_eval.py --split test")


def status() -> None:
    lock = load_lock()
    if not lock:
        print("no lock: gold-test has not been declared")
        return
    print(json.dumps({k: lock[k] for k in ("status", "declared_at", "run_dir", "gold_test_sha256")}, indent=2))
    mm = mismatches(lock)
    print("config matches the lock" if not mm else "CONFIG DIFFERS FROM LOCK:\n  " + "\n  ".join(mm))


if __name__ == "__main__":
    {"declare": declare, "status": status}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
