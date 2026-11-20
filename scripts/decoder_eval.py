#!/usr/bin/env python3
"""
decoder_eval.py — Phase D3 (development part). The real hybrid on gold-dev / gold-calib:
student (secep_ml.triage) -> decoder (secep_ml.decoder, configured backend) on every email -> final labels.

Gold-test is refused here; it gets its own one-time script after the prompt freeze (decision log, D3).

Run from ML_Training (GEMINI_API_KEY + SECEP_DECODER_MODEL set):
    python scripts\\decoder_eval.py --split devcalib --limit 20     # cheap first look (20 requests)
    python scripts\\decoder_eval.py --split devcalib                # all 276 (about 30 min at 10 rpm)
Re-running is free for emails already done (response cache) and resumes after a quota stop.
On a daily-quota stop (or 3 endpoint errors in a row) it PAUSES and asks for another account's key
(hidden input); the run then continues with the same model and prompt. Key switches are logged by
fingerprint in config.json; keys are never written anywhere.

Stage 1 (label-free): reads only email_uid, input_text, date, role, position -> classify -> enrich ->
    enrich_results.jsonl, predictions_student.csv, predictions_hybrid.csv (I4).
Stage 2 (labels, only when no email is left pending): score.py on student and hybrid, plus decoder metrics:
    Critical/High recall, flagged urgency moved to Critical, action correctness vs gold type, violations,
    schema validity (first attempt / after retry / failed), latency, tokens. -> metrics.json, report.md
Writes runs\\<date>-d3-dev-<split>\\.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import os
import json
import logging
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from secep_ml import decoder as D  # noqa: E402
from secep_ml import triage as TR  # noqa: E402

GOLD = ROOT / "Data" / "gold_final"
SPLITS = {"dev": ["gold_dev.csv"], "calib": ["gold_calib.csv"], "devcalib": ["gold_dev.csv", "gold_calib.csv"],
          "test": []}                                   # test: the file verified by runs/live_eval.lock.json
TEXT_COLS = ["email_uid", "input_text", "date", "recipient_role", "recipient_position"]
LABEL_COLS = ["email_uid", "type", "urgency", "sentiment"]


def quick_macro_f1(gold_df: pd.DataFrame, res: list, classes: dict) -> dict:
    """Macro-F1 over gold classes present (strict column if there is one) — a quick check only; score.py is the
    reference."""
    from sklearn.metrics import f1_score
    out = {}
    for h in ("type", "urgency", "sentiment"):
        g = gold_df[h]                                   # primary label (dev/calib: single-labelled = strict)
        rows = [x for x in res if g.get(x["email_uid"], "") in classes[h]]
        y = [g[x["email_uid"]] for x in rows]
        present = sorted(set(y))
        st = [x["triage"]["email_type" if h == "type" else h]["label"] for x in rows]
        hy = [x["enrich_result"]["final_labels"][h] for x in rows]
        out[h] = {"n": len(rows),
                  "student": float(f1_score(y, st, labels=present, average="macro", zero_division=0)) if rows else None,
                  "hybrid": float(f1_score(y, hy, labels=present, average="macro", zero_division=0)) if rows else None}
    return out
EXPECTED = {"Task": {"create_jira_issue", "add_board_card"}, "Meeting": {"add_calendar_event"},
            "Info": set(), "Credentials": set(), "Approval": {"add_board_card"}}
NEED_ONE = {"Task", "Meeting"}                    # these types should get at least one expected action


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_cols(path: Path, cols: list[str] | None = None) -> pd.DataFrame:
    """Read only the named columns (label-free reads never load label columns)."""
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=cols).astype(str)
    return pd.read_csv(path, dtype=str, keep_default_na=False, usecols=cols)


def action_ok(gold_type: str, types: set[str]) -> bool:
    real = types - {"none"}
    allowed = EXPECTED[gold_type]
    if not real <= allowed:
        return False
    return bool(real & allowed) if gold_type in NEED_ONE else True


def i4_row(uid: str, probs: dict, labels: dict, classes: dict) -> dict:
    row = {"email_uid": uid}
    for h, cl in classes.items():
        row[f"pred_{h}"] = labels[h]
        for c in cl:
            row[f"prob_{h}_{c}"] = probs[h][c]
    return row


class _MockLLM:  # tests only
    name, model, endpoint = "mock", "mock-1", "mock://"

    def generate(self, system, user, schema):
        adj = schema.get("properties", {}).get("adjudication", {}).get("properties", {})
        act = {"type": "add_board_card", "title": "Do it", "description": None, "priority": None,
               "due_date": None, "start": None, "end": None, "attendees": None}
        obj = {"summary_one_line": "Mock.", "summary_short": "Mock.", "actions": [act],
               "adjudication": {h: v["enum"][0] for h, v in adj.items()}}
        return D.LLMResult(text=json.dumps(obj), prompt_tokens=2500, output_tokens=150, latency_ms=2000.0)


def ask_for_key(reason: str, done: int, total: int, run: Path, key_env: str) -> str | None:
    """Pause on a quota stop or repeated errors. Returns a new key, "" to retry the same key, None to stop."""
    if not sys.stdin.isatty():
        return None
    print(f"\n*** PAUSED: {reason}. {done}/{total} emails done; progress is saved (response cache and "
          f"{run.name}\\enrich_results.partial.jsonl).")
    print(f"    Paste a {key_env} from ANOTHER Google account (input hidden) to continue with the same model,")
    print("    type r to retry the current key, or press Enter to stop (re-run the command later to resume).")
    for _ in range(4):
        try:
            k = getpass.getpass("    key> ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not k:
            return None
        if k.lower() == "r":
            return ""
        problem = key_problem(k)
        if not problem:
            return k
        print(f"    That does not look like a valid key ({problem}). Nothing was changed; paste it again "
              f"(right-click once, no extra text), or press Enter to stop.")
    return None


def key_problem(k: str) -> str:
    """Why a pasted API key cannot be right (the key is sent in an HTTP header, so it must be plain ASCII)."""
    if any(c.isspace() for c in k):
        return "it contains spaces or line breaks"
    if not k.isascii() or not k.isprintable():
        return "it contains non-ASCII characters, probably extra pasted text"
    if not 20 <= len(k) <= 60:
        return f"length {len(k)}; a Google key is about 39 characters"
    return ""


def _stub_embed(texts):
    out = []
    for t in texts:
        seed = int.from_bytes(hashlib.sha256(t.encode("utf-8")).digest()[:8], "little")
        v = np.random.default_rng(seed).standard_normal(768)
        out.append(v / np.linalg.norm(v))
    return np.asarray(out, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=list(SPLITS), default="devcalib")
    ap.add_argument("--limit", type=int, help="first N emails only (seeded shuffle), for a cheap look")
    ap.add_argument("--model-dir", type=Path, default=ROOT / "model_v1")
    ap.add_argument("--cache", type=Path, default=ROOT / "runs" / "decoder_cache")
    ap.add_argument("--temperature")
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--stub-encoder", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--mock-llm", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    lock = None
    if a.split == "test":                                # the one pre-declared gold-test run
        import importlib.util
        spec = importlib.util.spec_from_file_location("live_lock", ROOT / "scripts" / "live_lock.py")
        LL = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(LL)
        lock = LL.load_lock()
        if not lock:
            sys.exit("ERROR: gold-test is not declared. Run: python scripts\\live_lock.py declare")
        if lock["status"] == "spent":
            sys.exit("ERROR: the gold-test run is spent (runs/live_eval.lock.json). Gold-test is closed.")
        if a.limit or a.temperature or a.run_dir:
            sys.exit("ERROR: --limit / --temperature / --run-dir are not allowed on the locked test run")
        mm = LL.mismatches(lock)
        if mm:
            sys.exit("ERROR: current config differs from the lock:\n  " + "\n  ".join(mm))
        tf = ROOT / lock["gold_test_file"]
        if sha256(tf) != lock["gold_test_sha256"]:
            sys.exit("ERROR: gold-test file hash changed since the lock was declared")
        files = [tf]
        lock["history"].append({"event": "start" if lock["status"] == "declared" else "resume",
                                "at": datetime.now().isoformat(timespec="seconds")})
        lock["status"] = "running"
        LL.save_lock(lock)
        tag, run = "test", ROOT / lock["run_dir"]
    else:
        files = [GOLD / f for f in SPLITS[a.split]]
        tag = a.split + (f"-n{a.limit}" if a.limit else "")
        run = a.run_dir or ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-d3-dev-{tag}"
    run.mkdir(parents=True, exist_ok=True)

    # ---------------- stage 1: label-free
    df = pd.concat([read_cols(f, TEXT_COLS).assign(split=f.stem) for f in files], ignore_index=True)
    dup = df["email_uid"].duplicated()
    if dup.any():
        print(f"WARNING: {int(dup.sum())} duplicate email_uid rows across {[f.name for f in files]}; keeping the first")
        df = df[~dup].reset_index(drop=True)
    if a.limit:
        df = df.sample(frac=1, random_state=42).head(a.limit).reset_index(drop=True)

    over = {"cache_dir": str(a.cache)}
    if a.temperature:
        over["temperature"] = None if a.temperature.lower() == "none" else float(a.temperature)
    cfg = D.DecoderConfig.from_env(**over)
    dec = D.Decoder(cfg, backend=_MockLLM() if a.mock_llm else None)
    tri = TR.load(a.model_dir, embed_fn=_stub_embed if a.stub_encoder else None)
    classes = tri.manifest["classes"]

    config = {"created": datetime.now().isoformat(timespec="seconds"), "script": "scripts/decoder_eval.py",
              "split": a.split, "limit": a.limit, "rows": len(df), "backend": dec.backend.name,
              "model": dec.backend.model, "prompt_version": D.PROMPT_VERSION, "temperature": cfg.temperature,
              "rpm": cfg.rpm, "triage_model": tri.model_version, "manifest_sha256": tri.manifest_sha256,
              "review_threshold": tri.threshold, "seed": 42, "mock_llm": a.mock_llm, "stub_encoder": a.stub_encoder,
              "inputs_sha256": {f.name: sha256(f) for f in files},
              "schema_sha256": sha256(D.SCHEMA_DIR / "enrich.v1.1.json")}
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"{len(df)} emails, backend {dec.backend.name} {dec.backend.model}, prompt {D.PROMPT_VERSION}, "
          f"~{len(df) / max(cfg.rpm, 0.1):.0f} min at {cfg.rpm} rpm if nothing is cached")

    res, stud_rows, hyb_rows, stopped = [], [], [], None
    key_env = cfg.key_env()
    first_key = os.environ.get(key_env, "")
    key_log = [{"key": 1, "fingerprint": hashlib.sha256(first_key.encode()).hexdigest()[:8] if first_key else None,
                "from_email": 1, "reason": "start"}]
    partial = open(run / "enrich_results.partial.jsonl", "w", encoding="utf-8")
    rows = list(df.itertuples(index=False))
    t_start, i, consecutive_pending = time.perf_counter(), 0, 0
    while i < len(rows):
        r = rows[i]
        eid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"secep-gold:{r.email_uid}"))
        t = tri.classify({"input_text": r.input_text}, r.recipient_role, r.recipient_position,
                         email_id=eid, processed_at="2026-01-01T00:00:00.000Z")
        e = dec.enrich({"input_text": r.input_text, "date": r.date}, t, role=r.recipient_role,
                       position=r.recipient_position)
        if e["status"] == "enrich_pending":
            consecutive_pending += 1
            quota = "QuotaExhausted" in e["meta"]["errors"]
            if quota or consecutive_pending >= 3:
                reason = "daily quota exhausted" if quota else f"{consecutive_pending} endpoint errors in a row"
                k = ask_for_key(reason, i, len(rows), run, key_env)
                if k is None:
                    stopped = f"{reason} after {i} emails"
                    break
                if k:
                    fp = dec.replace_api_key(k, backend=_MockLLM() if a.mock_llm else None)
                    key_log.append({"key": len(key_log) + 1, "fingerprint": fp, "from_email": i + 1,
                                    "reason": reason})
                    print(f"    switched to key #{len(key_log)} (fingerprint {fp}); same model "
                          f"{dec.backend.model}, same prompt {D.PROMPT_VERSION}. Continuing.")
                consecutive_pending = 0
                continue                                           # retry the same email
            wait = 0 if a.mock_llm else 30
            print(f"    endpoint error on email {i + 1} ({e['meta']['errors'][-1]}); retrying it in {wait}s "
                  f"[{consecutive_pending}/3]", flush=True)
            time.sleep(wait)
            continue                                               # never skip: retry the same email
        else:
            consecutive_pending = 0
        i += 1
        partial.write(json.dumps({"email_uid": r.email_uid, "split": r.split, "triage": t, "enrich_result": e}) + "\n")
        partial.flush()
        res.append({"email_uid": r.email_uid, "split": r.split, "triage": t, "enrich_result": e})
        sp = {h: t[TR.OUT_KEY[h]]["probs"] for h in TR.HEADS}
        sl = {h: t[TR.OUT_KEY[h]]["label"] for h in TR.HEADS}
        stud_rows.append(i4_row(r.email_uid, sp, sl, classes))
        hp = {h: ({c: float(c == e["final_labels"][h]) for c in classes[h]} if e["sources"][h] == "llm" else sp[h])
              for h in TR.HEADS}
        hyb_rows.append(i4_row(r.email_uid, hp, e["final_labels"], classes))
        if i % 10 == 0 or i == len(df):
            print(f"  {i}/{len(df)}  {time.perf_counter() - t_start:.0f}s  last: {e['status']}"
                  f"{' (cache)' if e['meta']['cache_hit'] else ''}", flush=True)
    partial.close()
    config["api_keys"] = key_log                                   # fingerprints only, never keys
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    with open(run / "enrich_results.jsonl", "w", encoding="utf-8") as f:
        for x in res:
            f.write(json.dumps(x) + "\n")
    pd.DataFrame(stud_rows).to_csv(run / "predictions_student.csv", index=False, float_format="%.8f")
    pd.DataFrame(hyb_rows).to_csv(run / "predictions_hybrid.csv", index=False, float_format="%.8f")

    statuses = [x["enrich_result"]["status"] for x in res]
    pending = statuses.count("enrich_pending")
    if stopped or pending or len(res) < len(df):
        msg = f"INCOMPLETE: {stopped or ''} {pending} pending, {len(df) - len(res)} not reached. " \
              f"Re-run the same command later (after the quota resets); finished emails come from the cache."
        (run / "report.md").write_text(f"# D3 dev run — {tag}\n\n{msg}\n", encoding="utf-8")
        print(msg)
        sys.exit(2)

    # ---------------- stage 2: labels
    gold = pd.concat([read_cols(f, LABEL_COLS) for f in files], ignore_index=True).drop_duplicates("email_uid") \
        .set_index("email_uid")
    gold_eval = run / "gold_eval.csv"                     # gold rows for exactly the emails scored
    pd.concat([read_cols(f) for f in files]).drop_duplicates("email_uid").set_index("email_uid") \
        .loc[[x["email_uid"] for x in res]].reset_index().to_csv(gold_eval, index=False)

    score_py = ROOT / "scripts" / "score.py"
    baseline = GOLD / "human_baseline.json"
    for name in ("student", "hybrid"):
        cmd = [sys.executable, str(score_py), "--gold", str(gold_eval), "--pred", str(run / f"predictions_{name}.csv"),
               "--out", str(run / f"score_{name}")] + (["--baseline", str(baseline)] if baseline.exists() else [])
        p = subprocess.run(cmd, capture_output=True, text=True)
        (run / f"score_{name}.log").write_text(p.stdout + p.stderr, encoding="utf-8")
        print(f"score.py {name}: exit {p.returncode} -> {run / f'score_{name}'}")

    ok = [x for x in res if x["enrich_result"]["status"] == "enriched"]
    def eff(m):  # statistics of the call that produced the answer, even when it came from the cache
        return {**m, **m["orig"]} if m.get("cache_hit") and m.get("orig") else m
    meta = [eff(x["enrich_result"]["meta"]) for x in res]
    live = [m for m in meta if m["requests"]]
    lat = [m["latency_ms"] / max(m["requests"], 1) for m in live]

    def recall(level: str, who: str) -> dict:
        rows = [x for x in res if gold.loc[x["email_uid"], "urgency"] == level]
        if who == "student":
            hit = [x["triage"]["urgency"]["label"] == level for x in rows]
        else:
            hit = [x["enrich_result"]["final_labels"]["urgency"] == level for x in rows]
        return {"n": len(rows), "hits": int(sum(hit)), "recall": (sum(hit) / len(rows)) if rows else None}

    flagged_u = [x for x in res if "urgency" in x["enrich_result"]["flagged_heads"]]
    to_crit = [x for x in flagged_u if x["enrich_result"]["final_labels"]["urgency"] == "Critical"]
    act_rows = [x for x in ok if gold.loc[x["email_uid"], "type"] in EXPECTED]
    act_hits = [action_ok(gold.loc[x["email_uid"], "type"],
                          {a["type"] for a in x["enrich_result"]["enrich"]["actions"]}) for x in act_rows]
    by_type = {}
    for x, h in zip(act_rows, act_hits):
        g = gold.loc[x["email_uid"], "type"]
        by_type.setdefault(g, []).append(h)
    viol = {}
    for x in ok:
        for v in x["enrich_result"]["violations"]:
            viol[v["rule"]] = viol.get(v["rule"], 0) + 1
    changed = {h: sum(1 for x in res if h in x["enrich_result"]["flagged_heads"]
                      and x["enrich_result"]["final_labels"][h] != x["triage"][TR.OUT_KEY[h]]["label"])
               for h in TR.HEADS}
    full_gold = pd.concat([read_cols(f) for f in files]).drop_duplicates("email_uid").set_index("email_uid")
    qf1 = quick_macro_f1(full_gold, res, classes)
    act_types = {}
    for x in ok:
        for a_ in x["enrich_result"]["enrich"]["actions"]:
            act_types[a_["type"]] = act_types.get(a_["type"], 0) + 1
    metrics = {
        "quick_macro_f1": qf1, "action_types": act_types,
        "emails": len(res), "status": {s: statuses.count(s) for s in ("enriched", "enrich_failed", "enrich_pending")},
        "valid_first_attempt": sum(1 for m in meta if m["requests"] == 1 and not m["errors"]),
        "valid_after_retry": len(ok), "schema_valid_share": len(ok) / len(res),
        "flagged": {h: sum(1 for x in res if h in x["enrich_result"]["flagged_heads"]) for h in TR.HEADS},
        "changed_by_decoder": changed,
        "urgency_recall": {lvl: {"student": recall(lvl, "student"), "hybrid": recall(lvl, "hybrid")}
                           for lvl in ("Critical", "High")},
        "flagged_urgency_to_critical": {"flagged": len(flagged_u), "to_critical": len(to_crit)},
        "actions": {"accuracy": float(np.mean(act_hits)) if act_hits else None, "n": len(act_hits),
                    "by_gold_type": {k: {"n": len(v), "accuracy": float(np.mean(v))} for k, v in by_type.items()},
                    "share_with_any_action": float(np.mean([any(a["type"] != "none" for a in
                                                                x["enrich_result"]["enrich"]["actions"])
                                                            for x in ok])) if ok else None},
        "violations": viol,
        "latency_ms_per_request": {"median": float(np.median(lat)) if lat else None,
                                   "p95": float(np.percentile(lat, 95)) if lat else None, "n": len(lat)},
        "tokens_mean": {"in": float(np.mean([m["prompt_tokens"] for m in live])) if live else None,
                        "out": float(np.mean([m["output_tokens"] for m in live])) if live else None},
        "requests_total": sum(m["requests"] for m in meta), "cache_hits": sum(1 for m in meta if m["cache_hit"]),
        "requests_this_run": sum(x["enrich_result"]["meta"]["requests"] for x in res),
        "api_keys_used": len(key_log),
    }
    (run / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    def score_line(name):
        f = run / f"score_{name}" / "report.md"
        return f"- {name}: see `{f.relative_to(run)}`" if f.exists() else f"- {name}: score.py failed, see log"
    u = metrics["urgency_recall"]
    fmt = lambda d: f"{d['hits']}/{d['n']}" + (f" ({d['recall']:.0%})" if d["recall"] is not None else "")
    L = [f"# D3 dev run — {tag} — {config['created']}", "",
         f"Backend `{dec.backend.name}` model `{dec.backend.model}`, prompt `{D.PROMPT_VERSION}`, "
         f"{len(res)} emails ({a.split}). " + ("**Pre-declared one-time gold-test run** (runs/live_eval.lock.json)."
         if lock is not None else "**Indicative only:** gold-dev and gold-calib were used to tune the teacher."), "",
         "## Decoder", "",
         f"- Schema-valid: {len(ok)}/{len(res)} ({metrics['schema_valid_share']:.1%}); first attempt "
         f"{metrics['valid_first_attempt']}; failed {metrics['status']['enrich_failed']}.",
         f"- Flagged heads: {metrics['flagged']}; changed by decoder: {changed}.",
         f"- **Critical recall**: student {fmt(u['Critical']['student'])} → hybrid {fmt(u['Critical']['hybrid'])}. "
         f"High recall: student {fmt(u['High']['student'])} → hybrid {fmt(u['High']['hybrid'])}.",
         f"- Flagged urgency heads moved to Critical: {len(to_crit)} of {len(flagged_u)}.",
         f"- Actions vs gold type: accuracy {metrics['actions']['accuracy'] or 0:.0%} (n {len(act_hits)}); "
         + ", ".join(f"{k} {v['accuracy']:.0%} (n {v['n']})" for k, v in sorted(metrics['actions']['by_gold_type'].items()))
         + f"; any action on {metrics['actions']['share_with_any_action'] or 0:.0%} of emails.",
         f"- Action types proposed: {act_types or 'none'}.",
         f"- Post-check notes (repairs and drops): {viol or 'none'}.",
         f"- Latency per request: median {metrics['latency_ms_per_request']['median'] or 0:.0f} ms, "
         f"p95 {metrics['latency_ms_per_request']['p95'] or 0:.0f} ms (n {len(lat)}); "
         f"tokens/email in {metrics['tokens_mean']['in'] or 0:.0f}, out {metrics['tokens_mean']['out'] or 0:.0f}; "
         f"requests {metrics['requests_total']} in total ({metrics['requests_this_run']} this run, "
         f"{metrics['cache_hits']} answers from cache).", "",
         "## Classification", "", "Quick macro-F1 (primary gold label, classes present in gold; score.py is the reference):", "",
         "| head | n | student | hybrid | Δ |", "|---|---|---|---|---|"]
    L += [f"| {h} | {v['n']} | {v['student']:.3f} | {v['hybrid']:.3f} | {v['hybrid'] - v['student']:+.3f} |"
          for h, v in qf1.items() if v["student"] is not None]
    L += ["", score_line("student"), score_line("hybrid")]
    if a.mock_llm or a.stub_encoder:
        L += ["", "_Mock LLM / stub encoder: test run only._"]
    (run / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    if lock is not None:
        lock["status"] = "spent"
        lock["history"].append({"event": "spent", "at": datetime.now().isoformat(timespec="seconds"),
                                "emails": len(res), "metrics_sha256": sha256(run / "metrics.json"),
                                "api_keys": key_log})
        LL.save_lock(lock)
        print("gold-test lock -> SPENT")
    print("\n".join(L))
    print(f"\nwrote {run}")


if __name__ == "__main__":
    main()
