# Score report — 2026-11-19T21:36:38

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-19-final-eval\hybrid\predictions.csv` (sha256 a0e7e77c4abffdd3…)
- rows scored: 426 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 397 | **0.577** | 0.489–0.644 | 0.616 | 0.685 | 0.575 | **PASS** |
| urgency | 376 | **0.393** | 0.343–0.441 | 0.425 | 0.606 | 0.390 | **PASS** |
| sentiment | 400 | **0.419** | 0.343–0.496 | 0.457 | 0.835 | 0.412 | **PASS** |
| type_action | 397 | **0.736** | 0.689–0.777 | – | 0.753 | 0.731 | **PASS** |
| urgency_2 | 376 | **0.665** | 0.586–0.736 | – | 0.867 | 0.678 | FAIL |
| sentiment_2 | 400 | **0.699** | 0.632–0.761 | – | 0.855 | 0.633 | **PASS** |

## type

Rows: 397 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.453 | 0.500 | 0.475 | 86 | 95 |
| Info | 0.787 | 0.820 | 0.803 | 244 | 254 |
| Credentials | 0.800 | 0.615 | 0.696 | 13 | 10 |
| Meeting | 0.667 | 0.333 | 0.444 | 24 | 12 |
| Approval | 0.500 | 0.433 | 0.464 | 30 | 26 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 43 | 36 | 2 | 0 | 5 |
| Info | 35 | 200 | 0 | 1 | 8 |
| Credentials | 0 | 4 | 8 | 1 | 0 |
| Meeting | 8 | 8 | 0 | 8 | 0 |
| Approval | 9 | 6 | 0 | 2 | 13 |

## urgency

Rows: 376 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 0 |
| High | 0.455 | 0.341 | 0.390 | 44 | 33 |
| Medium | 0.421 | 0.472 | 0.445 | 108 | 121 |
| Low | 0.730 | 0.747 | 0.738 | 217 | 222 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 2 | 1 | 4 |
| High | 0 | 15 | 19 | 10 |
| Medium | 0 | 11 | 51 | 46 |
| Low | 0 | 5 | 50 | 162 |

## sentiment

Rows: 400 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.615 | 0.444 | 0.516 | 36 | 26 |
| Neutral | 0.918 | 0.913 | 0.916 | 345 | 343 |
| Negative | 0.087 | 0.182 | 0.118 | 11 | 23 |
| Frustrated | 0.125 | 0.125 | 0.125 | 8 | 8 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 16 | 17 | 2 | 1 |
| Neutral | 10 | 315 | 15 | 5 |
| Negative | 0 | 8 | 2 | 1 |
| Frustrated | 0 | 3 | 4 | 1 |

