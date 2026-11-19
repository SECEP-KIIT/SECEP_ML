# Score report — 2026-11-19T21:36:41

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-19-final-eval\hybrid\predictions.csv` (sha256 a0e7e77c4abffdd3…)
- rows scored: 286 (excluded 140; prediction rows ignored as not in gold: 140)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 286 | **0.539** | 0.437–0.621 | 0.539 | 0.640 | 0.575 | FAIL |
| urgency | 286 | **0.373** | 0.318–0.422 | 0.373 | 0.570 | 0.390 | FAIL |
| sentiment | 286 | **0.375** | 0.307–0.440 | 0.375 | 0.811 | 0.412 | FAIL |
| type_action | 286 | **0.684** | 0.628–0.738 | – | 0.703 | 0.731 | FAIL |
| urgency_2 | 286 | **0.653** | 0.568–0.731 | – | 0.857 | 0.678 | FAIL |
| sentiment_2 | 286 | **0.675** | 0.595–0.746 | – | 0.836 | 0.633 | **PASS** |

## type

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.414 | 0.439 | 0.426 | 66 | 70 |
| Info | 0.738 | 0.785 | 0.761 | 172 | 183 |
| Credentials | 0.857 | 0.600 | 0.706 | 10 | 7 |
| Meeting | 0.556 | 0.250 | 0.345 | 20 | 9 |
| Approval | 0.471 | 0.444 | 0.457 | 18 | 17 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 29 | 32 | 1 | 0 | 4 |
| Info | 31 | 135 | 0 | 1 | 5 |
| Credentials | 0 | 3 | 6 | 1 | 0 |
| Meeting | 7 | 8 | 0 | 5 | 0 |
| Approval | 3 | 5 | 0 | 2 | 8 |

## urgency

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 0 |
| High | 0.478 | 0.297 | 0.367 | 37 | 23 |
| Medium | 0.396 | 0.452 | 0.422 | 84 | 96 |
| Low | 0.683 | 0.722 | 0.702 | 158 | 167 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 2 | 1 | 4 |
| High | 0 | 11 | 17 | 9 |
| Medium | 0 | 6 | 38 | 40 |
| Low | 0 | 4 | 40 | 114 |

## sentiment

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.556 | 0.400 | 0.465 | 25 | 18 |
| Neutral | 0.902 | 0.905 | 0.903 | 243 | 244 |
| Negative | 0.105 | 0.182 | 0.133 | 11 | 19 |
| Frustrated | 0.000 | 0.000 | 0.000 | 7 | 5 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 10 | 13 | 2 | 0 |
| Neutral | 8 | 220 | 11 | 4 |
| Negative | 0 | 8 | 2 | 1 |
| Frustrated | 0 | 3 | 4 | 0 |

