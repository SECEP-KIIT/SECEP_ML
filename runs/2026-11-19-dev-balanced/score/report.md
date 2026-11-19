# Score report — 2026-11-19T13:50:58

- gold: `Data\gold_final\gold_dev.csv` (sha256 8377a7ac48bec380…)
- pred: `runs\2026-11-19-dev-balanced\predictions.csv` (sha256 3b597421f75e7c37…)
- rows scored: 184 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 184 | **0.449** | 0.340–0.550 | 0.449 | 0.505 | 0.575 | FAIL |
| urgency | 184 | **0.323** | 0.234–0.418 | 0.323 | 0.391 | 0.390 | FAIL |
| sentiment | 184 | **0.299** | 0.239–0.360 | 0.299 | 0.679 | 0.412 | FAIL |
| type_action | 184 | **0.644** | 0.571–0.710 | – | 0.652 | 0.731 | FAIL |
| urgency_2 | 184 | **0.541** | 0.461–0.616 | – | 0.641 | 0.678 | FAIL |
| sentiment_2 | 184 | **0.573** | 0.488–0.649 | – | 0.712 | 0.633 | FAIL |

## type

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.439 | 0.472 | 0.455 | 53 | 57 |
| Info | 0.821 | 0.460 | 0.590 | 100 | 56 |
| Credentials | 0.167 | 0.500 | 0.250 | 2 | 6 |
| Meeting | 0.500 | 0.615 | 0.552 | 13 | 16 |
| Approval | 0.265 | 0.812 | 0.400 | 16 | 49 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 25 | 7 | 3 | 4 | 14 |
| Info | 27 | 46 | 2 | 4 | 21 |
| Credentials | 0 | 1 | 1 | 0 | 0 |
| Meeting | 2 | 2 | 0 | 8 | 1 |
| Approval | 3 | 0 | 0 | 0 | 13 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.070**, equal-count-10 = 0.101. Review rate (top prob < 0.6) = 74.5% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 7 | 0.290 | 0.429 |
| 0.3–0.4 | 45 | 0.357 | 0.378 |
| 0.4–0.5 | 53 | 0.453 | 0.434 |
| 0.5–0.6 | 32 | 0.544 | 0.438 |
| 0.6–0.7 | 13 | 0.664 | 0.769 |
| 0.7–0.8 | 20 | 0.742 | 0.850 |
| 0.8–0.9 | 11 | 0.853 | 0.636 |
| 0.9–1.0 | 3 | 0.906 | 0.667 |

## urgency

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.250 | 0.143 | 0.182 | 7 | 4 |
| High | 0.153 | 0.321 | 0.207 | 28 | 59 |
| Medium | 0.354 | 0.411 | 0.380 | 56 | 65 |
| Low | 0.696 | 0.419 | 0.523 | 93 | 56 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 1 | 6 | 0 | 0 |
| High | 0 | 9 | 11 | 8 |
| Medium | 1 | 23 | 23 | 9 |
| Low | 2 | 21 | 31 | 39 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.084**, equal-count-10 = 0.090. Review rate (top prob < 0.6) = 88.6% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 2 | 0.294 | 0.500 |
| 0.3–0.4 | 63 | 0.364 | 0.254 |
| 0.4–0.5 | 73 | 0.447 | 0.411 |
| 0.5–0.6 | 25 | 0.539 | 0.400 |
| 0.6–0.7 | 12 | 0.649 | 0.583 |
| 0.7–0.8 | 7 | 0.745 | 0.857 |
| 0.8–0.9 | 2 | 0.821 | 1.000 |
| 0.9–1.0 | 0 | – | – |

## sentiment

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.273 | 0.375 | 0.316 | 16 | 22 |
| Neutral | 0.881 | 0.761 | 0.817 | 155 | 134 |
| Negative | 0.045 | 0.100 | 0.062 | 10 | 22 |
| Frustrated | 0.000 | 0.000 | 0.000 | 3 | 6 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 6 | 7 | 2 | 1 |
| Neutral | 13 | 118 | 19 | 5 |
| Negative | 3 | 6 | 1 | 0 |
| Frustrated | 0 | 3 | 0 | 0 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.058**, equal-count-10 = 0.104. Review rate (top prob < 0.6) = 40.2% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 10 | 0.358 | 0.300 |
| 0.4–0.5 | 33 | 0.450 | 0.576 |
| 0.5–0.6 | 31 | 0.553 | 0.452 |
| 0.6–0.7 | 29 | 0.641 | 0.724 |
| 0.7–0.8 | 28 | 0.754 | 0.750 |
| 0.8–0.9 | 27 | 0.855 | 0.852 |
| 0.9–1.0 | 26 | 0.933 | 0.923 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 91.8%

