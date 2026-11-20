# D1 parity — 2026-11-20T00:34:06

Model `model_v1` (manifest `09646396d00b…`), mode `mixed` {'type': 'prior', 'urgency': 'prior', 'sentiment': 'balanced'}, gold-dev 184 rows.

## A. Package vs predict.py (gate: max |diff| ≤ 1e-6, labels 100%)

| head | max diff vs predictions.csv | max diff vs code | label agreement | pass |
|---|---|---|---|---|
| type | 5.00e-09 | 0.00e+00 | 100.0% | ✓ |
| urgency | 4.98e-09 | 0.00e+00 | 100.0% | ✓ |
| sentiment | 4.99e-09 | 0.00e+00 | 100.0% | ✓ |

**Part A: PASS**

## B. CPU re-embedding vs stored Kaggle embeddings (report only)

Text from `Data\gold_final\gold_dev.csv`; embedded in 36.6 s. Cosine min 1.000000, median 1.000000, rows < 0.999: 0. Max element diff 7.41e-07.

| head | label agreement | labels changed | review flag changed | max prob diff |
|---|---|---|---|---|
| type | 100.0% | 0 | 0 | 2.49e-06 |
| urgency | 100.0% | 0 | 0 | 1.31e-06 |
| sentiment | 100.0% | 0 | 0 | 2.22e-06 |

Verdict: **ok**
