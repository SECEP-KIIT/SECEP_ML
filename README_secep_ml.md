# secep_ml — SECEP ML inference package (Phase D)

Self-contained Python package the backend services call. Train and serve share one text recipe
(`common/text.py`) and one set of numpy heads (`common/student.py`).

| Module | Role | Backend service |
|---|---|---|
| `secep_ml/triage.py` | student: text recipe → frozen mpnet → numpy heads → triage.v1.1 (per-head `needs_review` < 0.60) | M3 |
| `secep_ml/decoder.py` | one LLM call: summaries, ≤ 3 actions, adjudication of flagged heads → enrich.v1.1 | M4 |
| `secep_ml/pipeline.py` | student always, then decoder; decoder failure never loses triage | M3 + M4 |
| `scripts/retrain.py` | refit heads on stored embeddings + user corrections, gate, promote | Admin "retrain" |
| `secep_ml/schemas/` | triage.v1 (SRS), triage.v1.1, enrich.v1 (SRS), enrich.v1.1 | all |

## Install
```powershell
python -m pip install -r requirements.txt
```
The encoder (`sentence-transformers/all-mpnet-base-v2`) downloads once from the Hugging Face Hub. After that, set
`HF_HUB_OFFLINE=1` on the demo machine so start-up never depends on the network.

## Configure the decoder (environment variables, never in code)
| Variable | Example | Notes |
|---|---|---|
| `GEMINI_API_KEY` | (from Google AI Studio) | never commit; never paste into chats |
| `SECEP_DECODER_BACKEND` | `gemini` | `gemini` (default), `groq`, `ollama`, `vllm` |
| `SECEP_DECODER_MODEL` | `gemini-3.5-flash-lite` | always from config: free-tier models get renamed and retired |
| `SECEP_DECODER_RPM` | `10` | client-side throttle, keep below the free-tier limit |
| `SECEP_DECODER_TEMPERATURE` | `0.2` | `none` omits it, for models that reject sampling parameters |
| `SECEP_DECODER_CACHE` | `runs/decoder_cache` | response cache: re-runs never spend quota twice |
| `SECEP_DECODER_ENDPOINT` | `http://localhost:11434` | Ollama / vLLM base URL (self-hosted path, SRS DC-09) |

## Use
```python
from secep_ml import triage, decoder
from secep_ml.pipeline import Pipeline

tri = triage.load_promoted(".")                  # promoted.json if present, else model_v1; loads once (~10-25 s)
dec = decoder.Decoder(decoder.DecoderConfig.from_env())
pipe = Pipeline(tri, dec)                        # Pipeline(tri) = triage only

out = pipe.process_email(raw_bytes, "Manager", "to")   # role/position accept DB spellings
out["status"]          # triaged | enriched | enrich_pending | enrich_failed
out["triage"]          # triage.v1.1; triage.to_triage_v1(out["triage"]) -> the triage_results row
out["enrich"]["enrich"]  # enrich.v1: summary_one_line, summary_short, actions (store as proposed)
out["final_labels"], out["sources"]   # adjudicated heads have source "llm"
```
- Student: p95 ≈ 318 ms per email on a laptop CPU after load. Decoder (Gemini 3.5 Flash-Lite): ≈ 2–3 s.
- `enrich_pending` = endpoint down or quota spent: retry later (FR-DEC-007). `enrich_failed` = invalid twice (FR-DEC-002).
- Logs carry metadata only (endpoint, model, tokens, latency, status), never email text (FR-DEC-009).
- Data: only masked text leaves the machine. **Gemini free tier: Google may use the content to improve its
  products**: fine for the Enron demo, not for real employee mail (use the self-hosted backend or a paid tier).

## Retrain (laptop, seconds to minutes, no LLM)
```powershell
python scripts\retrain.py --corrections corrections.csv --promote
```
Corrections CSV: `email_uid, head, label, user_id, recipient_role, recipient_position, input_text`.
Gate: no gold-dev macro-F1 drop on any head, no class F1 drop > 0.03, better on held-out corrections.
Passing + `--promote` writes `model_vN/` and points `promoted.json` at it; the service reloads (`load_promoted`).

## Tests
```powershell
python -m pytest tests -q
```
Offline: stub encoder and mocked LLM; fixtures in `tests/fixtures/` (10 raw emails, 20 injection emails).
