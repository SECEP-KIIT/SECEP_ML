"""D1 tests for secep_ml.triage. Runs offline in seconds: the encoder is replaced by a deterministic stub,
and the heads are random arrays saved next to a copy of the real model_v1 manifest. What is tested is the
wrapping (text recipe, features, per-head modes, review flags, schema, determinism), not model accuracy.

    python -m pytest tests\\test_triage.py -q
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402

from common import student as S  # noqa: E402
from secep_ml import triage as TR  # noqa: E402

RAW = b"""Message-ID: <123.456.JavaMail.evans@thyme>
Date: Mon, 11 Jun 2001 06:41:00 -0700 (PDT)
From: jeff.skilling@enron.com
To: louise.kitchen@enron.com
Subject: Re: Q3 numbers - need by Friday
Mime-Version: 1.0
Content-Type: text/plain; charset=us-ascii
X-From: Skilling, Jeff

Louise,

Please send me the revised Q3 numbers by Friday noon. The login for the new
system is jskill and the password: Hunter2xyz

Thanks
Jeff

 -----Original Message-----
From: Kitchen, Louise
Sent: Sunday, June 10, 2001 5:00 PM
To: Skilling, Jeff
Subject: Q3 numbers

Do you still want the numbers this week?
"""


def stub_embed(texts):
    """Deterministic, text-dependent, L2-normalised 768-d vectors (stands in for mpnet)."""
    out = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:8], "little")
        v = np.random.default_rng(seed).standard_normal(768)
        out.append(v / np.linalg.norm(v))
    return np.asarray(out, dtype=np.float32)


@pytest.fixture(scope="module")
def model_dir(tmp_path_factory):
    src = ROOT / "model_v1" / "manifest.json"
    d = tmp_path_factory.mktemp("model_stub")
    shutil.copy(src, d / "manifest.json")
    m = json.loads(src.read_text(encoding="utf-8"))
    n_feat = m["emb_dim"] + len(m["roles"]) + len(m["positions"])
    rng = np.random.default_rng(42)
    arrays = {}
    for h, classes in m["classes"].items():          # scale 4 so confidences straddle 0.60
        arrays[f"W_{h}"] = rng.standard_normal((len(classes), n_feat)) * 4.0
        arrays[f"b_{h}"] = rng.standard_normal(len(classes))
    np.savez(d / "heads.npz", **arrays)
    return d


@pytest.fixture(scope="module")
def tri(model_dir):
    return TR.load(model_dir, embed_fn=stub_embed)


FIXED_TS = "2026-11-20T00:00:00.000Z"


def test_output_is_valid_v11_and_v1(tri):
    r = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    TR._validator("triage.v1.1").validate(r)
    TR._validator("triage.v1").validate(TR.to_triage_v1(r))
    assert r["schema"] == "triage.v1.1" and r["model_version"] == "model_v1"
    assert len(r["manifest_sha256"]) == 64


def test_schema_enums_match_manifest(tri):
    s = TR.load_schema("triage.v1.1")
    for h in TR.HEADS:
        assert s["properties"][TR.OUT_KEY[h]]["properties"]["label"]["enum"] == tri.manifest["classes"][h]


def test_heads_consistent(tri):
    r = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    review = []
    for h in TR.HEADS:
        o = r[TR.OUT_KEY[h]]
        assert abs(sum(o["probs"].values()) - 1) < 1e-9
        assert o["label"] == max(o["probs"], key=o["probs"].get)
        assert o["confidence"] == o["probs"][o["label"]]
        assert o["needs_review"] == (o["confidence"] < 0.60)
        if o["needs_review"]:
            review.append(h)
    assert r["review_heads"] == review and r["needs_review"] == bool(review)
    s = r["sentiment"]
    assert -1 <= s["score"] <= 1
    assert s["score"] == round(s["probs"]["Positive"] - s["probs"]["Negative"] - s["probs"]["Frustrated"], 4)


def test_review_flags_actually_vary(tri):
    """Guard against a stub that never crosses 0.60 (the test above would then prove nothing)."""
    flags = set()
    for i in range(40):
        r = tri.classify({"subject": f"msg {i}", "body": f"body number {i}"}, "Manager", "Cc",
                         processed_at=FIXED_TS)
        flags.update(r[TR.OUT_KEY[h]]["needs_review"] for h in TR.HEADS)
    assert flags == {True, False}


def test_determinism_same_and_new_instance(tri, model_dir):
    a = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    b = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    c = TR.load(model_dir, embed_fn=stub_embed).classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    assert a == b == c
    d = tri.classify(RAW, "Executive", "To")                    # unpinned timestamp: only that differs
    assert {k: v for k, v in d.items() if k != "processed_at"} == {k: v for k, v in a.items() if k != "processed_at"}


def test_text_recipe_applied(tri):
    prep = TR.Triage.prepare(RAW)
    assert prep["input_text"].startswith("Subject: Re: Q3 numbers - need by Friday\n\n")
    assert "Hunter2xyz" not in prep["input_text"] and "[MASKED:password]" in prep["input_text"]
    assert "Do you still want" not in prep["input_text"]          # quoted reply removed
    assert prep["date"] == "2001-06-11 06:41"


def test_fields_path_matches_raw_path(tri):
    from common import text as T
    e = T.parse_email(RAW)
    a = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    b = tri.classify({"subject": e["subject"], "body": e["body_raw"]}, "Executive", "To",
                     processed_at=FIXED_TS, email_id=a["email_id"])
    assert a["input_sha256"] == b["input_sha256"]
    for h in TR.HEADS:
        assert a[TR.OUT_KEY[h]] == b[TR.OUT_KEY[h]]


def test_input_text_used_verbatim(tri):
    p = TR.Triage.prepare({"input_text": "Subject: x\n\nhello"})
    assert p["input_text"] == "Subject: x\n\nhello"


@pytest.mark.parametrize("role,pos,unseen", [
    ("Engineer", "To", {"role": "Engineer"}),
    ("Manager", "Bcc", {"position": "Bcc"}),
    ("Manager", "bcc", {"position": "Bcc"}),
    ("Intern", "to", {"role": "Intern"}),
    ("Client-facing", "cc", None),
    ("manager", "TO", None),
])
def test_role_position_aliases_and_fallbacks(tri, model_dir, role, pos, unseen):
    r = tri.classify(RAW, role, pos, processed_at=FIXED_TS)
    assert r.get("unseen") == unseen
    fb = tri.classify(RAW, TR.normalise_role(role) if TR.normalise_role(role) in tri.manifest["roles"] else "Other",
                      TR.normalise_position(pos) if TR.normalise_position(pos) in tri.manifest["positions"]
                      else "List/Unknown", processed_at=FIXED_TS)
    for h in TR.HEADS:
        assert r[TR.OUT_KEY[h]]["probs"] == fb[TR.OUT_KEY[h]]["probs"]


def test_role_changes_prediction(tri):
    """Role/position are real features: changing them must change probabilities."""
    a = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    b = tri.classify(RAW, "Analyst", "Cc", processed_at=FIXED_TS)
    assert a["urgency"]["probs"] != b["urgency"]["probs"]


def test_batch_path_equals_student_code(tri):
    """probs_from_embeddings must be exactly common/student.predict_proba in the manifest's mode."""
    rng = np.random.default_rng(7)
    E = rng.standard_normal((25, 768)).astype(np.float32)
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    roles = list(rng.choice(tri.manifest["roles"], 25))
    pos = list(rng.choice(tri.manifest["positions"], 25))
    P, _ = tri.probs_from_embeddings(E, roles, pos)
    X, _ = S.build_features(E, roles, pos, tri.manifest["roles"], tri.manifest["positions"])
    Q = S.predict_proba(tri.manifest, tri.heads, X, "mixed")
    for h in TR.HEADS:
        assert np.array_equal(P[h], Q[h])


def test_single_equals_batch(tri):
    text = TR.Triage.prepare(RAW)["input_text"]
    r = tri.classify({"input_text": text}, "Executive", "To", processed_at=FIXED_TS)
    P, _ = tri.probs_from_embeddings(stub_embed([text]), ["Executive"], ["To"])
    for h in TR.HEADS:
        assert np.allclose(list(r[TR.OUT_KEY[h]]["probs"].values()), P[h][0], atol=0, rtol=0)


def test_uses_manifest_head_modes(tri):
    assert tri.head_modes == {"type": "prior", "urgency": "prior", "sentiment": "balanced"}


def test_validation_catches_bad_output(tri):
    r = tri.classify(RAW, "Executive", "To", processed_at=FIXED_TS)
    bad = copy.deepcopy(r)
    bad["urgency"]["label"] = "Urgent"
    with pytest.raises(jsonschema.ValidationError):
        TR._validator("triage.v1.1").validate(bad)


def test_email_id_passthrough_and_stable_default(tri):
    uid = "5f0c2a8e-6a1b-4d0e-9a51-1c2f6e7b9d10"
    assert tri.classify(RAW, "Executive", "To", email_id=uid)["email_id"] == uid
    a = tri.classify(RAW, "Executive", "To")["email_id"]
    assert a == tri.classify(RAW, "Executive", "To")["email_id"]
    assert a != tri.classify(RAW, "Executive", "Cc")["email_id"]


def test_bad_input_type_fails_loudly(tri):
    with pytest.raises(TypeError):
        tri.classify(12345, "Executive", "To")
