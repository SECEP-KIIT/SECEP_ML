# Retrain — 2026-11-20T03:58:02

Parent `model_v1`; corrections: {'rows_in': 110, 'users': 4, 'user_cap': 28, 'rows_after_cap': 106, 'train': 85, 'holdout': 21}; weight x2.0.

| head | gold-dev macro-F1 promoted | candidate | Δ | worst class Δ | pass |
|---|---|---|---|---|---|
| type | 0.566 | 0.565 | -0.002 | -0.011 | ✗ |
| urgency | 0.344 | 0.347 | +0.003 | -0.004 | ✓ |
| sentiment | 0.299 | 0.300 | +0.002 | +0.000 | ✓ |

Held-out corrections accuracy: promoted 0.0, candidate 0.6666666666666666 → ✓

Label agreement with parent on gold-dev: {'type': 0.9782608695652174, 'urgency': 0.9782608695652174, 'sentiment': 0.9945652173913043}; max prob diff {'type': 0.11075998855596542, 'urgency': 0.04738432287433178, 'sentiment': 0.023863625722808868}

**Gate: FAIL** — not promoted

# Retrain demo — 2026-11-20T03:58:02

140 synthetic SaaS emails: 84 feedback (corrected by 4 simulated users), 56 eval slice (never trained on). 110 corrections, weight x2.0.

| head | eval slice accuracy, before | after |
|---|---|---|
| type | 55% | 86% |
| urgency | 38% | 68% |
| sentiment | 82% | 88% |

Gate on gold-dev + held-out corrections: **FAIL** (candidate kept in the run folder; promoted.json untouched).
