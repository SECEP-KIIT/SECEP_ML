# Final evaluation on gold-test — 2026-11-19T21:36:42

- student mode: **mixed**; gold-test sha256 `a5b24fa8edce43f7…` verified; 426 emails
- strict macro-F1 with 95% bootstrap CI (2,000 resamples, seed 42); gate = human macro-F1 − 0.05

## View: all (426 emails, 0 excluded)

| System | Head / view | n | Strict macro-F1 | 95% CI | Human | Gate | Result |
|---|---|---|---|---|---|---|---|
| student | type | 397 | **0.501** | 0.412–0.576 | 0.625 | 0.575 | FAIL |
| student | urgency | 376 | **0.286** | 0.249–0.326 | 0.440 | 0.390 | FAIL |
| student | sentiment | 400 | **0.372** | 0.317–0.430 | 0.462 | 0.412 | FAIL |
| student | type_action | 397 | **0.690** | 0.640–0.735 | 0.781 | 0.731 | FAIL |
| student | urgency_2 | 376 | **0.517** | 0.464–0.578 | 0.728 | 0.678 | FAIL |
| student | sentiment_2 | 400 | **0.622** | 0.566–0.675 | 0.683 | 0.633 | FAIL |
| teacher | type | 397 | **0.599** | 0.514–0.665 | 0.625 | 0.575 | PASS |
| teacher | urgency | 376 | **0.402** | 0.356–0.449 | 0.440 | 0.390 | PASS |
| teacher | sentiment | 400 | **0.407** | 0.314–0.508 | 0.462 | 0.412 | FAIL |
| teacher | type_action | 397 | **0.754** | 0.708–0.796 | 0.781 | 0.731 | PASS |
| teacher | urgency_2 | 376 | **0.678** | 0.604–0.747 | 0.728 | 0.678 | PASS |
| teacher | sentiment_2 | 400 | **0.684** | 0.609–0.754 | 0.683 | 0.633 | PASS |
| hybrid | type | 397 | **0.577** | 0.489–0.644 | 0.625 | 0.575 | PASS |
| hybrid | urgency | 376 | **0.393** | 0.343–0.441 | 0.440 | 0.390 | PASS |
| hybrid | sentiment | 400 | **0.419** | 0.343–0.496 | 0.462 | 0.412 | PASS |
| hybrid | type_action | 397 | **0.736** | 0.689–0.777 | 0.781 | 0.731 | PASS |
| hybrid | urgency_2 | 376 | **0.665** | 0.586–0.736 | 0.728 | 0.678 | FAIL |
| hybrid | sentiment_2 | 400 | **0.699** | 0.632–0.761 | 0.683 | 0.633 | PASS |

## View: without_akashdeep_single (375 emails, 51 excluded)

| System | Head / view | n | Strict macro-F1 | 95% CI | Human | Gate | Result |
|---|---|---|---|---|---|---|---|
| student | type | 346 | **0.498** | 0.393–0.582 | 0.625 | 0.575 | FAIL |
| student | urgency | 325 | **0.293** | 0.254–0.395 | 0.440 | 0.390 | FAIL |
| student | sentiment | 349 | **0.379** | 0.318–0.442 | 0.462 | 0.412 | FAIL |
| student | type_action | 346 | **0.695** | 0.640–0.745 | 0.781 | 0.731 | FAIL |
| student | urgency_2 | 325 | **0.525** | 0.465–0.590 | 0.728 | 0.678 | FAIL |
| student | sentiment_2 | 349 | **0.643** | 0.580–0.697 | 0.683 | 0.633 | PASS |
| teacher | type | 346 | **0.614** | 0.521–0.686 | 0.625 | 0.575 | PASS |
| teacher | urgency | 325 | **0.413** | 0.363–0.554 | 0.440 | 0.390 | PASS |
| teacher | sentiment | 349 | **0.414** | 0.321–0.512 | 0.462 | 0.412 | PASS |
| teacher | type_action | 346 | **0.768** | 0.723–0.812 | 0.781 | 0.731 | PASS |
| teacher | urgency_2 | 325 | **0.680** | 0.598–0.753 | 0.728 | 0.678 | PASS |
| teacher | sentiment_2 | 349 | **0.697** | 0.619–0.770 | 0.683 | 0.633 | PASS |
| hybrid | type | 346 | **0.584** | 0.487–0.659 | 0.625 | 0.575 | PASS |
| hybrid | urgency | 325 | **0.402** | 0.352–0.536 | 0.440 | 0.390 | PASS |
| hybrid | sentiment | 349 | **0.426** | 0.345–0.508 | 0.462 | 0.412 | PASS |
| hybrid | type_action | 346 | **0.747** | 0.697–0.792 | 0.781 | 0.731 | PASS |
| hybrid | urgency_2 | 325 | **0.672** | 0.591–0.749 | 0.728 | 0.678 | FAIL |
| hybrid | sentiment_2 | 349 | **0.710** | 0.640–0.774 | 0.683 | 0.633 | PASS |

## View: single_labelled_only (286 emails, 140 excluded)

| System | Head / view | n | Strict macro-F1 | 95% CI | Human | Gate | Result |
|---|---|---|---|---|---|---|---|
| student | type | 286 | **0.491** | 0.381–0.581 | 0.625 | 0.575 | FAIL |
| student | urgency | 286 | **0.247** | 0.212–0.289 | 0.440 | 0.390 | FAIL |
| student | sentiment | 286 | **0.359** | 0.298–0.422 | 0.462 | 0.412 | FAIL |
| student | type_action | 286 | **0.646** | 0.588–0.704 | 0.781 | 0.731 | FAIL |
| student | urgency_2 | 286 | **0.499** | 0.450–0.563 | 0.728 | 0.678 | FAIL |
| student | sentiment_2 | 286 | **0.620** | 0.555–0.682 | 0.683 | 0.633 | FAIL |
| teacher | type | 286 | **0.567** | 0.467–0.651 | 0.625 | 0.575 | FAIL |
| teacher | urgency | 286 | **0.384** | 0.331–0.434 | 0.440 | 0.390 | FAIL |
| teacher | sentiment | 286 | **0.391** | 0.285–0.502 | 0.462 | 0.412 | FAIL |
| teacher | type_action | 286 | **0.722** | 0.665–0.771 | 0.781 | 0.731 | FAIL |
| teacher | urgency_2 | 286 | **0.670** | 0.584–0.747 | 0.728 | 0.678 | FAIL |
| teacher | sentiment_2 | 286 | **0.642** | 0.556–0.725 | 0.683 | 0.633 | PASS |
| hybrid | type | 286 | **0.539** | 0.437–0.621 | 0.625 | 0.575 | FAIL |
| hybrid | urgency | 286 | **0.373** | 0.318–0.422 | 0.440 | 0.390 | FAIL |
| hybrid | sentiment | 286 | **0.375** | 0.307–0.440 | 0.462 | 0.412 | FAIL |
| hybrid | type_action | 286 | **0.684** | 0.628–0.738 | 0.781 | 0.731 | FAIL |
| hybrid | urgency_2 | 286 | **0.653** | 0.568–0.731 | 0.728 | 0.678 | FAIL |
| hybrid | sentiment_2 | 286 | **0.675** | 0.595–0.746 | 0.683 | 0.633 | PASS |

## Student calibration and review routing (all gold-test rows)

| Head | ECE (equal-width 10) | ECE (equal-count 10) | Review rate (<0.60) |
|---|---|---|---|
| type | 0.051 | 0.066 | 39.9% |
| urgency | 0.061 | 0.099 | 70.4% |
| sentiment | 0.043 | 0.033 | 37.6% |

Any-head review rate: 78.9%

## Hybrid (what users see)

Student label where confident; LLM label where the head is flagged (top prob < threshold). The teacher (14B, 3 votes) stands in for the live 7B decoder, so this is an optimistic proxy.

| Head | Flagged | Label changed by LLM |
|---|---|---|
| type | 39.9% | 19.0% |
| urgency | 70.4% | 33.8% |
| sentiment | 37.6% | 18.8% |

