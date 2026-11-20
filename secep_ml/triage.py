"""secep_ml.triage — Phase D1. Student inference for one email (the M3 Triage path).

    t = load(Path("model_v1"))                     # encoder loaded once (~24 s), heads in numpy
    out = t.classify(raw_bytes, "Manager", "To")   # -> triage.v1.1 dict, schema-validated
    v1 = to_triage_v1(out)                         # exact SRS triage.v1 shape for triage_results

Pipeline: common/text.py process() -> input_text -> frozen encoder -> numpy heads (common/student.py,
per-head probability mode from the manifest) -> per-head label, confidence, probabilities, needs_review
(top probability < manifest review_threshold, 0.60) -> review_heads.

Accepted email inputs:
  * bytes / str          raw RFC-822 message (an Enron file, a Gmail `raw` message)
  * {"subject", "body"}  already-parsed fields; the body goes through the same clean_body() recipe
  * {"input_text"}       a pre-built model string, used verbatim (parity checks against stored data)

Determinism (FR-TRI-011): same input + same model -> identical output apart from `processed_at`,
which callers can pin. No sampling anywhere; the encoder runs in eval mode.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np

from . import _ROOT  # noqa: F401  (ensures `common` is importable)
from common import student as S
from common import text as T

log = logging.getLogger("secep_ml.triage")

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
HEADS = ("type", "urgency", "sentiment")
OUT_KEY = {"type": "email_type", "urgency": "urgency", "sentiment": "sentiment"}

# DB / API spellings -> I1 spellings (the DB uses lower-case positions and "Client-facing").
_POSITION_ALIASES = {"to": "To", "cc": "Cc", "bcc": "Bcc", "list/unknown": "List/Unknown", "list": "List/Unknown",
                     "unknown": "List/Unknown"}
_ROLE_ALIASES = {"client-facing": "ClientFacing", "clientfacing": "ClientFacing", "client facing": "ClientFacing"}

EmbedFn = Callable[[Sequence[str]], np.ndarray]


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def normalise_role(role: str) -> str:
    r = (role or "").strip()
    return _ROLE_ALIASES.get(r.lower(), next((c for c in S.ROLES_I1 if c.lower() == r.lower()), r))


def normalise_position(position: str) -> str:
    p = (position or "").strip()
    return _POSITION_ALIASES.get(p.lower(), p)


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _validator(name: str):
    import jsonschema
    schema = load_schema(name)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema, format_checker=cls.FORMAT_CHECKER)


def sentiment_score(p: Mapping[str, float]) -> float:
    """triage.v1 needs a score in [-1, 1]; the student has class probabilities only.
    score = P(Positive) - P(Negative) - P(Frustrated). Neutral pulls it towards 0."""
    s = p["Positive"] - p["Negative"] - p["Frustrated"]
    return float(min(1.0, max(-1.0, round(s, 4))))


def to_triage_v1(r: dict) -> dict:
    """triage.v1.1 -> the exact SRS triage.v1 object (what M3 writes to triage_results)."""
    return {
        "schema": "triage.v1",
        "email_id": r["email_id"],
        "email_type": {k: r["email_type"][k] for k in ("label", "confidence", "source")},
        "urgency": {k: r["urgency"][k] for k in ("label", "confidence")},
        "sentiment": {k: r["sentiment"][k] for k in ("label", "score", "confidence")},
        "needs_review": r["needs_review"],
        "model_version": r["model_version"],
        "processed_at": r["processed_at"],
    }


class Triage:
    def __init__(self, model_dir: Path | str, embed_fn: EmbedFn | None = None, device: str = "cpu",
                 mode: str | None = None, validate: bool = True):
        model_dir = Path(model_dir)
        self.model_dir = model_dir
        self.manifest, self.heads = S.load_model(model_dir)
        self.manifest_sha256 = _sha256_bytes((model_dir / "manifest.json").read_bytes())
        self.model_version = str(self.manifest.get("model") or model_dir.name)
        self.mode = mode or self.manifest.get("default_mode", "balanced")
        self.head_modes = S.head_modes(self.manifest, self.mode)
        self.threshold = float(self.manifest.get("review_threshold", 0.60))
        self.text_version = T.TEXT_VERSION
        want_tv = self.manifest.get("text_version")
        if want_tv and want_tv != T.TEXT_VERSION:
            raise RuntimeError(f"model trained on text recipe {want_tv}, common/text.py is {T.TEXT_VERSION}")
        missing = [h for h in HEADS if h not in self.heads]
        if missing:
            raise ValueError(f"{model_dir}: heads missing {missing}")
        self._embed = embed_fn or self._load_encoder(device)
        self._v11 = _validator("triage.v1.1") if validate else None
        log.info("triage loaded: model=%s manifest_sha256=%s mode=%s head_modes=%s threshold=%.2f text=%s",
                 self.model_version, self.manifest_sha256, self.mode, self.head_modes, self.threshold,
                 self.text_version)

    # ------------------------------------------------------------ encoder (identical to Student.embed)
    def _load_encoder(self, device: str) -> EmbedFn:
        from sentence_transformers import SentenceTransformer
        enc = SentenceTransformer(self.manifest["encoder"], device=device)
        enc.max_seq_length = self.manifest["max_seq_length"]
        enc.eval()

        def embed(texts: Sequence[str]) -> np.ndarray:
            return enc.encode(list(texts), batch_size=8, normalize_embeddings=True, convert_to_numpy=True,
                              show_progress_bar=False).astype(np.float32)
        return embed

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        E = np.asarray(self._embed(texts), dtype=np.float32)
        if E.shape != (len(texts), self.manifest.get("emb_dim", S.EMB_DIM)):
            raise ValueError(f"encoder returned shape {E.shape}")
        return E

    # ------------------------------------------------------------ input
    @staticmethod
    def prepare(email: bytes | str | Mapping) -> dict:
        """Any accepted input -> {input_text, message_id, date, masked_kinds, truncated}."""
        if isinstance(email, (bytes, bytearray, str)):
            p = T.process(bytes(email) if isinstance(email, bytearray) else email)
            return {k: p[k] for k in ("input_text", "message_id", "date", "subject", "masked_kinds", "truncated")}
        if isinstance(email, Mapping):
            if email.get("input_text"):
                return {"input_text": str(email["input_text"]), "message_id": email.get("message_id", ""),
                        "date": email.get("date", ""), "subject": email.get("subject", ""),
                        "masked_kinds": [], "truncated": False}
            if "body" in email or "subject" in email:
                c = T.clean_body(str(email.get("body") or ""))
                subj = T.clean_subject(str(email.get("subject") or ""))
                return {"input_text": T.format_input(subj, c["body"]), "message_id": email.get("message_id", ""),
                        "date": email.get("date", ""), "subject": subj, "masked_kinds": c["masked_kinds"],
                        "truncated": c["truncated"]}
        raise TypeError("email must be raw bytes/str, or a mapping with 'input_text' or 'subject'/'body'")

    # ------------------------------------------------------------ heads
    def probs_from_embeddings(self, E: np.ndarray, roles: Sequence[str], positions: Sequence[str]
                              ) -> tuple[dict[str, np.ndarray], dict]:
        """Batch path on stored embeddings (parity checks, retraining). Same code as predict.py."""
        roles = [normalise_role(r) for r in roles]
        positions = [normalise_position(p) for p in positions]
        X, unseen = S.build_features(np.asarray(E), roles, positions, self.manifest["roles"],
                                     self.manifest["positions"])
        return S.predict_proba(self.manifest, self.heads, X, self.mode), unseen

    # ------------------------------------------------------------ main entry
    def classify(self, email: bytes | str | Mapping, recipient_role: str, recipient_position: str, *,
                 email_id: str | None = None, processed_at: str | None = None) -> dict:
        prep = self.prepare(email)
        input_text = prep["input_text"]
        role, position = normalise_role(recipient_role), normalise_position(recipient_position)
        input_sha = _sha256_bytes(input_text.encode("utf-8"))

        P, unseen = self.probs_from_embeddings(self.embed([input_text]), [role], [position])

        out: dict = {"schema": "triage.v1.1",
                     "email_id": str(email_id) if email_id else str(uuid.uuid5(
                         uuid.NAMESPACE_URL, f"secep:{prep['message_id']}|{input_sha}|{role}|{position}"))}
        review = []
        for h in HEADS:
            classes = self.manifest["classes"][h]
            p = P[h][0]
            j = int(p.argmax())
            conf = float(p[j])
            flag = conf < self.threshold
            obj = {"label": classes[j], "confidence": conf, "source": "encoder", "needs_review": flag,
                   "probs": {c: float(v) for c, v in zip(classes, p)}}
            if h == "sentiment":
                obj["score"] = sentiment_score(obj["probs"])
            out[OUT_KEY[h]] = obj
            if flag:
                review.append(h)
        out.update({"needs_review": bool(review), "review_heads": review, "model_version": self.model_version,
                    "manifest_sha256": self.manifest_sha256, "text_version": self.text_version,
                    "input_sha256": input_sha,
                    "processed_at": processed_at or datetime.now(timezone.utc).isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z")})
        u = {k: next(iter(v)) for k, v in unseen.items() if v}
        if u:
            out["unseen"] = u
            log.info("unseen category mapped to fallback: %s", u)
        if self._v11 is not None:
            self._v11.validate(out)
        return out


def load(model_dir: Path | str, **kw) -> Triage:
    return Triage(model_dir, **kw)


def promoted_model_dir(root: Path | str) -> Path:
    """The model the service should serve: promoted.json (written by scripts/retrain.py) if present, else model_v1."""
    root = Path(root)
    p = root / "promoted.json"
    if p.exists():
        d = root / json.loads(p.read_text(encoding="utf-8"))["model_dir"]
        if (d / "manifest.json").exists():
            return d
        log.warning("promoted.json points to %s, which has no manifest; falling back to model_v1", d)
    return root / "model_v1"


def load_promoted(root: Path | str, **kw) -> Triage:
    return Triage(promoted_model_dir(root), **kw)
