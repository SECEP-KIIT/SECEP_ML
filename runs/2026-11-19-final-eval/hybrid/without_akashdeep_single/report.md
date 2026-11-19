# Score report — 2026-11-19T21:36:40

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-19-final-eval\hybrid\predictions.csv` (sha256 a0e7e77c4abffdd3…)
- rows scored: 375 (excluded 51; prediction rows ignored as not in gold: 51)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 346 | **0.584** | 0.487–0.659 | 0.627 | 0.691 | 0.575 | **PASS** |
| urgency | 325 | **0.402** | 0.352–0.536 | 0.437 | 0.615 | 0.390 | **PASS** |
| sentiment | 349 | **0.426** | 0.345–0.508 | 0.467 | 0.831 | 0.412 | **PASS** |
| type_action | 346 | **0.747** | 0.697–0.792 | – | 0.760 | 0.731 | **PASS** |
| urgency_2 | 325 | **0.672** | 0.591–0.749 | – | 0.871 | 0.678 | FAIL |
| sentiment_2 | 349 | **0.710** | 0.640–0.774 | – | 0.854 | 0.633 | **PASS** |

## type

Rows: 346 strict, 29 non-strict labelled, 0 blank, 39 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.494 | 0.512 | 0.503 | 82 | 85 |
| Info | 0.784 | 0.826 | 0.805 | 207 | 218 |
| Credentials | 0.750 | 0.545 | 0.632 | 11 | 8 |
| Meeting | 0.727 | 0.333 | 0.457 | 24 | 11 |
| Approval | 0.500 | 0.545 | 0.522 | 22 | 24 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 42 | 33 | 2 | 0 | 5 |
| Info | 28 | 171 | 0 | 1 | 7 |
| Credentials | 0 | 4 | 6 | 1 | 0 |
| Meeting | 8 | 8 | 0 | 8 | 0 |
| Approval | 7 | 2 | 0 | 1 | 12 |

## urgency

Rows: 325 strict, 50 non-strict labelled, 0 blank, 50 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 3 | 0 |
| High | 0.483 | 0.350 | 0.406 | 40 | 29 |
| Medium | 0.427 | 0.500 | 0.461 | 94 | 110 |
| Low | 0.747 | 0.739 | 0.743 | 188 | 186 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 0 | 2 |
| High | 0 | 14 | 18 | 8 |
| Medium | 0 | 10 | 47 | 37 |
| Low | 0 | 4 | 45 | 139 |

## sentiment

Rows: 349 strict, 26 non-strict labelled, 0 blank, 26 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.682 | 0.429 | 0.526 | 35 | 22 |
| Neutral | 0.910 | 0.919 | 0.914 | 296 | 299 |
| Negative | 0.095 | 0.200 | 0.129 | 10 | 21 |
| Frustrated | 0.143 | 0.125 | 0.133 | 8 | 7 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 15 | 17 | 2 | 1 |
| Neutral | 7 | 272 | 13 | 4 |
| Negative | 0 | 7 | 2 | 1 |
| Frustrated | 0 | 3 | 4 | 1 |

