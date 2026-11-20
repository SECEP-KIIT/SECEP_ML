# D3 dev run — devcalib-n120 — 2026-11-20T04:41:38

Backend `gemini` model `gemini-3.5-flash-lite`, prompt `enrich-1.1-3cffc3b6`, 120 emails (devcalib). **Indicative only:** gold-dev and gold-calib were used to tune the teacher.

## Decoder

- Schema-valid: 120/120 (100.0%); first attempt 120; failed 0.
- Flagged heads: {'type': 49, 'urgency': 83, 'sentiment': 39}; changed by decoder: {'type': 16, 'urgency': 33, 'sentiment': 16}.
- **Critical recall**: student 1/5 (20%) → hybrid 0/5 (0%). High recall: student 2/13 (15%) → hybrid 4/13 (31%).
- Flagged urgency heads moved to Critical: 0 of 83.
- Actions vs gold type: accuracy 84% (n 120); Approval 92% (n 13), Credentials 100% (n 3), Info 93% (n 67), Meeting 38% (n 8), Task 72% (n 29); any action on 33% of emails.
- Action types proposed: {'add_board_card': 27, 'create_jira_issue': 10, 'none': 65, 'add_calendar_event': 5}.
- Post-check notes (repairs and drops): {'attendees_missing_owner_added_by_m6': 5, 'attendee_invalid': 1}.
- Latency per request: median 1621 ms, p95 2102 ms (n 120); tokens/email in 2120, out 173; requests 120 in total (0 this run, 120 answers from cache).

## Classification

Quick macro-F1 (primary gold label, classes present in gold; score.py is the reference):

| head | n | student | hybrid | Δ |
|---|---|---|---|---|
| type | 120 | 0.523 | 0.619 | +0.096 |
| urgency | 120 | 0.396 | 0.443 | +0.047 |
| sentiment | 120 | 0.295 | 0.324 | +0.029 |

- student: see `score_student\report.md`
- hybrid: see `score_hybrid\report.md`
