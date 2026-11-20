# D3 dev run — devcalib — 2026-11-20T03:06:36

Backend `gemini` model `gemini-3.5-flash-lite`, prompt `enrich-1.1-c10dd7fa`, 276 emails (devcalib). **Indicative only:** gold-dev and gold-calib were used to tune the teacher.

## Decoder

- Schema-valid: 276/276 (100.0%); first attempt 276; failed 0.
- Flagged heads: {'type': 125, 'urgency': 210, 'sentiment': 104}; changed by decoder: {'type': 48, 'urgency': 96, 'sentiment': 43}.
- **Critical recall**: student 1/9 (11%) → hybrid 0/9 (0%). High recall: student 6/41 (15%) → hybrid 14/41 (34%).
- Flagged urgency heads moved to Critical: 0 of 210.
- Actions vs gold type: accuracy 69% (n 276); Approval 100% (n 27), Credentials 100% (n 4), Info 98% (n 154), Meeting 0% (n 17), Task 12% (n 74); any action on 4% of emails.
- Post-check violations: {'attendee_invalid': 4, 'missing_required': 19}.
- Latency per request: median 1664 ms, p95 2097 ms (n 276); tokens/email in 2012, out 167; requests 276 in total (256 this run, 20 answers from cache).

## Classification (score.py)

- student: see `score_student\report.md`
- hybrid: see `score_hybrid\report.md`
