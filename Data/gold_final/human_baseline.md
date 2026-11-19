# Human baseline (Stage 0, Job 4)

How well two labellers agree with each other on the 140 double-labelled emails, scored exactly the way the models will be scored. Treat these as the ceiling: a model that matches them is doing as well as a person.

| View | Pairs | Human macro-F1 | 95% CI | Same answer | κ | Teacher gate |
|---|---|---|---|---|---|---|
| type | 140 | **0.625** | 0.43 – 0.73 | 72% | 0.493 | 0.575 |
| urgency | 140 | **0.440** | 0.37 – 0.63 | 64% | 0.366 | 0.390 |
| sentiment | 140 | **0.462** | 0.34 – 0.59 | 81% | 0.397 | 0.412 |
| type_action | 140 | **0.781** | 0.70 – 0.85 | 79% | 0.561 | 0.731 |
| urgency_2 | 140 | **0.728** | 0.60 – 0.84 | 89% | 0.456 | 0.678 |
| sentiment_2 | 140 | **0.683** | 0.58 – 0.77 | 81% | 0.367 | 0.633 |

**Teacher gate** = human macro-F1 − 0.05. In Stage 2 the teacher's prompt is good enough when it reaches this on the tune set, instead of the fixed 0.70.

**Merged views**: type_action = Info vs needs-something; urgency_2 = Critical/High vs Medium/Low; sentiment_2 = Neutral vs not. Use them where a class has too few examples to score on its own.

## Human F1 per class

- **type**: Task 0.58, Info 0.83, Credentials 0.80, Meeting 0.62, Approval 0.30
- **urgency**: Critical 0.00, High 0.48, Medium 0.53, Low 0.74
- **sentiment**: Positive 0.63, Neutral 0.89, Negative 0.00, Frustrated 0.33
- **type_action**: Needs something 0.73, Info 0.83
- **urgency_2**: Act soon 0.52, Can wait 0.94
- **sentiment_2**: Neutral 0.89, Not neutral 0.48

Note: all double-labelled emails sit in gold-test, so this reads gold-test LABELS once. It uses no model output, and must be run before gold-test is sealed.
