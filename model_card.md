# SECEP email classifier — model card (model_v1)

*Phase C, 19 Nov 2026. Scope: the encoder-based classifier ("student") and the review routing that sends low-confidence heads to the LLM ("hybrid"). Phase D addendum, 20 Nov 2026: §13 evaluates the live decoder (summaries, actions, adjudication) and replaces the proxy hybrid of §6 as the headline for the shipped system.*

## 1. Purpose and intended use
Classifies each incoming corporate email for one recipient into **type** (Task, Info, Credentials, Meeting, Approval), **urgency** (Critical, High, Medium, Low) and **sentiment** (Positive, Neutral, Negative, Frustrated), so the SECEP board can group and sort mail.

- **Intended use:** triage support. Labels sort and highlight; the user still opens and reads the email. Every head carries a confidence; heads below 0.60 are flagged and re-decided by the LLM decoder.
- **Not intended for:** automatic actions without a user click; compliance, HR or legal decisions; mail from organisations or eras very different from the training data (see §10) without re-validation.
- **Inputs used:** email text, recipient role, recipient position (To/Cc/Bcc). Nothing else, so the model only uses what the live system has.

## 2. Design
- **Encoder:** `all-mpnet-base-v2`, frozen, max 384 tokens (no windowing).
- **Features:** 768-d embedding + one-hot recipient role (6 used) + position (3 used) = 777.
- **Heads:** one multinomial logistic regression per head, trained in scikit-learn, served in numpy only (`model_v1/heads.npz`). C = 1.0 (type), 0.3 (urgency), 0.3 (sentiment).
- **Class weighting:** fully balanced (`n / (k·n_c)`) × teacher vote weight, mean 1.
- **Per-head probability mode** (chosen on gold-dev before gold-test was used):
  - type: **prior-corrected**, `softmax((logits + log prior) / T)`, T = 1.33
  - urgency: **prior-corrected**, T = 1.91
  - sentiment: **balanced**, `softmax(logits / T)`, T = 0.86
  - prior = teacher-weighted class share in the training pool; temperatures fitted on gold-calib.
- **Review routing:** any head with top probability < 0.60 is flagged. The live decoder adjudicates only the flagged heads, in the same call that writes the summary, so the fast classification path is unaffected.
- Full configuration, versions and training-file SHA-256: `model_v1/manifest.json`.

## 3. Data
**Source:** Enron email corpus (one company, 1999–2002).

**Gold set (human labels):**
- 6 labellers; 900 labels covering 750 emails, of which 150 double-labelled.
- Inter-annotator agreement (Cohen's κ): type 0.49, urgency 0.37, sentiment 0.40.
- Disagreements: type settled by precedence (Credentials > Approval/Meeting > Task > Info); other unresolved disagreements are dropped from strict scoring.
- 48 emails dropped at finalisation (recorded in `issues.csv`): **dev 184** (of 200), **calib 92** (of 100), **test 426** (of 450). 702 gold emails in total, none in training.
- Gold-test sealed with SHA-256 `a5b24fa8…`; verified at final evaluation.

**Training pool (pseudo-labelled):**
- 10,000 emails: 6,000 uniform + 4,000 enriched for rarer classes. None overlap gold.
- Labelled by the teacher (§4); vote share used as a per-head training weight. Rows with no majority were given weight 0: 10 (type), 29 (urgency), 8 (sentiment).
- Class mix differs from gold. For example, the uniform pool is 70% Info against 54% in gold-dev, and Critical is 0.2% against 3.8%, because the gold sets were enriched.

**Truncation at 384 tokens:** pool 28%, gold-dev 26%, gold-calib 22%, gold-test 27%. Pool median 173 tokens, p95 ≈ 2,392.

## 4. Teacher (pseudo-labeller)
`Qwen2.5-7B-Instruct-AWQ` on vLLM 0.34.0. Prompt frozen at round 2 with 5 few-shot examples, up to 1,500 email tokens. 3 samples at temperature 0.7, majority vote, seed 42. (14B was tried and was too slow.)

Prompt tuning used gold-dev and gold-calib. The gold-test run used a label-free input built from embedding inputs and the labelling manifest:
- 426 emails, 450 s, 0 retries.
- Unanimous votes: type 93%, urgency 76%, sentiment 94%.

## 5. Targets
Gates are relative to human agreement: **gate = human macro-F1 − 0.05**.

| | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 |
|---|---|---|---|---|---|---|
| Human macro-F1 | 0.625 | 0.440 | 0.462 | 0.781 | 0.728 | 0.683 |
| Gate | 0.575 | 0.390 | 0.412 | 0.731 | 0.678 | 0.633 |

`_action` / `_2` are merged views, reported because rare classes are thin in gold-test.

**SRS NFR-ML-001–004** set absolute targets of macro-F1 0.75 (type), 0.60 (urgency), 0.60 (sentiment) and ECE ≤ 0.08. The three F1 targets are **above what humans achieve against each other** on this data, so no system here, human or model, meets them. Gates relative to human agreement are the operative targets; the SRS figures are reported for traceability and should be revised in the next SRS version.

## 6. Results on gold-test (final, single run)
Strict macro-F1 with 95% bootstrap CI (2,000 resamples, seed 42). n per head after dropping unresolved disagreements: type 397, urgency 376, sentiment 400.

**All 426 emails**

| System | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 |
|---|---|---|---|---|---|---|
| Student | 0.501 (0.41–0.58) ✗ | 0.286 (0.25–0.33) ✗ | 0.372 (0.32–0.43) ✗ | 0.690 (0.64–0.74) ✗ | 0.517 (0.46–0.58) ✗ | 0.622 (0.57–0.68) ✗ |
| Teacher | 0.599 (0.51–0.67) ✓ | 0.402 (0.36–0.45) ✓ | 0.407 (0.31–0.51) ✗ | 0.754 (0.71–0.80) ✓ | 0.678 (0.60–0.75) ✓ | 0.684 (0.61–0.75) ✓ |
| **Hybrid** | **0.577** (0.49–0.64) ✓ | **0.393** (0.34–0.44) ✓ | **0.419** (0.34–0.50) ✓ | **0.736** (0.69–0.78) ✓ | **0.665** (0.59–0.74) ✗ | **0.699** (0.63–0.76) ✓ |

**Robustness views** (strict macro-F1, ✓ = meets gate)

| View | System | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 |
|---|---|---|---|---|---|---|---|
| Without Akashdeep's single-labelled rows (375) | Student | 0.498 ✗ | 0.293 ✗ | 0.379 ✗ | 0.695 ✗ | 0.525 ✗ | 0.643 ✓ |
| | Teacher | 0.614 ✓ | 0.413 ✓ | 0.414 ✓ | 0.768 ✓ | 0.680 ✓ | 0.697 ✓ |
| | Hybrid | 0.584 ✓ | 0.402 ✓ | 0.426 ✓ | 0.747 ✓ | 0.672 ✗ | 0.710 ✓ |
| Single-labelled only (286) | Student | 0.491 ✗ | 0.247 ✗ | 0.359 ✗ | 0.646 ✗ | 0.499 ✗ | 0.620 ✗ |
| | Teacher | 0.567 ✗ | 0.384 ✗ | 0.391 ✗ | 0.722 ✗ | 0.670 ✗ | 0.642 ✓ |
| | Hybrid | 0.539 ✗ | 0.373 ✗ | 0.375 ✗ | 0.684 ✗ | 0.653 ✗ | 0.675 ✓ |

Full tables: `runs/2026-11-19-final-eval/final_summary.md`. Lenient scores are in `final_eval.json`.

### Reading the results
1. **The student on its own does not meet the gates.** Urgency is clearly below: the CI upper bounds, 0.33 strict and 0.58 merged, sit well under the gates. Type and sentiment are below the gate at the point estimate; their CIs reach it or come close.
2. **The shipped system, the hybrid, meets 5 of 6 gates.** urgency_2 misses by 0.013, well inside its CI. Every hybrid result is statistically indistinguishable from its gate, in both directions.
3. **The hybrid is an optimistic proxy.** It uses the 3-vote teacher, which also reads up to 1,500 tokens, as a stand-in for the live decoder's single 7B call. Expect the live system to score somewhat lower until the decoder is evaluated on its own. **Superseded by §13:** the live decoder (Gemini 3.5 Flash-Lite, single call) was evaluated on 20 Nov and scored at or above this proxy on 5 of 6 views.
4. **Removing Akashdeep's single-labelled rows changes little:** at most +0.02 on any head and system. There's no sign that one labeller skews the results.
5. **Single-labelled emails are harder for every system,** humans' gate included. The gates come from agreement on double-labelled emails, while single-labelled rows carry one labeller's noise and unresolved cases cannot be dropped. Read this view as a stress test, not the headline.
6. **Dev to test:** the student lost about 0.07 on type and 0.06 on urgency and gained 0.07 on sentiment. Gold-dev (184 emails) had CIs around ±0.1 and was also used to tune the teacher, so dev figures were indicative only.

## 7. Calibration and review routing (student, gold-test)

| Head | ECE equal-width (headline) | ECE equal-count | Flagged (< 0.60) | Label changed by LLM |
|---|---|---|---|---|
| type | 0.051 | 0.066 | 39.9% | 19.0% |
| urgency | 0.061 | 0.099 | 70.4% | 33.8% |
| sentiment | 0.043 | 0.033 | 37.6% | 18.8% |

- **ECE ≤ 0.08 (NFR-ML-004) is met on all three heads** at the headline measure. Urgency's equal-count ECE (0.099) is the one weak spot.
- **78.9% of emails have at least one flagged head**, so the LLM adjudicates most emails. This is by design, since the student is confident only where it is reliable, but it makes decoder throughput and cost first-order concerns for deployment (async path, NFR-PERF-004).
- "Label changed" is a share of all emails. About half of flagged heads end up with a different label after adjudication.

## 8. Latency (student, `predict_one`, laptop CPU, 50 emails)
Median 117 ms, p95 313 ms, max 327 ms (target 350 ms). Model load 24 s, once per process. The decoder adds its own asynchronous latency for flagged heads (measured in §13.7).

## 9. Ablation (NFR-ML-007; gold-dev, strict macro-F1, indicative)
Each row switches one component off and retrains. Differences under about 0.05 are within bootstrap noise on 184 emails.

| Variant | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 | ECE t/u/s | Review (any) |
|---|---|---|---|---|---|---|---|---|
| full | 0.566 | 0.344 | 0.299 | 0.725 | 0.607 | 0.573 | 0.077 / 0.069 / 0.058 | 82% |
| no role/position (embedding only) | 0.560 | **0.262** | 0.347 | 0.688 | 0.578 | 0.606 | 0.048 / 0.068 / 0.068 | 82% |
| no class balance | 0.606 | 0.299 | 0.258 | 0.712 | 0.617 | 0.524 | 0.058 / 0.106 / 0.032 | 73% |
| no teacher weight | 0.577 | 0.341 | 0.282 | 0.714 | 0.607 | 0.556 | 0.069 / 0.042 / 0.053 | 84% |
| no temperature | 0.566 | 0.344 | 0.299 | 0.725 | 0.607 | 0.573 | 0.091 / **0.147** / 0.062 | 70% |

- **Recipient role and position matter most for urgency** (−0.08 without them). This supports the recipient-aware design.
- **Temperature scaling does not change labels but is what keeps calibration in spec.** Without it, urgency ECE doubles to 0.147, and the review rate drops because the model becomes falsely confident.
- **Class balancing:** the unbalanced type head scored +0.04 on dev. That is within noise, and the merged type_action view got worse, so it was not adopted; candidate for v2 with more labelled data. Balancing protects rare classes, Credentials included, which feeds credential masking.
- **Teacher vote weighting:** no measurable effect either way.

## 10. Limitations
- **One company, one era.** Enron, 1999–2002. Vocabulary, roles and email habits differ from a modern organisation; re-validate before trusting it elsewhere.
- **Thin rare classes.** Critical, Frustrated, Credentials and Approval have few gold examples, so their per-class F1 is noisy. The merged views exist for this reason.
- **The teacher almost never predicts Critical:** 1 in 271 dev+calib emails, 0 in 426 test emails. The student inherits a weak Critical signal, and **in the hybrid a flagged urgency head can never be adjudicated to Critical.** Critical recall is the most important single check for the decoder evaluation. **Phase D result (§13.4):** the live decoder behaves the same way, 0 of 8 Critical emails found.
- **Teacher label noise.** About 10% clear type errors in the Phase B spot-check. The student learns from these labels.
- **Unseen categories.** Recipient role Engineer and position Bcc never occur in training; they are mapped to Other and List/Unknown.
- **Truncation.** 27% of test emails exceed 384 tokens, so the student sees only the start. The teacher reads up to 1,500 tokens, which accounts for part of the teacher–student gap.
- **Pool vs gold mix.** Prior correction learns the pool's class mix, not the enriched gold mix.
- **Masking false positives.** `text.py` masks "pass-…" patterns as credentials, which also catches some innocent words.
- **Hybrid proxy is optimistic** (§6, point 3). The live evaluation in §13 found the live hybrid at or above the proxy; see §13.2.
- Further limitations found in Phase D are listed in §13.9.

## 11. Deviations from plan
- **Pool and search reduced:** training pool of 10k instead of 25k; teacher prompt rounds capped at 3 (frozen at round 2); no encoder bake-off; C grid {0.3, 1, 3}.
- **Dropped:** role prior; MLP and fine-tuning escalation.
- **Prior correction and per-head modes** were added after C3; they were chosen on gold-dev before gold-test.
- **Per-head adjudication.** The LLM adjudicates any flagged head, not only type. This changes FR-DEC-006, the enrich.v1 schema and the M3 needs_review rule.
- **Teacher = 7B,** not 14B (throughput).
- **Gold-test = 426 emails,** not ~450: 24 dropped at finalisation; dev and calib similarly reduced.
- **Teacher dev comparison** used 179 of 184 dev emails. The 5 missing emails had their text rebuilt after the teacher run; the dev+calib figure is on 271 emails and matches Phase B exactly.
- **`final_eval.py` manifest check** relaxed before any scoring, from "manifest test uids must equal gold-test uids" to "gold-test uids must be a subset", because of the 24 dropped emails.
- `final_summary.md` describes the hybrid's teacher as "14B"; it is the 7B model (text error only).
- **Gold-test used a second time, by pre-declaration** (Phase D, §13.1): one logged live-hybrid run. The lock now reads *spent*; there is no third use.

## 12. Reproducibility
- Seed 42 throughout.
- Every run writes `runs/<date>-<name>/` with config, metrics and input fingerprints.
- Training file SHA-256 `75ee0555…` (in `manifest.json`).
- Gold-test was used once for Phase C; `runs/final_eval.lock.json` prevents silent re-runs. The Phase D live run is locked separately by `runs/live_eval.lock.json` (§13.1).

## 13. Live hybrid and decoder evaluation (Phase D, 20 Nov 2026)

### 13.1 What was evaluated
- **Decoder:** Google Gemini **`gemini-3.5-flash-lite`**, through the Gemini API free tier (demo hosting decision). One call per email returns the summary, the actions and the adjudication of every flagged head (schema `enrich.v1.1`, Gemini JSON-schema output, always re-validated in code, one retry). Temperature 0.2. Input: masked text up to about 3,000 tokens, recipient role and position, the student's labels and confidences, the labelling-guide v2 definitions and rules R1–R14.
- **Prompt version `enrich-1.1-3cffc3b6`** (hash of the prompt files). The first dev prompt (`c10dd7fa`) was replaced before any gold-test output (§13.8).
- **Pre-declared, one-time gold-test run** (decision log, D3 option a). `runs/live_eval.lock.json` froze the backend, model, prompt and schema hashes, manifest hash, review threshold 0.60, temperature, text version, the hashes of the five code files that shape the output, and the sealed gold-test hash (`a5b24fa8…`, verified). The lock now reads **spent**.
  - Run: 20 Nov 2026, 04:49–05:51 IST; 426 emails; 426 enriched, 0 failed.
  - It used two Google accounts' keys (same model; the second took over after the first account's daily quota ran out). A third key served the faithfulness check. Keys are logged as fingerprints only.
- **Data-use caveat:** content sent to the Gemini free tier may be used by Google to improve its products. Acceptable for Enron mail in this demo; **not acceptable for real employee mail.** Production should use the self-hosted model (Ollama and vLLM adapters are in the package) or a paid tier whose data terms have been checked.

### 13.2 Headline: strict macro-F1 on gold-test
n per head: type 397, urgency 376, sentiment 400. 95% bootstrap CI in brackets (2,000 resamples, seed 42). ✓ = meets gate.

| System | type | urgency | sentiment | type_action | urgency_2 | sentiment_2 |
|---|---|---|---|---|---|---|
| Gate | 0.575 | 0.390 | 0.412 | 0.731 | 0.678 | 0.633 |
| Student (§6) | 0.501 ✗ | 0.286 ✗ | 0.372 ✗ | 0.690 ✗ | 0.517 ✗ | 0.622 ✗ |
| Proxy hybrid (§6, 3-vote teacher) | 0.577 ✓ | 0.393 ✓ | 0.419 ✓ | 0.736 ✓ | 0.665 ✗ | 0.699 ✓ |
| **Live hybrid (Gemini, one call)** | **0.617** (0.52–0.69) ✓ | **0.409** (0.36–0.46) ✓ | **0.437** (0.36–0.52) ✓ | **0.772** (0.73–0.81) ✓ | **0.644** (0.56–0.72) ✗ | **0.711** (0.64–0.77) ✓ |
| Human agreement | 0.625 | 0.440 | 0.462 | 0.781 | 0.728 | 0.683 |

Lenient macro-F1 (alternative labels also accepted): live hybrid 0.668 / 0.433 / 0.493 for type / urgency / sentiment; student 0.536 / 0.301 / 0.415.

1. **The live hybrid meets 5 of 6 gates**, the same count as the proxy. It misses urgency_2 by 0.034; the CI (0.56–0.72) includes the gate.
2. **The live hybrid scored at or above the proxy on 5 of 6 views** (type +0.040, urgency +0.016, sentiment +0.018, type_action +0.036, sentiment_2 +0.012) and below on urgency_2 (−0.021). All differences are inside the CIs. §6 expected the live system to score lower; it did not. The reason is not established. Candidates, unverified: the decoder reads up to about 3,000 tokens against the teacher's 1,500, and its prompt carries the labelling-guide definitions and rules.
3. **Against the student** the hybrid adds +0.116 (type), +0.124 (urgency), +0.065 (sentiment), +0.081 (type_action), +0.128 (urgency_2), +0.088 (sentiment_2). The CIs overlap on most views and no paired bootstrap was run, so the overall gain is not claimed as significant; the clearer evidence is on the heads the decoder re-decides (§13.3).
4. **Against human agreement** the hybrid is closest on type (−0.008) and type_action (−0.009), then sentiment (−0.025) and urgency (−0.031), and furthest on urgency_2 (−0.084). On sentiment_2 it is above human agreement (+0.028).
5. The student row reproduces §6 to three decimals when scored through the new inference package, which is an independent check that the package matches the Phase C model.

### 13.3 What the decoder changes
Per head, over all 426 emails, and accuracy on the flagged heads that were scored strictly.

| Head | Flagged | Label changed by decoder | Accuracy on flagged heads, student → hybrid |
|---|---|---|---|
| type | 170 (39.9%) | 86 (51% of flagged) | 51% → 71% (n = 155) |
| urgency | 300 (70.4%) | 132 (44%) | 45% → 61% (n = 259) |
| sentiment | 160 (37.6%) | 72 (45%) | 50% → 85% (n = 149; 86% of gold sentiment is Neutral, so judge sentiment by macro-F1) |

Flag counts equal the student's review rates in §7, as they should. Accuracy figures are derived from the calibration tables of the two score reports (decoder-decided heads are scored as probability 1.0); exact counts are in `score_student/` and `score_hybrid/` `metrics.json`. Heads the student was confident about keep the student's label.

### 13.4 Urgency and Critical (the check §10 asked for)
- **Critical recall: student 0 of 8, hybrid 0 of 8** (all 426 rows; 7 in the strict set). The 95% upper bound for 0 of 8 is about 37%, so the sample cannot say how bad it is, only that no Critical email was found. The decoder moved **1 of 300** flagged urgency heads to Critical, and that email was not Critical. Gemini behaves like the teacher here, and the prompt line "Critical is rare but real" did not change it. **Do not rely on the Critical label.**
- **High recall:** 3 of 51 (6%) → 10 of 51 (20%).
- **Act soon (Critical + High, urgency_2):** recall 24% (12 of 51, up from 8%), precision 71% (12 of 17). **39 of 51 urgent emails are still labelled "can wait".** On the board, the top urgency columns will hold few emails and mostly correct ones; most urgent mail will sit among Medium and Low. Gold urgency itself is noisy (κ 0.37).

### 13.5 Actions
- **Any action is proposed on 35% of emails (148 of 426).** Proposed actions: board card 77, Jira issue 51, calendar event 31. (The first dev run proposed actions on 4% of emails: a prompt and post-check defect fixed before the freeze, §13.8.)
- **Action consistent with the gold type** (Task → Jira or board card; Meeting → calendar event; Info and Credentials → none; Approval → board card or none): overall 76%. Info 84% (n = 259), Credentials 92% (13), Approval 74% (34), **Task 62% (95)**, **Meeting 36% (25)**.
- **Meeting actions are weak.** 9 of 25, 95% Wilson interval about 20–56%. The dev go/no-go failed on this check (3 of 8); the freeze went ahead under a logged override because n = 8 could not separate 38% from 50%. The test set points the same way, so the weakness looks real: calendar events are under-proposed. Task cards are also missed for about 38% of gold Tasks. Present proposals as help when they appear, not as full coverage.
- **Post-check repairs and drops** (code, FR-DEC-003): 26 calendar events came without attendees and were kept (M6 adds the mailbox owner); 3 invalid attendee addresses removed; 1 end ≤ start; 1 end defaulted to start + 30 min. No action was dropped for a missing required field.

### 13.6 Summaries: faithfulness
- **Automatic check:** a second call to the same model (`faith-1-0c9eae46`) lists claims in the summaries that the email text does not support. Random sample of 100 of the 426 (seed 42), 0 check failures. **27% of the sampled summaries had at least one flagged claim.**
- **This is a screening figure, not a measured hallucination rate.** A first read of the first 20 sampled emails (Claude's read, not the human check) found 3 flagged: one looks like a false positive (the flagged one-line summary is supported by the thread), and two are statements about the recipient rather than the email's content, "no action or reply is required" (an inference) and "the recipient is on Cc" (the decoder is given the recipient position; the checker sees only the email text). So part of the 27% comes from the checker's design.
- **Human spot-check of those 20 is pending** (`runs/d3-live-gold-test/faithfulness/spot_check_20.csv`, column `human_supported` empty). Quote the 27% only with this caveat until it is filled.

### 13.7 Reliability, injection, latency
- **Schema-valid 426 of 426**; 425 on the first attempt, 1 after the retry; none ended `enrich_failed` or `enrich_pending`.
- **Injection suite (FR-DEC-004): 20 of 20 passed**, with every head forced to flagged (worst case): forced labels, injected Jira, calendar and board actions, prompt and rules leaks, format changes, delimiter escape, fake assistant turn, admin claim, secret unmasking, multilingual, base64, HTML comment, JSON injection, action flood, persona switch.
- **Latency.** Student p95 318 ms (target 350 ms; the margin is thin). Decoder per request: median 3.3 s, p95 8.3 s over the gold-test run, against 1.6 s and 2.1 s in the dev runs; the cause (free-tier load, the key change) was not investigated. Tokens per email about 2,100 in and 184 out. End to end (student + decoder, 5 uncached emails): median 5.9 s, p95 6.3 s.
- **Throughput.** The decoder runs on every email. The free tier allows about 500 requests per day per project for this model, so about 500 emails per day per project. Gold-test (426) plus the rest of Phase D needed two days' worth of quota across accounts.

### 13.8 Development runs and the pre-freeze fix
- **Dev run 1** (dev + calib, 276 emails, prompt `c10dd7fa`): schema-valid 276 of 276, but actions on only 4% of emails (Task 12%, Meeting 0%) and 19 actions dropped as missing required fields.
- **Fix, before any gold-test output:** the prompt now says when to propose each action type, maps Jira priority from urgency (FR-ORC-004) and adds the Critical line; post-checks repair instead of dropping (Jira priority from the final urgency, calendar end defaulted, calendar without attendees kept). New prompt version `enrich-1.1-3cffc3b6`.
- **Dev re-check** (120 emails): schema-valid 100%, any action 33%, Task 72%, Meeting 38% (3 of 8), hybrid macro-F1 above the student on every head. Meeting missed its 50% go/no-go bar; override logged in `decision_log.md` with the reason, then frozen. Dev scores are indicative (the prompt was tuned on them).

### 13.9 Retraining (D5) and notes for reading the numbers
**Retraining** (`scripts/retrain.py`, laptop CPU, seconds, no LLM)
- **Reproduction:** re-running the Phase C recipe on the same inputs gives the same gold-dev labels as `model_v1` for 99.5% of type, 100% of urgency and 100% of sentiment predictions.
- **Demo:** 140 synthetic modern SaaS-style emails written for this demo (not Enron). 84 were used as feedback: 110 corrections from 4 simulated users, weight ×2. The other 56 were never trained on. Accuracy on those 56: type 55% → 86%, urgency 38% → 68%, sentiment 82% → 88%.
- **The promotion gate refused the candidate:** type macro-F1 on gold-dev fell 0.002 (0.566 → 0.565), urgency +0.003, sentiment +0.002, no class F1 drop above 0.03, held-out corrections 0% → 67%. The gate demands no drop at all, so a 0.002 dip on 184 emails (CI about ±0.1) blocks promotion. The candidate stays in the run folder; `promoted.json` is untouched. Whether to allow a small tolerance is a team decision (SRS list).

**Reading the numbers**
- **Hybrid calibration figures are not meaningful.** Decoder-decided heads are scored with probability 1.0, so the hybrid's ECE (type 0.145, urgency 0.295, sentiment 0.069) and its 0% review rate are artifacts of the scoring file. The student's calibration (§7) stands. In the product, a head with `source = llm` should show its source, not a confidence.
- The `decoder_eval` report's quick macro-F1 (0.599 / 0.391 / 0.438) uses all 426 rows by primary label; the `score.py` strict figures above are the reference.

**Limitations found in Phase D**
- Critical is not detected (§13.4); urgent mail is mostly under-flagged (24% recall).
- Meeting and Task actions are under-proposed (§13.5).
- The faithfulness figure is an automatic screen with known false positives; the human check is pending (§13.6).
- The decoder depends on a free-tier external API: a quota stop pauses enrichment (emails stay `enrich_pending` with student labels), and content leaves the machine (§13.1).
- Decoder latency is several seconds and unstable on the free tier (§13.7).
- Retrain keeps every promoted version; pruning to the last three is not implemented.

### 13.10 Reproducibility
- Run folders: `runs/d3-live-gold-test/` (gold-test, `score_student/`, `score_hybrid/`, `faithfulness/`), `runs/2026-11-20-d3-dev-devcalib/`, `runs/d3-dev-recheck-n120/`, `runs/2026-11-20-injection/`, `runs/2026-11-20-d4-pipeline/`, `runs/2026-11-20-retrain-reproduce/`, `runs/2026-11-20-retrain-demo/`. Orchestration state: `runs/phase_d_state.json`; combined results: `phase_d_results.txt`.
- Lock: `runs/live_eval.lock.json` (status spent). Seeds 42. Responses are cached on disk by email, prompt version, model and flagged heads, so a re-run costs no quota.
- `scripts/decoder_eval.py` was edited after the freeze (key-prompt validation only). It is not among the hashed files and the edit does not touch decoding or scoring.
