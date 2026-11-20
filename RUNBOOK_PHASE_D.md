# Phase D — runbook

## The short version (recommended)
```powershell
cd C:\Dev\SECEP_ML\SECEP_ML\ML_Training
Expand-Archive -Path $HOME\Downloads\phase_d_final_v3.zip -DestinationPath . -Force
python scripts\run_phase_d.py
```
That one script runs every step below in order, with the go/no-go checks automated, and finishes by writing
`phase_d_results.txt`: send that file to Claude. It is safe to re-run at any time: finished steps are skipped and
cached API answers are reused. It asks you for input only twice: type `FREEZE` before the gold-test run, and paste
a second Google account's API key when the first account's daily quota runs out. If it stops, it prints why and
which file to send. `python scripts\run_phase_d.py --status` shows progress.

---

## The same steps by hand (reference)

Folder: `C:\Dev\SECEP_ML\SECEP_ML\ML_Training`. Quota: Gemini free tier ≈ 500 requests/day per Google account;
the counter resets at 13:30 IST. Today's first account has ≈ 219 left after the dev run. Budget from here: dev
re-check 120 + injection 20 + pipeline 5 + gold-test ~430 + faithfulness 100 ≈ 675 → expect one key swap during
the gold-test run (the script pauses and asks; paste a key from another Google account).

## 0. Let the running dev evaluation finish. Then install the bundle (2 min)
```powershell
cd C:\Dev\SECEP_ML\SECEP_ML\ML_Training
Expand-Archive -Path $HOME\Downloads\phase_d_final_v3.zip -DestinationPath . -Force
python -m pytest tests -q
Add-Content -Path Data\gold_final\decision_log.md -Value (Get-Content docs\decision_log_phase_d_additions.md -Raw -Encoding utf8) -Encoding utf8
Add-Content -Path .gitignore -Value "`nruns/decoder_cache/`n__pycache__/`n.pytest_cache/`n_backup_pre_c5/"
```
Expect all tests to pass (72 new + your scorer tests).

## 1. D5 retraining — no API, no quota (~5 min)
```powershell
python scripts\retrain.py --reproduce
python scripts\retrain_demo.py
```
- `--reproduce` must end with `REPRODUCTION: ... OK` (≥ 97% agreement with model_v1). If it says DIFFERS, stop
  here for D5 and send me `runs\<date>-retrain-reproduce\report.md` (D1–D4 are unaffected).
- The demo prints before/after accuracy on an untouched slice and the gate. If the slice barely moves at x2,
  run once more with `--corr-weight 10` (that is logged in demo.json).

## 1b. Re-check the revised prompt on dev — 120 requests (~13 min)
The dev run showed actions on only 4% of emails and no Critical; the prompt and post-checks were revised.
```powershell
python scripts\decoder_eval.py --split devcalib --limit 120
```
**Go to step 2 only if all three hold in the printed report:**
1. Schema-valid ≥ 99%.
2. Actions vs gold type: Task ≥ 50% and Meeting ≥ 50%.
3. Quick macro-F1 table: hybrid is not below student by more than 0.02 on any head.

Otherwise send me `runs\2026-11-20-d3-dev-devcalib-n120\report.md`. Critical recall is reported either way; it is not a gate.

## 2. Live checks — about 25 requests (~5 min)
```powershell
python scripts\injection_suite.py
python scripts\run_pipeline.py --n 5
```
- Injection: `20/20 passed` → continue. Any FAIL → send me `runs\<date>-injection\report.md` before step 3
  (a prompt fix must happen before the freeze).

## 3. Freeze and run gold-test ONCE (~45-60 min at 10 rpm; pause/key swap if the quota ends)
Only after steps 1b and 2 passed. Do not change the prompt files,
model or settings after this point.
```powershell
python scripts\live_lock.py declare
python scripts\decoder_eval.py --split test
python scripts\faithfulness.py --run runs\d3-live-gold-test
```
- If it stops (quota, closed window): run the SAME command again — it resumes; the lock stays "running".
- `faithfulness.py` uses the pre-declared n=100, seed 42 for the test run.
- One person fills `runs\d3-live-gold-test\faithfulness\spot_check_20.csv` (human_supported yes/no). Optional.

## 4. Send me everything in one file
```powershell
$files = Get-ChildItem runs -Recurse -Include report.md,faithfulness.json,demo.json,gate.json |
  Where-Object { $_.FullName -match "d3-|injection|retrain|d4-pipeline" }
$out = $files | ForEach-Object { "`n===== $($_.FullName.Substring((Get-Location).Path.Length+1)) =====`n" + (Get-Content $_.FullName -Raw -Encoding utf8) }
$out += "`n===== runs\live_eval.lock.json =====`n" + (Get-Content runs\live_eval.lock.json -Raw -Encoding utf8)
$out | Set-Content -Encoding utf8 phase_d_results.txt
```
Attach `phase_d_results.txt`. I then write model card §13, the SRS v1.3 change list and the final handover.

## 5. Commit (after step 4)
Branch + PR in the ML repo (two approvals): `secep_ml/`, `scripts/`, `tests/`, `docs/`, `requirements.txt`,
`README_secep_ml.md`, `RUNBOOK_PHASE_D.md`, `runs/live_eval.lock.json`, the run folders' report/metrics files,
`Data/gold_final/decision_log.md`. Never commit API keys or `runs/decoder_cache/`.
