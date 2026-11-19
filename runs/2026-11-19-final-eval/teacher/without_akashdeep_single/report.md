# Score report — 2026-11-19T21:36:39

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `runs\2026-11-19-teacher-gold-test\predictions.csv` (sha256 6e6f6f5811535868…)
- rows scored: 375 (excluded 51; prediction rows ignored as not in gold: 51)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 346 | **0.614** | 0.521–0.686 | 0.651 | 0.708 | 0.575 | **PASS** |
| urgency | 325 | **0.413** | 0.363–0.554 | 0.446 | 0.625 | 0.390 | **PASS** |
| sentiment | 349 | **0.414** | 0.321–0.512 | 0.420 | 0.868 | 0.412 | **PASS** |
| type_action | 346 | **0.768** | 0.723–0.812 | – | 0.777 | 0.731 | **PASS** |
| urgency_2 | 325 | **0.680** | 0.598–0.753 | – | 0.871 | 0.678 | **PASS** |
| sentiment_2 | 349 | **0.697** | 0.619–0.770 | – | 0.880 | 0.633 | **PASS** |

## type

Rows: 346 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.511 | 0.585 | 0.545 | 82 | 94 |
| Info | 0.812 | 0.816 | 0.814 | 207 | 208 |
| Credentials | 0.750 | 0.545 | 0.632 | 11 | 8 |
| Meeting | 0.833 | 0.417 | 0.556 | 24 | 12 |
| Approval | 0.500 | 0.545 | 0.522 | 22 | 24 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 48 | 26 | 2 | 0 | 6 |
| Info | 32 | 169 | 0 | 0 | 6 |
| Credentials | 0 | 4 | 6 | 1 | 0 |
| Meeting | 8 | 6 | 0 | 10 | 0 |
| Approval | 6 | 3 | 0 | 1 | 12 |

**Calibration** (strict rows, n=346): ECE equal-width-10 = **0.267**, equal-count-10 = 0.267. Review rate (top prob < 0.6) = 0.0% of 375 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 26 | 0.667 | 0.423 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 320 | 1.000 | 0.731 |

## urgency

Rows: 325 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 3 | 0 |
| High | 0.484 | 0.375 | 0.423 | 40 | 31 |
| Medium | 0.431 | 0.532 | 0.476 | 94 | 116 |
| Low | 0.775 | 0.734 | 0.754 | 188 | 178 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 1 | 1 |
| High | 0 | 15 | 19 | 6 |
| Medium | 0 | 11 | 50 | 33 |
| Low | 0 | 4 | 46 | 138 |

**Calibration** (strict rows, n=325): ECE equal-width-10 = **0.298**, equal-count-10 = 0.298. Review rate (top prob < 0.6) = 0.3% of 375 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 73 | 0.667 | 0.356 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 251 | 1.000 | 0.705 |

## sentiment

Rows: 349 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.765 | 0.371 | 0.500 | 35 | 17 |
| Neutral | 0.892 | 0.976 | 0.932 | 296 | 324 |
| Negative | 0.000 | 0.000 | 0.000 | 10 | 7 |
| Frustrated | 1.000 | 0.125 | 0.222 | 8 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 13 | 22 | 0 | 0 |
| Neutral | 4 | 289 | 3 | 0 |
| Negative | 0 | 10 | 0 | 0 |
| Frustrated | 0 | 3 | 4 | 1 |

**Calibration** (strict rows, n=349): ECE equal-width-10 = **0.114**, equal-count-10 = 0.114. Review rate (top prob < 0.6) = 0.0% of 375 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 19 | 0.667 | 0.474 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 330 | 1.000 | 0.891 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.3%

