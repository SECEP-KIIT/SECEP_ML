# C5: final evaluation on gold-test (run once)

## Order of operations (from `ML_Training`)

**1. Fix the per-head mode** (uses gold-dev, so it must happen before gold-test is touched):
```powershell
python scripts\set_head_modes.py --type prior --urgency prior --sentiment balanced `
  --dev-balanced runs\2026-11-19-dev-balanced\score\metrics.json `
  --dev-prior    runs\2026-11-19-dev-prior\score\metrics.json `
  --reason "gold-dev strict macro-F1: prior better for type and urgency, balanced better for sentiment (prior collapses sentiment to Neutral)"
```
Writes `head_mode` + `default_mode = "mixed"` into `model_v1\manifest.json`. `heads.npz` is untouched. After gold-test has been used, this script refuses to run.

**2. (Optional, recommended) Score the teacher on gold-dev with the same scorer**, so the model card can say how much of the gap is the teacher's and how much the student's:
```powershell
python scripts\score.py --gold Data\gold_final\gold_dev.csv --pred runs\2026-11-18-teacher-b1-r2\predictions.csv `
  --out runs\2026-11-19-teacher-dev --baseline Data\gold_final\human_baseline.json
```

**2b. Ablation table** (NFR-ML-007; gold-dev only; ~5–10 min):
```powershell
python scripts\ablate.py
```
→ `runs\<date>-ablation\ablation.md`. The `full` row should reproduce the C4 mixed-mode gold-dev numbers.

**3. Get the teacher's gold-test predictions** (Areeb, once, frozen prompt, Phase B Kaggle notebook):
`predictions.csv` in I4 format: `email_uid, pred_type, pred_urgency, pred_sentiment` + `prob_<head>_<Class>` (vote shares of the 3 samples). **A label on every one of the 426 rows** (if the three votes all differ, pick the first sample; blank labels fail the scorer). Put it in `Data\pseudo\teacher_gold_test_predictions.csv`.

**4. Run it:**
```powershell
python scripts\final_eval.py --teacher Data\pseudo\teacher_gold_test_predictions.csv
```
It checks the gold-test SHA-256, builds both exclude lists from `Data\labelling\manifest.csv`, predicts with the student, scores student and teacher over three views (all rows / without Akashdeep's single-labelled rows / single-labelled rows only), and writes `runs\<date>-final-eval\final_summary.md` + `final_eval.json`.
With a teacher file it scores three systems: **student**, **teacher**, and **hybrid** (student label where confident, teacher label on each head below 0.60, standing in for the live decoder's adjudication; optimistic, since the teacher is 14B with 3 votes and the live decoder is 7B with 1 call). The teacher file is validated *before* gold-test labels are read, so a broken file does not use up the run.
It refuses a second run unless `--rerun-reason "why"` is given, which is logged. If the `labellers` column spells the name differently, pass `--labeller <exact text>`.

## Log in decision_log.md
- Per-head modes (type: prior, urgency: prior, sentiment: balanced), chosen on gold-dev, before gold-test was opened.
- Review routing: *(decide: type-only per the SRS, or extend the decoder; see the chat)*.
- Prior correction learns class frequencies from the teacher-labelled pool; the gold sets were sampled to be richer in rare classes, so prior mode is penalised on gold relative to real mailboxes.
- Gold-test used once on `<date>`; reruns (if any) and their reasons.
