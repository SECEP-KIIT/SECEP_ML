# D1 inference on pool sample — 2026-11-20T00:44:25

Model `model_v1` (manifest `09646396d00b…`), text recipe 1.0, 20 pool emails (seed 42), 3 runs each.

| check | result | pass |
|---|---|---|
| classified + schema-valid | 20/20, invalid 0, problems 0 | ✓ |
| deterministic across 3 runs | 0 differ | ✓ |
| text parity with pool input_text | 0 mismatch | ✓ |
| latency (classify, after load) | median 172 ms, p95 318 ms, max 323 ms over 60 | ✓ |

Model load 8.4 s. Review rate: type 35%, urgency 65%, sentiment 25%, any head 65%

**D1 pool run: PASS**
