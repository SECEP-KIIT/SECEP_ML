# Score report — 2026-11-19T21:36:38

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `runs\2026-11-19-teacher-gold-test\predictions.csv` (sha256 6e6f6f5811535868…)
- rows scored: 426 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 397 | **0.599** | 0.514–0.665 | 0.634 | 0.695 | 0.575 | **PASS** |
| urgency | 376 | **0.402** | 0.356–0.449 | 0.433 | 0.614 | 0.390 | **PASS** |
| sentiment | 400 | **0.407** | 0.314–0.508 | 0.413 | 0.873 | 0.412 | FAIL |
| type_action | 397 | **0.754** | 0.708–0.796 | – | 0.766 | 0.731 | **PASS** |
| urgency_2 | 376 | **0.678** | 0.604–0.747 | – | 0.867 | 0.678 | **PASS** |
| sentiment_2 | 400 | **0.684** | 0.609–0.754 | – | 0.882 | 0.633 | **PASS** |

## type

Rows: 397 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.458 | 0.570 | 0.508 | 86 | 107 |
| Info | 0.813 | 0.803 | 0.808 | 244 | 241 |
| Credentials | 0.727 | 0.615 | 0.667 | 13 | 11 |
| Meeting | 0.769 | 0.417 | 0.541 | 24 | 13 |
| Approval | 0.520 | 0.433 | 0.473 | 30 | 25 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 49 | 29 | 2 | 0 | 6 |
| Info | 41 | 196 | 1 | 0 | 6 |
| Credentials | 0 | 4 | 8 | 1 | 0 |
| Meeting | 8 | 6 | 0 | 10 | 0 |
| Approval | 9 | 6 | 0 | 2 | 13 |

**Calibration** (strict rows, n=397): ECE equal-width-10 = **0.280**, equal-count-10 = 0.280. Review rate (top prob < 0.6) = 0.0% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 30 | 0.667 | 0.400 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 367 | 1.000 | 0.719 |

## urgency

Rows: 376 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 0 |
| High | 0.432 | 0.364 | 0.395 | 44 | 37 |
| Medium | 0.430 | 0.509 | 0.466 | 108 | 128 |
| Low | 0.758 | 0.737 | 0.748 | 217 | 211 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 3 | 2 | 2 |
| High | 0 | 16 | 20 | 8 |
| Medium | 0 | 12 | 55 | 41 |
| Low | 0 | 6 | 51 | 160 |

**Calibration** (strict rows, n=376): ECE equal-width-10 = **0.309**, equal-count-10 = 0.309. Review rate (top prob < 0.6) = 0.5% of 426 rows. Pred ≠ argmax on 1 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 2 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 82 | 0.667 | 0.354 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 292 | 1.000 | 0.692 |

## sentiment

Rows: 400 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.684 | 0.361 | 0.473 | 36 | 19 |
| Neutral | 0.901 | 0.971 | 0.934 | 345 | 372 |
| Negative | 0.000 | 0.000 | 0.000 | 11 | 8 |
| Frustrated | 1.000 | 0.125 | 0.222 | 8 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 13 | 23 | 0 | 0 |
| Neutral | 6 | 335 | 4 | 0 |
| Negative | 0 | 11 | 0 | 0 |
| Frustrated | 0 | 3 | 4 | 1 |

**Calibration** (strict rows, n=400): ECE equal-width-10 = **0.108**, equal-count-10 = 0.108. Review rate (top prob < 0.6) = 0.0% of 426 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 23 | 0.667 | 0.522 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 377 | 1.000 | 0.894 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.5%

