"""
common/text.py — THE recipe for turning a raw email into the text a model reads.

Every part of SECEP that shows an email to a model imports this file:
the gold-set rebuild, the training pool, the teacher (LLM) labelling,
encoder training and evaluation, and later the live triage service.
If the recipe changes, bump TEXT_VERSION — models trained on one version
must be served with the same version.

Steps, in order:
  1. parse_email()   raw file/bytes  -> headers + plain-text body
                     (multipart: prefers text/plain, falls back to HTML→text)
  2. split_quoted()  body -> (new text, quoted older messages)
                     handles Outlook/Enron "-----Original Message-----",
                     "From: … Sent: …" blocks, Lotus Notes headers,
                     Gmail "On <date>, X wrote:", and "> " lines.
                     Forwarded content is KEPT (it is usually the point of the mail).
  3. mask_secrets()  replaces passwords, PINs, one-time codes, card numbers,
                     API keys and long tokens with [MASKED:<kind>]
  4. normalise()     line endings, invisible characters, spacing
  5. format_input()  "Subject: …\\n\\n<body>"  ← the exact string models see

Only the Python standard library is used, so the live service can import it as-is.
"""
from __future__ import annotations

import html
import re
import unicodedata
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser

TEXT_VERSION = "1.0"
MAX_BODY_CHARS = 20000          # safety cap; long emails are windowed later, not here

# ------------------------------------------------------------------ 1. parsing
_bparser = BytesParser(policy=policy.default)


class _HTMLText(HTMLParser):
    """Minimal HTML → text: keeps visible text, turns block tags into line breaks."""
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "blockquote"}
    SKIP = {"script", "style", "head", "title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.out.append(data)


def html_to_text(s: str) -> str:
    p = _HTMLText()
    try:
        p.feed(s)
        p.close()
        return html.unescape("".join(p.out))
    except Exception:
        return re.sub(r"<[^>]+>", " ", s)


def _part_text(part) -> str:
    try:
        return part.get_content()
    except Exception:                                  # unknown/broken charset
        raw = part.get_payload(decode=True) or b""
        for enc in (part.get_content_charset() or "utf-8", "utf-8", "latin-1"):
            try:
                return raw.decode(enc)
            except Exception:
                continue
        return raw.decode("latin-1", errors="replace")


def parse_email(raw: bytes | str) -> dict:
    """Raw RFC-822 email (an Enron file, or a Gmail 'raw' message) -> fields."""
    if isinstance(raw, str):
        raw = raw.encode("latin-1", errors="replace")
    msg = _bparser.parsebytes(raw)

    body = ""
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
    except Exception:
        part = None
    if part is not None:
        body = _part_text(part)
        if part.get_content_type() == "text/html":
            body = html_to_text(body)
    elif not msg.is_multipart():
        body = _part_text(msg)

    def h(name):
        try:
            return str(msg.get(name, "") or "").strip()
        except Exception:
            return ""

    try:
        date = parsedate_to_datetime(h("Date"))
        date_iso = date.strftime("%Y-%m-%d %H:%M")
    except Exception:
        date_iso = ""
    return {
        "message_id": h("Message-ID"),
        "subject": h("Subject"),
        "from": h("X-From") or h("From"),
        "from_addr": next((a.lower() for _, a in getaddresses([h("From")]) if "@" in a), ""),
        "to": [a.lower() for _, a in getaddresses([h("To")]) if "@" in a],
        "cc": [a.lower() for _, a in getaddresses([h("Cc")]) if "@" in a],
        "date": date_iso,
        "body_raw": body or "",
    }


# ------------------------------------------------------------------ 2. quoted replies
_QUOTE_START = re.compile(
    r"(?:^|\n)[ \t]*(?:"
    r"-{2,}\s*Original Message\s*-{2,}"                       # Outlook / Enron
    r"|-{2,}\s*Original Appointment\s*-{2,}"
    r"|_{10,}\s*\n\s*From:"                                    # Outlook web separator
    r"|From:[^\n]{1,200}\n[ \t]*Sent:[^\n]*\n"                # Outlook header block
    r"|On [^\n]{5,200}(?:\n[^\n]{0,200})?wrote:[ \t]*\n"      # Gmail / Apple Mail
    r"|[^\n]{1,80}\n[ \t]*\d{1,2}/\d{1,2}/\d{2,4} \d{1,2}:\d{2}(?::\d{2})? ?[AP]M\s*\n[ \t]*To:"  # Lotus Notes
    r")",
    re.I,
)
_FORWARD = re.compile(r"-{2,}\s*Forwarded by|-{2,}\s*Forwarded message\s*-{2,}|Begin forwarded message:", re.I)


def split_quoted(body: str) -> tuple[str, str]:
    """Return (new_text, quoted_text). A quote marker that sits INSIDE a forwarded
    block is left alone, because the forwarded mail is the content."""
    m = _QUOTE_START.search(body)
    if m:
        fwd = _FORWARD.search(body)
        if fwd and fwd.start() < m.start():
            m = None                                   # the "reply" is part of a forward
    new, quoted = (body[: m.start()], body[m.start():]) if m else (body, "")
    keep, qlines = [], []
    for ln in new.split("\n"):
        (qlines if ln.lstrip().startswith(">") else keep).append(ln)
    quoted = "\n".join(qlines + ([quoted] if quoted else []))
    return "\n".join(keep), quoted.strip()


# ------------------------------------------------------------------ 3. secrets
# (pattern, kind). Applied in order. Values only — the label word stays, so the
# model still sees "password: [MASKED:password]" and can tell it is a Credentials mail.
_SECRETS = [
    (re.compile(r"(?i)\b(pass(?:word|wd|code)?|pwd|pw)\b(\s*(?:is|=|:|-)\s*)(\S{3,64})"), "password"),
    (re.compile(r"(?i)\b(pin(?:\s*(?:code|number|no\.?))?)\b(\s*(?:is|=|:|-)\s*)(\d{3,8})\b"), "pin"),
    (re.compile(r"(?i)\b((?:one[- ]time|verification|security|access|otp|auth(?:entication)?)\s*(?:code|pin)?)\b"
                r"(\s*(?:is|=|:|-)\s*)([A-Z0-9]{4,10})\b"), "code"),
    (re.compile(r"(?i)\b(api[_ -]?key|secret|token|access[_ -]?key)\b(\s*(?:is|=|:|-)\s*)(\S{8,})"), "key"),
]
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_LONG_TOKEN = re.compile(r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{32,}\b")


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total, alt = total + d, not alt
    return total % 10 == 0


def mask_secrets(text: str) -> tuple[str, list[str]]:
    """Return (masked_text, kinds_found)."""
    found = []
    for rx, kind in _SECRETS:
        def rep(m, kind=kind):
            found.append(kind)
            return f"{m.group(1)}{m.group(2)}[MASKED:{kind}]"
        text = rx.sub(rep, text)

    def card(m):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits):
            found.append("card")
            return "[MASKED:card]"
        return m.group(0)
    text = _CARD.sub(card, text)

    def tok(kind):
        def f(m):
            found.append(kind)
            return f"[MASKED:{kind}]"
        return f
    text = _AWS.sub(tok("key"), text)
    text = _LONG_TOKEN.sub(tok("token"), text)
    return text, found


# ------------------------------------------------------------------ 4. normalise
_INVISIBLE = dict.fromkeys(c for c in range(0x20) if c not in (9, 10))   # control chars except \t \n
_INVISIBLE.update({0x200B: None, 0x200C: None, 0x200D: None, 0xFEFF: None, 0x00AD: None})


def normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFKC", text).translate(_INVISIBLE)
    text = text.replace("\t", " ").replace(" ", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ------------------------------------------------------------------ 5. final string
def clean_body(body_raw: str) -> dict:
    """body text -> {'body', 'quoted', 'masked_kinds', 'truncated'}"""
    new, quoted = split_quoted(body_raw.replace("\r\n", "\n"))
    new, kinds = mask_secrets(new)
    quoted, qkinds = mask_secrets(quoted)
    new, quoted = normalise(new), normalise(quoted)
    truncated = len(new) > MAX_BODY_CHARS
    return {"body": new[:MAX_BODY_CHARS], "quoted": quoted[:MAX_BODY_CHARS],
            "masked_kinds": sorted(set(kinds + qkinds)), "truncated": truncated}


def clean_subject(subject: str) -> str:
    s, _ = mask_secrets(subject or "")
    return normalise(s.replace("\n", " "))


def format_input(subject: str, body: str) -> str:
    """The exact text an encoder or LLM is given for one email."""
    return f"Subject: {subject or '(no subject)'}\n\n{body or '(empty body)'}"


def process(raw: bytes | str) -> dict:
    """Whole recipe in one call: raw email -> everything downstream needs."""
    e = parse_email(raw)
    c = clean_body(e["body_raw"])
    subject = clean_subject(e["subject"])
    return {**{k: v for k, v in e.items() if k != "body_raw"},
            "subject": subject, "body": c["body"], "quoted": c["quoted"],
            "masked_kinds": c["masked_kinds"], "truncated": c["truncated"],
            "input_text": format_input(subject, c["body"]), "text_version": TEXT_VERSION}
