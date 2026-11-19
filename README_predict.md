# Prediction + gold-dev sanity (Phase C4)

## Commands (from `ML_Training`)
```powershell
# 1. retrain (adds class priors + a second temperature for prior-corrected mode; ~6 min, same model otherwise)
python scripts\train_heads.py

# 2. predict gold-dev in both modes
python scripts\predict.py --mode balanced --out runs\2026-11-19-dev-balanced
python scripts\predict.py --mode prior    --out runs\2026-11-19-dev-prior

# 3. score both against gold-dev
python scripts\score.py --gold Data\gold_final\gold_dev.csv --pred runs\2026-11-19-dev-balanced\predictions.csv --out runs\2026-11-19-dev-balanced\score --baseline Data\gold_final\human_baseline.json
python scripts\score.py --gold Data\gold_final\gold_dev.csv --pred runs\2026-11-19-dev-prior\predictions.csv    --out runs\2026-11-19-dev-prior\score    --baseline Data\gold_final\human_baseline.json

# 4. CPU latency of predict_one (embed + heads) over 50 emails
python scripts\predict.py --latency 50
```

## Two modes, one model
| Mode | Probabilities | Expect |
|---|---|---|
| `balanced` | softmax(logits / T) | Best macro-F1 on rare classes; probabilities spread thin, so a high review rate |
| `prior` | softmax((logits + log prior) / T_prior) | Reflects real class frequencies; much lower review rate; some rare-class recall lost |

The heads (W, b) are identical; only the last step differs. The mode is picked once, on gold-dev, then fixed in `manifest.json` (`default_mode`) before C5.

## Caveats
- **Gold-dev is indicative.** It was used to tune the teacher's prompt, and now to pick the mode. The clean number is gold-test (C5).
- `predict.py` refuses `gold_test.csv` until C5.
- numpy == scikit-learn parity is checked during training (≤ 1e-6, recorded as `parity_max_abs_diff` in the run's metrics.json).
- `Engineer` / `Bcc` → `Other` / `List/Unknown` (unseen in training); counted in `predict.json`.
