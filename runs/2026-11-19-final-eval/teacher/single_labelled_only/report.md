# Score report — 2026-11-19T21:36:41

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `runs\2026-11-19-teacher-gold-test\predictions.csv` (sha256 6e6f6f5811535868…)
- rows scored: 286 (excluded 140; prediction rows ignored as not in gold: 140)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 286 | **0.567** | 0.467–0.651 | 0.567 | 0.668 | 0.575 | FAIL |
| urgency | 286 | **0.384** | 0.331–0.434 | 0.384 | 0.580 | 0.390 | FAIL |
| sentiment | 286 | **0.391** | 0.285–0.502 | 0.391 | 0.853 | 0.412 | FAIL |
| type_action | 286 | **0.722** | 0.665–0.771 | – | 0.734 | 0.731 | FAIL |
| urgency_2 | 286 | **0.670** | 0.584–0.747 | – | 0.857 | 0.678 | FAIL |
| sentiment_2 | 286 | **0.642** | 0.556–0.725 | – | 0.864 | 0.633 | **PASS** |

## type

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.456 | 0.545 | 0.497 | 66 | 79 |
| Info | 0.776 | 0.785 | 0.780 | 172 | 174 |
| Credentials | 0.750 | 0.600 | 0.667 | 10 | 8 |
| Meeting | 0.700 | 0.350 | 0.467 | 20 | 10 |
| Approval | 0.467 | 0.389 | 0.424 | 18 | 15 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 36 | 25 | 1 | 0 | 4 |
| Info | 32 | 135 | 1 | 0 | 4 |
| Credentials | 0 | 3 | 6 | 1 | 0 |
| Meeting | 7 | 6 | 0 | 7 | 0 |
| Approval | 4 | 5 | 0 | 2 | 7 |

**Calibration** (strict rows, n=286): ECE equal-width-10 = **0.304**, equal-count-10 = 0.304. Review rate (top prob < 0.6) = 0.0% of 286 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 24 | 0.667 | 0.375 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 262 | 1.000 | 0.695 |

## urgency

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 0 |
| High | 0.444 | 0.324 | 0.375 | 37 | 27 |
| Medium | 0.412 | 0.500 | 0.452 | 84 | 102 |
| Low | 0.713 | 0.709 | 0.711 | 158 | 157 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 3 | 2 | 2 |
| High | 0 | 12 | 17 | 8 |
| Medium | 0 | 7 | 42 | 35 |
| Low | 0 | 5 | 41 | 112 |

**Calibration** (strict rows, n=286): ECE equal-width-10 = **0.340**, equal-count-10 = 0.340. Review rate (top prob < 0.6) = 0.7% of 286 rows. Pred ≠ argmax on 1 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 2 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 64 | 0.667 | 0.375 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 220 | 1.000 | 0.645 |

## sentiment

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.636 | 0.280 | 0.389 | 25 | 11 |
| Neutral | 0.881 | 0.971 | 0.924 | 243 | 268 |
| Negative | 0.000 | 0.000 | 0.000 | 11 | 6 |
| Frustrated | 1.000 | 0.143 | 0.250 | 7 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 7 | 18 | 0 | 0 |
| Neutral | 4 | 236 | 3 | 0 |
| Negative | 0 | 11 | 0 | 0 |
| Frustrated | 0 | 3 | 3 | 1 |

**Calibration** (strict rows, n=286): ECE equal-width-10 = **0.128**, equal-count-10 = 0.128. Review rate (top prob < 0.6) = 0.0% of 286 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 16 | 0.667 | 0.500 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 270 | 1.000 | 0.874 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.7%

