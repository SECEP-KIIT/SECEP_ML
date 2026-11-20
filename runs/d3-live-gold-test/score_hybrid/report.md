# Score report — 2026-11-20T05:51:05

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\d3-live-gold-test\gold_eval.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\d3-live-gold-test\predictions_hybrid.csv` (sha256 b0a06512e6cde0e9…)
- rows scored: 426 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 397 | **0.617** | 0.523–0.688 | 0.668 | 0.743 | 0.575 | **PASS** |
| urgency | 376 | **0.409** | 0.360–0.458 | 0.433 | 0.670 | 0.390 | **PASS** |
| sentiment | 400 | **0.437** | 0.360–0.517 | 0.493 | 0.838 | 0.412 | **PASS** |
| type_action | 397 | **0.772** | 0.727–0.812 | – | 0.793 | 0.731 | **PASS** |
| urgency_2 | 376 | **0.644** | 0.563–0.720 | – | 0.883 | 0.678 | FAIL |
| sentiment_2 | 400 | **0.711** | 0.644–0.772 | – | 0.858 | 0.633 | **PASS** |

## type

Rows: 397 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.562 | 0.581 | 0.571 | 86 | 89 |
| Info | 0.793 | 0.898 | 0.842 | 244 | 276 |
| Credentials | 1.000 | 0.538 | 0.700 | 13 | 7 |
| Meeting | 0.818 | 0.375 | 0.514 | 24 | 11 |
| Approval | 0.714 | 0.333 | 0.455 | 30 | 14 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 50 | 34 | 0 | 0 | 2 |
| Info | 22 | 219 | 0 | 1 | 2 |
| Credentials | 0 | 6 | 7 | 0 | 0 |
| Meeting | 5 | 10 | 0 | 9 | 0 |
| Approval | 12 | 7 | 0 | 1 | 10 |

**Calibration** (strict rows, n=397): ECE equal-width-10 = **0.145**, equal-count-10 = 0.147. Review rate (top prob < 0.6) = 0.0% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 66 | 0.648 | 0.667 |
| 0.7–0.8 | 60 | 0.746 | 0.617 |
| 0.8–0.9 | 62 | 0.855 | 0.887 |
| 0.9–1.0 | 209 | 0.984 | 0.761 |

## urgency

Rows: 376 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 1 |
| High | 0.625 | 0.227 | 0.333 | 44 | 16 |
| Medium | 0.553 | 0.481 | 0.515 | 108 | 94 |
| Low | 0.717 | 0.876 | 0.788 | 217 | 265 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 2 | 4 |
| High | 1 | 10 | 14 | 19 |
| Medium | 0 | 4 | 52 | 52 |
| Low | 0 | 1 | 26 | 190 |

**Calibration** (strict rows, n=376): ECE equal-width-10 = **0.295**, equal-count-10 = 0.292. Review rate (top prob < 0.6) = 0.0% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 51 | 0.648 | 0.725 |
| 0.7–0.8 | 50 | 0.752 | 0.820 |
| 0.8–0.9 | 16 | 0.840 | 1.000 |
| 0.9–1.0 | 259 | 1.000 | 0.610 |

## sentiment

Rows: 400 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.630 | 0.472 | 0.540 | 36 | 27 |
| Neutral | 0.924 | 0.910 | 0.917 | 345 | 340 |
| Negative | 0.120 | 0.273 | 0.167 | 11 | 25 |
| Frustrated | 0.125 | 0.125 | 0.125 | 8 | 8 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 17 | 16 | 2 | 1 |
| Neutral | 10 | 314 | 16 | 5 |
| Negative | 0 | 7 | 3 | 1 |
| Frustrated | 0 | 3 | 4 | 1 |

**Calibration** (strict rows, n=400): ECE equal-width-10 = **0.069**, equal-count-10 = 0.079. Review rate (top prob < 0.6) = 0.0% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 61 | 0.659 | 0.672 |
| 0.7–0.8 | 70 | 0.757 | 0.829 |
| 0.8–0.9 | 69 | 0.856 | 0.870 |
| 0.9–1.0 | 200 | 0.985 | 0.880 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.0%

