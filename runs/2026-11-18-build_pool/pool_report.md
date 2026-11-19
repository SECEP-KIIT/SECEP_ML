# Training pool report (20261118-103703)

- **10000 emails**: 6000 uniform + 4000 enriched (targets 6000 + 4000); 149 mailboxes
- Text recipe `common/text.py` v1.0; roles `common/roles.py` v1.0
- pool.parquet sha256 `8f0b45608a9f2857f8136cdf6bc9624f91191c35b328a5c9c6f18d4f399495f3`
- **Leakage gate: PASSED** — 0 gold Message-IDs, 0 gold uids, 0 gold threads, 0 gold texts, 0 duplicates; ≤2 per thread
- Received emails scanned: 181630; eligible after removal: 137259
- Median body 628 chars; 456 with secrets masked; 903 broadcasts (>15 recipients)

## Removed before sampling

| reason | n |
|---|---:|
| duplicate text | 41732 |
| leak: gold thread_id | 1156 |
| leak: gold Message-ID | 660 |
| leak: gold email (same text, any mailbox) | 536 |
| leak: gold subject + shared participants | 287 |

## Rejected after cleaning

| reason | n |
|---|---:|
| duplicate cleaned text | 7 |
| body too short after cleaning | 5 |

## Uniform slice (use this alone for the role prior)

**Role**

| value | n | share |
|---|---:|---:|
| ClientFacing | 1480 | 24.7% |
| Consultant | 1184 | 19.7% |
| Executive | 1019 | 17.0% |
| Other | 962 | 16.0% |
| Manager | 855 | 14.2% |
| Analyst | 500 | 8.3% |

**Position**

| value | n | share |
|---|---:|---:|
| To | 2708 | 45.1% |
| List/Unknown | 2545 | 42.4% |
| Cc | 747 | 12.4% |

**Folder**

| value | n | share |
|---|---:|---:|
| inbox | 2517 | 41.9% |
| custom | 2029 | 33.8% |
| deleted | 1454 | 24.2% |

## Enriched slice

**Picked for**

| value | n | share |
|---|---:|---:|
| any-tag | 1578 | 39.5% |
| tension | 747 | 18.7% |
| credentials | 700 | 17.5% |
| approval | 594 | 14.8% |
| meeting | 381 | 9.5% |

**Tags carried (an email can carry several)**

| value | n | share |
|---|---:|---:|
| q4 | 2691 | 42.4% |
| tension | 1200 | 18.9% |
| meeting | 1009 | 15.9% |
| approval | 748 | 11.8% |
| credentials | 700 | 11.0% |

**Role**

| value | n | share |
|---|---:|---:|
| ClientFacing | 1233 | 30.8% |
| Consultant | 759 | 19.0% |
| Manager | 733 | 18.3% |
| Executive | 576 | 14.4% |
| Other | 464 | 11.6% |
| Analyst | 235 | 5.9% |

## Roles

- From gold mapping: 19 mailboxes; approximate titles: 107; unknown → Other: 24. See roles_used.csv.
- Mailboxes with no own address found (position = List/Unknown): 1
