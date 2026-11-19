# Score report — 2026-11-19T13:51:00

- gold: `Data\gold_final\gold_dev.csv` (sha256 8377a7ac48bec380…)
- pred: `runs\2026-11-19-dev-prior\predictions.csv` (sha256 281c77d6b1d52a8e…)
- rows scored: 184 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 184 | **0.566** | 0.401–0.688 | 0.566 | 0.663 | 0.575 | FAIL |
| urgency | 184 | **0.344** | 0.239–0.448 | 0.344 | 0.511 | 0.390 | FAIL |
| sentiment | 184 | **0.258** | 0.224–0.341 | 0.258 | 0.848 | 0.412 | FAIL |
| type_action | 184 | **0.725** | 0.657–0.786 | – | 0.734 | 0.731 | FAIL |
| urgency_2 | 184 | **0.607** | 0.512–0.699 | – | 0.815 | 0.678 | FAIL |
| sentiment_2 | 184 | **0.524** | 0.454–0.617 | – | 0.853 | 0.633 | FAIL |

## type

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.548 | 0.434 | 0.484 | 53 | 42 |
| Info | 0.718 | 0.840 | 0.774 | 100 | 117 |
| Credentials | 0.500 | 0.500 | 0.500 | 2 | 2 |
| Meeting | 0.600 | 0.462 | 0.522 | 13 | 10 |
| Approval | 0.615 | 0.500 | 0.552 | 16 | 13 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 23 | 23 | 1 | 2 | 4 |
| Info | 13 | 84 | 0 | 2 | 1 |
| Credentials | 0 | 1 | 1 | 0 | 0 |
| Meeting | 2 | 5 | 0 | 6 | 0 |
| Approval | 4 | 4 | 0 | 0 | 8 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.077**, equal-count-10 = 0.074. Review rate (top prob < 0.6) = 43.5% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 8 | 0.377 | 0.250 |
| 0.4–0.5 | 33 | 0.455 | 0.576 |
| 0.5–0.6 | 39 | 0.550 | 0.641 |
| 0.6–0.7 | 35 | 0.637 | 0.657 |
| 0.7–0.8 | 27 | 0.759 | 0.630 |
| 0.8–0.9 | 24 | 0.846 | 0.792 |
| 0.9–1.0 | 18 | 0.947 | 0.944 |

## urgency

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 1.000 | 0.143 | 0.250 | 7 | 1 |
| High | 0.143 | 0.071 | 0.095 | 28 | 14 |
| Medium | 0.400 | 0.321 | 0.356 | 56 | 45 |
| Low | 0.589 | 0.785 | 0.673 | 93 | 124 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 1 | 5 | 0 | 1 |
| High | 0 | 2 | 9 | 17 |
| Medium | 0 | 5 | 18 | 33 |
| Low | 0 | 2 | 18 | 73 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.069**, equal-count-10 = 0.114. Review rate (top prob < 0.6) = 75.5% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 28 | 0.375 | 0.500 |
| 0.4–0.5 | 83 | 0.452 | 0.422 |
| 0.5–0.6 | 28 | 0.534 | 0.393 |
| 0.6–0.7 | 24 | 0.648 | 0.625 |
| 0.7–0.8 | 11 | 0.753 | 0.909 |
| 0.8–0.9 | 9 | 0.848 | 0.889 |
| 0.9–1.0 | 1 | 0.904 | 1.000 |

## sentiment

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.500 | 0.062 | 0.111 | 16 | 2 |
| Neutral | 0.852 | 1.000 | 0.920 | 155 | 182 |
| Negative | 0.000 | 0.000 | 0.000 | 10 | 0 |
| Frustrated | 0.000 | 0.000 | 0.000 | 3 | 0 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 1 | 15 | 0 | 0 |
| Neutral | 0 | 155 | 0 | 0 |
| Negative | 1 | 9 | 0 | 0 |
| Frustrated | 0 | 3 | 0 | 0 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.046**, equal-count-10 = 0.069. Review rate (top prob < 0.6) = 2.7% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 3 | 0.469 | 0.000 |
| 0.5–0.6 | 2 | 0.542 | 1.000 |
| 0.6–0.7 | 13 | 0.671 | 0.692 |
| 0.7–0.8 | 39 | 0.755 | 0.821 |
| 0.8–0.9 | 84 | 0.850 | 0.881 |
| 0.9–1.0 | 43 | 0.922 | 0.907 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 76.6%

