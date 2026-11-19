#!/usr/bin/env python3
"""
train_heads.py — Phase C3. Trains the three student heads on teacher labels and calibrates them.

Run from ML_Training (defaults match the folder layout; ~2-10 min on a laptop CPU):
    python scripts\\train_heads.py
    python scripts\\train_heads.py --out model_v1 --run-name train-heads

Inputs (I3 + C2):
    Data\\pseudo\\pseudo_train.csv          teacher labels + weight_<head>
    Data\\emb\\pool_emb.npy / _uids.txt      embeddings (joined by uid, never by row order)
    Data\\gold_final\\gold_calib.csv + Data\\emb\\gold_calib_*   temperature calibration only
Outputs:
    <out>\\heads.npz + manifest.json        (I5)
    runs\\<date>-<run-name>\\config.json, metrics.json, fingerprints.json

Per head:
    rows      = non-blank label and weight_<head> > 0
    features  = embedding + one-hot role + one-hot position (common/student.py)
    weight    = balanced class weight n/(k*n_c) x teacher weight_<head>, rescaled to mean 1
    C         = argmin over {0.3, 1, 3} of 5-fold stratified CV log-loss (weighted like training)
    T         = argmin NLL of softmax(logits/T) on gold-calib strict rows (unweighted, real priors)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
from scipy.optimize import minimize_scalar  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import log_loss  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from common import metrics as M  # noqa: E402
from common import student as S  # noqa: E402

SEED = 42
C_GRID = [0.3, 1.0, 3.0]
N_FOLDS = 5


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg: str) -> None:
    sys.exit(f"ERROR: {msg}")


def balanced_weights(y: np.ndarray, classes: list[str]) -> dict[str, float]:
    n, k = len(y), len(classes)
    counts = {c: int((y == c).sum()) for c in classes}
    return {c: n / (k * counts[c]) for c in classes}


def fit_lr(X, y, w, C):
    clf = LogisticRegression(C=C, max_iter=3000, tol=1e-6, random_state=SEED)
    clf.fit(X, y, sample_weight=w)
    return clf


def fit_temperature(z: np.ndarray, y_idx: np.ndarray) -> tuple[float, float, float]:
    """Returns (T, nll_before, nll_after); NLL is the mean over rows."""
    def nll(logT):
        P = S.softmax(z / np.exp(logT))
        return float(-np.mean(np.log(np.clip(P[np.arange(len(y_idx)), y_idx], 1e-12, None))))
    r = minimize_scalar(nll, bounds=(np.log(0.05), np.log(20.0)), method="bounded",
                        options={"xatol": 1e-6})
    return float(np.exp(r.x)), nll(0.0), float(r.fun)


def text_check(df: pd.DataFrame, uid_col: str, emb_inputs_csv: Path, what: str) -> str:
    """The text that was embedded must be the text that was labelled."""
    if not emb_inputs_csv.exists():
        return f"skipped ({emb_inputs_csv.name} not found)"
    ref = pd.read_csv(emb_inputs_csv, dtype=str, keep_default_na=False).set_index("uid")["input_text"]
    mine = df.set_index(uid_col)["input_text"]
    common = mine.index.intersection(ref.index)
    diff = int((mine.loc[common] != ref.loc[common]).sum())
    if diff:
        fail(f"{what}: {diff} rows whose input_text differs from what was embedded ({emb_inputs_csv})")
    return f"ok ({len(common)} rows identical)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train", type=Path, default=ROOT / "Data" / "pseudo" / "pseudo_train.csv")
    ap.add_argument("--train-emb", type=Path, default=ROOT / "Data" / "emb" / "pool")
    ap.add_argument("--calib", type=Path, default=ROOT / "Data" / "gold_final" / "gold_calib.csv")
    ap.add_argument("--calib-emb", type=Path, default=ROOT / "Data" / "emb" / "gold_calib")
    ap.add_argument("--out", type=Path, default=ROOT / "model_v1")
    ap.add_argument("--run-name", default="train-heads")
    a = ap.parse_args()
    t_start = time.time()
    run = ROOT / "runs" / f"{date.today()}-{a.run_name}"
    run.mkdir(parents=True, exist_ok=True)

    # ---------------- load + checks
    tr = pd.read_csv(a.train, dtype=str, keep_default_na=False)
    need = ["email_uid", "input_text", "recipient_role", "recipient_position", *M.HEADS,
            *[f"weight_{h}" for h in M.HEADS]]
    if miss := [c for c in need if c not in tr.columns]:
        fail(f"training file missing columns {miss}")
    if tr["email_uid"].duplicated().any():
        fail("training file has duplicate email_uid")
    cal = pd.read_csv(a.calib, dtype=str, keep_default_na=False)

    E_pool, pool_uids = S.load_embeddings(a.train_emb)
    E_cal, cal_uids = S.load_embeddings(a.calib_emb)
    X_emb = S.align(E_pool, pool_uids, tr["email_uid"].tolist(), "training file")
    Xc_emb = S.align(E_cal, cal_uids, cal["email_uid"].tolist(), "gold_calib")

    checks = {"train_text": text_check(tr, "email_uid", ROOT / "Data" / "emb_inputs" / "pool.csv", "training file"),
              "calib_text": text_check(cal, "email_uid", ROOT / "Data" / "emb_inputs" / "gold_calib.csv", "gold_calib")}
    gold_uids = set()
    for n in ("gold_dev", "gold_calib", "gold_test"):
        p = ROOT / "Data" / "emb" / f"{n}_uids.txt"
        if p.exists():
            gold_uids |= set(p.read_text(encoding="utf-8").splitlines())
    leak = sorted(set(tr["email_uid"]) & gold_uids)
    if leak:
        fail(f"{len(leak)} training uids are gold emails, e.g. {leak[:3]}")
    checks["gold_overlap"] = f"0 of {len(gold_uids)} gold uids in training"
    for k, v in checks.items():
        print(f"check {k}: {v}")

    # ---------------- features
    role_cats = [r for r in S.ROLES_I1 if r in set(tr["recipient_role"])]
    pos_cats = [p for p in S.POSITIONS_I1 if p in set(tr["recipient_position"])]
    for fb, cats in ((S.ROLE_FALLBACK, role_cats), (S.POSITION_FALLBACK, pos_cats)):
        if fb not in cats:
            cats.append(fb)  # fallback must exist as a column even if training never used it
    X, unseen_tr = S.build_features(X_emb, tr["recipient_role"], tr["recipient_position"], role_cats, pos_cats)
    Xc, unseen_cal = S.build_features(Xc_emb, cal["recipient_role"], cal["recipient_position"], role_cats, pos_cats)
    print(f"features: {X.shape[1]} = {S.EMB_DIM} emb + {len(role_cats)} roles {role_cats} "
          f"+ {len(pos_cats)} positions {pos_cats}")
    if unseen_tr["role"] or unseen_tr["position"] or unseen_cal["role"] or unseen_cal["position"]:
        print(f"WARNING unseen categories mapped to fallback: train {unseen_tr}, calib {unseen_cal}")

    heads, manifest_heads, metrics = {}, {}, {"heads": {}}
    skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED)

    for h, classes in M.HEADS.items():
        t0 = time.time()
        w_teacher = pd.to_numeric(tr[f"weight_{h}"], errors="coerce").fillna(0).to_numpy()
        keep = (tr[h] != "").to_numpy() & (w_teacher > 0)
        y = tr.loc[keep, h].to_numpy()
        bad = sorted(set(y) - set(classes))
        if bad:
            fail(f"{h}: unknown labels {bad}")
        absent = [c for c in classes if c not in set(y)]
        if absent:
            fail(f"{h}: classes {absent} have no training rows; cannot train a {len(classes)}-class head")
        Xh = X[keep]
        cw = balanced_weights(y, classes)
        w = np.array([cw[c] for c in y]) * w_teacher[keep]
        w = w / w.mean()

        # ---- C by CV log-loss
        cv = {}
        for C in C_GRID:
            ll_w, ll_u, f1 = [], [], []
            for tr_i, va_i in skf.split(Xh, y):
                clf = fit_lr(Xh[tr_i], y[tr_i], w[tr_i], C)
                P = clf.predict_proba(Xh[va_i])
                ll_w.append(log_loss(y[va_i], P, sample_weight=w[va_i], labels=clf.classes_))
                ll_u.append(log_loss(y[va_i], P, labels=clf.classes_))
                f1.append(M.macro_f1(list(y[va_i]), list(clf.classes_[P.argmax(1)]), classes))
            cv[C] = {"logloss_weighted": float(np.mean(ll_w)), "logloss_unweighted": float(np.mean(ll_u)),
                     "macro_f1_vs_teacher": float(np.mean(f1)), "logloss_weighted_sd": float(np.std(ll_w))}
            print(f"  {h:<9} C={C:<4} cv logloss(w)={cv[C]['logloss_weighted']:.4f} "
                  f"macroF1 vs teacher={cv[C]['macro_f1_vs_teacher']:.3f}")
        C_best = min(C_GRID, key=lambda c: cv[c]["logloss_weighted"])

        # ---- final fit; reorder sklearn's (alphabetical) classes to I1 order
        clf = fit_lr(Xh, y, w, C_best)
        order = [list(clf.classes_).index(c) for c in classes]
        W, b = clf.coef_[order].copy(), clf.intercept_[order].copy()

        # ---- numpy vs sklearn parity (T = 1) on calib features
        P_sk = clf.predict_proba(Xc)[:, order]
        parity = float(np.abs(P_sk - S.head_proba(Xc, W, b)).max())
        if parity > 1e-6:
            fail(f"{h}: numpy heads differ from sklearn by {parity:.2e} (> 1e-6)")

        # ---- temperature on gold-calib strict rows
        cs = ((cal[f"{h}_strict"].str.lower() == "true") & (cal[h] != "")).to_numpy()
        yc = cal.loc[cs, h].tolist()
        yc_idx = np.array([classes.index(v) for v in yc])
        z = S.logits(Xc[cs], W, b)
        T, nll0, nll1 = fit_temperature(z, yc_idx)
        if T < 0.051 or T > 19.9:
            print(f"  WARNING {h}: temperature {T:.3f} hit the search bound [0.05, 20]; check calib labels/features")
        P0, P1 = S.softmax(z), S.softmax(z / T)
        pred_c = [classes[i] for i in P1.argmax(1)]
        correct = [p == t for p, t in zip(pred_c, yc)]
        ece0, _ = M.ece(P0.max(1), correct, 10, "width")
        ece1, bins1 = M.ece(P1.max(1), correct, 10, "width")
        ece1c, _ = M.ece(P1.max(1), correct, 10, "count")

        # ---- prior-corrected variant: undo the balanced weighting in the probabilities.
        # Balanced training learns p(c|x)/pi_c (up to a constant); adding log pi_c to the logits restores
        # real-world class frequencies. pi_c = teacher-weighted training share. T is refitted for this variant.
        prior = np.array([w_teacher[keep][y == c].sum() for c in classes])
        prior = prior / prior.sum()
        zp = z + np.log(prior)
        Tp, nllp0, nllp1 = fit_temperature(zp, yc_idx)
        Pp = S.softmax(zp / Tp)
        pred_p = [classes[i] for i in Pp.argmax(1)]
        ece_p, _ = M.ece(Pp.max(1), [p == t for p, t in zip(pred_p, yc)], 10, "width")

        heads[h] = (W, b)
        manifest_heads[h] = {"C": C_best, "temperature": T, "prior": prior.tolist(), "temperature_prior": Tp}
        metrics["heads"][h] = {
            "train_rows": int(keep.sum()), "dropped_blank_or_zero_weight": int((~keep).sum()),
            "class_counts": {c: int((y == c).sum()) for c in classes},
            "class_weight": cw, "teacher_weight_counts": {str(k): int(v) for k, v in
                                                         pd.Series(w_teacher[keep]).value_counts().items()},
            "cv": {str(k): v for k, v in cv.items()}, "C": C_best,
            "parity_max_abs_diff": parity,
            "calib": {"n": int(cs.sum()), "temperature": T, "nll_before": nll0, "nll_after": nll1,
                      "ece_width10_before": ece0, "ece_width10_after": ece1, "ece_count10_after": ece1c,
                      "review_rate_after": M.review_rate(P1.max(1)),
                      "macro_f1_indicative": M.macro_f1(yc, pred_c, classes), "bins_after": bins1},
            "calib_prior_corrected": {"prior": dict(zip(classes, prior.tolist())), "temperature": Tp,
                                      "nll_before": nllp0, "nll_after": nllp1, "ece_width10_after": ece_p,
                                      "review_rate_after": M.review_rate(Pp.max(1)),
                                      "macro_f1_indicative": M.macro_f1(yc, pred_p, classes)},
            "seconds": round(time.time() - t0, 1)}
        print(f"  {h:<9} -> C={C_best}  T={T:.3f}  calib NLL {nll0:.3f}->{nll1:.3f}  "
              f"ECE {ece0:.3f}->{ece1:.3f}  review {M.review_rate(P1.max(1)):.0%}  parity {parity:.1e}  "
              f"({time.time() - t0:.0f}s)")
        print(f"  {h:<9}    prior-corrected: T={Tp:.3f}  calib NLL {nllp0:.3f}->{nllp1:.3f}  ECE {ece_p:.3f}  "
              f"review {M.review_rate(Pp.max(1)):.0%}  macroF1(calib, indicative) "
              f"{M.macro_f1(yc, pred_c, classes):.3f}->{M.macro_f1(yc, pred_p, classes):.3f}")

    # ---------------- write model (I5) + run folder
    fp = {"train": {"path": str(a.train.relative_to(ROOT)), "sha256": sha256(a.train)},
          "train_emb": {"path": f"{a.train_emb.relative_to(ROOT)}_emb.npy", "sha256": sha256(Path(f"{a.train_emb}_emb.npy"))},
          "calib": {"path": str(a.calib.relative_to(ROOT)), "sha256": sha256(a.calib)},
          "calib_emb": {"path": f"{a.calib_emb.relative_to(ROOT)}_emb.npy", "sha256": sha256(Path(f"{a.calib_emb}_emb.npy"))}}
    manifest = {
        "model": a.out.name, "created": datetime.now().isoformat(timespec="seconds"),
        "encoder": S.ENCODER, "max_seq_length": S.MAX_TOKENS, "emb_dim": S.EMB_DIM, "normalised": True,
        "feature_order": ["embedding", "recipient_role", "recipient_position"],
        "roles": role_cats, "positions": pos_cats,
        "role_fallback": S.ROLE_FALLBACK, "position_fallback": S.POSITION_FALLBACK,
        "classes": dict(M.HEADS),
        "temperatures": {h: manifest_heads[h]["temperature"] for h in M.HEADS},
        "C": {h: manifest_heads[h]["C"] for h in M.HEADS},
        "class_prior": {h: manifest_heads[h]["prior"] for h in M.HEADS},
        "temperatures_prior": {h: manifest_heads[h]["temperature_prior"] for h in M.HEADS},
        "default_mode": "balanced",
        "class_weighting": "balanced n/(k*n_c) x teacher weight_<head>, mean 1",
        "training_file_sha256": fp["train"]["sha256"], "inputs": fp,
        "review_threshold": M.REVIEW_THRESHOLD, "seed": SEED,
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "sklearn": sklearn.__version__},
    }
    S.save_model(a.out, heads, manifest)
    config = {"argv": sys.argv[1:], "C_grid": C_GRID, "folds": N_FOLDS, "seed": SEED, "out": str(a.out)}
    metrics.update({"checks": checks, "unseen": {"train": unseen_tr, "calib": unseen_cal},
                    "features": int(X.shape[1]), "seconds_total": round(time.time() - t_start, 1)})

    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, float) and o != o:
            return None
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        return o

    for name, obj in (("config", config), ("metrics", metrics), ("fingerprints", fp)):
        (run / f"{name}.json").write_text(json.dumps(clean(obj), indent=2), encoding="utf-8")
    print(f"\nwrote {a.out / 'heads.npz'}, {a.out / 'manifest.json'} and {run}  "
          f"({time.time() - t_start:.0f}s total)")
    print("note: calib macro-F1/ECE above are on the same rows T was fitted on -> indicative only; "
          "C4 reports gold-dev, C5 gold-test.")


if __name__ == "__main__":
    main()
