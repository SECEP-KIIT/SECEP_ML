# Retrain — 2026-11-20T03:57:44

Parent `model_v1`; corrections: None; weight x2.0.

| head | gold-dev macro-F1 promoted | candidate | Δ | worst class Δ | pass |
|---|---|---|---|---|---|
| type | 0.566 | 0.569 | +0.002 | +0.000 | ✓ |
| urgency | 0.344 | 0.344 | +0.000 | +0.000 | ✓ |
| sentiment | 0.299 | 0.299 | +0.000 | +0.000 | ✓ |

Held-out corrections accuracy: promoted None, candidate None → ✗

Label agreement with parent on gold-dev: {'type': 0.9945652173913043, 'urgency': 1.0, 'sentiment': 1.0}; max prob diff {'type': 0.00466207454603057, 'urgency': 0.0023216558590775094, 'sentiment': 0.00393559829751533}

**Reproduction check only** (no corrections): gate not applicable, nothing saved.
