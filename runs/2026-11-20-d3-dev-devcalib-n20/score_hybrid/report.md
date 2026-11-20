# Score report — 2026-11-20T03:06:26

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib-n20\gold_eval.csv` (sha256 c26634fe3e1d9590…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib-n20\predictions_hybrid.csv` (sha256 4a5d5bec1e9fc145…)
- rows scored: 20 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 20 | **0.698** | 0.319–0.939 | 0.698 | 0.800 | 0.575 | **PASS** |
| urgency | 20 | **0.478** | 0.234–0.831 | 0.478 | 0.700 | 0.390 | **PASS** |
| sentiment | 20 | **0.366** | 0.237–0.740 | 0.366 | 0.700 | 0.412 | FAIL |
| type_action | 20 | **0.829** | 0.601–1.000 | – | 0.850 | 0.731 | **PASS** |
| urgency_2 | 20 | **0.722** | 0.444–1.000 | – | 0.900 | 0.678 | **PASS** |
| sentiment_2 | 20 | **0.531** | 0.355–0.762 | – | 0.700 | 0.633 | FAIL |

## type

Rows: 20 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.667 | 0.500 | 0.571 | 4 | 3 |
| Info | 0.800 | 1.000 | 0.889 | 12 | 15 |
| Credentials | – | – | – | 0 | 0 |
| Meeting | 1.000 | 0.500 | 0.667 | 2 | 1 |
| Approval | 1.000 | 0.500 | 0.667 | 2 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 2 | 2 | 0 | 0 | 0 |
| Info | 0 | 12 | 0 | 0 | 0 |
| Credentials | 0 | 0 | 0 | 0 | 0 |
| Meeting | 0 | 1 | 0 | 1 | 0 |
| Approval | 1 | 0 | 0 | 0 | 1 |

**Calibration** (strict rows, n=20): ECE equal-width-10 = **0.217**, equal-count-10 = 0.254. Review rate (top prob < 0.6) = 0.0% of 20 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 4 | 0.637 | 0.750 |
| 0.7–0.8 | 4 | 0.740 | 1.000 |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 12 | 0.987 | 0.750 |

## urgency

Rows: 20 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 1 | 0 |
| High | 1.000 | 0.500 | 0.667 | 2 | 1 |
| Medium | 0.400 | 0.400 | 0.400 | 5 | 5 |
| Low | 0.786 | 0.917 | 0.846 | 12 | 14 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 0 | 1 | 0 |
| High | 0 | 1 | 1 | 0 |
| Medium | 0 | 0 | 2 | 3 |
| Low | 0 | 0 | 1 | 11 |

**Calibration** (strict rows, n=20): ECE equal-width-10 = **0.377**, equal-count-10 = 0.377. Review rate (top prob < 0.6) = 0.0% of 20 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 3 | 0.656 | 1.000 |
| 0.7–0.8 | 2 | 0.746 | 1.000 |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 15 | 1.000 | 0.600 |

## sentiment

Rows: 20 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.500 | 0.200 | 0.286 | 5 | 2 |
| Neutral | 0.722 | 0.929 | 0.812 | 14 | 18 |
| Negative | – | – | – | 0 | 0 |
| Frustrated | 0.000 | 0.000 | 0.000 | 1 | 0 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 1 | 4 | 0 | 0 |
| Neutral | 1 | 13 | 0 | 0 |
| Negative | 0 | 0 | 0 | 0 |
| Frustrated | 0 | 1 | 0 | 0 |

**Calibration** (strict rows, n=20): ECE equal-width-10 = **0.309**, equal-count-10 = 0.358. Review rate (top prob < 0.6) = 0.0% of 20 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 6 | 0.650 | 0.833 |
| 0.7–0.8 | 2 | 0.760 | 1.000 |
| 0.8–0.9 | 1 | 0.842 | 0.000 |
| 0.9–1.0 | 11 | 0.978 | 0.636 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.0%

