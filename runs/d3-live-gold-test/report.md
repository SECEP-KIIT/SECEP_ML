# D3 dev run — test — 2026-11-20T05:03:33

Backend `gemini` model `gemini-3.5-flash-lite`, prompt `enrich-1.1-3cffc3b6`, 426 emails (test). **Pre-declared one-time gold-test run** (runs/live_eval.lock.json).

## Decoder

- Schema-valid: 426/426 (100.0%); first attempt 425; failed 0.
- Flagged heads: {'type': 170, 'urgency': 300, 'sentiment': 160}; changed by decoder: {'type': 86, 'urgency': 132, 'sentiment': 72}.
- **Critical recall**: student 0/8 (0%) → hybrid 0/8 (0%). High recall: student 3/51 (6%) → hybrid 10/51 (20%).
- Flagged urgency heads moved to Critical: 1 of 300.
- Actions vs gold type: accuracy 76% (n 426); Approval 74% (n 34), Credentials 92% (n 13), Info 84% (n 259), Meeting 36% (n 25), Task 62% (n 95); any action on 35% of emails.
- Action types proposed: {'add_board_card': 77, 'create_jira_issue': 51, 'none': 234, 'add_calendar_event': 31}.
- Post-check notes (repairs and drops): {'attendees_missing_owner_added_by_m6': 26, 'attendee_invalid': 3, 'end_not_after_start': 1, 'end_defaulted_30min': 1}.
- Latency per request: median 3344 ms, p95 8328 ms (n 426); tokens/email in 2101, out 184; requests 427 in total (366 this run, 61 answers from cache).

## Classification

Quick macro-F1 (primary gold label, classes present in gold; score.py is the reference):

| head | n | student | hybrid | Δ |
|---|---|---|---|---|
| type | 426 | 0.485 | 0.599 | +0.114 |
| urgency | 426 | 0.283 | 0.391 | +0.108 |
| sentiment | 426 | 0.377 | 0.438 | +0.061 |

- student: see `score_student\report.md`
- hybrid: see `score_hybrid\report.md`
