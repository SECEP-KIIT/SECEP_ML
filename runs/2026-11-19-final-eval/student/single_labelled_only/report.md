# Score report — 2026-11-19T21:36:40

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\Data\sealed\gold_test.csv` (sha256 a5b24fa8edce43f7…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-19-final-eval\student\predictions.csv` (sha256 5cd2100499777a9a…)
- rows scored: 286 (excluded 140; prediction rows ignored as not in gold: 140)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 286 | **0.491** | 0.381–0.581 | 0.491 | 0.629 | 0.575 | FAIL |
| urgency | 286 | **0.247** | 0.212–0.289 | 0.247 | 0.490 | 0.390 | FAIL |
| sentiment | 286 | **0.359** | 0.298–0.422 | 0.359 | 0.689 | 0.412 | FAIL |
| type_action | 286 | **0.646** | 0.588–0.704 | – | 0.678 | 0.731 | FAIL |
| urgency_2 | 286 | **0.499** | 0.450–0.563 | – | 0.815 | 0.678 | FAIL |
| sentiment_2 | 286 | **0.620** | 0.555–0.682 | – | 0.727 | 0.633 | FAIL |

## type

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.413 | 0.394 | 0.403 | 66 | 63 |
| Info | 0.700 | 0.814 | 0.753 | 172 | 200 |
| Credentials | 1.000 | 0.500 | 0.667 | 10 | 5 |
| Meeting | 0.500 | 0.150 | 0.231 | 20 | 6 |
| Approval | 0.500 | 0.333 | 0.400 | 18 | 12 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 26 | 37 | 0 | 1 | 2 |
| Info | 27 | 140 | 0 | 1 | 4 |
| Credentials | 0 | 5 | 5 | 0 | 0 |
| Meeting | 5 | 12 | 0 | 3 | 0 |
| Approval | 5 | 6 | 0 | 1 | 6 |

**Calibration** (strict rows, n=286): ECE equal-width-10 = **0.071**, equal-count-10 = 0.080. Review rate (top prob < 0.6) = 39.5% of 286 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 10 | 0.369 | 0.600 |
| 0.4–0.5 | 50 | 0.459 | 0.500 |
| 0.5–0.6 | 53 | 0.549 | 0.491 |
| 0.6–0.7 | 49 | 0.649 | 0.612 |
| 0.7–0.8 | 44 | 0.751 | 0.545 |
| 0.8–0.9 | 46 | 0.854 | 0.848 |
| 0.9–1.0 | 34 | 0.935 | 0.882 |

## urgency

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 7 | 0 |
| High | 0.133 | 0.054 | 0.077 | 37 | 15 |
| Medium | 0.271 | 0.226 | 0.247 | 84 | 70 |
| Low | 0.592 | 0.753 | 0.663 | 158 | 201 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 1 | 1 | 5 |
| High | 0 | 2 | 18 | 17 |
| Medium | 0 | 5 | 19 | 60 |
| Low | 0 | 7 | 32 | 119 |

**Calibration** (strict rows, n=286): ECE equal-width-10 = **0.072**, equal-count-10 = 0.081. Review rate (top prob < 0.6) = 71.0% of 286 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 41 | 0.374 | 0.293 |
| 0.4–0.5 | 99 | 0.452 | 0.333 |
| 0.5–0.6 | 63 | 0.540 | 0.508 |
| 0.6–0.7 | 38 | 0.646 | 0.658 |
| 0.7–0.8 | 34 | 0.751 | 0.794 |
| 0.8–0.9 | 11 | 0.849 | 1.000 |
| 0.9–1.0 | 0 | – | – |

## sentiment

Rows: 286 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.353 | 0.480 | 0.407 | 25 | 34 |
| Neutral | 0.923 | 0.741 | 0.822 | 243 | 195 |
| Negative | 0.135 | 0.455 | 0.208 | 11 | 37 |
| Frustrated | 0.000 | 0.000 | 0.000 | 7 | 20 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 12 | 8 | 3 | 2 |
| Neutral | 21 | 180 | 25 | 17 |
| Negative | 0 | 5 | 5 | 1 |
| Frustrated | 1 | 2 | 4 | 0 |

**Calibration** (strict rows, n=286): ECE equal-width-10 = **0.041**, equal-count-10 = 0.029. Review rate (top prob < 0.6) = 39.2% of 286 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 18 | 0.370 | 0.556 |
| 0.4–0.5 | 36 | 0.453 | 0.389 |
| 0.5–0.6 | 58 | 0.552 | 0.569 |
| 0.6–0.7 | 40 | 0.650 | 0.600 |
| 0.7–0.8 | 48 | 0.756 | 0.792 |
| 0.8–0.9 | 47 | 0.854 | 0.872 |
| 0.9–1.0 | 39 | 0.936 | 0.949 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 79.7%

