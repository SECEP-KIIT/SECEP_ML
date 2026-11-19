#!/usr/bin/env python3
"""
set_head_modes.py — Phase C4/C5 bridge. Fixes which probability mode each head uses, BEFORE gold-test is opened.

Run from ML_Training:
    python scripts\\set_head_modes.py --type prior --urgency prior --sentiment balanced ^
        --dev-balanced runs\\2026-11-19-dev-balanced\\score\\metrics.json ^
        --dev-prior    runs\\2026-11-19-dev-prior\\score\\metrics.json ^
        --reason "gold-dev strict macro-F1: prior better for type/urgency, balanced for sentiment"

Writes into model_v1\\manifest.json: head_mode {type, urgency, sentiment}, default_mode = "mixed", and
head_mode_note (time, reason, and the gold-dev numbers behind the choice). heads.npz is not touched.
The manifest's hash changes, so final_eval.py records the exact manifest used.
Refuses if the final evaluation has already been run (runs\\final_eval.lock.json exists).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADS = ["type", "urgency", "sentiment"]


def dev_f1(path: Path) -> dict:
    m = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for h in HEADS:
        out[h] = {"macro_f1": m["heads"][h]["strict"]["macro_f1"],
                  "review_rate": m.get("calibration", {}).get(h, {}).get("review_rate")}
    out["review_rate_any_head"] = m.get("review_rate_any_head")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "model_v1")
    for h in HEADS:
        ap.add_argument(f"--{h}", choices=["balanced", "prior"], required=True)
    ap.add_argument("--dev-balanced", type=Path)
    ap.add_argument("--dev-prior", type=Path)
    ap.add_argument("--reason", required=True)
    a = ap.parse_args()

    if (ROOT / "runs" / "final_eval.lock.json").exists():
        sys.exit("ERROR: gold-test has already been used; the mode may not be changed after seeing it.")
    mf = a.model / "manifest.json"
    man = json.loads(mf.read_text(encoding="utf-8"))
    modes = {h: getattr(a, h) for h in HEADS}
    if "prior" in modes.values() and "class_prior" not in man:
        sys.exit("ERROR: model has no class_prior; re-run train_heads.py first")

    note = {"set": datetime.now().isoformat(timespec="seconds"), "reason": a.reason}
    if a.dev_balanced and a.dev_prior:
        note["gold_dev_indicative"] = {"balanced": dev_f1(a.dev_balanced), "prior": dev_f1(a.dev_prior)}
    man["head_mode"], man["default_mode"], man["head_mode_note"] = modes, "mixed", note
    mf.write_text(json.dumps(man, indent=2), encoding="utf-8")

    print(f"head modes written to {mf}: {modes}  (default_mode = mixed)")
    if "gold_dev_indicative" in note:
        g = note["gold_dev_indicative"]
        print(f"{'head':<11}{'balanced F1':>12}{'prior F1':>10}   chosen")
        for h in HEADS:
            print(f"{h:<11}{g['balanced'][h]['macro_f1']:>12.3f}{g['prior'][h]['macro_f1']:>10.3f}   {modes[h]}")


if __name__ == "__main__":
    main()
