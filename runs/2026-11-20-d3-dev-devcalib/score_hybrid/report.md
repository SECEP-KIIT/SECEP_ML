# Score report — 2026-11-20T03:32:52

- gold: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib\gold_eval.csv` (sha256 ba8fe9c43cc14fb4…)
- pred: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training\runs\2026-11-20-d3-dev-devcalib\predictions_hybrid.csv` (sha256 47c4a7aee87b34b9…)
- rows scored: 276 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 276 | **0.630** | 0.488–0.729 | 0.630 | 0.725 | 0.575 | **PASS** |
| urgency | 276 | **0.412** | 0.356–0.461 | 0.412 | 0.627 | 0.390 | **PASS** |
| sentiment | 276 | **0.360** | 0.292–0.424 | 0.360 | 0.793 | 0.412 | FAIL |
| type_action | 276 | **0.737** | 0.682–0.788 | – | 0.757 | 0.731 | **PASS** |
| urgency_2 | 276 | **0.694** | 0.607–0.771 | – | 0.866 | 0.678 | **PASS** |
| sentiment_2 | 276 | **0.613** | 0.537–0.687 | – | 0.804 | 0.633 | FAIL |

## type

Rows: 276 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.762 | 0.432 | 0.552 | 74 | 42 |
| Info | 0.719 | 0.929 | 0.810 | 154 | 199 |
| Credentials | 0.667 | 0.500 | 0.571 | 4 | 3 |
| Meeting | 0.750 | 0.529 | 0.621 | 17 | 12 |
| Approval | 0.700 | 0.519 | 0.596 | 27 | 20 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 32 | 37 | 0 | 1 | 4 |
| Info | 6 | 143 | 1 | 2 | 2 |
| Credentials | 0 | 2 | 2 | 0 | 0 |
| Meeting | 2 | 6 | 0 | 9 | 0 |
| Approval | 2 | 11 | 0 | 0 | 14 |

**Calibration** (strict rows, n=276): ECE equal-width-10 = **0.153**, equal-count-10 = 0.153. Review rate (top prob < 0.6) = 0.0% of 276 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 50 | 0.643 | 0.580 |
| 0.7–0.8 | 38 | 0.750 | 0.658 |
| 0.8–0.9 | 33 | 0.853 | 0.788 |
| 0.9–1.0 | 155 | 0.990 | 0.774 |

## urgency

Rows: 276 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.000 | 0.000 | 0.000 | 9 | 0 |
| High | 0.737 | 0.341 | 0.467 | 41 | 19 |
| Medium | 0.536 | 0.353 | 0.426 | 85 | 56 |
| Low | 0.642 | 0.915 | 0.754 | 141 | 201 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 0 | 2 | 6 | 1 |
| High | 0 | 14 | 9 | 18 |
| Medium | 0 | 2 | 30 | 53 |
| Low | 0 | 1 | 11 | 129 |

**Calibration** (strict rows, n=276): ECE equal-width-10 = **0.335**, equal-count-10 = 0.313. Review rate (top prob < 0.6) = 0.0% of 276 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 32 | 0.650 | 0.594 |
| 0.7–0.8 | 18 | 0.752 | 0.889 |
| 0.8–0.9 | 15 | 0.847 | 0.933 |
| 0.9–1.0 | 211 | 1.000 | 0.588 |

## sentiment

Rows: 276 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.400 | 0.348 | 0.372 | 23 | 20 |
| Neutral | 0.867 | 0.904 | 0.885 | 230 | 240 |
| Negative | 0.188 | 0.176 | 0.182 | 17 | 16 |
| Frustrated | 0.000 | 0.000 | 0.000 | 6 | 0 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 8 | 15 | 0 | 0 |
| Neutral | 10 | 208 | 12 | 0 |
| Negative | 2 | 12 | 3 | 0 |
| Frustrated | 0 | 5 | 1 | 0 |

**Calibration** (strict rows, n=276): ECE equal-width-10 = **0.091**, equal-count-10 = 0.118. Review rate (top prob < 0.6) = 0.0% of 276 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 0 | – | – |
| 0.4–0.5 | 0 | – | – |
| 0.5–0.6 | 0 | – | – |
| 0.6–0.7 | 46 | 0.648 | 0.674 |
| 0.7–0.8 | 49 | 0.750 | 0.776 |
| 0.8–0.9 | 42 | 0.855 | 0.833 |
| 0.9–1.0 | 139 | 0.983 | 0.827 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 0.0%

