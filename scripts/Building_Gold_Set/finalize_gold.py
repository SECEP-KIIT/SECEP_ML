#!/usr/bin/env python3
"""
finalize_gold.py — steps 2–6 of the SECEP gold-set plan (single labelling pass).

Input
  --sheet     the frozen download of the labelling workbook (gold_raw_v1.xlsx)
  --manifest  manifest.csv written by build_gold_sheet.py

What it does
  2  Merge + validate   reads every labeller tab, normalises values, joins to the
                        manifest on email_uid, logs blanks / invalid values /
                        unsure-without-note / exclude, checks every email has the
                        labellers the manifest says it should.
  3  Labeller check     each person's class mix vs the rest of the team, and each
                        person's agreement with their partners on shared emails.
                        Flags outliers by a rule fixed on the command line.
  4  Agreement          Fleiss κ (nominal) per head on the double-labelled emails,
                        linear-weighted κ for urgency, % agreement, bootstrap 95% CI,
                        labeller-vs-labeller confusion matrices.
  5  Resolution         agreed → label; Type conflicts settled by guide precedence;
                        the rest marked unresolved with both labels kept
                        (strict scoring drops them, lenient accepts either).
  6  Final gold         gold_{test,dev,calib}.csv (+ .parquet if pyarrow is present),
                        per-split class counts, SHA-256 of gold_test, decision log.

Usage
  python finalize_gold.py --sheet gold_raw_v1.xlsx --manifest manifest.csv --out gold_final
  # after reading the report, if you pre-decide to drop an outlier's solo test rows:
  python finalize_gold.py ... --drop-outlier Milan

Needs: pandas, openpyxl (pyarrow optional for parquet).
"""
import argparse
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd

ENUMS = {
    "type": ["Task", "Info", "Credentials", "Meeting", "Approval"],
    "urgency": ["Critical", "High", "Medium", "Low"],          # ordinal, most → least
    "sentiment": ["Positive", "Neutral", "Negative", "Frustrated"],
    "unsure": ["type", "urgency", "sentiment", "multiple", "exclude"],
}
HEADS = ["type", "urgency", "sentiment"]
HEADER = {  # sheet header -> field
    "Type": "type", "Urgency": "urgency", "Sentiment": "sentiment", "Unsure": "unsure",
    "Notes": "notes", "email_uid": "uid", "Labeller": "labeller", "Row #": "row_no",
    "Subject": "subject", "Body": "body", "Thread context (earlier)": "context",
    "Date": "date", "From": "from", "To": "to", "Cc": "cc",
    "Recipient role": "role_sheet", "Position": "position_sheet",
}
# Type disagreements the guide's precedence can settle: {a, b} -> winner.
# Credentials wins over everything; Approval / Meeting win over Task.
# Info-vs-anything and Approval-vs-Meeting are judgement calls -> unresolved.
PRECEDENCE = {
    frozenset({"Credentials", "Task"}): "Credentials",
    frozenset({"Credentials", "Info"}): "Credentials",
    frozenset({"Credentials", "Meeting"}): "Credentials",
    frozenset({"Credentials", "Approval"}): "Credentials",
    frozenset({"Approval", "Task"}): "Approval",
    frozenset({"Meeting", "Task"}): "Meeting",
}


# ------------------------------------------------------------------ helpers
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_value(field, raw):
    """Return (canonical value or '', problem or None)."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return "", None
    s = str(raw).strip()
    if not s:
        return "", None
    lookup = {v.lower(): v for v in ENUMS[field]}
    v = lookup.get(s.lower())
    return (v, None) if v else ("", f"invalid {field} value {s!r}")


def agreement(pairs, cats, weighted=False):
    """Scott/Fleiss-style κ for 2 ratings per item (raters may differ per item).
    weighted=True uses linear weights over the order of `cats`."""
    pairs = [(a, b) for a, b in pairs if a and b]
    n = len(pairs)
    if n == 0:
        return {"n": 0, "kappa": float("nan"), "pct": float("nan")}
    idx = {c: i for i, c in enumerate(cats)}
    k = len(cats)

    def w(a, b):
        if not weighted:
            return 1.0 if a == b else 0.0
        return 1.0 - abs(idx[a] - idx[b]) / (k - 1)

    po = sum(w(a, b) for a, b in pairs) / n
    marg = Counter([a for a, _ in pairs] + [b for _, b in pairs])
    p = {c: marg[c] / (2 * n) for c in cats}
    pe = sum(p[a] * p[b] * w(a, b) for a in cats for b in cats)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return {"n": n, "kappa": kappa, "pct": sum(a == b for a, b in pairs) / n}


def boot_ci(pairs, cats, weighted, B=2000, seed=0):
    pairs = [(a, b) for a, b in pairs if a and b]
    if len(pairs) < 5:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        s = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        kv = agreement(s, cats, weighted)["kappa"]
        if kv == kv:
            vals.append(kv)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def band(k):
    if k != k:
        return "n/a"
    return ("poor" if k < 0 else "slight" if k <= .20 else "fair" if k <= .40 else
            "moderate" if k <= .60 else "substantial" if k <= .80 else "almost perfect")


def md_table(df):
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.values) + " |")
    return "\n".join(out)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="gold_final")
    ap.add_argument("--drop-outlier", action="append", default=[],
                    help="labeller whose single-labelled gold-test rows are removed (repeatable)")
    ap.add_argument("--outlier-gap", type=float, default=0.20,
                    help="flag a labeller whose type κ with partners is this far below the team's")
    ap.add_argument("--outlier-floor", type=float, default=0.40,
                    help="…and below this absolute κ")
    ap.add_argument("--mix-gap", type=float, default=0.15,
                    help="flag a class share differing from the rest of the team by this much")
    ap.add_argument("--min-test-class", type=int, default=15)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    log = [f"# Gold-set decision log", "",
           f"- Run: {datetime.now().isoformat(timespec='seconds')}",
           f"- Sheet: `{os.path.basename(a.sheet)}` sha256 `{sha256(a.sheet)}`",
           f"- Manifest: `{os.path.basename(a.manifest)}` sha256 `{sha256(a.manifest)}`",
           f"- Outlier rule (fixed before any model results): type κ with partners < team κ − {a.outlier_gap} "
           f"AND < {a.outlier_floor}", f"- Dropped outliers: {', '.join(a.drop_outlier) or 'none'}", ""]

    # ---------------- step 2: read + normalise
    xl = pd.ExcelFile(a.sheet)
    frames = []
    for name in xl.sheet_names:
        df = xl.parse(name, dtype=str)
        if "email_uid" not in df.columns:
            continue
        df = df.rename(columns={k: v for k, v in HEADER.items() if k in df.columns})
        df["tab"] = name
        if "labeller" not in df.columns or df["labeller"].isna().all():
            df["labeller"] = name
        frames.append(df)
    if not frames:
        sys.exit("No labeller tabs found (no 'email_uid' column in any sheet).")
    lab = pd.concat(frames, ignore_index=True)
    lab = lab[lab["uid"].notna() & (lab["uid"].str.strip() != "")].copy()
    lab["uid"] = lab["uid"].str.strip()
    lab["labeller"] = lab["labeller"].fillna(lab["tab"]).str.strip()
    for f in ["type", "urgency", "sentiment", "unsure", "notes"]:
        if f not in lab.columns:
            lab[f] = ""
    issues = []
    for i, r in lab.iterrows():
        for f in ["type", "urgency", "sentiment", "unsure"]:
            v, prob = norm_value(f, r[f])
            lab.at[i, f] = v
            if prob:
                issues.append((r["labeller"], r["uid"], r.get("row_no", ""), "invalid", prob))
        lab.at[i, "notes"] = "" if pd.isna(r["notes"]) else str(r["notes"]).strip()
    lab["exclude"] = lab["unsure"] == "exclude"
    for _, r in lab.iterrows():
        if r["exclude"]:
            issues.append((r["labeller"], r["uid"], r.get("row_no", ""), "exclude", "marked exclude"))
            continue
        miss = [h for h in HEADS if not r[h]]
        if miss:
            issues.append((r["labeller"], r["uid"], r.get("row_no", ""), "blank", "missing " + ", ".join(miss)))
        if r["unsure"] and not r["notes"]:
            issues.append((r["labeller"], r["uid"], r.get("row_no", ""), "unsure_no_note",
                           f"unsure={r['unsure']} without a note"))
    dup = lab.duplicated(["uid", "labeller"], keep=False)
    for _, r in lab[dup].iterrows():
        issues.append((r["labeller"], r["uid"], r.get("row_no", ""), "duplicate", "same email twice in one tab"))
    lab = lab.drop_duplicates(["uid", "labeller"], keep="first")

    man = pd.read_csv(a.manifest, dtype=str)
    man["overlap"] = man["overlap"].str.lower() == "true"
    expected = {r.email_uid: set(str(r.labellers).split("+")) for r in man.itertuples()}
    got = lab.groupby("uid")["labeller"].apply(set).to_dict()
    for uid, exp in expected.items():
        g = got.get(uid, set())
        if g != exp:
            issues.append(("+".join(sorted(g)) or "-", uid, "", "coverage",
                           f"expected {sorted(exp)} got {sorted(g)}"))
    for uid in set(got) - set(expected):
        issues.append(("+".join(sorted(got[uid])), uid, "", "unknown_uid", "not in manifest"))
    pd.DataFrame(issues, columns=["labeller", "email_uid", "row_no", "kind", "detail"]) \
        .to_csv(os.path.join(a.out, "issues.csv"), index=False)
    ic = Counter(k for _, _, _, k, _ in issues)
    log += ["## Step 2 — validation", "",
            f"- Label rows read: {len(lab)} from {lab['labeller'].nunique()} labellers",
            *[f"- {k}: {v}" for k, v in sorted(ic.items())],
            "- Blanks are never filled; a blank head drops that email from that head only.", ""]

    # ---------------- step 3: labeller mix
    mix_rows, flags = [], []
    clean = lab[~lab["exclude"]]
    for h in HEADS:
        for L in sorted(clean["labeller"].unique()):
            mine = clean[(clean["labeller"] == L) & (clean[h] != "")][h]
            rest = clean[(clean["labeller"] != L) & (clean[h] != "")][h]
            if len(mine) == 0 or len(rest) == 0:
                continue
            for c in ENUMS[h]:
                sm, sr = (mine == c).mean(), (rest == c).mean()
                mix_rows.append({"head": h, "labeller": L, "class": c, "labeller_share": round(sm, 3),
                                 "rest_share": round(sr, 3), "diff": round(sm - sr, 3)})
                if abs(sm - sr) >= a.mix_gap and (mine == c).sum() >= 5:
                    flags.append(f"{L}: {h}={c} {sm:.0%} vs team {sr:.0%}")
    pd.DataFrame(mix_rows).to_csv(os.path.join(a.out, "labeller_mix.csv"), index=False)

    # ---------------- step 4: agreement on double-labelled emails
    by_uid = {u: g for u, g in lab.groupby("uid")}
    ov_uids = [u for u in man.loc[man["overlap"], "email_uid"] if u in by_uid and len(by_uid[u]) == 2]
    pairs = {h: [] for h in HEADS}
    pair_who = []
    conf = {h: Counter() for h in HEADS}
    for u in ov_uids:
        g = by_uid[u].sort_values("labeller")
        if g["exclude"].any():
            continue
        r1, r2 = g.iloc[0], g.iloc[1]
        pair_who.append((u, r1["labeller"], r2["labeller"]))
        for h in HEADS:
            pairs[h].append((r1[h], r2[h]))
            if r1[h] and r2[h]:
                conf[h][tuple(sorted((r1[h], r2[h])))] += 1
    ag_rows = []
    for h in HEADS:
        s = agreement(pairs[h], ENUMS[h])
        lo, hi = boot_ci(pairs[h], ENUMS[h], False)
        ag_rows.append({"head": h, "metric": "Fleiss κ", "n": s["n"], "kappa": round(s["kappa"], 3),
                        "95% CI": f"{lo:.2f} – {hi:.2f}", "band": band(s["kappa"]), "% agree": f"{s['pct']:.0%}"})
        if h == "urgency":
            sw = agreement(pairs[h], ENUMS[h], weighted=True)
            lo, hi = boot_ci(pairs[h], ENUMS[h], True)
            ag_rows.append({"head": h, "metric": "linear-weighted κ", "n": sw["n"], "kappa": round(sw["kappa"], 3),
                            "95% CI": f"{lo:.2f} – {hi:.2f}", "band": band(sw["kappa"]), "% agree": ""})
    ag = pd.DataFrame(ag_rows)
    team_type_k = agreement(pairs["type"], ENUMS["type"])["kappa"]

    per_lab = []
    for L in sorted(lab["labeller"].unique()):
        row = {"labeller": L}
        for h in HEADS:
            pl = [pairs[h][i] for i, (_, x, y) in enumerate(pair_who) if L in (x, y)]
            s = agreement(pl, ENUMS[h])
            row[f"{h} κ"] = round(s["kappa"], 3)
            row[f"{h} n"] = s["n"]
        row["flag"] = ""
        k = row["type κ"]
        if k == k and k < team_type_k - a.outlier_gap and k < a.outlier_floor:
            row["flag"] = "OUTLIER (rule met)"
        per_lab.append(row)
    per_lab = pd.DataFrame(per_lab)

    # ---------------- step 5: resolution
    disagreements, gold = [], []
    for u, g in by_uid.items():
        m = man[man["email_uid"] == u]
        if m.empty:
            continue
        m = m.iloc[0]
        g = g.sort_values("labeller")
        first = g.iloc[0]
        rec = {"email_uid": u, "split": m["split"], "overlap": bool(m["overlap"]),
               "labellers": "+".join(g["labeller"]), "n_labels": len(g),
               "excluded": bool(g["exclude"].any()),
               "unsure": "|".join(sorted({x for x in g["unsure"] if x and x != "exclude"})),
               "notes": " || ".join(f"{r.labeller}: {r.notes}" for r in g.itertuples() if r.notes)}
        for col in ["subject", "date", "from", "to", "cc", "body", "context"]:
            rec[col] = first.get(col, "")
        for col in ["owner_custodian", "bucket", "recipient_custodian", "recipient_role", "recipient_position",
                    "folder_category", "folder", "q4_2001", "tension", "hints", "broadcast", "thread_id",
                    "thread_size", "message_id", "source_path"]:
            if col in m.index:
                rec[col] = m[col]
        for h in HEADS:
            vals = [v for v in g[h] if v]
            if len(vals) == 0:
                lab_, alt, status = "", "", "missing"
            elif len(vals) == 1:
                lab_, alt, status = vals[0], "", "single" if len(g) == 1 else "single_of_two"
            elif vals[0] == vals[1]:
                lab_, alt, status = vals[0], "", "agreed"
            elif h == "type" and frozenset(vals) in PRECEDENCE:
                lab_ = PRECEDENCE[frozenset(vals)]
                alt = [v for v in vals if v != lab_][0]
                status = "precedence"
            else:
                lab_, alt, status = vals[0], vals[1], "unresolved"
            if status in ("precedence", "unresolved"):
                disagreements.append({"email_uid": u, "split": m["split"], "head": h,
                                      "labeller_a": g.iloc[0]["labeller"], "label_a": g.iloc[0][h],
                                      "labeller_b": g.iloc[1]["labeller"], "label_b": g.iloc[1][h],
                                      "resolution": status, "final": lab_ if status == "precedence" else "",
                                      "subject": rec["subject"], "notes": rec["notes"]})
            rec[f"{h}"] = lab_
            rec[f"{h}_alt"] = alt                    # lenient scoring accepts either
            rec[f"{h}_status"] = status
            rec[f"{h}_strict"] = status in ("single", "single_of_two", "agreed", "precedence")
        gold.append(rec)
    gold = pd.DataFrame(gold)
    pd.DataFrame(disagreements).to_csv(os.path.join(a.out, "disagreements.csv"), index=False)

    # outlier drop: single-labelled gold-test rows of named labellers
    gold["dropped_outlier"] = False
    for L in a.drop_outlier:
        mask = (gold["split"] == "test") & (gold["n_labels"] == 1) & (gold["labellers"] == L)
        gold.loc[mask, "dropped_outlier"] = True
    final = gold[~gold["excluded"] & ~gold["dropped_outlier"]].copy()

    # ---------------- step 6: write gold sets
    hashes, split_rows, warn = {}, [], []
    for sp in ["test", "dev", "calib"]:
        part = final[final["split"] == sp].sort_values("email_uid")
        p = os.path.join(a.out, f"gold_{sp}.csv")
        part.to_csv(p, index=False)
        try:
            part.to_parquet(os.path.join(a.out, f"gold_{sp}.parquet"), index=False)
        except Exception:
            pass
        hashes[sp] = sha256(p)
        for h in HEADS:
            cnt = Counter(part.loc[part[f"{h}_strict"], h])
            for c in ENUMS[h]:
                split_rows.append({"split": sp, "head": h, "class": c, "strict_n": cnt.get(c, 0)})
                if sp == "test" and cnt.get(c, 0) < a.min_test_class:
                    warn.append(f"gold-test {h}={c}: only {cnt.get(c, 0)} (report with wide CI)")
    with open(os.path.join(a.out, "gold_test.sha256"), "w") as fh:
        fh.write(f"{hashes['test']}  gold_test.csv\n")
    sc = pd.DataFrame(split_rows)
    sc_wide = sc.pivot_table(index=["head", "class"], columns="split", values="strict_n", aggfunc="sum") \
        .reindex(columns=["test", "dev", "calib"]).reset_index()

    # ---------------- reports
    status_ct = {h: Counter(final[f"{h}_status"]) for h in HEADS}
    rep = ["# Gold-set agreement report", "",
           f"Double-labelled emails used: {len(pair_who)} (excluded ones removed).", "",
           "## Inter-annotator agreement (step 4)", "", md_table(ag), "",
           "Bands (Landis & Koch): ≤0.20 slight · 0.21–0.40 fair · 0.41–0.60 moderate · "
           "0.61–0.80 substantial · >0.80 almost perfect. These κ values are the human ceiling the model is judged against.", "",
           "## Per-labeller agreement with their partners (step 3)", "", md_table(per_lab), "",
           f"Outlier rule: type κ < team κ ({team_type_k:.2f}) − {a.outlier_gap} and < {a.outlier_floor}. "
           "Per-labeller κ rests on ~50 emails, so treat it as a screen, not a verdict.", "",
           "## Class-mix flags (step 3)", "",
           *([f"- {f}" for f in flags] or ["- none above the threshold"]), "",
           "## Labeller-vs-labeller confusion (step 4)", ""]
    for h in HEADS:
        rep.append(f"**{h}** — most frequent disagreements:")
        dis = [(k, v) for k, v in conf[h].most_common() if k[0] != k[1]][:8]
        rep += [f"- {k[0]} ↔ {k[1]}: {v}" for k, v in dis] or ["- none"]
        rep.append("")
    rep += ["## Resolution (step 5)", ""]
    for h in HEADS:
        rep.append(f"- {h}: " + ", ".join(f"{k} {v}" for k, v in sorted(status_ct[h].items())))
    rep += ["", "## Final gold sets (step 6) — strict counts per class", "", md_table(sc_wide.fillna(0)), "",
            *([f"⚠ {w}" for w in warn] or ["All gold-test classes meet the minimum."]), ""]
    with open(os.path.join(a.out, "agreement_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(rep))

    log += ["## Step 3 — labeller check", "",
            *[f"- {r['labeller']}: type κ {r['type κ']}" + (f" — {r['flag']}" if r['flag'] else "")
              for _, r in per_lab.iterrows()], "",
            "## Step 4 — agreement", "",
            *[f"- {r['head']} {r['metric']}: {r['kappa']} ({r['95% CI']}), {r['band']}" for _, r in ag.iterrows()], "",
            "## Step 5 — resolution rules", "",
            "- Agreed labels kept. Missing on one side → the other label stands (single_of_two).",
            "- Type conflicts settled by guide precedence: Credentials > Approval/Meeting > Task.",
            "- Info-vs-X and Approval-vs-Meeting left unresolved; both labels kept (`*_alt`).",
            "- Unresolved rows: excluded from strict scoring, lenient scoring accepts either label.",
            "- Any labeller marking `exclude` removes the email.",
            "- The teacher LLM is never used to break ties in gold sets.", "",
            "## Step 6 — final gold sets", "",
            *[f"- gold_{sp}: {int((final['split'] == sp).sum())} emails, sha256 `{hashes[sp]}`" for sp in hashes],
            f"- Excluded: {int(gold['excluded'].sum())}; dropped as outlier rows: {int(gold['dropped_outlier'].sum())}",
            "- gold-test is SEALED from this point until final evaluation.", ""]
    with open(os.path.join(a.out, "decision_log.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log))

    print("\n".join(rep))
    print(f"\nWrote to {a.out}/: gold_test.csv gold_dev.csv gold_calib.csv gold_test.sha256 "
          "agreement_report.md decision_log.md disagreements.csv issues.csv labeller_mix.csv", file=sys.stderr)


if __name__ == "__main__":
    main()
