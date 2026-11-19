# Score report — 2026-11-19T21:16:10

- gold: `runs\2026-11-19-gold_dev_teacher179.csv` (sha256 61d5248427838e5e…)
- pred: `runs\2026-11-18-teacher-b1-r2\predictions.csv` (sha256 faaa1ba1202378c9…)
- rows scored: 179 (excluded 0; prediction rows ignored as not in gold: 92)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 179 | **0.539** | 0.398–0.658 | 0.539 | 0.709 | 0.575 | FAIL |
| urgency | 179 | **0.471** | 0.359–0.590 | 0.471 | 0.598 | 0.390 | **PASS** |
| sentiment | 179 | **0.389** | 0.295–0.487 | 0.389 | 0.844 | 0.412 | FAIL |
| type_action | 179 | **0.800** | 0.736–0.856 | – | 0.804 | 0.731 | **PASS** |
| urgency_2 | 179 | **0.739** | 0.645–0.817 | – | 0.860 | 0.678 | **PASS** |
| sentiment_2 | 179 | **0.622** | 0.522–0.719 | – | 0.844 | 0.633 | FAIL |

## type

Rows: 179 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.659 | 0.558 | 0.604 | 52 | 44 |
| Info | 0.796 | 0.869 | 0.831 | 99 | 108 |
| Credentials | 0.200 | 1.000 | 0.333 | 1 | 5 |
| Meeting | 1.000 | 0.333 | 0.500 | 12 | 4 |
| Approval | 0.389 | 0.467 | 0.424 | 15 | 18 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 29 | 11 | 3 | 0 | 9 |
| Info | 11 | 86 | 0 | 0 | 2 |
| Credentials | 0 | 0 | 1 | 0 | 0 |
| Meeting | 2 | 6 | 0 | 4 | 0 |
| Approval | 2 | 5 | 1 | 0 | 7 |

**Calibration** (strict rows, n=179): ECE equal-width-10 = **0.263**, equal-count-10 = 0.263. Review rate (top prob < 0.6) = 0.6% of 179 rows. Pred ≠ argmax on 1 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 13 | 0.667 | 0.308 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 165 | 1.000 | 0.745 |

## urgency

Rows: 179 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 1.000 | 0.143 | 0.250 | 7 | 1 |
| High | 0.435 | 0.385 | 0.408 | 26 | 23 |
| Medium | 0.492 | 0.527 | 0.509 | 55 | 59 |
| Low | 0.698 | 0.736 | 0.717 | 91 | 96 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 1 | 5 | 0 | 1 |
| High | 0 | 10 | 8 | 8 |
| Medium | 0 | 6 | 29 | 20 |
| Low | 0 | 2 | 22 | 67 |

**Calibration** (strict rows, n=179): ECE equal-width-10 = **0.318**, equal-count-10 = 0.318. Review rate (top prob < 0.6) = 0.6% of 179 rows. Pred ≠ argmax on 1 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 1 | 0.333 | 0.000 |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 43 | 0.667 | 0.558 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 135 | 1.000 | 0.615 |

## sentiment

Rows: 179 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.750 | 0.375 | 0.500 | 16 | 8 |
| Neutral | 0.867 | 0.960 | 0.911 | 150 | 166 |
| Negative | 0.250 | 0.100 | 0.143 | 10 | 4 |
| Frustrated | 0.000 | 0.000 | 0.000 | 3 | 1 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 6 | 10 | 0 | 0 |
| Neutral | 2 | 144 | 3 | 1 |
| Negative | 0 | 9 | 1 | 0 |
| Frustrated | 0 | 3 | 0 | 0 |

**Calibration** (strict rows, n=179): ECE equal-width-10 = **0.132**, equal-count-10 = 0.132. Review rate (top prob < 0.6) = 0.0% of 179 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 13 | 0.667 | 0.538 |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 166 | 1.000 | 0.867 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 1.1%

