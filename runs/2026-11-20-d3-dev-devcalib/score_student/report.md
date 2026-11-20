# Score report — 2026-11-20T03:32:51

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib\gold_eval.csv` (sha256 ba8fe9c43cc14fb4…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib\predictions_student.csv` (sha256 038e669b0ba4f581…)
- rows scored: 276 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 276 | **0.565** | 0.436–0.660 | 0.565 | 0.656 | 0.575 | FAIL |
| urgency | 276 | **0.351** | 0.266–0.449 | 0.351 | 0.514 | 0.390 | FAIL |
| sentiment | 276 | **0.315** | 0.261–0.369 | 0.315 | 0.678 | 0.412 | FAIL |
| type_action | 276 | **0.699** | 0.643–0.751 | – | 0.710 | 0.731 | FAIL |
| urgency_2 | 276 | **0.634** | 0.559–0.708 | – | 0.826 | 0.678 | FAIL |
| sentiment_2 | 276 | **0.587** | 0.521–0.652 | – | 0.714 | 0.633 | FAIL |

## type

Rows: 276 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.517 | 0.419 | 0.463 | 74 | 60 |
| Info | 0.710 | 0.812 | 0.758 | 154 | 176 |
| Credentials | 0.500 | 0.500 | 0.500 | 4 | 4 |
| Meeting | 0.538 | 0.412 | 0.467 | 17 | 13 |
| Approval | 0.696 | 0.593 | 0.640 | 27 | 23 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 31 | 35 | 1 | 3 | 4 |
| Info | 22 | 125 | 1 | 3 | 3 |
| Credentials | 0 | 2 | 2 | 0 | 0 |
| Meeting | 2 | 8 | 0 | 7 | 0 |
| Approval | 5 | 6 | 0 | 0 | 16 |

**Calibration** (strict rows, n=276): ECE equal-width-10 = **0.076**, equal-count-10 = 0.060. Review rate (top prob < 0.6) = 45.3% of 276 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 8 | 0.377 | 0.250 |
| 0.4–0.5 | 56 | 0.462 | 0.571 |
| 0.5–0.6 | 61 | 0.551 | 0.623 |
| 0.6–0.7 | 50 | 0.643 | 0.580 |
| 0.7–0.8 | 38 | 0.750 | 0.658 |
| 0.8–0.9 | 33 | 0.853 | 0.788 |
| 0.9–1.0 | 30 | 0.947 | 0.967 |

## urgency

Rows: 276 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 1.000 | 0.111 | 0.200 | 9 | 1 |
| High | 0.240 | 0.146 | 0.182 | 41 | 25 |
| Medium | 0.409 | 0.318 | 0.358 | 85 | 66 |
| Low | 0.587 | 0.766 | 0.665 | 141 | 184 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 1 | 7 | 0 | 1 |
| High | 0 | 6 | 10 | 25 |
| Medium | 0 | 8 | 27 | 50 |
| Low | 0 | 4 | 29 | 108 |

**Calibration** (strict rows, n=276): ECE equal-width-10 = **0.053**, equal-count-10 = 0.078. Review rate (top prob < 0.6) = 76.1% of 276 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 41 | 0.374 | 0.439 |
| 0.4–0.5 | 119 | 0.448 | 0.420 |
| 0.5–0.6 | 50 | 0.538 | 0.480 |
| 0.6–0.7 | 32 | 0.650 | 0.594 |
| 0.7–0.8 | 18 | 0.752 | 0.889 |
| 0.8–0.9 | 15 | 0.847 | 0.933 |
| 0.9–1.0 | 1 | 0.904 | 1.000 |

## sentiment

Rows: 276 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.273 | 0.391 | 0.321 | 23 | 33 |
| Neutral | 0.879 | 0.761 | 0.816 | 230 | 199 |
| Negative | 0.094 | 0.176 | 0.122 | 17 | 32 |
| Frustrated | 0.000 | 0.000 | 0.000 | 6 | 12 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 9 | 10 | 2 | 2 |
| Neutral | 19 | 175 | 26 | 10 |
| Negative | 5 | 9 | 3 | 0 |
| Frustrated | 0 | 5 | 1 | 0 |

**Calibration** (strict rows, n=276): ECE equal-width-10 = **0.033**, equal-count-10 = 0.028. Review rate (top prob < 0.6) = 37.7% of 276 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 1 | 0.294 | 0.000 |
| 0.3–0.4 | 14 | 0.360 | 0.286 |
| 0.4–0.5 | 45 | 0.453 | 0.511 |
| 0.5–0.6 | 44 | 0.555 | 0.523 |
| 0.6–0.7 | 46 | 0.648 | 0.674 |
| 0.7–0.8 | 49 | 0.750 | 0.776 |
| 0.8–0.9 | 42 | 0.855 | 0.833 |
| 0.9–1.0 | 35 | 0.932 | 0.943 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 81.5%

