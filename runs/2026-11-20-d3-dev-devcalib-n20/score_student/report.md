# Score report — 2026-11-20T03:06:25

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib-n20\gold_eval.csv` (sha256 c26634fe3e1d9590…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib-n20\predictions_student.csv` (sha256 ee6549b9bcbe5d38…)
- rows scored: 20 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 20 | **0.457** | 0.196–0.731 | 0.457 | 0.700 | 0.575 | FAIL |
| urgency | 20 | **0.321** | 0.183–0.608 | 0.321 | 0.650 | 0.390 | FAIL |
| sentiment | 20 | **0.252** | 0.160–0.551 | 0.252 | 0.600 | 0.412 | FAIL |
| type_action | 20 | **0.687** | 0.412–0.886 | – | 0.750 | 0.731 | FAIL |
| urgency_2 | 20 | **0.722** | 0.444–1.000 | – | 0.900 | 0.678 | **PASS** |
| sentiment_2 | 20 | **0.561** | 0.335–0.785 | – | 0.650 | 0.633 | FAIL |

## type

Rows: 20 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.500 | 0.250 | 0.333 | 4 | 2 |
| Info | 0.706 | 1.000 | 0.828 | 12 | 17 |
| Credentials | – | – | – | 0 | 0 |
| Meeting | 0.000 | 0.000 | 0.000 | 2 | 0 |
| Approval | 1.000 | 0.500 | 0.667 | 2 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 1 | 3 | 0 | 0 | 0 |
| Info | 0 | 12 | 0 | 0 | 0 |
| Credentials | 0 | 0 | 0 | 0 | 0 |
| Meeting | 0 | 2 | 0 | 0 | 0 |
| Approval | 1 | 0 | 0 | 0 | 1 |

**Calibration** (strict rows, n=20): ECE equal-width-10 = **0.148**, equal-count-10 = 0.209. Review rate (top prob < 0.6) = 50.0% of 20 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.396 | 0.000 |
| 0.4–0.5 | 5 | 0.441 | 0.600 |
| 0.5–0.6 | 4 | 0.527 | 0.500 |
| 0.6–0.7 | 4 | 0.637 | 0.750 |
| 0.7–0.8 | 4 | 0.740 | 1.000 |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 2 | 0.922 | 1.000 |

## urgency

Rows: 20 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 1 | 0 |
| High | 0.000 | 0.000 | 0.000 | 2 | 1 |
| Medium | 0.667 | 0.400 | 0.500 | 5 | 3 |
| Low | 0.688 | 0.917 | 0.786 | 12 | 16 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 0 | 0 |
| High | 0 | 0 | 0 | 2 |
| Medium | 0 | 0 | 2 | 3 |
| Low | 0 | 0 | 1 | 11 |

**Calibration** (strict rows, n=20): ECE equal-width-10 = **0.134**, equal-count-10 = 0.315. Review rate (top prob < 0.6) = 75.0% of 20 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 2 | 0.384 | 0.500 |
| 0.4–0.5 | 10 | 0.441 | 0.500 |
| 0.5–0.6 | 3 | 0.558 | 0.667 |
| 0.6–0.7 | 3 | 0.656 | 1.000 |
| 0.7–0.8 | 2 | 0.746 | 1.000 |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 0 | – | – |

## sentiment

Rows: 20 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.333 | 0.200 | 0.250 | 5 | 3 |
| Neutral | 0.733 | 0.786 | 0.759 | 14 | 15 |
| Negative | 0.000 | 0.000 | 0.000 | 0 | 2 |
| Frustrated | 0.000 | 0.000 | 0.000 | 1 | 0 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 1 | 3 | 1 | 0 |
| Neutral | 2 | 11 | 1 | 0 |
| Negative | 0 | 0 | 0 | 0 |
| Frustrated | 0 | 1 | 0 | 0 |

**Calibration** (strict rows, n=20): ECE equal-width-10 = **0.256**, equal-count-10 = 0.236. Review rate (top prob < 0.6) = 35.0% of 20 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.371 | 0.000 |
| 0.4–0.5 | 3 | 0.458 | 0.000 |
| 0.5–0.6 | 3 | 0.568 | 0.333 |
| 0.6–0.7 | 6 | 0.650 | 0.833 |
| 0.7–0.8 | 2 | 0.760 | 1.000 |
| 0.8–0.9 | 1 | 0.842 | 0.000 |
| 0.9–1.0 | 4 | 0.939 | 1.000 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 80.0%

