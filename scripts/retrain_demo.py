#!/usr/bin/env python3
"""
retrain_demo.py — Phase D5 simulated demo (no LLM, no server, laptop CPU).

  1. Writes ~150 modern SaaS-style notification emails (GitHub, Jira, CI, PagerDuty, invoices, calendar,
     2FA codes, newsletters...) from templates, with labels set by the labelling-guide rules. Not Enron.
  2. Embeds them on CPU with the frozen encoder (common/text.py recipe first).
  3. Shows model_v1's accuracy on them, split into a FEEDBACK set (60%) and an untouched EVAL slice (40%).
  4. Feedback: users correct model_v1's mistakes on the feedback set -> corrections CSV (4 simulated users).
  5. retrain.py (x2 corrections, 20% held out, gate on gold-dev) -> candidate saved in the run folder.
     The demo NEVER touches promoted.json or model_vN at the root.
  6. Compares v1 vs candidate on the EVAL slice (never trained on) and prints the gate.

    python scripts\\retrain_demo.py                    # about 1-2 minutes
    python scripts\\retrain_demo.py --corr-weight 10   # if x2 is too weak to move the slice (log as a deviation)
Writes runs\\<date>-retrain-demo\\{saas_emails.csv, corrections.csv, report.md, demo.json, model_candidate\\}.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import student as S  # noqa: E402
from common import text as T  # noqa: E402

HEADS = ("type", "urgency", "sentiment")
REPOS = ["payments-api", "web-frontend", "data-pipeline", "auth-service", "mobile-app", "infra-terraform"]
PEOPLE = ["Priya Nair", "Tom Becker", "Aisha Khan", "Diego Ramos", "Mei Chen", "Lukas Weber", "Sara Ali"]
SERVICES = ["checkout-api", "search-service", "billing-worker", "login-gateway", "notifications"]
VENDORS = ["Atlassian", "Figma", "Datadog", "Vercel", "Notion", "Zoom"]


def templates(rng, d0: date):
    """Yield (subject, body, type, urgency, sentiment). Labels follow labelling-guide v2 (R4, R5, R10, R11...)."""
    p, r, n = lambda: rng.choice(PEOPLE), lambda: rng.choice(REPOS), lambda: int(rng.integers(100, 9999))
    fmt = lambda d: d.strftime("%a %d %b %Y")
    T_ = []
    for _ in range(12):
        k = n(); due = d0 + timedelta(days=int(rng.integers(1, 3)))
        T_.append((f"[acme/{r()}] Review requested on PR #{k}", f"{p()} requested your review on pull request #{k}: "
                   f"\"Refactor retry logic\". The release branch is cut on {fmt(due)}, please review before then.\n\n"
                   f"View it on GitHub.", "Task", "High", "Neutral"))
    for _ in range(10):
        k = n()
        T_.append((f"[acme/{r()}] PR #{k} merged", f"Pull request #{k} \"Bump dependencies\" was merged into main by {p()}."
                   f"\n\nYou are receiving this because you are subscribed to this repository.", "Info", "Low", "Neutral"))
    for _ in range(8):
        T_.append((f"[acme/{r()}] Critical security alert: remote code execution in a dependency",
                   "Dependabot found a critical vulnerability (CVSS 9.8) in a package used in production. "
                   "Exploitation is reported in the wild. Patch and redeploy within 24 hours.", "Task", "Critical", "Neutral"))
    for _ in range(10):
        T_.append((f"Build failed: acme/{r()} on main", f"The CI pipeline failed on main (commit {rng.integers(10**6, 10**7):x}). "
                   "Deploys are blocked until it is green. Please fix today - you authored the last commit.",
                   "Task", "High", "Neutral"))
    for _ in range(12):
        k = n(); due = d0 + timedelta(days=int(rng.integers(5, 13)))
        T_.append((f"[JIRA] PLAT-{k} assigned to you", f"{p()} assigned PLAT-{k} \"Add audit logging to exports\" to you. "
                   f"Due date: {fmt(due)}. Priority: Medium.", "Task", "Medium", "Neutral"))
    for _ in range(8):
        k = n()
        T_.append((f"[JIRA] {p()} mentioned you on PLAT-{k}", f"{p()} mentioned you: \"@you could you check the export "
                   f"logs and tell me if the timeout is ours or the client's?\"", "Task", "Medium", "Neutral"))
    for _ in range(8):
        k = n()
        T_.append((f"[JIRA] PLAT-{k} resolved", f"PLAT-{k} was moved to Done by {p()}. No further action is required.",
                   "Info", "Low", "Neutral"))
    for _ in range(8):
        v = rng.choice(VENDORS)
        T_.append((f"Your {v} receipt", f"Thanks for your payment. Invoice {n()} for ${rng.integers(20, 900)}.00 was charged "
                   "to the card on file. No action is needed.", "Info", "Low", "Neutral"))
    for _ in range(8):
        due = d0 + timedelta(days=int(rng.integers(1, 3)))
        T_.append((f"Approval needed: invoice INV-{n()} (${rng.integers(2, 40)},{rng.integers(100, 999)})",
                   f"Please approve or reject this vendor invoice from {rng.choice(VENDORS)} by {fmt(due)}. "
                   "Use the Approve / Reject buttons in the finance portal.", "Approval", "High", "Neutral"))
    for _ in range(8):
        st = d0 + timedelta(days=int(rng.integers(1, 3)))
        T_.append((f"Invitation: Sprint planning @ {fmt(st)} 10:00", f"{p()} has invited you to Sprint planning on {fmt(st)} "
                   "10:00-11:00 (Zoom). Please accept or decline.", "Meeting", "High", "Neutral"))
    for _ in range(6):
        st = d0 + timedelta(days=int(rng.integers(6, 14)))
        T_.append((f"Invitation: Quarterly architecture review @ {fmt(st)}", f"You are invited to the quarterly architecture "
                   f"review on {fmt(st)} 14:00. Please RSVP.", "Meeting", "Medium", "Neutral"))
    for _ in range(8):
        T_.append((f"Your {rng.choice(VENDORS)} verification code", f"Your verification code is {rng.integers(100000, 999999)}. "
                   "It expires in 10 minutes. If you did not request it, ignore this email.", "Credentials", "Low", "Neutral"))
    for _ in range(6):
        T_.append(("Action required: activate your new SSO account", "An administrator created your SSO account. "
                   "Your temporary password: Welcome-" + str(rng.integers(1000, 9999)) + "! Activate it within 48 hours "
                   "or it will be disabled.", "Credentials", "High", "Neutral"))
    for _ in range(8):
        v = rng.choice(VENDORS)
        T_.append((f"What's new at {v} this month", f"New in {v}: faster search, dark mode and 3 integrations. Read the "
                   "release notes on our blog. Unsubscribe any time.", "Info", "Low", "Neutral"))
    for _ in range(8):
        s = rng.choice(SERVICES)
        T_.append((f"[PagerDuty] TRIGGERED: {s} is down", f"Incident #{n()}: {s} health checks are failing since "
                   "08:52 UTC; error rate 87%. Customers cannot check out. You are on call - acknowledge now.",
                   "Task", "Critical", "Neutral"))
    for _ in range(6):
        T_.append((f"Re: Ticket #{n()} still broken - third time asking", "This is the THIRD time I am reporting this. "
                   "The export has been broken for a week and nobody has replied. Fix it today or we escalate to "
                   "your manager.", "Task", "High", "Frustrated"))
    for _ in range(6):
        T_.append((f"Kudos from {p()}", f"{p()} gave you kudos: \"Huge thanks for jumping on the outage last night - "
                   "you saved the launch!\"", "Info", "Low", "Positive"))
    return T_


def build_emails(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i, (subj, body, ty, ur, se) in enumerate(templates(rng, date(2026, 11, 10))):
        sent = date(2026, 11, 10)
        c = T.clean_body(body)
        s = T.clean_subject(subj)
        rows.append({"email_uid": f"saas{i:04d}", "input_text": T.format_input(s, c["body"]), "date": f"{sent} 09:00",
                     "recipient_role": rng.choice(["Manager", "Analyst", "Consultant", "Other", "Executive"]),
                     "recipient_position": "To", "type": ty, "urgency": ur, "sentiment": se})
    return pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)


def accuracy(man, heads, E, df) -> dict:
    X, _ = S.build_features(E, df["recipient_role"].tolist(), df["recipient_position"].tolist(),
                            man["roles"], man["positions"])
    P = S.predict_proba(man, heads, X, "mixed" if man.get("head_mode") else "balanced")
    out = {}
    for h in HEADS:
        pred = np.array(man["classes"][h])[P[h].argmax(1)]
        out[h] = {"acc": float((pred == df[h].to_numpy()).mean()), "pred": pred.tolist()}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corr-weight", type=float, default=2.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--stub-encoder", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("retrain", ROOT / "scripts" / "retrain.py")
    RT = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(RT)
    from secep_ml import triage as TR

    run = ROOT / "runs" / f"{datetime.now():%Y-%m-%d}-retrain-demo"
    run.mkdir(parents=True, exist_ok=True)
    df = build_emails(a.seed)
    df.to_csv(run / "saas_emails.csv", index=False)
    if a.stub_encoder:
        import hashlib
        E = np.asarray([(lambda v: v / np.linalg.norm(v))(np.random.default_rng(int.from_bytes(
            hashlib.sha256(t.encode()).digest()[:8], "little")).standard_normal(768)) for t in df["input_text"]],
            dtype=np.float32)
    else:
        print(f"embedding {len(df)} emails on CPU ...", flush=True)
        E = TR.load(ROOT / "model_v1").embed(df["input_text"].tolist())
    np.save(run / "saas_emb.npy", E)
    (run / "saas_uids.txt").write_text("\n".join(df["email_uid"]) + "\n", encoding="utf-8")

    n_fb = int(0.6 * len(df))
    fb, ev = df.iloc[:n_fb].reset_index(drop=True), df.iloc[n_fb:].reset_index(drop=True)
    E_fb, E_ev = E[:n_fb], E[n_fb:]
    parent_dir = TR.promoted_model_dir(ROOT)
    man1, heads1 = S.load_model(parent_dir)
    acc_fb, acc_ev1 = accuracy(man1, heads1, E_fb, fb), accuracy(man1, heads1, E_ev, ev)

    corr = []                                             # users correct only the mistakes they see
    for i, r in fb.iterrows():
        for h in HEADS:
            if acc_fb[h]["pred"][i] != r[h]:
                corr.append({"email_uid": r.email_uid, "head": h, "label": r[h], "user_id": f"user{i % 4 + 1}",
                             "recipient_role": r.recipient_role, "recipient_position": r.recipient_position})
    corr = pd.DataFrame(corr)
    corr.to_csv(run / "corrections.csv", index=False)
    print(f"{len(corr)} corrections from {corr['email_uid'].nunique() if len(corr) else 0} emails "
          f"(model {parent_dir.name} was wrong on those heads)")
    if len(corr) < 5:
        sys.exit("too few corrections for a meaningful demo (model already right on this slice)")
    E_corr = S.align(E_fb, fb["email_uid"].tolist(), corr["email_uid"].tolist(), "corrections")

    res = RT.run(parent_dir, corr, E_corr, run, a.corr_weight, 0.2, 0.25, 0.0, promote=False,
                 model_out=run / "model_candidate")
    man2, heads2 = S.load_model(run / "model_candidate")
    acc_ev2 = accuracy(man2, heads2, E_ev, ev)
    demo = {"emails": len(df), "feedback": len(fb), "eval_slice": len(ev), "corrections": len(corr),
            "corr_weight": a.corr_weight, "parent": parent_dir.name,
            "eval_slice_accuracy": {h: {"before": acc_ev1[h]["acc"], "after": acc_ev2[h]["acc"]} for h in HEADS},
            "gate_pass": res["gate"]["pass"], "stub_encoder": a.stub_encoder}
    (run / "demo.json").write_text(json.dumps(demo, indent=2), encoding="utf-8")
    L = ["", f"# Retrain demo — {datetime.now().isoformat(timespec='seconds')}", "",
         f"{len(df)} synthetic SaaS emails: {len(fb)} feedback (corrected by 4 simulated users), {len(ev)} eval slice "
         f"(never trained on). {len(corr)} corrections, weight x{a.corr_weight}.", "",
         "| head | eval slice accuracy, before | after |", "|---|---|---|"]
    L += [f"| {h} | {acc_ev1[h]['acc']:.0%} | {acc_ev2[h]['acc']:.0%} |" for h in HEADS]
    L += ["", f"Gate on gold-dev + held-out corrections: **{'PASS' if res['gate']['pass'] else 'FAIL'}** "
          f"(candidate kept in the run folder; promoted.json untouched)."]
    if a.stub_encoder:
        L += ["", "_Stub encoder: test run._"]
    with open(run / "report.md", "a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {run}")


if __name__ == "__main__":
    main()
