#!/usr/bin/env python3
"""
final_eval.py — Phase C5. The one-time evaluation on sealed gold-test.

Run from ML_Training, ONLY after: model mode chosen (manifest default_mode or --mode) and the teacher's
gold-test predictions exist (I4 format, one label on every row).

    python scripts\\final_eval.py --teacher path\\to\\teacher_gold_test_predictions.csv
    python scripts\\final_eval.py --no-teacher          # student only (say why in the decision log)
Options: --mode balanced|prior   --labeller Akashdeep   --model model_v1   --run-name final-eval

What it does, in order:
  1. Refuses to run twice (runs\\final_eval.lock.json) unless --rerun-reason "..." is given (logged).
  2. Verifies SHA-256 of gold_test.csv against Data\\gold_final\\gold_test.sha256.
  3. Builds the two exclude lists from Data\\labelling\\manifest.csv (no labels involved):
       akashdeep_single  = test rows labelled by one person, who is --labeller
       double_labelled   = all test rows with overlap == True
  4. Student predictions on gold-test (embeddings from C2, heads in numpy) in the chosen mode.
  5. score.py for student and teacher, three views each:
       all | without_<labeller>_single | single_labelled_only (double-labelled rows removed)
  6. Writes runs\\<date>-<run-name>\\{final_eval.json, final_summary.md, ...} and the lock file.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd  # noqa: E402

import predict as PR  # noqa: E402
import score as SC  # noqa: E402
from common import metrics as M  # noqa: E402

NAMES = list(M.HEADS) + list(M.VIEWS)


def fail(msg: str) -> None:
    sys.exit(f"ERROR: {msg}")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def f3(x) -> str:
    return "–" if x is None else f"{x:.3f}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "model_v1")
    ap.add_argument("--mode", choices=["balanced", "prior"])
    ap.add_argument("--teacher", type=Path, help="teacher predictions on gold-test (I4 format)")
    ap.add_argument("--no-teacher", action="store_true")
    ap.add_argument("--labeller", default="Akashdeep", help="whose single-labelled test rows to exclude in check 1")
    ap.add_argument("--run-name", default="final-eval")
    ap.add_argument("--rerun-reason")
    a = ap.parse_args()
    if not a.teacher and not a.no_teacher:
        fail("give --teacher <file> or --no-teacher")
    if a.teacher and not a.teacher.exists():
        fail(f"teacher file not found: {a.teacher}")

    D = ROOT / "Data"
    lock = ROOT / "runs" / "final_eval.lock.json"
    if lock.exists() and not a.rerun_reason:
        fail(f"gold-test was already used ({lock}). It is spent. To run again, pass "
             f"--rerun-reason \"why\" (the reason is logged in the new run).")

    # ---- 1. integrity
    sha_file = D / "gold_final" / "gold_test.sha256"
    m = re.search(r"\b[0-9a-fA-F]{64}\b", sha_file.read_text(encoding="utf-8"))
    if not m:
        fail(f"no 64-hex SHA-256 found in {sha_file}")
    expected = m.group(0).lower()
    cands = [p for p in (D / "sealed" / "gold_test.csv", D / "gold_final" / "gold_test.csv") if p.exists()]
    hashes = {p: sha256(p) for p in cands}
    good = [p for p, h in hashes.items() if h == expected]
    for p, h in hashes.items():
        print(f"sha256 {p.relative_to(ROOT)}: {'MATCH' if h == expected else 'MISMATCH'} ({h[:16]}…)")
    if not good:
        fail(f"no gold_test.csv matches {sha_file.name} (expected {expected[:16]}…). Do not proceed; "
             f"someone changed the sealed file, or the .sha256 covers a different file.")
    gold_path = good[0]
    gold = pd.read_csv(gold_path, dtype=str, keep_default_na=False)

    # ---- 2. the text that was embedded is the text in gold-test
    emb_in = D / "emb_inputs" / "gold_test.csv"
    if emb_in.exists():
        ref = pd.read_csv(emb_in, dtype=str, keep_default_na=False).set_index("uid")["input_text"]
        mine = gold.set_index("email_uid")["input_text"]
        common = mine.index.intersection(ref.index)
        if len(common) != len(gold) or (mine.loc[common] != ref.loc[common]).any():
            fail("gold-test text differs from what was embedded in C2")

    # ---- 3. exclude lists from the manifest (no labels)
    man = pd.read_csv(D / "labelling" / "manifest.csv", dtype=str, keep_default_na=False)
    mt = man[man["split"].str.lower() == "test"]
    gold_uids = set(gold["email_uid"])
    missing = gold_uids - set(mt["email_uid"])
    if missing:
        fail(f"{len(missing)} gold-test uids are missing from the labelling manifest")
    n_dropped = int((~mt["email_uid"].isin(gold_uids)).sum())
    mt = mt[mt["email_uid"].isin(gold_uids)]
    print(f"manifest: {n_dropped} test uids not in sealed gold-test (dropped at finalisation, see issues.csv); using {len(mt)}")
    ov = mt["overlap"].str.lower().isin(["true", "1", "yes"])
    single_by = mt[(~ov) & mt["labellers"].str.contains(a.labeller, case=False, regex=False)]
    dbl = mt[ov]
    print(f"test rows {len(mt)}: double-labelled {len(dbl)}, single-labelled {int((~ov).sum())}, "
          f"of which {a.labeller}: {len(single_by)}")
    if len(single_by) == 0:
        fail(f"no single-labelled test rows for labeller {a.labeller!r}; check the name against "
             f"the `labellers` column of manifest.csv")

    run = ROOT / "runs" / f"{date.today()}-{a.run_name}"
    run.mkdir(parents=True, exist_ok=True)
    f_single = run / f"exclude_{a.labeller.lower()}_single.txt"
    f_double = run / "exclude_double_labelled.txt"
    f_single.write_text("\n".join(single_by["email_uid"]) + "\n", encoding="utf-8")
    f_double.write_text("\n".join(dbl["email_uid"]) + "\n", encoding="utf-8")

    # ---- 4. student predictions
    manifest = json.loads((a.model / "manifest.json").read_text(encoding="utf-8"))
    mode = a.mode or manifest.get("default_mode", "balanced")
    if a.mode and a.mode != manifest.get("default_mode"):
        print(f"WARNING: --mode {a.mode} differs from manifest default_mode {manifest.get('default_mode')!r}; "
              f"fix the manifest so the model card matches.")
    with contextlib.redirect_stdout(io.StringIO()):
        PR.batch_predict(a.model, gold_path, D / "emb" / "gold_test", mode, run / "student")
    print(f"student predictions written ({mode} mode)")

    # teacher file must be valid BEFORE the labels are read: a broken file must not spend gold-test
    adjudication = None
    if a.teacher:
        SC.validate_pred(pd.read_csv(a.teacher, dtype=str, keep_default_na=False), set(gold["email_uid"]))
        # hybrid = what users see: student label where confident, LLM (teacher proxy) label where flagged
        st = pd.read_csv(run / "student" / "predictions.csv", dtype=str, keep_default_na=False).set_index("email_uid")
        te = pd.read_csv(a.teacher, dtype=str, keep_default_na=False).set_index("email_uid").loc[st.index]
        thr = manifest.get("review_threshold", 0.60)
        hy = pd.DataFrame(index=st.index)
        adjudication = {}
        for h, classes in M.HEADS.items():
            conf = st[[f"prob_{h}_{c}" for c in classes]].astype(float).max(axis=1)
            flag = conf < thr
            hy[f"pred_{h}"] = st[f"pred_{h}"].where(~flag, te[f"pred_{h}"])
            adjudication[h] = {"flagged": float(flag.mean()),
                               "changed": float((flag & (st[f"pred_{h}"] != te[f"pred_{h}"])).mean())}
        (run / "hybrid").mkdir(parents=True, exist_ok=True)
        hy.reset_index().to_csv(run / "hybrid" / "predictions.csv", index=False)
        print("hybrid (student + LLM on flagged heads): " + "  ".join(
            f"{h} flagged {v['flagged']:.0%} changed {v['changed']:.0%}" for h, v in adjudication.items()))

    # point of no return: scoring reads the labels
    lock.write_text(json.dumps({"started": datetime.now().isoformat(timespec="seconds"), "run": str(run),
                                "gold_sha256": expected, "mode": mode, "rerun_reason": a.rerun_reason},
                               indent=2), encoding="utf-8")

    # ---- 5. score
    systems = {"student": run / "student" / "predictions.csv"}
    if a.teacher:
        systems["teacher"] = a.teacher
        systems["hybrid"] = run / "hybrid" / "predictions.csv"
    views ={"all": None, f"without_{a.labeller.lower()}_single": f_single, "single_labelled_only": f_double}
    base = D / "gold_final" / "human_baseline.json"
    results, paths = {}, {}
    for vname, excl in views.items():
        results[vname], paths[vname] = {}, {}
        for sname, pred in systems.items():
            out = run / sname / vname
            argv = ["--gold", str(gold_path), "--pred", str(pred), "--out", str(out), "--baseline", str(base)]
            if excl:
                argv += ["--exclude-uids", str(excl)]
            with contextlib.redirect_stdout(io.StringIO()):
                met = SC.main(argv)
            rows = {}
            for k in NAMES:
                r = met["heads"][k] if k in M.HEADS else met["views"][k]
                g = met["gate"][k]
                rows[k] = {"n": r["strict"]["n"], "macro_f1": r["strict"]["macro_f1"],
                           "ci": r["strict"]["macro_f1_ci"], "accuracy": r["strict"]["accuracy"],
                           "lenient_macro_f1": r.get("lenient", {}).get("macro_f1"),
                           "gate": g["gate"], "human": g["human_macro_f1"], "pass": g["pass"]}
            results[vname][sname] = {"n_rows": met["n_rows"], "n_excluded": met["n_excluded"], "views": rows,
                                     "calibration": {h: {kk: c[kk] for kk in
                                                         ("ece_width10", "ece_count10", "review_rate", "n_ece")}
                                                     for h, c in met.get("calibration", {}).items()},
                                     "review_rate_any_head": met.get("review_rate_any_head")}
            paths[vname][sname] = str(out.relative_to(ROOT))

    # ---- 6. outputs
    final = {"created": datetime.now().isoformat(timespec="seconds"), "mode": mode, "rerun_reason": a.rerun_reason,
             "gold_test": {"path": str(gold_path.relative_to(ROOT)), "sha256": expected, "rows": len(gold)},
             "exclude": {"labeller": a.labeller, "single_rows": len(single_by), "double_rows": len(dbl)},
             "model": {"path": str(a.model), "manifest_sha256": sha256(a.model / "manifest.json")},
             "teacher_predictions": ({"path": str(a.teacher), "sha256": sha256(a.teacher)} if a.teacher else None),
             "hybrid_adjudication": adjudication,
             "hybrid_note": "hybrid = student label where top prob >= threshold, teacher label where below; the "
                            "teacher (Qwen2.5-14B, 3 votes) stands in for the live decoder (Qwen2.5-7B, 1 call), "
                            "so the hybrid figure is an optimistic proxy",
             "results": results, "score_dirs": paths}
    (run / "final_eval.json").write_text(json.dumps(final, indent=2, default=float), encoding="utf-8")

    L = [f"# Final evaluation on gold-test — {final['created']}", "",
         f"- student mode: **{mode}**; gold-test sha256 `{expected[:16]}…` verified; {len(gold)} emails",
         f"- strict macro-F1 with 95% bootstrap CI (2,000 resamples, seed 42); gate = human macro-F1 − 0.05", ""]
    for vname, per in results.items():
        n_any = next(iter(per.values()))
        L += [f"## View: {vname} ({n_any['n_rows']} emails, {n_any['n_excluded']} excluded)", "",
              "| System | Head / view | n | Strict macro-F1 | 95% CI | Human | Gate | Result |", "|---|---|---|---|---|---|---|---|"]
        for sname, r in per.items():
            for k in NAMES:
                v = r["views"][k]
                L.append(f"| {sname} | {k} | {v['n']} | **{f3(v['macro_f1'])}** | {f3(v['ci'][0])}–{f3(v['ci'][1])} | "
                         f"{f3(v['human'])} | {f3(v['gate'])} | {'PASS' if v['pass'] else 'FAIL'} |")
        L.append("")
    cal = results["all"]["student"]["calibration"]
    L += ["## Student calibration and review routing (all gold-test rows)", "",
          "| Head | ECE (equal-width 10) | ECE (equal-count 10) | Review rate (<0.60) |", "|---|---|---|---|"]
    for h, c in cal.items():
        L.append(f"| {h} | {f3(c['ece_width10'])} | {f3(c['ece_count10'])} | {c['review_rate']:.1%} |")
    L.append(f"\nAny-head review rate: {results['all']['student']['review_rate_any_head']:.1%}\n")
    if adjudication:
        L += ["## Hybrid (what users see)", "",
              "Student label where confident; LLM label where the head is flagged (top prob < threshold). "
              "The teacher (14B, 3 votes) stands in for the live 7B decoder, so this is an optimistic proxy.", "",
              "| Head | Flagged | Label changed by LLM |", "|---|---|---|"]
        for h, v in adjudication.items():
            L.append(f"| {h} | {v['flagged']:.1%} | {v['changed']:.1%} |")
        L.append("")
    (run / "final_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    lk = json.loads(lock.read_text(encoding="utf-8"))
    lk["completed"] = datetime.now().isoformat(timespec="seconds")
    lock.write_text(json.dumps(lk, indent=2), encoding="utf-8")

    print(f"\nwrote {run / 'final_summary.md'} and final_eval.json\n")
    print(f"{'view':<28}{'system':<9}" + "".join(f"{k[:11]:>12}" for k in NAMES))
    for vname, per in results.items():
        for sname, r in per.items():
            print(f"{vname:<28}{sname:<9}" + "".join(
                f"{f3(r['views'][k]['macro_f1']):>8}{'✓' if r['views'][k]['pass'] else '✗':>4}" for k in NAMES))
    print("\n✓ = meets gate (human macro-F1 − 0.05). gold-test is now spent; log this run in decision_log.md.")


if __name__ == "__main__":
    main()
