#!/usr/bin/env python3
"""
make_fake_preds.py — Phase C1 self-test. Writes three fake I4 prediction files for a gold file.

Run from ML_Training:
    python scripts\\make_fake_preds.py --gold Data\\gold_final\\gold_dev.csv --out runs\\<date>-scorer-selftest\\fake

    perfect.csv   every head = gold label, one-hot probabilities      -> strict macro-F1 must be 1.0
    all_info.csv  type = Info for every row (urgency, sentiment = gold) -> compare with the hand calculation
    random.csv    random probabilities (Dirichlet(1), seed 42), pred = argmax

Rows with a blank gold label get the first class (they are never scored).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import metrics as M  # noqa: E402


def one_hot(labels: list[str], classes: list[str]) -> np.ndarray:
    P = np.zeros((len(labels), len(classes)))
    P[np.arange(len(labels)), [classes.index(v) for v in labels]] = 1.0
    return P


def frame(uids, labels: dict, probs: dict) -> pd.DataFrame:
    df = pd.DataFrame({"email_uid": uids})
    for h, classes in M.HEADS.items():
        df[f"pred_{h}"] = labels[h]
        for j, c in enumerate(classes):
            df[f"prob_{h}_{c}"] = np.round(probs[h][:, j], 6)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    gold = pd.read_csv(a.gold, dtype=str, keep_default_na=False)
    uids = gold["email_uid"].tolist()
    a.out.mkdir(parents=True, exist_ok=True)

    gl = {h: [v if v else cs[0] for v in gold[h]] for h, cs in M.HEADS.items()}

    frame(uids, gl, {h: one_hot(gl[h], cs) for h, cs in M.HEADS.items()}).to_csv(a.out / "perfect.csv", index=False)

    ai = dict(gl, type=["Info"] * len(uids))
    frame(uids, ai, {h: one_hot(ai[h], cs) for h, cs in M.HEADS.items()}).to_csv(a.out / "all_info.csv", index=False)

    rng = np.random.default_rng(M.SEED)
    rp = {h: rng.dirichlet(np.ones(len(cs)), size=len(uids)) for h, cs in M.HEADS.items()}
    rp = {h: np.round(P, 6) / np.round(P, 6).sum(axis=1, keepdims=True) for h, P in rp.items()}
    rl = {h: [cs[j] for j in rp[h].argmax(axis=1)] for h, cs in M.HEADS.items()}
    frame(uids, rl, rp).to_csv(a.out / "random.csv", index=False)

    # Hand calculation for all-Info on type (strict rows only): Info F1 = 2*n_info/(2*n_info + n_other),
    # every other used class has tp=0 -> F1 0; macro = Info F1 / number of used classes.
    s = gold[(gold["type_strict"].str.lower() == "true") & (gold["type"] != "")]["type"]
    n_info, n_other = int((s == "Info").sum()), int((s != "Info").sum())
    used = sorted(set(s) | {"Info"})
    f_info = 2 * n_info / (2 * n_info + n_other)
    print(f"wrote perfect.csv, all_info.csv, random.csv to {a.out}")
    print(f"expected all_info type: Info F1 = 2*{n_info}/(2*{n_info}+{n_other}) = {f_info:.6f}; "
          f"used classes {used} -> macro-F1 = {f_info:.6f}/{len(used)} = {f_info / len(used):.6f}; "
          f"accuracy = {n_info}/{n_info + n_other} = {n_info / (n_info + n_other):.6f}")
    print(f"expected all_info type_action: macro-F1 = ({f_info:.6f} + 0)/2 = {f_info / 2:.6f}")


if __name__ == "__main__":
    main()
