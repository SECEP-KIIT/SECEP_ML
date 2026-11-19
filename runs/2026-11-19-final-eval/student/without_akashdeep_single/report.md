# Score report — 2026-11-19T21:36:39

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-19-final-eval\student\predictions.csv` (sha256 5cd2100499777a9a…)
- rows scored: 375 (excluded 51; prediction rows ignored as not in gold: 51)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 346 | **0.498** | 0.393–0.582 | 0.536 | 0.665 | 0.575 | FAIL |
| urgency | 325 | **0.293** | 0.254–0.395 | 0.310 | 0.572 | 0.390 | FAIL |
| sentiment | 349 | **0.379** | 0.318–0.442 | 0.428 | 0.713 | 0.412 | FAIL |
| type_action | 346 | **0.695** | 0.640–0.745 | – | 0.720 | 0.731 | FAIL |
| urgency_2 | 325 | **0.525** | 0.465–0.590 | – | 0.843 | 0.678 | FAIL |
| sentiment_2 | 349 | **0.643** | 0.580–0.697 | – | 0.751 | 0.633 | **PASS** |

## type

Rows: 346 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.494 | 0.488 | 0.491 | 82 | 81 |
| Info | 0.731 | 0.841 | 0.782 | 207 | 238 |
| Credentials | 1.000 | 0.364 | 0.533 | 11 | 4 |
| Meeting | 0.500 | 0.167 | 0.250 | 24 | 8 |
| Approval | 0.533 | 0.364 | 0.432 | 22 | 15 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 40 | 37 | 0 | 1 | 4 |
| Info | 29 | 174 | 0 | 1 | 3 |
| Credentials | 0 | 7 | 4 | 0 | 0 |
| Meeting | 6 | 14 | 0 | 4 | 0 |
| Approval | 6 | 6 | 0 | 2 | 8 |

**Calibration** (strict rows, n=346): ECE equal-width-10 = **0.050**, equal-count-10 = 0.072. Review rate (top prob < 0.6) = 41.1% of 375 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 12 | 0.370 | 0.750 |
| 0.4–0.5 | 63 | 0.460 | 0.476 |
| 0.5–0.6 | 64 | 0.552 | 0.484 |
| 0.6–0.7 | 56 | 0.645 | 0.643 |
| 0.7–0.8 | 50 | 0.745 | 0.640 |
| 0.8–0.9 | 54 | 0.855 | 0.889 |
| 0.9–1.0 | 47 | 0.936 | 0.936 |

## urgency

Rows: 325 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 3 | 0 |
| High | 0.188 | 0.075 | 0.107 | 40 | 16 |
| Medium | 0.389 | 0.298 | 0.337 | 94 | 72 |
| Low | 0.654 | 0.824 | 0.729 | 188 | 237 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 0 | 2 |
| High | 0 | 3 | 18 | 19 |
| Medium | 0 | 5 | 28 | 61 |
| Low | 0 | 7 | 26 | 155 |

**Calibration** (strict rows, n=325): ECE equal-width-10 = **0.072**, equal-count-10 = 0.111. Review rate (top prob < 0.6) = 70.9% of 375 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 45 | 0.376 | 0.267 |
| 0.4–0.5 | 105 | 0.449 | 0.429 |
| 0.5–0.6 | 75 | 0.543 | 0.600 |
| 0.6–0.7 | 44 | 0.648 | 0.750 |
| 0.7–0.8 | 43 | 0.753 | 0.884 |
| 0.8–0.9 | 13 | 0.839 | 1.000 |
| 0.9–1.0 | 0 | – | – |

## sentiment

Rows: 349 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.436 | 0.486 | 0.459 | 35 | 39 |
| Neutral | 0.927 | 0.767 | 0.839 | 296 | 245 |
| Negative | 0.093 | 0.400 | 0.151 | 10 | 43 |
| Frustrated | 0.045 | 0.125 | 0.067 | 8 | 22 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 17 | 11 | 4 | 3 |
| Neutral | 21 | 227 | 31 | 17 |
| Negative | 0 | 5 | 4 | 1 |
| Frustrated | 1 | 2 | 4 | 1 |

**Calibration** (strict rows, n=349): ECE equal-width-10 = **0.051**, equal-count-10 = 0.042. Review rate (top prob < 0.6) = 37.1% of 375 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 21 | 0.370 | 0.524 |
| 0.4–0.5 | 42 | 0.456 | 0.357 |
| 0.5–0.6 | 65 | 0.551 | 0.600 |
| 0.6–0.7 | 50 | 0.658 | 0.700 |
| 0.7–0.8 | 63 | 0.755 | 0.810 |
| 0.8–0.9 | 62 | 0.856 | 0.871 |
| 0.9–1.0 | 46 | 0.941 | 0.957 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 78.9%

