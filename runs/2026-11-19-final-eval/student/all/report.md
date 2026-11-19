# Score report — 2026-11-19T21:36:37

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-19-final-eval\student\predictions.csv` (sha256 5cd2100499777a9a…)
- rows scored: 426 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 397 | **0.501** | 0.412–0.576 | 0.536 | 0.665 | 0.575 | FAIL |
| urgency | 376 | **0.286** | 0.249–0.326 | 0.301 | 0.559 | 0.390 | FAIL |
| sentiment | 400 | **0.372** | 0.317–0.430 | 0.415 | 0.705 | 0.412 | FAIL |
| type_action | 397 | **0.690** | 0.640–0.735 | – | 0.720 | 0.731 | FAIL |
| urgency_2 | 376 | **0.517** | 0.464–0.578 | – | 0.843 | 0.678 | FAIL |
| sentiment_2 | 400 | **0.622** | 0.566–0.675 | – | 0.738 | 0.633 | FAIL |

## type

Rows: 397 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.455 | 0.465 | 0.460 | 86 | 88 |
| Info | 0.740 | 0.840 | 0.787 | 244 | 277 |
| Credentials | 1.000 | 0.462 | 0.632 | 13 | 6 |
| Meeting | 0.500 | 0.167 | 0.250 | 24 | 8 |
| Approval | 0.500 | 0.300 | 0.375 | 30 | 18 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 40 | 41 | 0 | 1 | 4 |
| Info | 33 | 205 | 0 | 1 | 5 |
| Credentials | 0 | 7 | 6 | 0 | 0 |
| Meeting | 6 | 14 | 0 | 4 | 0 |
| Approval | 9 | 10 | 0 | 2 | 9 |

**Calibration** (strict rows, n=397): ECE equal-width-10 = **0.051**, equal-count-10 = 0.066. Review rate (top prob < 0.6) = 39.9% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 13 | 0.372 | 0.692 |
| 0.4–0.5 | 72 | 0.461 | 0.472 |
| 0.5–0.6 | 70 | 0.550 | 0.514 |
| 0.6–0.7 | 66 | 0.648 | 0.667 |
| 0.7–0.8 | 60 | 0.746 | 0.617 |
| 0.8–0.9 | 62 | 0.855 | 0.887 |
| 0.9–1.0 | 54 | 0.937 | 0.907 |

## urgency

Rows: 376 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 0 |
| High | 0.188 | 0.068 | 0.100 | 44 | 16 |
| Medium | 0.360 | 0.296 | 0.325 | 108 | 89 |
| Low | 0.646 | 0.806 | 0.717 | 217 | 271 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 1 | 5 |
| High | 0 | 3 | 21 | 20 |
| Medium | 0 | 5 | 32 | 71 |
| Low | 0 | 7 | 35 | 175 |

**Calibration** (strict rows, n=376): ECE equal-width-10 = **0.061**, equal-count-10 = 0.099. Review rate (top prob < 0.6) = 70.4% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 51 | 0.375 | 0.294 |
| 0.4–0.5 | 124 | 0.449 | 0.411 |
| 0.5–0.6 | 84 | 0.544 | 0.595 |
| 0.6–0.7 | 51 | 0.648 | 0.725 |
| 0.7–0.8 | 50 | 0.752 | 0.820 |
| 0.8–0.9 | 16 | 0.840 | 1.000 |
| 0.9–1.0 | 0 | – | – |

## sentiment

Rows: 400 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.391 | 0.500 | 0.439 | 36 | 46 |
| Neutral | 0.935 | 0.748 | 0.831 | 345 | 276 |
| Negative | 0.094 | 0.455 | 0.156 | 11 | 53 |
| Frustrated | 0.040 | 0.125 | 0.061 | 8 | 25 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 18 | 11 | 4 | 3 |
| Neutral | 27 | 258 | 40 | 20 |
| Negative | 0 | 5 | 5 | 1 |
| Frustrated | 1 | 2 | 4 | 1 |

**Calibration** (strict rows, n=400): ECE equal-width-10 = **0.043**, equal-count-10 = 0.033. Review rate (top prob < 0.6) = 37.6% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 23 | 0.369 | 0.478 |
| 0.4–0.5 | 51 | 0.457 | 0.373 |
| 0.5–0.6 | 75 | 0.551 | 0.587 |
| 0.6–0.7 | 61 | 0.659 | 0.672 |
| 0.7–0.8 | 70 | 0.757 | 0.829 |
| 0.8–0.9 | 69 | 0.856 | 0.870 |
| 0.9–1.0 | 51 | 0.939 | 0.961 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 78.9%

