# Gold-set agreement report

Double-labelled emails used: 140 (excluded ones removed).

## Inter-annotator agreement (step 4)

| head | metric | n | kappa | 95% CI | band | % agree |
|---|---|---|---|---|---|---|
| type | Fleiss κ | 140 | 0.493 | 0.36 – 0.61 | moderate | 72% |
| urgency | Fleiss κ | 140 | 0.366 | 0.22 – 0.50 | fair | 64% |
| urgency | linear-weighted κ | 140 | 0.41 | 0.27 – 0.55 | moderate |  |
| sentiment | Fleiss κ | 140 | 0.397 | 0.19 – 0.57 | fair | 81% |

Bands (Landis & Koch): ≤0.20 slight · 0.21–0.40 fair · 0.41–0.60 moderate · 0.61–0.80 substantial · >0.80 almost perfect. These κ values are the human ceiling the model is judged against.

## Per-labeller agreement with their partners (step 3)

| labeller | type κ | type n | urgency κ | urgency n | sentiment κ | sentiment n | flag |
|---|---|---|---|---|---|---|---|
| Akashdeep | 0.3 | 47 | 0.206 | 47 | 0.313 | 47 |  |
| Amitava | 0.45 | 49 | 0.348 | 49 | 0.441 | 49 |  |
| Ampa | 0.527 | 49 | 0.291 | 49 | 0.51 | 49 |  |
| Areeb | 0.496 | 46 | 0.419 | 46 | 0.221 | 46 |  |
| Milan | 0.609 | 45 | 0.503 | 45 | 0.43 | 45 |  |
| Sumana | 0.526 | 44 | 0.367 | 44 | 0.516 | 44 |  |

Outlier rule: type κ < team κ (0.49) − 0.2 and < 0.4. Per-labeller κ rests on ~50 emails, so treat it as a screen, not a verdict.

## Class-mix flags (step 3)

- Amitava: urgency=Low 71% vs team 51%
- Milan: urgency=Medium 45% vs team 28%
- Milan: urgency=Low 41% vs team 57%
- Areeb: sentiment=Neutral 68% vs team 86%

## Labeller-vs-labeller confusion (step 4)

**type** — most frequent disagreements:
- Info ↔ Task: 20
- Approval ↔ Task: 9
- Info ↔ Meeting: 4
- Approval ↔ Info: 4
- Approval ↔ Meeting: 1
- Credentials ↔ Info: 1

**urgency** — most frequent disagreements:
- Low ↔ Medium: 34
- High ↔ Medium: 8
- High ↔ Low: 6
- Critical ↔ Low: 1
- Critical ↔ High: 1

**sentiment** — most frequent disagreements:
- Neutral ↔ Positive: 13
- Negative ↔ Neutral: 9
- Frustrated ↔ Neutral: 4

## Resolution (step 5)

- type: agreed 101, precedence 10, single 562, unresolved 29
- urgency: agreed 90, single 562, unresolved 50
- sentiment: agreed 114, single 562, unresolved 26

## Final gold sets (step 6) — strict counts per class

| head | class | test | dev | calib |
|---|---|---|---|---|
| sentiment | Frustrated | 8 | 3 | 3 |
| sentiment | Negative | 11 | 10 | 7 |
| sentiment | Neutral | 345 | 155 | 75 |
| sentiment | Positive | 36 | 16 | 7 |
| type | Approval | 30 | 16 | 11 |
| type | Credentials | 13 | 2 | 2 |
| type | Info | 244 | 100 | 54 |
| type | Meeting | 24 | 13 | 4 |
| type | Task | 86 | 53 | 21 |
| urgency | Critical | 7 | 7 | 2 |
| urgency | High | 44 | 28 | 13 |
| urgency | Low | 217 | 93 | 48 |
| urgency | Medium | 108 | 56 | 29 |

⚠ gold-test type=Credentials: only 13 (report with wide CI)
⚠ gold-test urgency=Critical: only 7 (report with wide CI)
⚠ gold-test sentiment=Negative: only 11 (report with wide CI)
⚠ gold-test sentiment=Frustrated: only 8 (report with wide CI)
