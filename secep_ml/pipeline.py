"""secep_ml.pipeline — Phase D4. One call per email: student triage, then the decoder.

    pipe = Pipeline(triage.load("model_v1"), Decoder(DecoderConfig.from_env()))   # decoder=None: triage only
    out = pipe.process_email(raw_bytes, "Manager", "To")

Rules (handover D4, SRS FR-DEC-006/007):
  * the student always runs; its result is never lost;
  * the decoder runs on every email (summary + actions); its adjudication overrides only the flagged heads
    (source "llm" for those heads);
  * decoder down / quota spent -> status "enrich_pending"; invalid output twice or any unexpected decoder error
    -> "enrich_failed"; labels then stay the student's. With no decoder configured -> status "triaged".
"""
from __future__ import annotations

import logging
import time
from typing import Mapping

from .decoder import Decoder
from .triage import HEADS, OUT_KEY, Triage

log = logging.getLogger("secep_ml.pipeline")


class Pipeline:
    def __init__(self, triage: Triage, decoder: Decoder | None = None):
        self.triage, self.decoder = triage, decoder

    def process_email(self, raw: bytes | str | Mapping, recipient_role: str, recipient_position: str,
                      today: str | None = None, email_id: str | None = None) -> dict:
        t0 = time.perf_counter()
        tri = self.triage.classify(raw, recipient_role, recipient_position, email_id=email_id)
        t_tri = (time.perf_counter() - t0) * 1000
        final = {h: tri[OUT_KEY[h]]["label"] for h in HEADS}
        sources = {h: "encoder" for h in HEADS}
        enrich, status, err = None, "triaged", None
        if self.decoder is not None:
            try:
                e = self.decoder.enrich(raw, tri, role=recipient_role, position=recipient_position, today=today)
                enrich, status = e, e["status"]
                if status == "enriched":
                    final, sources = e["final_labels"], e["sources"]
            except Exception as ex:                       # never lose the triage result
                status, err = "enrich_failed", f"{type(ex).__name__}"
                log.error("pipeline decoder error email_id=%s error=%s", tri["email_id"], err)
        return {"schema": "pipeline_result.v1", "email_id": tri["email_id"], "status": status,
                "triage": tri, "enrich": enrich, "final_labels": final, "sources": sources,
                "needs_review_heads": tri["review_heads"], "error": err,
                "latency_ms": {"triage": t_tri, "total": (time.perf_counter() - t0) * 1000}}
