# Score report — 2026-11-19T02:49:04

- gold: `Data\gold_final\gold_dev.csv` (sha256 8377a7ac48bec380…)
- pred: `runs\2026-11-19-scorer-selftest\fake\perfect.csv` (sha256 0d2d72cefc6563ad…)
- rows scored: 184 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 184 | **1.000** | 1.000–1.000 | 1.000 | 1.000 | 0.575 | **PASS** |
| urgency | 184 | **1.000** | 1.000–1.000 | 1.000 | 1.000 | 0.390 | **PASS** |
| sentiment | 184 | **1.000** | 1.000–1.000 | 1.000 | 1.000 | 0.412 | **PASS** |
| type_action | 184 | **1.000** | 1.000–1.000 | – | 1.000 | 0.731 | **PASS** |
| urgency_2 | 184 | **1.000** | 1.000–1.000 | – | 1.000 | 0.678 | **PASS** |
| sentiment_2 | 184 | **1.000** | 1.000–1.000 | – | 1.000 | 0.633 | **PASS** |

## type

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 1.000 | 1.000 | 1.000 | 53 | 53 |
| Info | 1.000 | 1.000 | 1.000 | 100 | 100 |
| Credentials | 1.000 | 1.000 | 1.000 | 2 | 2 |
| Meeting | 1.000 | 1.000 | 1.000 | 13 | 13 |
| Approval | 1.000 | 1.000 | 1.000 | 16 | 16 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 53 | 0 | 0 | 0 | 0 |
| Info | 0 | 100 | 0 | 0 | 0 |
| Credentials | 0 | 0 | 2 | 0 | 0 |
| Meeting | 0 | 0 | 0 | 13 | 0 |
| Approval | 0 | 0 | 0 | 0 | 16 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.000**, equal-count-10 = 0.000. Review rate (top prob < 0.6) = 0.0% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 0 | – | – |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 184 | 1.000 | 1.000 |

## urgency

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 1.000 | 1.000 | 1.000 | 7 | 7 |
| High | 1.000 | 1.000 | 1.000 | 28 | 28 |
| Medium | 1.000 | 1.000 | 1.000 | 56 | 56 |
| Low | 1.000 | 1.000 | 1.000 | 93 | 93 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 7 | 0 | 0 | 0 |
| High | 0 | 28 | 0 | 0 |
| Medium | 0 | 0 | 56 | 0 |
| Low | 0 | 0 | 0 | 93 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.000**, equal-count-10 = 0.000. Review rate (top prob < 0.6) = 0.0% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 0 | – | – |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 184 | 1.000 | 1.000 |

## sentiment

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 1.000 | 1.000 | 1.000 | 16 | 16 |
| Neutral | 1.000 | 1.000 | 1.000 | 155 | 155 |
| Negative | 1.000 | 1.000 | 1.000 | 10 | 10 |
| Frustrated | 1.000 | 1.000 | 1.000 | 3 | 3 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 16 | 0 | 0 | 0 |
| Neutral | 0 | 155 | 0 | 0 |
| Negative | 0 | 0 | 10 | 0 |
| Frustrated | 0 | 0 | 0 | 3 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.000**, equal-count-10 = 0.000. Review rate (top prob < 0.6) = 0.0% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 0 | – | – |
| 0.7–0.8 | 0 | – | – |
| 0.8–0.9 | 0 | – | – |
| 0.9–1.0 | 184 | 1.000 | 1.000 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.0%

