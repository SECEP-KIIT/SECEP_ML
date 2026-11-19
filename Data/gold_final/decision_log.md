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
