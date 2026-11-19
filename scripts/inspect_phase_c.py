"""Phase C pre-flight: confirm I2/I3 and gold/baseline schemas before writing C1-C3.

Run from ML_Training:   python scripts/inspect_phase_c.py > runs/phase_c_inspect.txt
Read-only. Never opens anything under Data/sealed/ (only lists file names).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "Data"
HEADS = ["type", "urgency", "sentiment"]
SHOW_COUNTS = HEADS + ["recipient_role", "recipient_position", "sample"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def describe(df: pd.DataFrame, name: str, path: Path) -> None:
    print(f"\n=== {name}  ({path.relative_to(ROOT)})  sha256[:16]={sha(path)}")
    print(f"rows={len(df)}  cols={len(df.columns)}")
    print("columns:", list(df.columns))
    print("dtypes:", {c: str(t) for c, t in df.dtypes.items()})
    if "email_uid" in df.columns:
        print(f"email_uid unique={df['email_uid'].nunique()}  dupes={df['email_uid'].duplicated().sum()}  "
              f"example={df['email_uid'].iloc[0]!r}")
    for c in df.columns:
        if c in SHOW_COUNTS or c.endswith(("_status", "_strict", "_alt")) or c.startswith("weight"):
            vc = df[c].value_counts(dropna=False)
            if len(vc) <= 15:
                print(f"  {c}: {vc.to_dict()}")
            else:
                print(f"  {c}: {len(vc)} distinct; describe={df[c].describe().to_dict()}")
    if "input_text" in df.columns:
        lens = df["input_text"].fillna("").str.len()
        print(f"  input_text chars: median={lens.median():.0f} p95={lens.quantile(.95):.0f} "
              f"empty={(lens == 0).sum()}")
        print("  input_text[0][:200]:", repr(df["input_text"].iloc[0][:200]))


def main() -> None:
    print("ROOT:", ROOT)
    print("\nData/gold_final:", sorted(p.name for p in (D / "gold_final").glob("*")))
    sealed = D / "sealed"
    print("Data/sealed (names only):", sorted(p.name for p in sealed.glob("*")) if sealed.exists() else "MISSING")

    for name in ["gold_dev", "gold_calib"]:
        p = D / "gold_final" / f"{name}.csv"
        if p.exists():
            describe(pd.read_csv(p, keep_default_na=True), name, p)
        else:
            print(f"\n!! missing {p}")

    for name, p, reader in [
        ("pool (I2)", D / "pool" / "pool.parquet", pd.read_parquet),
        ("pseudo_train (I3)", D / "pseudo" / "pseudo_train.csv", pd.read_csv),
    ]:
        if p.exists():
            describe(reader(p), name, p)
        else:
            print(f"\n!! missing {p}  -> list of {p.parent}:",
                  sorted(x.name for x in p.parent.glob('*')) if p.parent.exists() else "no folder")

    # Cross-checks: overlap between pool/pseudo and gold (must be zero)
    try:
        gold_uids = set()
        for name in ["gold_dev", "gold_calib"]:
            gold_uids |= set(pd.read_csv(D / "gold_final" / f"{name}.csv", usecols=["email_uid"])["email_uid"])
        pseudo = pd.read_csv(D / "pseudo" / "pseudo_train.csv", usecols=["email_uid"])
        pool = pd.read_parquet(D / "pool" / "pool.parquet", columns=["email_uid"])
        print(f"\npseudo∩gold(dev+calib)={len(set(pseudo.email_uid) & gold_uids)}  "
              f"pseudo⊆pool={set(pseudo.email_uid) <= set(pool.email_uid)}  "
              f"pseudo rows={len(pseudo)} pool rows={len(pool)}")
    except Exception as e:  # noqa: BLE001
        print("\ncross-check skipped:", e)

    hb = D / "gold_final" / "human_baseline.json"
    if hb.exists():
        print(f"\n=== human_baseline.json  sha256[:16]={sha(hb)}")
        print(json.dumps(json.load(hb.open()), indent=1)[:4000])

    man = D / "gold_final" / "manifest.csv"
    for cand in [man, D / "labelling" / "manifest.csv", D / "sealed" / "manifest.csv"]:
        if cand.exists() and "sealed" not in cand.parts:
            m = pd.read_csv(cand, nrows=5)
            print(f"\n=== {cand.relative_to(ROOT)} columns:", list(m.columns))
            break
    else:
        hits = [str(p.relative_to(ROOT)) for p in D.rglob("manifest*.csv") if "sealed" not in p.parts]
        print("\nmanifest.csv candidates:", hits)


if __name__ == "__main__":
    main()
