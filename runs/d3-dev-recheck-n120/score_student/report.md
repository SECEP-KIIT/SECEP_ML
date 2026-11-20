# Score report — 2026-11-20T04:41:58

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\d3-dev-recheck-n120\gold_eval.csv` (sha256 cfe84b7032c1ed2f…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\d3-dev-recheck-n120\predictions_student.csv` (sha256 d4319e0d5dd7c6dd…)
- rows scored: 120 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 120 | **0.523** | 0.347–0.658 | 0.523 | 0.667 | 0.575 | FAIL |
| urgency | 120 | **0.396** | 0.254–0.538 | 0.396 | 0.583 | 0.390 | **PASS** |
| sentiment | 120 | **0.295** | 0.233–0.352 | 0.295 | 0.658 | 0.412 | FAIL |
| type_action | 120 | **0.705** | 0.610–0.782 | – | 0.725 | 0.731 | FAIL |
| urgency_2 | 120 | **0.677** | 0.543–0.799 | – | 0.867 | 0.678 | FAIL |
| sentiment_2 | 120 | **0.557** | 0.467–0.652 | – | 0.683 | 0.633 | FAIL |

## type

Rows: 120 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.458 | 0.379 | 0.415 | 29 | 24 |
| Info | 0.702 | 0.881 | 0.781 | 67 | 84 |
| Credentials | 1.000 | 0.333 | 0.500 | 3 | 1 |
| Meeting | 1.000 | 0.125 | 0.222 | 8 | 1 |
| Approval | 0.800 | 0.615 | 0.696 | 13 | 10 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 11 | 16 | 0 | 0 | 2 |
| Info | 8 | 59 | 0 | 0 | 0 |
| Credentials | 0 | 2 | 1 | 0 | 0 |
| Meeting | 1 | 6 | 0 | 1 | 0 |
| Approval | 4 | 1 | 0 | 0 | 8 |

**Calibration** (strict rows, n=120): ECE equal-width-10 = **0.093**, equal-count-10 = 0.149. Review rate (top prob < 0.6) = 40.8% of 120 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 3 | 0.366 | 0.333 |
| 0.4–0.5 | 21 | 0.455 | 0.667 |
| 0.5–0.6 | 25 | 0.549 | 0.560 |
| 0.6–0.7 | 22 | 0.645 | 0.682 |
| 0.7–0.8 | 20 | 0.757 | 0.600 |
| 0.8–0.9 | 12 | 0.856 | 0.667 |
| 0.9–1.0 | 17 | 0.944 | 0.941 |

## urgency

Rows: 120 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 1.000 | 0.200 | 0.333 | 5 | 1 |
| High | 0.222 | 0.154 | 0.182 | 13 | 9 |
| Medium | 0.429 | 0.273 | 0.333 | 33 | 21 |
| Low | 0.652 | 0.841 | 0.734 | 69 | 89 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 1 | 3 | 0 | 1 |
| High | 0 | 2 | 2 | 9 |
| Medium | 0 | 3 | 9 | 21 |
| Low | 0 | 1 | 10 | 58 |

**Calibration** (strict rows, n=120): ECE equal-width-10 = **0.049**, equal-count-10 = 0.111. Review rate (top prob < 0.6) = 69.2% of 120 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 12 | 0.379 | 0.500 |
| 0.4–0.5 | 50 | 0.446 | 0.440 |
| 0.5–0.6 | 21 | 0.535 | 0.619 |
| 0.6–0.7 | 19 | 0.650 | 0.684 |
| 0.7–0.8 | 10 | 0.753 | 0.900 |
| 0.8–0.9 | 7 | 0.842 | 0.857 |
| 0.9–1.0 | 1 | 0.904 | 1.000 |

## sentiment

Rows: 120 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.333 | 0.462 | 0.387 | 13 | 18 |
| Neutral | 0.859 | 0.737 | 0.793 | 99 | 85 |
| Negative | 0.000 | 0.000 | 0.000 | 4 | 14 |
| Frustrated | 0.000 | 0.000 | 0.000 | 4 | 3 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 6 | 6 | 1 | 0 |
| Neutral | 10 | 73 | 13 | 3 |
| Negative | 2 | 2 | 0 | 0 |
| Frustrated | 0 | 4 | 0 | 0 |

**Calibration** (strict rows, n=120): ECE equal-width-10 = **0.062**, equal-count-10 = 0.108. Review rate (top prob < 0.6) = 32.5% of 120 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 6 | 0.362 | 0.167 |
| 0.4–0.5 | 19 | 0.451 | 0.474 |
| 0.5–0.6 | 14 | 0.567 | 0.500 |
| 0.6–0.7 | 16 | 0.654 | 0.438 |
| 0.7–0.8 | 26 | 0.752 | 0.769 |
| 0.8–0.9 | 17 | 0.858 | 0.824 |
| 0.9–1.0 | 22 | 0.935 | 0.955 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 74.2%

