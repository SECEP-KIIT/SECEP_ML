#!/usr/bin/env python3
"""
rebuild_gold_text.py — Stage 0, Job 3.

Re-reads every gold email from the ORIGINAL Enron file and runs it through the
shared recipe in common/text.py, so the gold sets hold the same full, cleaned text
that training and the live system will use. Labels are not touched.

Run from  C:\\Dev\\SECEP_ML\\ML_Training :
    python scripts\\rebuild_gold_text.py

Defaults (change with flags if your folders differ):
    --gold-dir  Data\\gold_final
    --maildir   Data\\raw\\maildir

What it does
  1. Backs up the current gold files to  gold_final\\_backup_<time>\\
  2. For each email in gold_test / gold_dev / gold_calib:
       - opens maildir\\<source_path>, checks its Message-ID matches the manifest
       - runs common.text.process()
       - replaces subject/body with the clean versions; adds input_text,
         quoted, masked_kinds, body_chars, text_version
       - keeps the old sheet text as body_sheet (for comparison only)
  3. Writes the files back (.csv and .parquet), recomputes SHA-256 fingerprints,
     updates gold_test.sha256 and appends an entry to decision_log.md
  If ANY email cannot be found or does not match, nothing is overwritten.
"""
import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # ...\ML_Training
sys.path.insert(0, str(ROOT))

import pandas as pd                                  # noqa: E402
from common.text import TEXT_VERSION, process        # noqa: E402

SPLITS = ["test", "dev", "calib"]


def win_long(path: str) -> str:
    """Enron files are named '1.', '2.' … and Windows drops a trailing dot from
    normal paths. The \\\\?\\ prefix stops that."""
    if os.name != "nt":
        return path
    path = os.path.abspath(path)
    if path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold-dir", default=str(ROOT / "Data" / "gold_final"))
    ap.add_argument("--maildir", default=str(ROOT / "Data" / "raw" / "maildir"))
    a = ap.parse_args()
    gold_dir, maildir = Path(a.gold_dir), Path(a.maildir)
    if not gold_dir.is_dir():
        sys.exit(f"Gold folder not found: {gold_dir}")
    if not maildir.is_dir():
        sys.exit(f"maildir not found: {maildir}\nMove the Enron 'maildir' folder there, or pass --maildir <path>.")

    frames, problems = {}, []
    for sp in SPLITS:
        f = gold_dir / f"gold_{sp}.csv"
        if not f.exists():
            sys.exit(f"Missing {f}")
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        if "body_sheet" in df.columns:
            sys.exit(f"{f.name} already has body_sheet — it looks rebuilt already. "
                     "Restore from a _backup_ folder if you want to run again.")
        out = []
        for _, r in df.iterrows():
            rel = [p for p in re.split(r"[\\/]", r["source_path"]) if p]
            path = win_long(str(maildir.joinpath(*rel)))
            try:
                with open(path, "rb") as fh:
                    raw = fh.read()
            except OSError as e:
                problems.append((sp, r["email_uid"], "file not found", f"{r['source_path']} ({e.__class__.__name__})"))
                out.append(None)
                continue
            p = process(raw)
            if r.get("message_id") and p["message_id"].strip() != r["message_id"].strip():
                problems.append((sp, r["email_uid"], "Message-ID mismatch",
                                 f"manifest {r['message_id']} vs file {p['message_id']}"))
            out.append(p)
        frames[sp] = (df, out)
        print(f"  gold_{sp}: read {sum(o is not None for o in out)}/{len(df)} emails")

    if problems:
        rep = gold_dir / "rebuild_problems.csv"
        pd.DataFrame(problems, columns=["split", "email_uid", "problem", "detail"]).to_csv(rep, index=False)
        sys.exit(f"\n{len(problems)} problem(s) — nothing was changed. See {rep}\n"
                 "Usual cause: --maildir points at the wrong folder, or extraction was incomplete.")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = gold_dir / f"_backup_{stamp}"
    backup.mkdir()
    for f in gold_dir.iterdir():
        if f.is_file() and (f.name.startswith("gold_") or f.name == "decision_log.md"):
            shutil.copy2(f, backup / f.name)

    hashes, stats = {}, []
    for sp in SPLITS:
        df, out = frames[sp]
        df = df.copy()
        df["body_sheet"] = df["body"]
        df["subject"] = [p["subject"] for p in out]
        df["body"] = [p["body"] for p in out]
        df["quoted"] = [p["quoted"] for p in out]
        df["input_text"] = [p["input_text"] for p in out]
        df["masked_kinds"] = ["|".join(p["masked_kinds"]) for p in out]
        df["body_chars"] = [len(p["body"]) for p in out]
        df["text_version"] = TEXT_VERSION
        csv_path = gold_dir / f"gold_{sp}.csv"
        df.to_csv(csv_path, index=False)
        try:
            df.to_parquet(gold_dir / f"gold_{sp}.parquet", index=False)
        except Exception as e:
            print(f"  (parquet not written for {sp}: {e.__class__.__name__}; CSV is enough)")
        hashes[sp] = sha256(csv_path)
        stats.append((sp, len(df), int((df["body_chars"] > 6000).sum()),
                      int((df["masked_kinds"] != "").sum()), int((df["body_chars"] < 20).sum()),
                      int(df["body_chars"].median())))

    (gold_dir / "gold_test.sha256").write_text(f"{hashes['test']}  gold_test.csv\n", encoding="utf-8")
    entry = [
        "", f"## Stage 0 — gold text rebuilt ({stamp})", "",
        f"- Text recipe: common/text.py, TEXT_VERSION {TEXT_VERSION}",
        "- Source: original Enron files via manifest source_path; Message-IDs verified",
        "- Labels unchanged; previous sheet text kept as body_sheet",
        f"- Backup of previous files: {backup.name}/",
        *[f"- gold_{sp}: {n} emails · {longer} were longer than the sheet's 6,000-char cut · "
          f"{masked} had secrets masked · {tiny} near-empty bodies · median {med} chars"
          for sp, n, longer, masked, tiny, med in stats],
        *[f"- gold_{sp}.csv sha256 `{h}`" for sp, h in hashes.items()],
        "- gold-test is SEALED from this point until final evaluation.",
    ]
    with open(gold_dir / "decision_log.md", "a", encoding="utf-8") as fh:
        fh.write("\n".join(entry) + "\n")

    print("\nDone. Summary:")
    print("\n".join(entry[3:]))


if __name__ == "__main__":
    main()
