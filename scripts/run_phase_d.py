#!/usr/bin/env python3
"""
run_phase_d.py — runs everything left in Phase D, in order, with the go/no-go checks automated.

    python scripts\\run_phase_d.py            # run / resume; safe to re-run at any time
    python scripts\\run_phase_d.py --status   # what is done, what is next

Re-running never repeats a finished step (state in runs\\phase_d_state.json) and never re-spends API quota
(response cache). It stops, and tells you exactly what to send, only when a check fails. It asks you for input
only twice: to confirm the gold-test freeze (irreversible), and for a second Google account's API key when the
first one's daily quota runs out (pasted at the prompt; never stored).

Steps
  1  tests                pytest (offline)
  2  housekeeping         append Phase D decisions to decision_log.md; .gitignore lines (idempotent)
  3  retrain-reproduce    D5: the retrain recipe must reproduce model_v1 (>= 97% label agreement on gold-dev)
  4  retrain-demo         D5 demo; re-run once at x10 correction weight if x2 moves nothing (logged)
  5  dev-recheck          D3: revised prompt on 120 dev/calib emails -> GO/NO-GO
  6  injection            D3: 20/20 must pass
  7  pipeline             D4: 5 pool emails end to end
  8  freeze               D3: live_lock.py declare (asks you to confirm)
  9  gold-test            D3: the one gold-test run (pauses for a new key on quota; resumable)
 10  faithfulness         D3: pre-declared n=100 on the gold-test run
 11  collect              everything into phase_d_results.txt -> send that file
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "runs" / "phase_d_state.json"
PY = sys.executable
DEV_RUN = ROOT / "runs" / "d3-dev-recheck-n120"
GO_RULES = {"schema_valid_min": 0.99, "task_action_min": 0.50, "meeting_action_min": 0.50, "f1_drop_max": 0.02}


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")


def mark(st: dict, step: str, **info) -> None:
    st[step] = {"status": "done", "at": datetime.now().isoformat(timespec="seconds"), **info}
    save_state(st)


def sh(args: list[str], mock: list[str] | None = None) -> int:
    cmd = [PY] + args + (mock or [])
    print(f"\n$ python {' '.join(args)}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode          # inherits the console: key prompts work


def stop(msg: str, send: str | None = None) -> None:
    print("\n" + "=" * 78 + f"\nSTOPPED: {msg}")
    if send:
        print(f"Send Claude: {send}")
    print("Fix or report, then run `python scripts\\run_phase_d.py` again; finished steps are skipped.\n" + "=" * 78)
    sys.exit(1)


def latest(pattern: str) -> Path | None:
    c = sorted((ROOT / "runs").glob(pattern), key=lambda p: p.stat().st_mtime)
    return c[-1] if c else None


# ------------------------------------------------------------------ steps
def s_tests(st, a):
    if sh(["-m", "pytest", "tests", "-q"]) != 0:
        stop("tests failed", "the pytest output")
    mark(st, "tests")


def s_housekeeping(st, a):
    log = ROOT / "Data" / "gold_final" / "decision_log.md"
    add = (ROOT / "docs" / "decision_log_phase_d_additions.md").read_text(encoding="utf-8")
    cur = log.read_text(encoding="utf-8") if log.exists() else ""
    if "## Phase D decisions · 2026-11-20" not in cur:
        with open(log, "a", encoding="utf-8") as f:
            f.write(add)
        print("decision_log.md: Phase D decisions appended")
    else:
        print("decision_log.md: Phase D decisions already present")
    gi = ROOT / ".gitignore"
    lines = ["runs/decoder_cache/", "__pycache__/", ".pytest_cache/", "_backup_pre_c5/"]
    have = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    new = [l for l in lines if l not in have]
    if new:
        with open(gi, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(new) + "\n")
    mark(st, "housekeeping")


def s_reproduce(st, a):
    if sh(["scripts/retrain.py", "--reproduce"]) != 0:
        stop("retrain.py --reproduce crashed", "the error above")
    g = json.loads((latest("*-retrain-reproduce") / "gate.json").read_text(encoding="utf-8"))
    worst = min(g["dev_label_agreement_vs_parent"].values())
    ok = worst >= 0.97
    print(f"reproduction: worst-head agreement {worst:.1%} -> {'OK' if ok else 'DIFFERS'}")
    mark(st, "retrain-reproduce", agreement=worst, ok=ok)
    if not ok:
        print("D5 retraining recipe does not match Phase C closely enough: the D5 demo is skipped. "
              "D3/D4 continue (unaffected). Report this in the results.")


def s_demo(st, a):
    if not st.get("retrain-reproduce", {}).get("ok"):
        mark(st, "retrain-demo", skipped="reproduction failed")
        return
    for w in ("2", "10"):
        if sh(["scripts/retrain_demo.py", "--corr-weight", w], a.mock_flags_encoder) != 0:
            stop("retrain_demo.py crashed", "the error above")
        d = json.loads((latest("*-retrain-demo") / "demo.json").read_text(encoding="utf-8"))
        gain = max(v["after"] - v["before"] for v in d["eval_slice_accuracy"].values())
        print(f"demo at x{w}: best eval-slice gain {gain:+.0%}, gate {'PASS' if d['gate_pass'] else 'FAIL'}")
        if gain >= 0.05 or w == "10":
            mark(st, "retrain-demo", corr_weight=w, best_gain=gain, gate=d["gate_pass"])
            return


def s_dev(st, a):
    rc = sh(["scripts/decoder_eval.py", "--split", "devcalib", "--limit", "120", "--run-dir", str(DEV_RUN)],
            a.mock_flags_both)
    if rc != 0:
        stop("dev re-check incomplete (quota stop or error)" if rc == 2 else "dev re-check failed",
             None if rc == 2 else "the error above")
    m = json.loads((DEV_RUN / "metrics.json").read_text(encoding="utf-8"))
    bt = m["actions"]["by_gold_type"]
    checks = {
        "schema-valid >= 99%": m["schema_valid_share"] >= GO_RULES["schema_valid_min"],
        "Task action accuracy >= 50%": bt.get("Task", {}).get("accuracy", 0) >= GO_RULES["task_action_min"],
        "Meeting action accuracy >= 50%": bt.get("Meeting", {}).get("accuracy", 0) >= GO_RULES["meeting_action_min"],
        "hybrid macro-F1 >= student - 0.02 on every head": all(
            v["n"] > 0 and v["student"] is not None and v["hybrid"] >= v["student"] - GO_RULES["f1_drop_max"]
            for v in m["quick_macro_f1"].values())}
    for h, v in m["quick_macro_f1"].items():
        print(f"  macro-F1 {h:<9} n {v['n']:<4} student {v['student'] or 0:.3f}  hybrid {v['hybrid'] or 0:.3f}")
    for k, v in checks.items():
        print(f"  {'GO   ' if v else 'NO-GO'}  {k}")
    if not all(checks.values()):
        if not a.accept_nogo:
            stop("the revised prompt did not pass the go/no-go check; gold-test is NOT frozen",
                 f"{DEV_RUN / 'report.md'}")
        failed = [k for k, v in checks.items() if not v]
        entry = (f"\n\n### D3 · {datetime.now():%Y-%m-%d %H:%M} · Go/no-go override before the freeze\n"
                 f"Dev re-check ({DEV_RUN.name}, prompt in the lock): failed {failed}. Proceeding to the freeze "
                 f"anyway. Reason: {a.accept_nogo}\nAll other checks passed: "
                 f"{[k for k, v in checks.items() if v]}. The failed check is reported as a limitation in the "
                 f"model card; the gold-test metrics are unchanged and pre-declared.\n")
        with open(ROOT / "Data" / "gold_final" / "decision_log.md", "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"OVERRIDE logged in decision_log.md: {failed}")
        mark(st, "dev-recheck", checks=checks, override=a.accept_nogo)
        return
    mark(st, "dev-recheck", checks=checks)


def s_injection(st, a):
    rc = sh(["scripts/injection_suite.py"], a.mock_flags_both)
    if rc != 0:
        stop("injection suite did not pass 20/20 (or stopped); gold-test is NOT frozen",
             f"{latest('*-injection') / 'report.md'}")
    mark(st, "injection")


def s_pipeline(st, a):
    if a.mock:
        mark(st, "pipeline", skipped="mock")
        return
    if sh(["scripts/run_pipeline.py", "--n", "5"]) != 0:
        stop("pipeline run failed", "the error above")
    mark(st, "pipeline")


def s_freeze(st, a):
    lock = ROOT / "runs" / "live_eval.lock.json"
    if lock.exists():
        print("lock already exists:", json.loads(lock.read_text(encoding="utf-8"))["status"])
        mark(st, "freeze")
        return
    print("\nAll checks passed. Next is IRREVERSIBLE: freeze the prompt/model/settings and run gold-test once.")
    if not a.yes:
        if not sys.stdin.isatty() or input("Type FREEZE to continue (anything else stops): ").strip() != "FREEZE":
            stop("freeze not confirmed (nothing was frozen)")
    if sh(["scripts/live_lock.py", "declare"]) != 0:
        stop("declare failed", "the error above")
    mark(st, "freeze")


def s_test(st, a):
    rc = sh(["scripts/decoder_eval.py", "--split", "test"], a.mock_flags_both)
    if rc == 2:
        stop("gold-test run paused (quota / stopped at the key prompt). It is resumable: run this script again, "
             "after 13:30 IST or with another account's key")
    if rc != 0:
        stop("gold-test run failed", "the error above")
    mark(st, "gold-test")


def s_faith(st, a):
    if sh(["scripts/faithfulness.py", "--run", "runs/d3-live-gold-test"], a.mock_flags_llm) != 0:
        stop("faithfulness check failed", "the error above")
    f = json.loads((ROOT / "runs" / "d3-live-gold-test" / "faithfulness" / "faithfulness.json").read_text(encoding="utf-8"))
    if not f["complete"]:
        stop("faithfulness check incomplete (quota). Run this script again later; it resumes from the cache")
    mark(st, "faithfulness", share=f["share_with_unsupported_claim"])


def s_collect(st, a):
    keep = ("d3-", "injection", "retrain", "d4-pipeline")
    names = ("report.md", "faithfulness.json", "demo.json", "gate.json", "metrics.json")
    files = sorted(p for p in (ROOT / "runs").rglob("*")
                   if p.is_file() and p.name in names and any(k in str(p.relative_to(ROOT)) for k in keep))
    parts = [f"===== {p.relative_to(ROOT)} =====\n{p.read_text(encoding='utf-8', errors='replace')}" for p in files]
    for extra in ("runs/live_eval.lock.json", "runs/phase_d_state.json"):
        p = ROOT / extra
        if p.exists():
            parts.append(f"===== {extra} =====\n{p.read_text(encoding='utf-8')}")
    out = ROOT / "phase_d_results.txt"
    out.write_text("\n\n".join(parts), encoding="utf-8")
    mark(st, "collect", file=str(out.name), files=len(files))
    print(f"\nPHASE D RUNS COMPLETE. Send Claude: {out}")


STEPS = [("tests", s_tests), ("housekeeping", s_housekeeping), ("retrain-reproduce", s_reproduce),
         ("retrain-demo", s_demo), ("dev-recheck", s_dev), ("injection", s_injection), ("pipeline", s_pipeline),
         ("freeze", s_freeze), ("gold-test", s_test), ("faithfulness", s_faith), ("collect", s_collect)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--yes", action="store_true", help="do not ask before the freeze")
    ap.add_argument("--redo", help="mark one step as not done (e.g. collect) and run from there")
    ap.add_argument("--accept-nogo", metavar="REASON",
                    help="proceed past a failed dev go/no-go check; REASON is written to decision_log.md")
    ap.add_argument("--mock", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    a.mock_flags_both = ["--stub-encoder", "--mock-llm"] if a.mock else []
    a.mock_flags_encoder = ["--stub-encoder"] if a.mock else []
    a.mock_flags_llm = ["--mock-llm"] if a.mock else []
    st = load_state()
    if a.redo:
        st.pop(a.redo, None)
        save_state(st)
    if a.status:
        for name, _ in STEPS:
            print(f"  {'done' if name in st else '    '}  {name}  {st.get(name, {}).get('at', '')}")
        return
    t0 = time.time()
    for name, fn in STEPS:
        if name in st:
            print(f"[skip] {name} (done {st[name]['at']})")
            continue
        print(f"\n{'#' * 78}\n# {name}\n{'#' * 78}", flush=True)
        fn(st, a)
    print(f"\nall steps done in {(time.time() - t0) / 60:.0f} min this session")


if __name__ == "__main__":
    main()
