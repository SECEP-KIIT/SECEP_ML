#!/usr/bin/env python3
"""
prepare_embed_inputs.py — Phase C2, step 1 (local). Builds the text-only upload for Kaggle.

Run from ML_Training:
    python scripts\\prepare_embed_inputs.py

Writes Data\\emb_inputs\\:
    pool.csv, gold_dev.csv, gold_calib.csv, gold_test.csv   columns: uid, input_text   (nothing else)
    embed.py                                                 copy of scripts\\embed.py, for the notebook
    inputs_manifest.json                                     row counts, source + output SHA-256, text_version

gold_test: only email_uid and input_text are read (usecols), so no label column is ever loaded.
The test file stays sealed for scoring until C5; its embeddings are computed now only so the
same encoder run covers every split.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "Data"
OUT = D / "emb_inputs"

SOURCES = {  # name -> (path, uid column)
    "pool": (D / "pool" / "pool.parquet", "pool_uid"),
    "gold_dev": (D / "gold_final" / "gold_dev.csv", "email_uid"),
    "gold_calib": (D / "gold_final" / "gold_calib.csv", "email_uid"),
    "gold_test": (D / "gold_final" / "gold_test.csv", "email_uid"),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path, cols: list[str]) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=cols).astype(str)
    return pd.read_csv(path, usecols=cols, dtype=str, keep_default_na=False)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"created": datetime.now().isoformat(timespec="seconds"), "files": {}}
    for name, (src, uid_col) in SOURCES.items():
        cols = [uid_col, "input_text", "text_version"]
        try:
            df = read(src, cols)
        except (ValueError, KeyError):          # no text_version column
            cols = cols[:2]
            df = read(src, cols)
        if df[uid_col].duplicated().any():
            raise SystemExit(f"ERROR: {name}: duplicate {uid_col}")
        empty = int((df["input_text"].str.strip() == "").sum())
        if empty:
            raise SystemExit(f"ERROR: {name}: {empty} rows with empty input_text")
        versions = sorted(df["text_version"].unique().tolist()) if "text_version" in df else ["(none)"]
        out = OUT / f"{name}.csv"
        df.rename(columns={uid_col: "uid"})[["uid", "input_text"]].to_csv(out, index=False, encoding="utf-8")
        manifest["files"][name] = {"source": str(src.relative_to(ROOT)), "source_sha256": sha256(src),
                                   "uid_column": uid_col, "rows": len(df), "text_version": versions,
                                   "csv_sha256": sha256(out)}
        print(f"{name:<11} {len(df):>6} rows  text_version={versions}  -> {out.relative_to(ROOT)}")

    def norm(v: str) -> str:  # "1" and "1.0" are the same version
        try:
            return str(float(v))
        except ValueError:
            return v

    vs = {n: tuple(f["text_version"]) for n, f in manifest["files"].items()}
    if len({tuple(norm(x) for x in v) for v in vs.values()}) > 1:
        print("\nWARNING: text_version differs between files:", vs,
              "\n  -> check these are the same common/text.py recipe before trusting the embeddings.")

    shutil.copy2(ROOT / "scripts" / "embed.py", OUT / "embed.py")
    (OUT / "inputs_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total = sum(p.stat().st_size for p in OUT.iterdir()) / 1e6
    print(f"\nUpload the contents of {OUT.relative_to(ROOT)} ({total:.1f} MB) as a private Kaggle dataset.")


if __name__ == "__main__":
    main()
