"""secep_ml.decoder — Phase D2. One LLM call per email: summaries, actions and adjudication of flagged heads.

    dec = Decoder(DecoderConfig.from_env())                 # backend + model from environment / config
    res = dec.enrich(email, triage_result)                  # email: raw bytes or {"subject","body","date"}
    res["status"]  -> "enriched" | "enrich_failed" | "enrich_pending"

Contract (SRS FR-DEC-001..009, Phase D handover §0 and D2):
  * Input to the LLM: subject + masked body (common/text.py recipe, quotes removed), truncated to ~3,000 tokens,
    wrapped in <email> tags as untrusted data; the student's labels and confidences; for each flagged head
    the allowed values with labelling-guide definitions and rules; today's date (the email's date); role.
  * Output: enrich.v1.1 = enrich.v1 + `adjudication` (exactly the flagged heads). Constrained by the backend's
    JSON-schema feature, then ALWAYS validated in code (jsonschema). Invalid -> one retry -> enrich_failed.
  * Post-checks in code: unknown action types dropped + logged; per-type required fields; due_date / start not
    before the email date; end after start; attendees must be e-mail addresses. Violations are counted.
  * Endpoint failures (timeouts, 5xx, 429 after backoff, daily quota) -> enrich_pending; triage is never lost.
  * Backends: Gemini (default, google-genai SDK), Groq (OpenAI-compatible, strict json_schema), Ollama, vLLM.
  * Logging is metadata only (endpoint, model, tokens, latency, status, email_id); never email text (FR-DEC-009).
  * Responses are cached on disk by (email, prompt version, model, flagged heads), so re-runs spend no quota.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Mapping, Protocol

from . import _ROOT  # noqa: F401
from common import text as T

log = logging.getLogger("secep_ml.decoder")

PKG = Path(__file__).resolve().parent
SCHEMA_DIR, PROMPT_DIR = PKG / "schemas", PKG / "prompts"
HEADS = ("type", "urgency", "sentiment")
OUT_KEY = {"type": "email_type", "urgency": "urgency", "sentiment": "sentiment"}
ALLOWED_ACTIONS = ("create_jira_issue", "add_board_card", "add_calendar_event", "none")
MAX_EMAIL_CHARS = 12_000          # ~3,000 tokens at ~4 chars/token (no tokenizer for hosted models)
EMAIL_RX = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

SYSTEM_TEMPLATE = (PROMPT_DIR / "system_enrich_v1_1.txt").read_text(encoding="utf-8")
DEFINITIONS = json.loads((PROMPT_DIR / "label_definitions.json").read_text(encoding="utf-8"))
PROMPT_VERSION = "enrich-1.1-" + hashlib.sha256(
    (SYSTEM_TEMPLATE + json.dumps(DEFINITIONS, sort_keys=True)).encode("utf-8")).hexdigest()[:8]


# =============================================================== errors / results
class BackendUnavailable(Exception):
    """Endpoint unreachable, timed out or rate-limited after retries -> enrich_pending (FR-DEC-007)."""


class QuotaExhausted(BackendUnavailable):
    """Daily quota spent: no point retrying today."""


class InvalidOutput(Exception):
    """The endpoint itself rejected the model's output as not matching the schema (counts as an invalid attempt)."""


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0.0
    attempts: int = 1                      # HTTP attempts inside the backend (429/5xx retries)


class LLMBackend(Protocol):
    name: str
    model: str
    endpoint: str

    def generate(self, system: str, user: str, schema: dict) -> LLMResult: ...


# =============================================================== config
@dataclass
class DecoderConfig:
    backend: str = "gemini"                        # gemini | groq | ollama | vllm
    model: str = ""                                # never hard-coded: env SECEP_DECODER_MODEL or argument
    endpoint: str = ""                             # base URL override; each backend has its default
    api_key_env: str = ""                          # "" = backend default (GROQ_API_KEY / GEMINI_API_KEY)
    reasoning_effort: str | None = None            # reasoning models only (e.g. gpt-oss: low | medium | high)
    strict: bool = True                            # strict JSON-schema mode where the endpoint offers it
    temperature: float | None = 0.2                # None = don't send (newer Gemini models drop sampling params)
    timeout_s: float = 60.0
    rpm: float = 10.0                              # client-side throttle, keep under the free-tier limit
    max_retries: int = 3                           # FR-DEC-007: up to 3 retries with backoff
    backoff_base_s: float = 2.0
    max_output_tokens: int = 1024
    cache_dir: str | None = None
    nullable_enum_style: str = "anyOf"             # how nullable enums are sent to the backend: anyOf | type_array

    @classmethod
    def from_env(cls, **over) -> "DecoderConfig":
        env = os.environ.get
        t = env("SECEP_DECODER_TEMPERATURE", "0.2")
        c = cls(backend=env("SECEP_DECODER_BACKEND", "gemini"), model=env("SECEP_DECODER_MODEL", ""),
                reasoning_effort=env("SECEP_DECODER_REASONING_EFFORT") or None,
                temperature=None if t.strip().lower() in ("", "none", "off") else float(t),
                endpoint=env("SECEP_DECODER_ENDPOINT", ""), rpm=float(env("SECEP_DECODER_RPM", "10")),
                cache_dir=env("SECEP_DECODER_CACHE") or None)
        for k, v in over.items():
            setattr(c, k, v)
        return c

    def key_env(self) -> str:
        return self.api_key_env or {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY"}.get(self.backend, "")


# =============================================================== throttle + retry helpers
class Throttle:
    def __init__(self, rpm: float):
        self.min_gap = 60.0 / rpm if rpm > 0 else 0.0
        self._last = 0.0

    def wait(self, sleep=time.sleep, now=time.monotonic) -> None:
        gap = self.min_gap - (now() - self._last)
        if gap > 0:
            sleep(gap)
        self._last = now()


_RETRY_DELAY_RX = re.compile(r"retry[_ ]?delay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", re.I)


def retry_delay_from(err_text: str, header: str | None, attempt: int, base: float) -> float:
    """Server hint first (Retry-After header, or RetryInfo.retryDelay in the error body), else exponential."""
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    m = _RETRY_DELAY_RX.search(err_text or "")
    if m:
        return float(m.group(1)) + 0.5
    return base * (2 ** attempt)


def _is_daily_quota(err_text: str) -> bool:
    return bool(re.search(r"PerDay|per day|daily", err_text or "", re.I))


# =============================================================== backends
class GeminiBackend:
    """Google Gemini via the official google-genai SDK (response_json_schema). Key from env, model from config."""
    name = "gemini"

    def __init__(self, cfg: DecoderConfig, client=None, sleep=time.sleep, call=None):
        if not cfg.model:
            raise ValueError("Gemini model name not set: SECEP_DECODER_MODEL or DecoderConfig(model=...)")
        self.cfg, self.model, self._sleep = cfg, cfg.model, sleep
        self.endpoint = "generativelanguage.googleapis.com"
        self.throttle = Throttle(cfg.rpm)
        self._call = call or self._sdk_call             # tests inject a fake call; no SDK needed
        if client is None and call is None:
            key = os.environ.get(cfg.key_env())
            if not key:
                raise ValueError(f"environment variable {cfg.key_env()} is not set")
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=int(cfg.timeout_s * 1000)))
        self.client = client

    def _sdk_call(self, system: str, user: str, schema: dict):
        from google.genai import types
        kw = {} if self.cfg.temperature is None else {"temperature": self.cfg.temperature}
        cfg = types.GenerateContentConfig(system_instruction=system, max_output_tokens=self.cfg.max_output_tokens,
                                          response_mime_type="application/json", response_json_schema=schema, **kw)
        return self.client.models.generate_content(model=self.model, contents=user, config=cfg)

    def generate(self, system: str, user: str, schema: dict) -> LLMResult:
        last = ""
        for attempt in range(self.cfg.max_retries + 1):
            self.throttle.wait(sleep=self._sleep)
            t0 = time.perf_counter()
            try:
                r = self._call(system, user, schema)
            except Exception as e:                                   # SDK raises google.genai.errors.APIError
                code = getattr(e, "code", None) or getattr(e, "status_code", None)
                last = f"{type(e).__name__} {code}: {str(e)[:500]}"
                body = str(getattr(e, "details", "") or "") + " " + str(e)
                if code == 429 and _is_daily_quota(body):
                    log.warning("decoder quota exhausted endpoint=%s model=%s", self.endpoint, self.model)
                    raise QuotaExhausted(last) from e
                network = code is None and re.search(r"Timeout|Connect|Network|RemoteProtocol|ReadError",
                                                     type(e).__name__)
                if code is None and not network:
                    raise                                        # a bug, not an outage: never retry silently
                retryable = code in (429, 500, 502, 503, 504) or network
                if not retryable or attempt == self.cfg.max_retries:
                    if code in (400, 401, 403, 404):
                        raise                                        # config or schema error: surface it
                    raise BackendUnavailable(last) from e
                delay = retry_delay_from(body, None, attempt, self.cfg.backoff_base_s)
                log.info("decoder retry endpoint=%s model=%s code=%s attempt=%d sleep=%.1fs",
                         self.endpoint, self.model, code, attempt + 1, delay)
                self._sleep(delay)
                continue
            um = getattr(r, "usage_metadata", None)
            return LLMResult(text=r.text or "", latency_ms=(time.perf_counter() - t0) * 1000, attempts=attempt + 1,
                             prompt_tokens=getattr(um, "prompt_token_count", None),
                             output_tokens=getattr(um, "candidates_token_count", None))
        raise BackendUnavailable(last)


class _HTTPJSONBackend:
    """Shared HTTP plumbing for Ollama and OpenAI-compatible (vLLM) endpoints; stdlib only."""
    name = "http"

    def __init__(self, cfg: DecoderConfig, sleep=time.sleep):
        if not cfg.model:
            raise ValueError("model name not set")
        self.cfg, self.model, self._sleep = cfg, cfg.model, sleep
        self.throttle = Throttle(cfg.rpm)

    def _post(self, url: str, payload: dict, headers: dict | None = None) -> tuple[dict, float, int]:
        last = ""
        hdr = {"Content-Type": "application/json", "User-Agent": "secep-ml/0.1", **(headers or {})}
        for attempt in range(self.cfg.max_retries + 1):
            self.throttle.wait(sleep=self._sleep)
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=hdr)
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.cfg.timeout_s) as resp:
                    return json.loads(resp.read().decode("utf-8")), (time.perf_counter() - t0) * 1000, attempt + 1
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode("utf-8", "replace")[:600]
                except Exception:
                    body = ""
                last = f"HTTP {e.code}: {body[:300]}"
                if e.code == 400 and re.search(r"json_validate_failed|does not match the expected schema", body, re.I):
                    raise InvalidOutput(last) from e                 # model output rejected by the endpoint
                if e.code == 429 and _is_daily_quota(body):
                    log.warning("decoder quota exhausted endpoint=%s model=%s", self.endpoint, self.model)
                    raise QuotaExhausted(last) from e
                if e.code in (400, 401, 403, 404, 413, 422):
                    raise RuntimeError(f"{self.name} rejected the request: {last}") from e   # config error
                if e.code not in (429, 500, 502, 503, 504) or attempt == self.cfg.max_retries:
                    raise BackendUnavailable(last) from e
                delay = retry_delay_from(body, e.headers.get("Retry-After"), attempt, self.cfg.backoff_base_s)
                log.info("decoder retry endpoint=%s model=%s code=%s attempt=%d sleep=%.1fs",
                         self.endpoint, self.model, e.code, attempt + 1, delay)
                self._sleep(delay)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = f"{type(e).__name__}"
                if attempt == self.cfg.max_retries:
                    raise BackendUnavailable(last) from e
                self._sleep(retry_delay_from("", None, attempt, self.cfg.backoff_base_s))
        raise BackendUnavailable(last)


class OllamaBackend(_HTTPJSONBackend):
    """Self-hosted path (SRS DC-09): Ollama /api/chat with format = JSON schema."""
    name = "ollama"

    def __init__(self, cfg: DecoderConfig, sleep=time.sleep):
        super().__init__(cfg, sleep)
        self.endpoint = (cfg.endpoint or "http://localhost:11434").rstrip("/")

    def generate(self, system: str, user: str, schema: dict) -> LLMResult:
        body = {"model": self.model, "stream": False, "format": schema,
                "options": {"seed": 42, **({} if self.cfg.temperature is None else {"temperature": self.cfg.temperature})},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        r, ms, n = self._post(f"{self.endpoint}/api/chat", body)
        return LLMResult(text=r.get("message", {}).get("content", ""), latency_ms=ms, attempts=n,
                         prompt_tokens=r.get("prompt_eval_count"), output_tokens=r.get("eval_count"))


class VLLMBackend(_HTTPJSONBackend):
    """OpenAI-compatible endpoint (vLLM on Kaggle) with json_schema response format. Optional."""
    name = "vllm"

    def __init__(self, cfg: DecoderConfig, sleep=time.sleep):
        super().__init__(cfg, sleep)
        self.endpoint = (cfg.endpoint or "http://localhost:8000").rstrip("/")

    def generate(self, system: str, user: str, schema: dict) -> LLMResult:
        body = {"model": self.model, "max_tokens": self.cfg.max_output_tokens,
                **({} if self.cfg.temperature is None else {"temperature": self.cfg.temperature}),
                "seed": 42, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "response_format": {"type": "json_schema",
                                    "json_schema": {"name": "enrich", "schema": schema, "strict": True}}}
        r, ms, n = self._post(f"{self.endpoint}/v1/chat/completions", body)
        u = r.get("usage", {})
        return LLMResult(text=r["choices"][0]["message"]["content"], latency_ms=ms, attempts=n,
                         prompt_tokens=u.get("prompt_tokens"), output_tokens=u.get("completion_tokens"))


class GroqBackend(_HTTPJSONBackend):
    """GroqCloud, OpenAI-compatible chat completions with Structured Outputs (json_schema, strict where supported).
    Key from GROQ_API_KEY; model from config (e.g. openai/gpt-oss-120b)."""
    name = "groq"

    def __init__(self, cfg: DecoderConfig, sleep=time.sleep, api_key: str | None = None):
        super().__init__(cfg, sleep)
        self.endpoint = (cfg.endpoint or "https://api.groq.com/openai/v1").rstrip("/")
        self._key = api_key or os.environ.get(cfg.key_env())
        if not self._key:
            raise ValueError(f"environment variable {cfg.key_env()} is not set")

    def generate(self, system: str, user: str, schema: dict) -> LLMResult:
        body = {"model": self.model, "max_completion_tokens": self.cfg.max_output_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "response_format": {"type": "json_schema",
                                    "json_schema": {"name": "enrich", "strict": self.cfg.strict, "schema": schema}}}
        if self.cfg.temperature is not None:
            body["temperature"] = self.cfg.temperature
        if self.cfg.reasoning_effort:
            body["reasoning_effort"] = self.cfg.reasoning_effort
        r, ms, n = self._post(f"{self.endpoint}/chat/completions", body,
                              headers={"Authorization": f"Bearer {self._key}"})
        u = r.get("usage", {}) or {}
        return LLMResult(text=r["choices"][0]["message"].get("content") or "", latency_ms=ms, attempts=n,
                         prompt_tokens=u.get("prompt_tokens"), output_tokens=u.get("completion_tokens"))


def make_backend(cfg: DecoderConfig) -> LLMBackend:
    return {"groq": GroqBackend, "gemini": GeminiBackend, "ollama": OllamaBackend,
            "vllm": VLLMBackend}[cfg.backend](cfg)


# =============================================================== schemas
def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _validator(name: str):
    import jsonschema
    s = load_schema(name)
    cls = jsonschema.validators.validator_for(s)
    return cls(s, format_checker=cls.FORMAT_CHECKER)


_V11 = None


def validator():
    global _V11
    if _V11 is None:
        _V11 = _validator("enrich.v1.1")
    return _V11


def generation_schema(flagged: list[str], nullable_enum_style: str = "anyOf") -> dict:
    """The schema sent to the backend's constrained decoder. Same shape as enrich.v1.1, but: adjudication lists
    exactly the flagged heads (all required); length/format bounds are dropped (they bloat the decoder's state
    machine and are checked in code anyway); nullable enums use a form hosted decoders accept."""
    s = load_schema("enrich.v1.1")
    s.pop("$schema", None), s.pop("$id", None), s.pop("description", None)

    def strip(o):
        if isinstance(o, dict):
            for k in ("maxLength", "format", "maxItems", "minItems"):
                o.pop(k, None)
            for v in o.values():
                strip(v)
        elif isinstance(o, list):
            for v in o:
                strip(v)
    strip(s)
    pr = s["properties"]["actions"]["items"]["properties"]
    vals = [v for v in pr["priority"]["enum"] if v is not None]
    pr["priority"] = ({"anyOf": [{"type": "string", "enum": vals}, {"type": "null"}]}
                      if nullable_enum_style == "anyOf" else {"type": ["string", "null"], "enum": vals + [None]})
    pr["type"] = {"type": "string", "enum": list(ALLOWED_ACTIONS)}
    adj = s["properties"]["adjudication"]
    if flagged:
        adj["properties"] = {h: {"type": "string", "enum": adj["properties"][h]["enum"]} for h in flagged}
        adj["required"] = list(flagged)
    else:
        del s["properties"]["adjudication"]
        s["required"].remove("adjudication")
    return s


# =============================================================== prompt
def _escape(s: str) -> str:
    """Stop the email from closing our delimiter early."""
    return re.sub(r"</?\s*email\s*>", lambda m: m.group(0).replace("email", "e-mail"), s, flags=re.I)


def prepare_email(email: bytes | str | Mapping) -> dict:
    """-> {subject, body, date, message_id} with the training-time text recipe (masked, quotes removed)."""
    if isinstance(email, (bytes, bytearray, str)):
        p = T.process(bytes(email) if isinstance(email, bytearray) else email)
        return {"subject": p["subject"], "body": p["body"], "date": p["date"], "message_id": p["message_id"]}
    if email.get("input_text"):                          # already the model string: split it, don't re-clean
        it = str(email["input_text"])
        m = re.match(r"Subject: (.*?)\n\n(.*)\Z", it, re.S)
        subj, body = (m.group(1), m.group(2)) if m else ("", it)
        return {"subject": "" if subj == "(no subject)" else subj, "body": "" if body == "(empty body)" else body,
                "date": str(email.get("date") or ""), "message_id": str(email.get("message_id") or "")}
    c = T.clean_body(str(email.get("body") or ""))
    return {"subject": T.clean_subject(str(email.get("subject") or "")), "body": c["body"],
            "date": str(email.get("date") or ""), "message_id": str(email.get("message_id") or "")}


def flagged_heads(triage: Mapping) -> list[str]:
    if "review_heads" in triage:
        return [h for h in HEADS if h in triage["review_heads"]]
    return ["type"] if triage.get("needs_review") else []         # plain triage.v1: SRS rule (type only)


_POS = {"to": "To", "cc": "Cc", "bcc": "List/Unknown", "list/unknown": "List/Unknown", "list": "List/Unknown",
        "unknown": "List/Unknown", "": "List/Unknown"}


def normalise_position(position: str | None) -> str:
    """Same mapping the student uses: Bcc and unknown -> List/Unknown (guide R9: label as if To)."""
    return _POS.get((position or "").strip().lower(), "List/Unknown")


def build_prompt(prep: dict, triage: Mapping, role: str, today: str, position: str = "List/Unknown"
                 ) -> tuple[str, str, bool]:
    flagged = flagged_heads(triage)
    system = SYSTEM_TEMPLATE.replace("{date}", today).replace("{role_category}", role or "Other")
    lines = [f"Recipient (mailbox owner): role {role or 'Other'}, position {position}.",
             "Classifier labels for this email (confidence in brackets):"]
    for h in HEADS:
        o = triage[OUT_KEY[h]]
        lines.append(f"- {h}: {o['label']} ({o['confidence']:.2f})")
    if flagged:
        lines.append("\nRe-decide these labels and put your choice in `adjudication`.")
        lines += [f"- {g}" for g in DEFINITIONS.get("general", [])]
        for h in flagged:
            d = DEFINITIONS[h]
            lines.append(f"\n{h} — choose one of: {', '.join(d['classes'])}")
            lines += [f"  {c}: {t}" for c, t in d["classes"].items()]
            lines += [f"  Rule: {r}" for r in d.get("rules", [])]
    else:
        lines.append("\nNo labels need re-deciding.")
    body = prep["body"] or "(empty body)"
    truncated = len(body) > MAX_EMAIL_CHARS
    if truncated:
        cut = body.rfind(" ", 0, MAX_EMAIL_CHARS)
        body = body[: cut if cut > MAX_EMAIL_CHARS * 0.9 else MAX_EMAIL_CHARS] + "\n[truncated]"
    lines += ["", "<email>", _escape(f"Subject: {prep['subject'] or '(no subject)'}\n\n{body}"), "</email>"]
    return system, "\n".join(lines), truncated


# =============================================================== post-checks
def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(s[:10])
        except ValueError:
            return None


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.replace(tzinfo=None) if d.tzinfo else d
    except ValueError:
        return None


PRIORITY_FROM_URGENCY = {"Critical": "Highest", "High": "High", "Medium": "Medium", "Low": "Low"}  # FR-ORC-004


def post_check(obj: dict, email_date: str, urgency: str | None = None) -> tuple[dict, list[dict]]:
    """Business rules in code (handover D2). Returns (cleaned enrich object, violations).
    Repairs where the intent is clear (Jira priority from urgency; calendar end = start + 30 min; missing attendees
    left for M6 to fill with the mailbox owner); drops only actions that cannot be executed."""
    v: list[dict] = []
    ed = _parse_date(email_date)
    kept = []
    for i, a in enumerate(obj.get("actions", [])):
        t = a.get("type")
        if t == "none":
            kept.append(a)
            continue
        a = dict(a)
        if a.get("attendees") is not None:
            good = [x for x in a["attendees"] if isinstance(x, str) and EMAIL_RX.match(x.strip())]
            if len(good) != len(a["attendees"]):
                v.append({"action": i, "rule": "attendee_invalid", "dropped": len(a["attendees"]) - len(good)})
            a["attendees"] = good or None
        dd = _parse_date(a.get("due_date"))
        if a.get("due_date") and ed and dd and dd < ed:
            v.append({"action": i, "rule": "due_before_email"})
            a["due_date"] = None
        if t == "create_jira_issue" and not a.get("priority") and urgency in PRIORITY_FROM_URGENCY:
            a["priority"] = PRIORITY_FROM_URGENCY[urgency]
            v.append({"action": i, "rule": "priority_from_urgency", "repaired": True})
        need = {"create_jira_issue": ("title", "priority"), "add_board_card": ("title",),
                "add_calendar_event": ("title", "start", "end")}[t]
        if t == "add_calendar_event":
            s_, e_ = _parse_dt(a.get("start")), _parse_dt(a.get("end"))
            if s_ and ed and s_.date() < ed:
                v.append({"action": i, "rule": "start_before_email"})
                a["start"], s_ = None, None
            if s_ and (e_ is None or e_ <= s_):
                if e_ is not None:
                    v.append({"action": i, "rule": "end_not_after_start"})
                a["end"] = (s_ + timedelta(minutes=30)).isoformat(timespec="seconds")
                v.append({"action": i, "rule": "end_defaulted_30min", "repaired": True})
            if not a.get("attendees"):
                v.append({"action": i, "rule": "attendees_missing_owner_added_by_m6", "repaired": True})
        missing = [k for k in need if not a.get(k)]
        if missing:
            v.append({"action": i, "rule": "missing_required", "type": t, "fields": missing, "dropped_action": True})
            continue
        kept.append(a)
    out = dict(obj)
    out["actions"] = kept
    return out, v


# =============================================================== cache
class Cache:
    def __init__(self, folder: str | Path | None):
        self.folder = Path(folder) if folder else None

    def _path(self, key: str) -> Path:
        return self.folder / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict | None:
        if not self.folder:
            return None
        p = self._path(key)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def put(self, key: str, value: dict) -> None:
        if not self.folder:
            return
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(value), encoding="utf-8")
        tmp.replace(p)


# =============================================================== decoder
@dataclass
class EnrichMeta:
    backend: str
    model: str
    endpoint: str
    prompt_version: str
    requests: int = 0                  # LLM calls made (0 on cache hit; 1; 2 with the validation retry)
    http_attempts: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cache_hit: bool = False
    email_truncated: bool = False
    orig: dict | None = None           # on a cache hit: requests/tokens/latency of the call that produced it
    errors: list = field(default_factory=list)


class Decoder:
    def __init__(self, cfg: DecoderConfig | None = None, backend: LLMBackend | None = None):
        self.cfg = cfg or DecoderConfig.from_env()
        self.backend = backend or make_backend(self.cfg)
        self.cache = Cache(self.cfg.cache_dir)

    def replace_api_key(self, key: str, backend: LLMBackend | None = None) -> str:
        """Swap to another account's API key mid-run (same backend, same model, same prompt).
        The key lives only in this process; returns a short fingerprint for logs (never the key)."""
        os.environ[self.cfg.key_env()] = key
        self.backend = backend or make_backend(self.cfg)
        return hashlib.sha256(key.encode()).hexdigest()[:8]

    def cache_key(self, email_id: str, prep: dict, triage: Mapping, role: str, today: str) -> str:
        k = json.dumps([email_id, hashlib.sha256((prep["subject"] + "\n" + prep["body"]).encode()).hexdigest(),
                        PROMPT_VERSION, self.backend.name, self.backend.model, flagged_heads(triage),
                        [triage[OUT_KEY[h]]["label"] for h in HEADS], role, today])
        return hashlib.sha256(k.encode()).hexdigest()

    def enrich(self, email: bytes | str | Mapping, triage: Mapping, role: str | None = None,
               position: str | None = None, today: str | None = None) -> dict:
        prep = prepare_email(email)
        email_id = str(triage.get("email_id", ""))
        role = role or str(triage.get("recipient_role") or "Other")
        today = (today or prep["date"] or date.today().isoformat())[:10]
        flagged = flagged_heads(triage)
        position = normalise_position(position)
        system, user, truncated = build_prompt(prep, triage, role, today, position)
        schema = generation_schema(flagged, self.cfg.nullable_enum_style)
        meta = EnrichMeta(self.backend.name, self.backend.model, getattr(self.backend, "endpoint", ""),
                          PROMPT_VERSION, email_truncated=truncated)
        key = self.cache_key(email_id, prep, triage, f"{role}|{position}", today)

        cached = self.cache.get(key)
        if cached is not None:
            meta.cache_hit = True
            meta.orig = cached.get("orig")
            return self._finish("enriched", cached["enrich"], cached["violations"], flagged, triage, meta,
                                cached.get("dropped_types", []))

        for attempt in (1, 2):                                       # FR-DEC-002: one retry on invalid output
            try:
                r = self.backend.generate(system, user, schema)
            except BackendUnavailable as e:
                meta.errors.append(type(e).__name__)
                self._log(email_id, "enrich_pending", meta)
                return self._finish("enrich_pending", None, [], flagged, triage, meta)
            except InvalidOutput:
                meta.requests += 1
                meta.errors.append(f"invalid#{attempt}: endpoint schema check failed")
                continue
            meta.requests += 1
            meta.http_attempts += r.attempts
            meta.prompt_tokens += r.prompt_tokens or 0
            meta.output_tokens += r.output_tokens or 0
            meta.latency_ms += r.latency_ms
            ok, obj, err, dropped_types, pre = self._validate(r.text, flagged)
            if ok:
                urg = obj["adjudication"].get("urgency") or triage[OUT_KEY["urgency"]]["label"]
                obj, violations = post_check(obj, prep["date"] or today, urgency=urg)
                violations = pre + violations
                self.cache.put(key, {"enrich": obj, "violations": violations, "dropped_types": dropped_types,
                                     "orig": {"requests": meta.requests, "http_attempts": meta.http_attempts,
                                              "prompt_tokens": meta.prompt_tokens,
                                              "output_tokens": meta.output_tokens,
                                              "latency_ms": meta.latency_ms, "errors": list(meta.errors)}})
                self._log(email_id, "enriched", meta)
                return self._finish("enriched", obj, violations, flagged, triage, meta, dropped_types)
            meta.errors.append(f"invalid#{attempt}: {err}")
        self._log(email_id, "enrich_failed", meta)
        return self._finish("enrich_failed", None, [], flagged, triage, meta)

    @staticmethod
    def _validate(text: str, flagged: list[str]) -> tuple[bool, dict | None, str, list[str], list[dict]]:
        try:
            obj = json.loads(text)
        except (json.JSONDecodeError, TypeError) as e:
            return False, None, f"not JSON ({type(e).__name__})", [], []
        if not isinstance(obj, dict):
            return False, None, "not an object", [], []
        obj.setdefault("adjudication", {})
        dropped, pre = [], []
        if isinstance(obj.get("actions"), list):                       # FR-DEC-003: drop + log unknown types
            keep = []
            for a in obj["actions"]:
                if isinstance(a, dict) and a.get("type") not in ALLOWED_ACTIONS:
                    dropped.append(str(a.get("type"))[:40])
                else:
                    keep.append(a)
            obj["actions"] = keep
            for i, a in enumerate(keep):                               # bad attendees: clean, don't fail the email
                if isinstance(a, dict) and isinstance(a.get("attendees"), list):
                    good = [x for x in a["attendees"] if isinstance(x, str) and EMAIL_RX.match(x.strip())]
                    if len(good) != len(a["attendees"]):
                        pre.append({"action": i, "rule": "attendee_invalid",
                                    "dropped": len(a["attendees"]) - len(good)})
                        a["attendees"] = good or None
        errs = sorted(validator().iter_errors(obj), key=lambda e: list(e.path))
        if errs:
            e = errs[0]
            return False, None, f"{'/'.join(map(str, e.path)) or '<root>'}: {e.validator}", dropped, pre
        if set(obj["adjudication"]) != set(flagged):
            return False, None, f"adjudication heads {sorted(obj['adjudication'])} != flagged {flagged}", dropped, pre
        if dropped:
            log.warning("decoder dropped unknown action types: %s", dropped)
        return True, obj, "", dropped, pre

    def _finish(self, status, obj, violations, flagged, triage, meta, dropped_types=()) -> dict:
        final, sources = {}, {}
        for h in HEADS:
            adj = (obj or {}).get("adjudication", {}).get(h)
            if h in flagged and adj:
                final[h], sources[h] = adj, "llm"
            else:
                final[h], sources[h] = triage[OUT_KEY[h]]["label"], triage[OUT_KEY[h]].get("source", "encoder")
        enrich_v1 = None if obj is None else {k: obj[k] for k in ("summary_one_line", "summary_short", "actions")}
        return {"schema": "enrich_result.v1.1", "email_id": triage.get("email_id"), "status": status,
                "enrich": enrich_v1, "adjudication": (obj or {}).get("adjudication", {}), "flagged_heads": flagged,
                "final_labels": final, "sources": sources, "violations": list(violations),
                "dropped_action_types": list(dropped_types), "meta": asdict(meta)}

    @staticmethod
    def _log(email_id: str, status: str, m: EnrichMeta) -> None:          # FR-DEC-009: metadata only
        log.info("decoder email_id=%s status=%s backend=%s endpoint=%s model=%s prompt=%s requests=%d "
                 "attempts=%d tokens_in=%d tokens_out=%d latency_ms=%.0f cache=%s",
                 email_id, status, m.backend, m.endpoint, m.model, m.prompt_version, m.requests, m.http_attempts,
                 m.prompt_tokens, m.output_tokens, m.latency_ms, m.cache_hit)
