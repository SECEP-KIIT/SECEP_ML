# Score report — 2026-11-19T02:49:15

- gold: `Data\gold_final\gold_dev.csv` (sha256 8377a7ac48bec380…)
- pred: `runs\2026-11-19-scorer-selftest\fake\random.csv` (sha256 d4120405fccf0df4…)
- rows scored: 184 (excluded 0; prediction rows ignored as not in gold: 0)
- bootstrap: 2000 resamples, seed 42

## Summary (strict macro-F1)

| View | n | Strict macro-F1 | 95% CI | Lenient macro-F1 | Accuracy | Gate | Result |
|---|---|---|---|---|---|---|---|
| type | 184 | **0.140** | 0.093–0.189 | 0.140 | 0.196 | 0.575 | FAIL |
| urgency | 184 | **0.257** | 0.191–0.318 | 0.257 | 0.288 | 0.390 | FAIL |
| sentiment | 184 | **0.163** | 0.116–0.208 | 0.163 | 0.239 | 0.412 | FAIL |
| type_action | 184 | **0.437** | 0.361–0.507 | – | 0.462 | 0.731 | FAIL |
| urgency_2 | 184 | **0.448** | 0.376–0.516 | – | 0.511 | 0.678 | FAIL |
| sentiment_2 | 184 | **0.324** | 0.259–0.388 | – | 0.326 | 0.633 | FAIL |

## type

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Task | 0.205 | 0.151 | 0.174 | 53 | 39 |
| Info | 0.511 | 0.230 | 0.317 | 100 | 45 |
| Credentials | 0.000 | 0.000 | 0.000 | 2 | 34 |
| Meeting | 0.074 | 0.154 | 0.100 | 13 | 27 |
| Approval | 0.077 | 0.188 | 0.109 | 16 | 39 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Task | Info | Credentials | Meeting | Approval |
|---|---|---|---|---|---|
| Task | 8 | 15 | 10 | 8 | 12 |
| Info | 25 | 23 | 17 | 15 | 20 |
| Credentials | 1 | 1 | 0 | 0 | 0 |
| Meeting | 1 | 2 | 4 | 2 | 4 |
| Approval | 4 | 4 | 3 | 2 | 3 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.255**, equal-count-10 = 0.255. Review rate (top prob < 0.6) = 87.0% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 9 | 0.283 | 0.000 |
| 0.3–0.4 | 57 | 0.347 | 0.175 |
| 0.4–0.5 | 67 | 0.441 | 0.239 |
| 0.5–0.6 | 27 | 0.554 | 0.148 |
| 0.6–0.7 | 17 | 0.649 | 0.176 |
| 0.7–0.8 | 6 | 0.716 | 0.500 |
| 0.8–0.9 | 1 | 0.804 | 0.000 |
| 0.9–1.0 | 0 | – | – |

## urgency

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Critical | 0.070 | 0.429 | 0.120 | 7 | 43 |
| High | 0.182 | 0.286 | 0.222 | 28 | 44 |
| Medium | 0.345 | 0.357 | 0.351 | 56 | 58 |
| Low | 0.564 | 0.237 | 0.333 | 93 | 39 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Critical | High | Medium | Low |
|---|---|---|---|---|
| Critical | 3 | 0 | 2 | 2 |
| High | 5 | 8 | 10 | 5 |
| Medium | 13 | 13 | 20 | 10 |
| Low | 22 | 23 | 26 | 22 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.243**, equal-count-10 = 0.253. Review rate (top prob < 0.6) = 73.4% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 4 | 0.282 | 0.500 |
| 0.3–0.4 | 34 | 0.365 | 0.324 |
| 0.4–0.5 | 52 | 0.449 | 0.308 |
| 0.5–0.6 | 45 | 0.548 | 0.244 |
| 0.6–0.7 | 31 | 0.651 | 0.194 |
| 0.7–0.8 | 10 | 0.737 | 0.200 |
| 0.8–0.9 | 6 | 0.847 | 0.667 |
| 0.9–1.0 | 2 | 0.914 | 0.500 |

## sentiment

Rows: 184 strict, 0 non-strict labelled, 0 blank, 0 with an alt label.

| Class | Precision | Recall | F1 | Support | Predicted |
|---|---|---|---|---|---|
| Positive | 0.149 | 0.438 | 0.222 | 16 | 47 |
| Neutral | 0.897 | 0.226 | 0.361 | 155 | 39 |
| Negative | 0.042 | 0.200 | 0.069 | 10 | 48 |
| Frustrated | 0.000 | 0.000 | 0.000 | 3 | 50 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Positive | Neutral | Negative | Frustrated |
|---|---|---|---|---|
| Positive | 7 | 3 | 3 | 3 |
| Neutral | 36 | 35 | 42 | 42 |
| Negative | 2 | 1 | 2 | 5 |
| Frustrated | 2 | 0 | 1 | 0 |

**Calibration** (strict rows, n=184): ECE equal-width-10 = **0.274**, equal-count-10 = 0.274. Review rate (top prob < 0.6) = 77.2% of 184 rows. Pred ≠ argmax on 0 rows.

| Bin | n | Mean conf | Accuracy |
|---|---|---|---|
| 0.0–0.1 | 0 | – | – |
| 0.1–0.2 | 0 | – | – |
| 0.2–0.3 | 0 | – | – |
| 0.3–0.4 | 38 | 0.370 | 0.263 |
| 0.4–0.5 | 60 | 0.445 | 0.250 |
| 0.5–0.6 | 44 | 0.536 | 0.205 |
| 0.6–0.7 | 21 | 0.641 | 0.190 |
| 0.7–0.8 | 14 | 0.755 | 0.286 |
| 0.8–0.9 | 6 | 0.840 | 0.333 |
| 0.9–1.0 | 1 | 0.940 | 0.000 |

**Any-head review rate** (an email is reviewed if any head is below 0.6): 100.0%

