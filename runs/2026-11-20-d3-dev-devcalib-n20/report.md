# D3 dev run — devcalib-n20 — 2026-11-20T03:04:06

Backend `gemini` model `gemini-3.5-flash-lite`, prompt `enrich-1.1-c10dd7fa`, 20 emails (devcalib). **Indicative only:** gold-dev and gold-calib were used to tune the teacher.

## Decoder

- Schema-valid: 20/20 (100.0%); first attempt 20; failed 0.
- Flagged heads: {'type': 10, 'urgency': 15, 'sentiment': 7}; changed by decoder: {'type': 2, 'urgency': 5, 'sentiment': 3}.
- **Critical recall**: student 0/1 (0%) → hybrid 0/1 (0%). High recall: student 0/2 (0%) → hybrid 1/2 (50%).
- Flagged urgency heads moved to Critical: 0 of 15.
- Actions vs gold type: accuracy 70% (n 20); Approval 100% (n 2), Info 100% (n 12), Meeting 0% (n 2), Task 0% (n 4); any action on 0% of emails.
- Post-check violations: {'attendee_invalid': 1, 'missing_required': 1}.
- Latency per request: median 1753 ms, p95 2083 ms (n 20); tokens/email in 2113, out 158; requests 20 in total (20 this run, 0 answers from cache).

## Classification (score.py)

- student: see `score_student\report.md`
- hybrid: see `score_hybrid\report.md`
