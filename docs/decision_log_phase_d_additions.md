

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
