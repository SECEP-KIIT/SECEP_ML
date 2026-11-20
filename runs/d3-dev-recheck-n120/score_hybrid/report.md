# Score report — 2026-11-20T04:41:59

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\d3-dev-recheck-n120\gold_eval.csv` (sha256 cfe84b7032c1ed2f…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\d3-dev-recheck-n120\predictions_hybrid.csv` (sha256 a04a7df359212067…)
- rows scored: 120 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 120 | **0.619** | 0.429–0.755 | 0.619 | 0.742 | 0.575 | **PASS** |
| urgency | 120 | **0.443** | 0.349–0.528 | 0.443 | 0.700 | 0.390 | **PASS** |
| sentiment | 120 | **0.324** | 0.258–0.391 | 0.324 | 0.750 | 0.412 | FAIL |
| type_action | 120 | **0.777** | 0.692–0.850 | – | 0.792 | 0.731 | **PASS** |
| urgency_2 | 120 | **0.676** | 0.531–0.799 | – | 0.883 | 0.678 | FAIL |
| sentiment_2 | 120 | **0.589** | 0.485–0.696 | – | 0.758 | 0.633 | FAIL |

## type

Rows: 120 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.652 | 0.517 | 0.577 | 29 | 23 |
| Info | 0.750 | 0.940 | 0.834 | 67 | 84 |
| Credentials | 1.000 | 0.333 | 0.500 | 3 | 1 |
| Meeting | 1.000 | 0.375 | 0.545 | 8 | 3 |
| Approval | 0.778 | 0.538 | 0.636 | 13 | 9 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 15 | 12 | 0 | 0 | 2 |
| Info | 4 | 63 | 0 | 0 | 0 |
| Credentials | 0 | 2 | 1 | 0 | 0 |
| Meeting | 1 | 4 | 0 | 3 | 0 |
| Approval | 3 | 3 | 0 | 0 | 7 |

**Calibration** (strict rows, n=120): ECE equal-width-10 = **0.144**, equal-count-10 = 0.160. Review rate (top prob < 0.6) = 0.0% of 120 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 22 | 0.645 | 0.682 |
| 0.7–0.8 | 20 | 0.757 | 0.600 |
| 0.8–0.9 | 12 | 0.856 | 0.667 |
| 0.9–1.0 | 66 | 0.986 | 0.818 |

## urgency

Rows: 120 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 5 | 0 |
| High | 0.667 | 0.308 | 0.421 | 13 | 6 |
| Medium | 0.571 | 0.485 | 0.525 | 33 | 28 |
| Low | 0.744 | 0.928 | 0.826 | 69 | 86 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 4 | 0 |
| High | 0 | 4 | 3 | 6 |
| Medium | 0 | 1 | 16 | 16 |
| Low | 0 | 0 | 5 | 64 |

**Calibration** (strict rows, n=120): ECE equal-width-10 = **0.251**, equal-count-10 = 0.259. Review rate (top prob < 0.6) = 0.0% of 120 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 19 | 0.650 | 0.684 |
| 0.7–0.8 | 10 | 0.753 | 0.900 |
| 0.8–0.9 | 7 | 0.842 | 0.857 |
| 0.9–1.0 | 84 | 0.999 | 0.667 |

## sentiment

Rows: 120 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.429 | 0.462 | 0.444 | 13 | 14 |
| Neutral | 0.857 | 0.848 | 0.853 | 99 | 98 |
| Negative | 0.000 | 0.000 | 0.000 | 4 | 8 |
| Frustrated | 0.000 | 0.000 | 0.000 | 4 | 0 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 6 | 7 | 0 | 0 |
| Neutral | 7 | 84 | 8 | 0 |
| Negative | 1 | 3 | 0 | 0 |
| Frustrated | 0 | 4 | 0 | 0 |

**Calibration** (strict rows, n=120): ECE equal-width-10 = **0.126**, equal-count-10 = 0.142. Review rate (top prob < 0.6) = 0.0% of 120 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 16 | 0.654 | 0.438 |
| 0.7–0.8 | 26 | 0.752 | 0.769 |
| 0.8–0.9 | 17 | 0.858 | 0.824 |
| 0.9–1.0 | 61 | 0.977 | 0.803 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.0%

