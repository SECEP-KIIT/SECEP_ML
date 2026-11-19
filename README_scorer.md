# Scorer (Phase C1): `common/metrics.py` + `scripts/score.py`

Every number in the report comes from here. The maths is in `common/metrics.py` as pure functions; `score.py` only reads, validates and writes.

## Run (from `ML_Training`)

```
python -m pytest tests -q
python scripts\make_fake_preds.py --gold Data\gold_final\gold_dev.csv --out runs\2026-11-19-scorer-selftest\fake
python scripts\score.py --gold Data\gold_final\gold_dev.csv --pred runs\2026-11-19-scorer-selftest\fake\perfect.csv  --out runs\2026-11-19-scorer-selftest\perfect  --baseline Data\gold_final\human_baseline.json
python scripts\score.py --gold Data\gold_final\gold_dev.csv --pred runs\2026-11-19-scorer-selftest\fake\all_info.csv --out runs\2026-11-19-scorer-selftest\all_info --baseline Data\gold_final\human_baseline.json
python scripts\score.py --gold Data\gold_final\gold_dev.csv --pred runs\2026-11-19-scorer-selftest\fake\random.csv   --out runs\2026-11-19-scorer-selftest\random   --baseline Data\gold_final\human_baseline.json
```

Optional: `--exclude-uids file.txt` (one uid per line; `#` comments are allowed) and `--n-boot` (default 2000).

Outputs: `metrics.json` (config, SHA-256 of every input, all numbers) and `report.md` (gate table, per-class P/R/F1, confusion matrices, calibration bins).

## What it reports (per head; merged views in brackets)
1. **Strict**: rows with `<head>_strict == True` and a non-blank label. Macro-F1, accuracy, per-class P/R/F1/support, confusion matrix.
2. **Lenient**: all non-blank rows. A prediction is correct if it equals `<head>` or `<head>_alt`.
3. **Merged views** (strict): type_action, urgency_2, sentiment_2, with the same class labels as `human_baseline.py`.
4. **Gate** (`--baseline`): PASS if strict macro-F1 ≥ `teacher_gate_macro_f1`, per head and per view.
5. **Bootstrap 95% CI** for every macro-F1: 2,000 resamples of emails, seed 42, percentile method.
6. **Calibration** (only when `prob_*` columns exist): ECE with 10 equal-width bins (headline) and 10 equal-count bins (secondary), on strict rows. Review rate = share of all rows with top probability < 0.60, per head and for any head.

## Decisions (agreed 19 Nov 2026)
| Item | Choice | Why |
|---|---|---|
| Lenient F1 | Correct → the truth is the label the prediction matched. Wrong → the truth is the **primary** label. | Deterministic, and the primary label is the one the precedence rules chose. |
| Absent classes | **Same as `human_baseline.py`**: a class is dropped from the macro average only if neither truth nor prediction uses it. A class that is predicted but absent from the truth stays in with F1 = 0. The same rule applies inside every bootstrap resample. | The gate compares the model against the human number, so both must be computed the same way. This equals sklearn `f1_score(labels=<used classes>, average="macro", zero_division=0)`, which a test checks. |
| ECE | Top-label; 10 equal-width bins as the headline, 10 equal-count as a secondary number; bin counts reported. | Equal-width is the standard and comparable. With ~180 rows some width bins are sparse, so equal-count shows whether the headline is stable. |
| Bad input | **Fail loudly**: unknown or blank class, duplicate uid, gold uid missing from the predictions, partial or non-numeric probability columns, probability sum off by > 1e-3. Sums within 1e-3 are renormalised silently. Extra prediction rows (uids not in gold) are ignored and counted. | Every report number comes from this code, so a silent error is worse than a crash. Ignoring extra rows lets one predictions file cover dev + calib. |

Notes:
- Gold is read as text (`dtype=str, keep_default_na=False`), the same as `human_baseline.py`. Otherwise an all-blank `*_alt` column loads as float NaN.
- Bootstrap CIs use numpy's generator with seed 42. `human_baseline.py` used Python `random` with seed 0. The CIs are therefore not bit-identical, but the point estimates are.
- On gold-dev and gold-calib every row is `single` and strict, so lenient = strict there. The lenient score only differs on gold-test.
- **The teacher's predictions file must give a label for every row.** If the 3 teacher votes all differ, Phase B has to pick one (for example the first sample), with probabilities ⅓/⅓/⅓. A blank label fails the run.

## Self-test results (paste the gold-dev output here)
Hand calculation for **all-Info** on gold-dev type (Info 100, Task 53, Approval 16, Meeting 13, Credentials 2):
- Info: tp = 100, fp = 84, fn = 0 → F1 = 200/284 = **0.704225**. The other four classes each have tp = 0 → F1 0.
- Macro-F1 = 0.704225 / 5 = **0.140845**. Accuracy = 100/184 = 0.543478.
- type_action macro-F1 = (0.704225 + 0) / 2 = **0.352113**.

| File | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 |
|---|---|---|---|---|---|---|
| perfect | (must be 1.000) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| all_info | (must be 0.141) | (gold → 1.000) | (gold → 1.000) | (must be 0.352) | 1.000 | 1.000 |
| random | … | … | … | … | … | … |

`tests/test_metrics.py` covers the lenient rule, the absent-class rule (both directions plus sklearn parity), the hand calculation, view labels, confusion orientation, bootstrap determinism, ECE and review rate.
