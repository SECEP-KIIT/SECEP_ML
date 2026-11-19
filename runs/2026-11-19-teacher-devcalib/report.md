# Score report — 2026-11-19T21:27:07

- gold: `runs\2026-11-19-gold_devcalib_teacher.csv` (sha256 7fbbe9c1f788e9c0…)
- pred: `runs\2026-11-18-teacher-b1-r2\predictions.csv` (sha256 faaa1ba1202378c9…)
- rows scored: 271 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 271 | **0.602** | 0.478–0.696 | 0.602 | 0.723 | 0.575 | **PASS** |
| urgency | 271 | **0.474** | 0.384–0.573 | 0.474 | 0.609 | 0.390 | **PASS** |
| sentiment | 271 | **0.415** | 0.330–0.493 | 0.415 | 0.838 | 0.412 | **PASS** |
| type_action | 271 | **0.791** | 0.737–0.836 | – | 0.797 | 0.731 | **PASS** |
| urgency_2 | 271 | **0.765** | 0.690–0.829 | – | 0.875 | 0.678 | **PASS** |
| sentiment_2 | 271 | **0.643** | 0.557–0.721 | – | 0.841 | 0.633 | **PASS** |

## type

Rows: 271 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.651 | 0.562 | 0.603 | 73 | 63 |
| Info | 0.799 | 0.856 | 0.826 | 153 | 164 |
| Credentials | 0.333 | 0.667 | 0.444 | 3 | 6 |
| Meeting | 0.800 | 0.500 | 0.615 | 16 | 10 |
| Approval | 0.500 | 0.538 | 0.519 | 26 | 28 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 41 | 18 | 3 | 1 | 10 |
| Info | 17 | 131 | 0 | 1 | 4 |
| Credentials | 0 | 1 | 2 | 0 | 0 |
| Meeting | 2 | 6 | 0 | 8 | 0 |
| Approval | 3 | 8 | 1 | 0 | 14 |

**Calibration** (strict rows, n=271): ECE equal-width-10 = **0.250**, equal-count-10 = 0.250. Review rate (top prob < 0.6) = 0.4% of 271 rows. Pred ≠ argmax on 1 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 20 | 0.667 | 0.250 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 250 | 1.000 | 0.764 |

## urgency

Rows: 271 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 1.000 | 0.111 | 0.200 | 9 | 1 |
| High | 0.486 | 0.462 | 0.474 | 39 | 37 |
| Medium | 0.477 | 0.500 | 0.488 | 84 | 88 |
| Low | 0.717 | 0.748 | 0.732 | 139 | 145 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 1 | 7 | 0 | 1 |
| High | 0 | 18 | 13 | 8 |
| Medium | 0 | 10 | 42 | 32 |
| Low | 0 | 2 | 33 | 104 |

**Calibration** (strict rows, n=271): ECE equal-width-10 = **0.311**, equal-count-10 = 0.311. Review rate (top prob < 0.6) = 0.4% of 271 rows. Pred ≠ argmax on 1 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 63 | 0.667 | 0.508 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 207 | 1.000 | 0.643 |

## sentiment

Rows: 271 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.615 | 0.348 | 0.444 | 23 | 13 |
| Neutral | 0.867 | 0.956 | 0.909 | 225 | 248 |
| Negative | 0.444 | 0.235 | 0.308 | 17 | 9 |
| Frustrated | 0.000 | 0.000 | 0.000 | 6 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 8 | 15 | 0 | 0 |
| Neutral | 5 | 215 | 4 | 1 |
| Negative | 0 | 13 | 4 | 0 |
| Frustrated | 0 | 5 | 1 | 0 |

**Calibration** (strict rows, n=271): ECE equal-width-10 = **0.139**, equal-count-10 = 0.139. Review rate (top prob < 0.6) = 0.0% of 271 rows. Pred ≠ argmax on 0 rows.

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
| 0.9–1.0 | 252 | 1.000 | 0.865 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.7%

