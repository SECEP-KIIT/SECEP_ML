# Student heads (Phase C3): `scripts/train_heads.py` + `common/student.py`

## Run (from `ML_Training`)
```
python scripts\train_heads.py
```
Defaults: `Data\pseudo\pseudo_train.csv` + `Data\emb\pool_*` → `model_v1\`; calibration on `Data\gold_final\gold_calib.csv` + `Data\emb\gold_calib_*`.
Run log: `runs\<date>-train-heads\{config,metrics,fingerprints}.json`. Takes a few minutes on a laptop CPU.

## Before training it checks (and fails loudly otherwise)
- Every training uid has an embedding (joined **by uid**, never by row order).
- `input_text` in the training file and in gold_calib is byte-identical to what was embedded (`Data\emb_inputs\`).
- No training uid is a gold email (dev/calib/test uid lists).
- Every class of every head has at least one training row.
- numpy heads == scikit-learn `predict_proba` within 1e-6.

## Model (I5)
- Features: 768 mpnet dims + one-hot role + one-hot position, recorded in `manifest.json`.
- One multinomial logistic regression per head. A row is used for a head only if its label is non-blank and `weight_<head>` > 0.
- Sample weight = balanced class weight n/(k·n_c) × `weight_<head>`, rescaled to mean 1.
- C ∈ {0.3, 1, 3} chosen by 5-fold stratified CV log-loss (seed 42, weighted like training).
- Temperature per head, fitted on gold-calib strict rows by minimising NLL of softmax(logits/T).
- `heads.npz` holds plain arrays `W_<head>` (k × 777) and `b_<head>`; no pickle.

## Decisions (agreed 19 Nov 2026)
| Item | Choice | Why |
|---|---|---|
| Unseen role/position | Mapped to `Other` / `List/Unknown`, counted and warned | Those are the model's own catch-all categories, so its behaviour stays in-distribution. `Engineer` (in I1, absent from pool and gold) and `Bcc` (absent) take this path. |
| Class weighting | Fully balanced × teacher weight | Matches the plan and serves macro-F1, which the gate scores. Cost: the model leans toward rare classes, and rare-class probabilities run high. Temperature softens confidence but cannot undo that lean. |
| Temperature | One T per head on gold-calib | Fixes over/under-confidence so the 0.60 review threshold means what it says. Fitted on human-labelled gold-calib because the training data has teacher labels and balanced weights, and in-sample probabilities are always overconfident. |
| Leakage | Calib numbers printed by C3 are on the rows T was fitted on, so they are indicative only. Gold-dev (C4) was used for teacher tuning, so it is indicative too. The one clean score is gold-test, opened once in C5. | |

## Log in decision_log.md
- Truncation at 384 tokens: pool 28%, gold_dev 26%, gold_calib 22%, gold_test 27%. Median email 173 tokens, p95 ≈ 2,400 (long forwarded chains). No windowing (compressed-plan cut).
- gold_test has 426 rows (briefs said ~450).
- Teacher file: 10/29/8 rows without a majority for type/urgency/sentiment, weight 0, skipped per head.
- `Engineer` and `Bcc` never occur in training; at inference they map to `Other` / `List/Unknown`.
- Pool uid column is `pool_uid` (I2 says `email_uid`); the teacher file uses `email_uid`; the C3 join verifies they match.
