# Gold-set decision log

- Run: 2026-11-12T03:14:24
- Sheet: `gold_raw_v1.xlsx` sha256 `c3c13f77dd8d8b7da9d907c57d68bed095ec9edbb1d624d5c7b78899b77c3cdb`
- Manifest: `manifest.csv` sha256 `dd8b54a64c3510d1b7c86b24a201d61e0c000d46ef6c09635ba0b75e4cc3546c`
- Outlier rule (fixed before any model results): type κ with partners < team κ − 0.2 AND < 0.4
- Dropped outliers: none

## Step 2 — validation

- Label rows read: 900 from 6 labellers
- exclude: 50
- Blanks are never filled; a blank head drops that email from that head only.

## Step 3 — labeller check

- Akashdeep: type κ 0.3
- Amitava: type κ 0.45
- Ampa: type κ 0.527
- Areeb: type κ 0.496
- Milan: type κ 0.609
- Sumana: type κ 0.526

## Step 4 — agreement

- type Fleiss κ: 0.493 (0.36 – 0.61), moderate
- urgency Fleiss κ: 0.366 (0.22 – 0.50), fair
- urgency linear-weighted κ: 0.41 (0.27 – 0.55), moderate
- sentiment Fleiss κ: 0.397 (0.19 – 0.57), fair

## Step 5 — resolution rules

- Agreed labels kept. Missing on one side → the other label stands (single_of_two).
- Type conflicts settled by guide precedence: Credentials > Approval/Meeting > Task.
- Info-vs-X and Approval-vs-Meeting left unresolved; both labels kept (`*_alt`).
- Unresolved rows: excluded from strict scoring, lenient scoring accepts either label.
- Any labeller marking `exclude` removes the email.
- The teacher LLM is never used to break ties in gold sets.

## Step 6 — final gold sets

- gold_test: 426 emails, sha256 `839514776e56f7348ca53582e3a299d150a05ac54f4e5a0a528bada79325565e`
- gold_dev: 184 emails, sha256 `8712edc8739ac75f9ea3643eb1f5803fc79d6ce943e5cd0dd184d76b087f64c0`
- gold_calib: 92 emails, sha256 `58a120c5503c8dc8d04a022a52cbc96a1b8f272a606cb307c8b62fd12f196218`
- Excluded: 48; dropped as outlier rows: 0
- gold-test is SEALED from this point until final evaluation.

## Stage 0 — gold text rebuilt (20261112-042457)

- Text recipe: common/text.py, TEXT_VERSION 1.0
- Source: original Enron files via manifest source_path; Message-IDs verified
- Labels unchanged; previous sheet text kept as body_sheet
- Backup of previous files: _backup_20261112-042457/
- gold_test: 426 emails · 17 were longer than the sheet's 6,000-char cut · 18 had secrets masked · 1 near-empty bodies · median 622 chars
- gold_dev: 184 emails · 14 were longer than the sheet's 6,000-char cut · 6 had secrets masked · 0 near-empty bodies · median 558 chars
- gold_calib: 92 emails · 6 were longer than the sheet's 6,000-char cut · 1 had secrets masked · 0 near-empty bodies · median 526 chars
- gold_test.csv sha256 `a5b24fa8edce43f721ee461c0c9d20a7f948e0c2bc4f100d7aab829c66421a52`
- gold_dev.csv sha256 `8377a7ac48bec3805cd33a04929cad98d294d1950cbaf6a93667953463d7f360`
- gold_calib.csv sha256 `71c32204d4ff918684e7cb33de48037266d609bbd8941040bfd179e6ae5acdff`
- gold-test is SEALED from this point until final evaluation.

## Stage 0 — human baseline (2026-11-12 04:43)

- type: human macro-F1 0.625 (CI 0.43–0.73), κ 0.493, n 140 → teacher gate 0.575
- urgency: human macro-F1 0.440 (CI 0.37–0.63), κ 0.366, n 140 → teacher gate 0.390
- sentiment: human macro-F1 0.462 (CI 0.34–0.59), κ 0.397, n 140 → teacher gate 0.412
- type_action: human macro-F1 0.781 (CI 0.70–0.85), κ 0.561, n 140 → teacher gate 0.731
- urgency_2: human macro-F1 0.728 (CI 0.60–0.84), κ 0.456, n 140 → teacher gate 0.678
- sentiment_2: human macro-F1 0.683 (CI 0.58–0.77), κ 0.367, n 140 → teacher gate 0.633
- Teacher gate rule: human macro-F1 − 0.05 on the tune set (replaces the fixed 0.70).
- Planned robustness check (decided before any model results): final gold-test scores will also be reported excluding Akashdeep's single-labelled test rows.

(2026-11-16 9:19)
-Final scores will also be reported on single-labelled test emails only, because the double-labelled ones were read during the rule session.
-Teacher prompt tuning uses gold-dev and gold-calib together.
-The rule session read the double-labelled test emails.

## Phase A — training pool built (20261118-103703)

- 10000 emails: 6000 uniform + 4000 enriched (Q4-2001, tension, credentials/approval/meeting keywords), received folders only, all mailboxes
- Cut for the 14-hour plan: 10k pool instead of 25k
- Leakage removed: gold Message-IDs, gold uids (any mailbox), gold thread_ids, same subject with ≥2 shared participants, same cleaned text. Gate passed (0 overlap).
- Roles: common/roles.py v1.0 — gold's 19 exact; other mailboxes from approximate public titles; unknown → Other. Role prior must use the uniform slice only.
- pool.parquet sha256 `8f0b45608a9f2857f8136cdf6bc9624f91191c35b328a5c9c6f18d4f399495f3`; run record 2026-11-18-build_pool/

## 2026-11-18 — Teacher model (Phase B setup)
- Teacher = **Qwen2.5-7B-Instruct-AWQ** (vLLM 0.34.0, 2×T4, tensor-parallel 2, fp16, prefix caching).
- 14B-AWQ ran at 0.47 emails/s (10k ≈ 5.8 h), below the 0.93/s needed for the 3 h B2 box. 7B ran at 1.14/s (10k ≈ 2.45 h). JSON validity 1.0 for both.
- Trade-off: 7B is less self-consistent (type unanimity 0.87 vs 0.97 for 14B). B1 scores it against the human gate before B2.
- Teacher email cap: 1,500 tokens per email body (student keeps its own 384-token truncation).
- vLLM 0.34.0 because Kaggle now runs Python 3.13; older vLLM versions won't install there.
- Run folder: runs/2026-11-18-teacher-throughput/

(2026-11-19 , 3:00)
- The pool doesn’t match I2. It has pool_uid instead of email_uid, and slice instead of sample. C2/C3 will treat pool_uid as the join key unless Phase B’s labels use something else.
- pseudo_train.csv doesn’t exist yet. There’s no Data\pseudo\ folder at all. C2 (embedding) can go ahead without it, but C3 (training) can’t. Where did Phase B’s teacher output land? Probably still in the Kaggle notebook output.

## 2026-11-18 — Teacher prompt tuning (Phase B1)
- Teacher inputs dataset: gold_dev, gold_calib, labelling-guide v2, human_baseline.json, common/text.py only. gold_test not uploaded; the notebook refuses to run if it is attached.
- Tuned on dev+calib (n 271), strict macro-F1, gate = human − 0.05.
- Round 1: type 0.585, urgency 0.407, sentiment 0.425 — all pass.
- Round 2 (added rules for Task/Approval/Meeting/Credentials boundaries + SRS urgency definitions): type 0.602, urgency 0.474, sentiment 0.415 — all pass; sentiment by only +0.003 (about one email).
- Frozen at round 2; no round 3 (all heads pass, no sentiment pattern to target). Approval→Info errors rose 4 → 8 under the "agreeing is Info" rule; humans' own Approval F1 is ~0.3, so the label is noisy.
- Frozen prompt (5 few-shots): runs/2026-11-18-teacher-throughput/frozen_prompt.json. Every later teacher run uses exactly this file.

## 2026-11-18 — Pseudo-labelling (Phase B2)
- 10,000 pool emails, n 3, temperature 0.7, per-head majority vote. Weight 1.0 (3/3), 0.67 (2/3); no majority → blank label + weight 0 (type 10, urgency 29, sentiment 8 rows).
- Resumable shards; kernel crash at shard 15/20 resumed without loss. Type yield 99.9%.
- Spot check (30 random rows, reviewed by Claude; borderlines confirmed by ___): clear errors type 10% (23% incl. borderline), urgency 7% (17%), sentiment 0% (7%). Main failure: instructions inside broadcast/announcement emails labelled Info. Consistent with the teacher's dev macro-F1 ≈ 0.60. Accepted; not re-run.
- Known issue: common/text.py credential masking false-positives on "pass-" words ("pass-through" → "Pass-[MASKED:password]") and misses some username/password-hint fields. Left unchanged for v1 so gold, pool and live text stay identical (a change would invalidate embeddings). Fix with the credential-masking track after v1.
- Run folders: runs/2026-11-18-teacher-b1-r1/, -b1-r2/, -b2/.

## 2026-11-19 — Phase C setup (closes the 3:00 note)
- Phase B output found in the Kaggle notebook output; saved as Data/pseudo/pseudo_train.csv. Folder spelled `psuedo`, renamed to `pseudo`.
- pseudo_train.csv uses email_uid, which holds the same ids as the pool's pool_uid. Join verified in C3: 10,000 rows matched, text identical to the embedded text.
- Cuts for the compressed plan: teacher prompt rounds capped at 3; no encoder bake-off; 384-token truncation, no windowing; C grid {0.3, 1, 3}; role prior dropped; MLP / fine-tuning escalation dropped; ONNX optional; retraining = script + one simulated run.

## 2026-11-19 — Scorer (C1)
- common/metrics.py, scripts/score.py, tests/test_metrics.py (17 tests pass).
- Lenient F1: a correct prediction counts for whichever label it matched; a wrong prediction counts against the primary label.
- Absent classes handled exactly as in human_baseline.py, so human and model scores are comparable.
- ECE: 10 equal-width bins (headline) + 10 equal-count bins (reported).
- Bad input (unknown class, missing uid, probabilities not summing to 1) fails loudly.
- dev and calib are all single-labelled, so lenient = strict there; gold-test is the first set where they differ.

## 2026-11-19 — Embeddings (C2)
- Frozen all-mpnet-base-v2 on a Kaggle T4, 384-token truncation, L2-normalised. CPU parity cosine 1.000000.
- Truncated: pool 28%, gold_dev 26%, gold_calib 22%, gold_test 27%. Pool median 173 tokens, p95 ≈ 2,392.
- gold_test embedded only; labels not read.

## 2026-11-19 — Student heads (C3)
- Features 777 = 768 embedding + 6 roles + 3 positions. Engineer and Bcc never occur in training → mapped to Other / List/Unknown.
- C by cross-validated log-loss: type 1.0, urgency 0.3, sentiment 0.3.
- Class weights fully balanced × teacher vote weight. 0 of 702 gold uids in training. numpy = scikit-learn to 2e-16.
- Prior correction added (deviation): softmax((logits + log prior) / T_prior), prior = teacher-weighted class share in the training pool, T refit on gold-calib. Reason: balanced heads flagged 67–84% of emails for review.
- Pool mix ≠ gold mix: uniform pool Info 70% vs gold_dev 54%, Critical 0.2% vs 3.8%, Frustrated 0.3% vs 1.6% (gold sets were enriched). Prior mode learns the pool mix, so it is penalised on gold relative to real mailboxes.
- Model folder: model_v1/ (heads.npz, manifest.json); training file sha256 75ee0555… (full hash in manifest.json).

## 2026-11-19 — Mode, routing, latency (C4; decided on gold-dev before gold-test)
- Per-head mode: type prior, urgency prior, sentiment balanced (set_head_modes.py). Strict macro-F1, balanced vs prior: type 0.449 / 0.566, urgency 0.323 / 0.344, sentiment 0.299 / 0.258. Prior mode collapses sentiment to Neutral (182/184).
- Temperatures in use: type 1.33 (prior), urgency 1.91 (prior), sentiment 0.86 (balanced).
- Review routing option (a): 0.60 threshold on every head. Flagged heads are re-decided by the LLM in the same call that writes the summary (no extra round trip).
- Rejected: (b) type-only, which loses the urgency/sentiment correction; (c) per-head thresholds tuned to a target rate, which trades accuracy for load.
- This changes FR-DEC-006 (type-only in SRS v1.1), the enrich.v1 schema and the M3 needs_review rule. Amitava to be told. The LLM stage is async (NFR-PERF-004); the fast path is unaffected.
- Latency (predict_one, laptop CPU, 50 emails): median 117 ms, p95 313 ms, max 327 ms (target 350); model load 24 s.
- Ablation (dev, indicative): without role/position, urgency −0.08; without temperature, urgency ECE 0.069 → 0.147; unbalanced type head +0.04 (within noise, type_action worse) → class balancing kept, v2 candidate; teacher vote weighting has no measurable effect.

## 2026-11-19 — Final evaluation (C5)
- Teacher re-scored with our scorer on dev+calib (271): 0.602 / 0.474 / 0.415, identical to Phase B. 5 dev emails have no round-2 teacher prediction; all 5 are in rebuild_problems.csv (text rebuilt after the teacher run). Teacher on the 179 dev emails: 0.539 / 0.471 / 0.389.
- Gold-test hash: the Step 6 hash (839514…) is the pre-rebuild file. The sealed file is the rebuilt one (a5b24fa8…, Stage 0 rebuild entry), verified MATCH at final evaluation.
- Labelling manifest has 450 test uids; 24 dropped at finalisation (in issues.csv) → 426. final_eval.py check changed from "manifest uids == gold-test uids" to "every gold-test uid is in the manifest" before any scoring.
- Teacher gold-test run (Kaggle): frozen round-2 prompt, label-free input built from Data/emb_inputs/gold_test.csv + manifest.csv (gold_test.csv never opened). 426 emails, 450 s, 0 retries. Unanimous votes: type 93%, urgency 76%, sentiment 94%.
- vLLM warm-up error `No module named 'cutlass'` on first start; a full session restart cleared it. No packages or engine settings changed.
- Final evaluation run once, 2026-11-19 21:36 (runs/2026-11-19-final-eval/, locked by runs/final_eval.lock.json). Gold-test is now spent; no future model is tuned or gated on it.
- Test rows 426: double-labelled 140, single-labelled 286 (Akashdeep 51). Strict n: type 397, urgency 376, sentiment 400.
- Strict macro-F1 (type / urgency / sentiment): student 0.501 / 0.286 / 0.372 (fails all six gates); teacher 0.599 / 0.402 / 0.407; hybrid 0.577 / 0.393 / 0.419 (meets 5 of 6; urgency_2 0.665 vs gate 0.678, within CI).
- Robustness: without Akashdeep's single-labelled rows ≈ +0.01 for every system (no labeller skew). Single-labelled-only view lower for every system.
- Student ECE (equal-width) 0.051 / 0.061 / 0.043 — NFR-ML-004 met.
- Flagged < 0.60: type 39.9%, urgency 70.4%, sentiment 37.6%, any head 78.9%. LLM changed the label on 19% / 34% / 19% of emails.
- The hybrid is an optimistic proxy (3-vote teacher reading 1,500 tokens vs the live decoder's single call). The live decoder is evaluated in Phase D.
- Teacher Critical blind spot: 0 Critical predictions on gold-test, 1 in 271 dev+calib. A flagged urgency head cannot become Critical in the hybrid → Critical recall is a required check in the decoder evaluation.
- SRS NFR-ML-001–003 (0.75 / 0.60 / 0.60) exceed human agreement (0.625 / 0.440 / 0.462). Human-relative gates remain the operative targets; revise in SRS v1.3.
- Known text error: final_summary.md calls the hybrid's teacher "14B"; it is 7B. Not re-run.
- Model card: model_card.md (project copy: claude/model-card-v1.md).

## D3 · 2026-11-20 · Live hybrid evaluation on gold-test: second planned use (option a)

**Decision:** option (a). Run the live hybrid once on gold-test, pre-declared here before any decoder output on gold-test exists. Decided by Akashdeep (Sky).

**Why:** the model card's hybrid figures (§6) used the 3-vote Qwen 7B teacher as a stand-in for the live decoder. The decoder that actually ships (one Gemini Flash-Lite call adjudicating every flagged head) has never been measured. Critical recall is the main open risk: the teacher predicted 0 Critical in 426 test emails. Only a gold-test run replaces the optimistic proxy with a real figure. Dev-only results (option b) would remain indicative.

**What runs:** `model_v1` student (unchanged, `manifest_sha256` 09646396d00b…) + `secep_ml.decoder` with the Gemini backend, on all 426 gold-test emails, one call per email (plus at most one validation retry). Same backend, model, prompt and schema as the demo.

**Conditions, fixed now:**
1. **Prompt development uses gold-dev + gold-calib only.** Gold-test labels are not opened, and no gold-test email is sent to the decoder, until the lock below exists.
2. **Freeze before the run.** The lock records:
   - backend, model ID, decoder prompt version (hash of the prompt files) and `enrich.v1.1` schema SHA-256;
   - `model_v1` manifest SHA-256, temperature 0.2, review threshold 0.60;
   - the gold-test SHA-256, which must equal the sealed hash `a5b24fa8…`.

   It is written by a script to `runs/live_eval.lock.json` with status `declared`. The evaluation script refuses to start without the lock, if any frozen value differs, or if the status is `spent`.
3. **Label-free inputs.** Decoder inputs are built without label columns. Labels are loaded only by `score.py` at scoring time.
4. **One run.**
   - Emails left `enrich_pending` (quota or endpoint errors) are completed later with the identical frozen configuration. The response cache makes this a continuation, not a re-run.
   - `enrich_failed` emails stay failed: the hybrid keeps the student's labels for them, and they are counted and reported.
   - The run may span days and Google Cloud projects, but never more than one model.
5. **No tuning on test.** No prompt, threshold or code change after any gold-test output has been seen.
   - If a bug is found in the scoring or post-check code, the fix and the re-score are logged; LLM outputs are not regenerated.
   - A bug in the prompt or decoder call is reported as a limitation, not fixed and re-run.
6. **Pre-declared metrics** (reported whatever the result, next to the proxy hybrid and the student):
   1. Hybrid classification with `score.py`: strict and lenient macro-F1 for the 3 heads and 3 merged views, gates, 95% bootstrap CIs (2,000 resamples, seed 42), and both robustness views.
   2. Urgency: Critical recall and High recall against gold, and how many flagged urgency heads the decoder moved to Critical.
   3. Actions: accuracy against the type-derived expectation:
      - Task → `create_jira_issue` or `add_board_card`;
      - Meeting → `add_calendar_event`;
      - Info, Credentials → none;
      - Approval → board card or none.

      Also the share of emails with any action, and post-check violation counts.
   4. Summary faithfulness: a second model call on a random sample of 100 test emails (seed 42), reporting the share of summaries with at least one unsupported claim. Plus a human spot-check of 20 by one person.
   5. Schema validity: first attempt, after retry, and the `enrich_failed` count (NFR-ML-006 asks ≥ 99%).
   6. Latency: decoder median and p95 including network; requests per email.
7. **Data caveat:** content sent on the Gemini free tier may be used by Google to improve its products. That is acceptable for the public Enron corpus, not for real employee mail, and it is stated in the model card.
8. **After this run gold-test is fully spent.** No further evaluation of any model or prompt may use it. Future models are gated on new data or held-out corrections (D5).

**Lock files:** `runs/final_eval.lock.json` (C5, first use) stays as it is. `runs/live_eval.lock.json` will be created at prompt freeze, before the run, and set to `spent` when it completes.


---

## Phase D decisions · 2026-11-20

**D1 (inference package)**
- `triage.v1.1` (ML side) = SRS triage.v1 + per-head `needs_review`, `probs`, `source`; `review_heads`; manifest,
  text-recipe and input hashes. `to_triage_v1()` gives the exact SRS row, so the DB contract is unchanged.
- Sentiment score = P(Positive) − P(Negative) − P(Frustrated), clipped to [−1, 1] (SRS §6.7 M3 formula).
- DB spellings (`to/cc/bcc`, `Client-facing`) are mapped to the ML names; unseen values → fallback, reported.
- Acceptance: gold-dev parity max diff 0 (vs code), 20/20 pool emails valid, deterministic, train/serve text parity
  0 mismatches, p95 318 ms (target 350; thin margin, re-measure on the demo machine).

**D2 (decoder)**
- Decoder = Gemini 3.5 Flash-Lite (free tier) via google-genai `response_json_schema`; temperature 0.2. Groq was
  briefly selected and withdrawn the same night before any output (see D3 amendments).
- Prompt = SRS §6.7 system prompt + anti-injection rules + labelling-guide v2 copied verbatim (definitions,
  precedence, Approval clarification, R1–R14) for the flagged heads only + recipient role AND position (R9).
  Prompt version = hash of the prompt files.
- Unknown action types and invalid attendee addresses are removed before validation (no retry spent); other
  business-rule failures null the field or drop the action and are counted as violations.
- **Prompt revision after the dev run (20 Nov 03:40, before any gold-test output)** — dev+calib (276, prompt
  `enrich-1.1-c10dd7fa`): schema-valid 100%, but actions on only 4% of emails (Task 12%, Meeting 0%) and Critical
  recall 0/9 (0 of 210 flagged urgency heads moved to Critical). Changes: the system prompt now says when to propose
  each action type, sets Jira priority from urgency (FR-ORC-004 mapping) and states that Critical is rare but real
  (deadline within 24 h or outage/loss under way). Post-checks now REPAIR instead of drop where intent is clear:
  Jira priority from the final urgency; calendar end = start + 30 min when missing or not after start; calendar
  events without attendees are kept and M6 adds the mailbox owner (SRS v1.3 change to the per-type rule).
  New prompt version recorded in the lock. Dev figures for both versions are kept in their run folders.
- Email text sent to the LLM ≈ 3,000 tokens, approximated as 12,000 characters (no tokenizer for hosted models).
- Quota handling: on the daily limit the evaluation pauses and accepts another Google account's key; same model
  and prompt; key fingerprints (never keys) are logged in the run's config.json.

**D3 (evaluation)**
- Injection suite: 20 synthetic emails, every head forced to flagged (worst case).
- Faithfulness: a second call to the same model lists unsupported claims; test sample n = 100, seed 42 (fixed
  in the lock); a 20-email human spot-check sheet is written alongside.
- "Expected action" for the action metric: Task → Jira or board card (≥ 1 required); Meeting → calendar event
  (required); Info, Credentials → none; Approval → board card or none. Both an empty action list and a `none`
  action mean "no action".

**D5 (retraining)**
- `scripts/retrain.py` re-implements the Phase C head training from the model card (C from manifest, balanced ×
  teacher weight, mean 1; temperatures on gold-calib; prior from the pool). `--reproduce` (no corrections)
  measures agreement with model_v1 on gold-dev; result recorded in the retrain run.
- **Deviation:** gold-dev is used for the gate ONLY, not as training data (the handover listed it as an input;
  training on it would make the gate measure training data). Gold-test is not used (spent) — deviation from
  FR-ML-012.
- User cap (25%) applies only with ≥ 4 distinct users; with fewer it is recorded as "not applied".
- Promotion writes `model_vN/` + `promoted.json` (with the previous model's name); old versions are not deleted.
- The demo uses 140 template-written SaaS notification emails (not Enron); its candidate model is kept in the run
  folder and never promoted.


### D3 · 2026-11-20 04:42 · Go/no-go override before the freeze
Dev re-check (d3-dev-recheck-n120, prompt in the lock): failed ['Meeting action accuracy >= 50%']. Proceeding to the freeze anyway. Reason: Meeting action accuracy 3/8 (38 pct): n=8 is too small to tell from 50 pct (95 pct CI about 9-76 pct). All other checks passed with large gains (actions 4 to 33 pct of emails, Task 12 to 72 pct, hybrid macro-F1 +0.03 to +0.10 on every head). Tuning on 8 examples would overfit dev; Meeting actions and Critical recall are reported as limitations.
All other checks passed: ['schema-valid >= 99%', 'Task action accuracy >= 50%', 'hybrid macro-F1 >= student - 0.02 on every head']. The failed check is reported as a limitation in the model card; the gold-test metrics are unchanged and pre-declared.
