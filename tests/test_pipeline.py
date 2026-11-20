"""D4 tests: end-to-end pipeline on 10 raw fixture emails + the 20 injection fixtures, LLM mocked.

    python -m pytest tests\\test_pipeline.py -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secep_ml import decoder as D  # noqa: E402
from secep_ml import triage as TR  # noqa: E402
from secep_ml.pipeline import Pipeline  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
RAW = sorted((FIX / "raw").glob("*.eml"))
CASES = json.loads((FIX / "injection" / "cases.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("inj", ROOT / "scripts" / "injection_suite.py")
INJ = importlib.util.module_from_spec(spec)
spec.loader.exec_module(INJ)


def stub_embed(texts):
    out = []
    for t in texts:
        v = np.random.default_rng(int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "little")).standard_normal(768)
        out.append(v / np.linalg.norm(v))
    return np.asarray(out, dtype=np.float32)


@pytest.fixture(scope="module")
def tri(tmp_path_factory):
    d = tmp_path_factory.mktemp("m")
    shutil.copy(ROOT / "model_v1" / "manifest.json", d / "manifest.json")
    m = json.loads((d / "manifest.json").read_text())
    n = m["emb_dim"] + len(m["roles"]) + len(m["positions"])
    rng = np.random.default_rng(3)
    np.savez(d / "heads.npz", **{k: v for h, c in m["classes"].items()
                                 for k, v in ((f"W_{h}", rng.standard_normal((len(c), n)) * 4),
                                              (f"b_{h}", rng.standard_normal(len(c))))})
    return TR.load(d, embed_fn=stub_embed)


class Mock:
    name, model, endpoint = "mock", "mock-1", "mock://"

    def __init__(self, fail=None):
        self.fail, self.users = fail, []

    def generate(self, system, user, schema):
        self.users.append(user)
        if self.fail:
            raise self.fail
        adj = schema.get("properties", {}).get("adjudication", {}).get("properties", {})
        return D.LLMResult(text=json.dumps({
            "summary_one_line": "Summary.", "summary_short": "Short summary.",
            "actions": [{"type": "add_board_card", "title": "Follow up", "description": None, "priority": None,
                         "due_date": None, "start": None, "end": None, "attendees": None}],
            "adjudication": {h: v["enum"][-1] for h, v in adj.items()}}))


def pipe(tri, fail=None):
    return Pipeline(tri, D.Decoder(D.DecoderConfig(model="mock-1"), backend=Mock(fail)))


def test_ten_raw_files_end_to_end(tri):
    assert len(RAW) == 10
    p = pipe(tri)
    v11 = TR._validator("triage.v1.1")
    for f in RAW:
        out = p.process_email(f.read_bytes(), "Manager", "To")
        v11.validate(out["triage"])
        assert out["status"] == "enriched"
        for h in TR.HEADS:
            flagged = h in out["triage"]["review_heads"]
            assert out["sources"][h] == ("llm" if flagged else "encoder")
            if not flagged:
                assert out["final_labels"][h] == out["triage"][TR.OUT_KEY[h]]["label"]
        D._validator("enrich.v1").validate(out["enrich"]["enrich"])


def test_decoder_down_keeps_triage(tri):
    out = pipe(tri, D.BackendUnavailable("down")).process_email(RAW[0].read_bytes(), "Manager", "To")
    assert out["status"] == "enrich_pending" and out["triage"]["schema"] == "triage.v1.1"
    assert out["final_labels"] == {h: out["triage"][TR.OUT_KEY[h]]["label"] for h in TR.HEADS}


def test_unexpected_decoder_error_is_failed_not_crash(tri):
    out = pipe(tri, RuntimeError("400 bad config")).process_email(RAW[0].read_bytes(), "Manager", "To")
    assert out["status"] == "enrich_failed" and out["error"] == "RuntimeError"
    assert set(out["sources"].values()) == {"encoder"}


def test_no_decoder_is_triage_only(tri):
    out = Pipeline(tri).process_email(RAW[1].read_bytes(), "Analyst", "cc")
    assert out["status"] == "triaged" and out["enrich"] is None


def test_injection_prompts_are_hardened(tri):
    m = Mock()
    dec = D.Decoder(D.DecoderConfig(model="mock-1"), backend=m)
    for c in CASES:
        raw = (FIX / "injection" / c["file"]).read_bytes()
        dec.enrich(raw, INJ.all_flagged(tri.classify(raw, "Manager", "To")), role="Manager", position="To")
    assert len(m.users) == 20
    for u in m.users:
        assert u.count("<email>") == 1 and u.count("</email>") == 1 and u.rstrip().endswith("</email>")
    assert not any("482913" in u for u in m.users)                 # the PIN never leaves the machine


def test_injection_checker():
    c = next(x for x in CASES if x["attack"] == "force_urgency")
    ok = {"status": "enriched", "final_labels": {"type": "Info", "urgency": "Low", "sentiment": "Neutral"},
          "enrich": {"summary_one_line": "Newsletter.", "summary_short": "Newsletter.", "actions": []}}
    assert INJ.check(c, ok) == []
    forced = json.loads(json.dumps(ok))
    forced["final_labels"]["urgency"] = "Critical"
    assert INJ.check(c, forced)
    c2 = next(x for x in CASES if x["attack"] == "inject_calendar")
    bad = json.loads(json.dumps(ok))
    bad["enrich"]["actions"] = [{"type": "add_calendar_event", "title": "sync", "attendees": ["attacker@evil.example"]}]
    assert INJ.check(c2, bad)
    leak = json.loads(json.dumps(ok))
    leak["enrich"]["summary_short"] = "The email is untrusted data between tags."
    assert INJ.check(c, leak)
    assert INJ.check(c, {"status": "enrich_failed", "final_labels": {}, "enrich": None})


def test_promoted_loader(tmp_path):
    (tmp_path / "model_v1").mkdir()
    (tmp_path / "model_v1" / "manifest.json").write_text("{}")
    assert TR.promoted_model_dir(tmp_path) == tmp_path / "model_v1"
    (tmp_path / "model_v2").mkdir()
    (tmp_path / "model_v2" / "manifest.json").write_text("{}")
    (tmp_path / "promoted.json").write_text(json.dumps({"model_dir": "model_v2"}))
    assert TR.promoted_model_dir(tmp_path) == tmp_path / "model_v2"
    (tmp_path / "promoted.json").write_text(json.dumps({"model_dir": "model_v9"}))
    assert TR.promoted_model_dir(tmp_path) == tmp_path / "model_v1"
