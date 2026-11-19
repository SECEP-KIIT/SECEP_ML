# Ablation (gold-dev, strict macro-F1; indicative)

Each row switches one thing off and retrains with the shipped C per head; Δ is against `full`. Head modes: {'type': 'prior', 'urgency': 'prior', 'sentiment': 'balanced'}.

| Variant | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 | ECE type | ECE urg. | ECE sent. | Review (any head) |
|---|---|---|---|---|---|---|---|---|---|---|
| full | 0.566 | 0.344 | 0.299 | 0.725 | 0.607 | 0.573 | 0.077 | 0.069 | 0.058 | 82% |
| embedding_only | 0.560 (-0.007) | 0.262 (-0.081) | 0.347 (+0.048) | 0.688 (-0.036) | 0.578 (-0.029) | 0.606 (+0.034) | 0.048 | 0.068 | 0.068 | 82% |
| no_class_balance | 0.606 (+0.040) | 0.299 (-0.045) | 0.258 (-0.041) | 0.712 (-0.013) | 0.617 (+0.010) | 0.524 (-0.048) | 0.058 | 0.106 | 0.032 | 73% |
| no_teacher_weight | 0.577 (+0.010) | 0.341 (-0.003) | 0.282 (-0.016) | 0.714 (-0.011) | 0.607 (+0.000) | 0.556 (-0.017) | 0.069 | 0.042 | 0.053 | 84% |
| no_temperature | 0.566 (+0.000) | 0.344 (+0.000) | 0.299 (+0.000) | 0.725 (+0.000) | 0.607 (+0.000) | 0.573 (+0.000) | 0.091 | 0.147 | 0.062 | 70% |

gold-dev has 184 emails; differences under ~0.05 are within bootstrap noise (C4 CIs are ±0.1).
