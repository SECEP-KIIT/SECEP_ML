#!/usr/bin/env python3
"""
human_baseline.py — Stage 0, Job 4.

Measures how well your labellers agree with EACH OTHER on the double-labelled
emails, in the same units the models will be scored in. It only reads labels;
it never changes a gold file, so it is safe to run after rebuild_gold_text.py.

Run from  C:\\Dev\\SECEP_ML\\ML_Training :
    python scripts\\human_baseline.py --promise-exclude Akashdeep

Outputs (in Data\\gold_final):
    human_baseline.md     readable report
    human_baseline.json   the same numbers for later scripts (teacher gate, final evaluation)
    decision_log.md       one entry appended

How the two labels are recovered from the gold files:
    status agreed                → (label, label)
    status precedence/unresolved → (label, label_alt)   ← the two people's original answers
    single / single_of_two / missing → not a pair, skipped

Views measured:
    4/5-class   the real heads (type, urgency, sentiment)
    type_action     Info  vs  everything else (does the email need anything from me?)
    urgency_2       act soon (Critical, High)  vs  can wait (Medium, Low)
    sentiment_2     Neutral  vs  not Neutral
"""
import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import pandas as pd  # noqa: E402

ENUMS = {
    "type": ["Task", "Info", "Credentials", "Meeting", "Approval"],
    "urgency": ["Critical", "High", "Medium", "Low"],
    "sentiment": ["Positive", "Neutral", "Negative", "Frustrated"],
}
MERGES = {   # view name -> (head, mapping, classes)
    "type_action": ("type", lambda v: "Info" if v == "Info" else "Needs something",
                    ["Needs something", "Info"]),
    "urgency_2": ("urgency", lambda v: "Act soon" if v in ("Critical", "High") else "Can wait",
                  ["Act soon", "Can wait"]),
    "sentiment_2": ("sentiment", lambda v: "Neutral" if v == "Neutral" else "Not neutral",
                    ["Neutral", "Not neutral"]),
}
GATE_MARGIN = 0.05   # teacher must reach human macro-F1 minus this


# ------------------------------------------------------------------ metrics
def per_class_f1(pairs, classes):
    """F1 per class treating the first label as truth and the second as prediction.
    (Per-class F1 is the same whichever way round, so the order does not matter.)"""
    out = {}
    for c in classes:
        tp = sum(a == c and b == c for a, b in pairs)
        fp = sum(a != c and b == c for a, b in pairs)
        fn = sum(a == c and b != c for a, b in pairs)
        if tp + fp + fn == 0:
            continue                          # class never used by either person
        out[c] = 2 * tp / (2 * tp + fp + fn)
    return out


def macro_f1(pairs, classes):
    f = per_class_f1(pairs, classes)
    return sum(f.values()) / len(f) if f else float("nan")


def kappa(pairs, classes):
    n = len(pairs)
    if not n:
        return float("nan")
    po = sum(a == b for a, b in pairs) / n
    marg = {c: 0 for c in classes}
    for a, b in pairs:
        marg[a] += 1
        marg[b] += 1
    pe = sum((marg[c] / (2 * n)) ** 2 for c in classes)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def boot(pairs, classes, fn, B=2000, seed=0):
    rng = random.Random(seed)
    vals = []
    for _ in range(B):
        s = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        v = fn(s, classes)
        if v == v:
            vals.append(v)
    vals.sort()
    return vals[int(.025 * len(vals))], vals[int(.975 * len(vals)) - 1]


def summarise(pairs, classes):
    lo, hi = boot(pairs, classes, macro_f1)
    return {"n": len(pairs), "macro_f1": macro_f1(pairs, classes), "macro_f1_ci": [lo, hi],
            "accuracy": sum(a == b for a, b in pairs) / len(pairs),
            "kappa": kappa(pairs, classes), "per_class_f1": per_class_f1(pairs, classes)}


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold-dir", default=str(ROOT / "Data" / "gold_final"))
    ap.add_argument("--promise-exclude", metavar="NAME",
                    help="also record the robustness promise: final scores will be reported "
                         "with and without NAME's single-labelled test rows")
    a = ap.parse_args()
    gd = Path(a.gold_dir)

    gold = pd.concat([pd.read_csv(gd / f"gold_{s}.csv", dtype=str, keep_default_na=False)
                      for s in ("test", "dev", "calib")], ignore_index=True)
    gold = gold[gold["overlap"].str.lower() == "true"]
    if gold.empty:
        sys.exit("No double-labelled emails found in the gold files.")

    pairs = {}
    for h in ENUMS:
        p = []
        for _, r in gold.iterrows():
            st = r[f"{h}_status"]
            if st == "agreed":
                p.append((r[h], r[h]))
            elif st in ("precedence", "unresolved") and r[f"{h}_alt"]:
                p.append((r[h], r[f"{h}_alt"]))
        pairs[h] = p

    res = {h: summarise(pairs[h], ENUMS[h]) for h in ENUMS}
    for view, (h, f, classes) in MERGES.items():
        res[view] = summarise([(f(x), f(y)) for x, y in pairs[h]], classes)
    gate = {k: round(v["macro_f1"] - GATE_MARGIN, 3) for k, v in res.items()}

    # ---------------- write
    payload = {"created": datetime.now().isoformat(timespec="seconds"),
               "double_labelled_emails": int(len(gold)), "gate_margin": GATE_MARGIN,
               "results": res, "teacher_gate_macro_f1": gate,
               "robustness_promise": a.promise_exclude}
    (gd / "human_baseline.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def row(name, r):
        lo, hi = r["macro_f1_ci"]
        return (f"| {name} | {r['n']} | **{r['macro_f1']:.3f}** | {lo:.2f} – {hi:.2f} | "
                f"{r['accuracy']:.0%} | {r['kappa']:.3f} | {gate[name]:.3f} |")

    md = ["# Human baseline (Stage 0, Job 4)", "",
          f"How well two labellers agree with each other on the {len(gold)} double-labelled emails, "
          "scored exactly the way the models will be scored. Treat these as the ceiling: "
          "a model that matches them is doing as well as a person.", "",
          "| View | Pairs | Human macro-F1 | 95% CI | Same answer | κ | Teacher gate |",
          "|---|---|---|---|---|---|---|",
          *[row(k, res[k]) for k in ENUMS], *[row(k, res[k]) for k in MERGES], "",
          f"**Teacher gate** = human macro-F1 − {GATE_MARGIN}. In Stage 2 the teacher's prompt is good enough "
          "when it reaches this on the tune set, instead of the fixed 0.70.", "",
          "**Merged views**: type_action = Info vs needs-something; urgency_2 = Critical/High vs Medium/Low; "
          "sentiment_2 = Neutral vs not. Use them where a class has too few examples to score on its own.", "",
          "## Human F1 per class", ""]
    for k in list(ENUMS) + list(MERGES):
        pc = ", ".join(f"{c} {v:.2f}" for c, v in res[k]["per_class_f1"].items())
        md.append(f"- **{k}**: {pc}")
    md += ["", "Note: all double-labelled emails sit in gold-test, so this reads gold-test LABELS once. "
           "It uses no model output, and must be run before gold-test is sealed."]
    (gd / "human_baseline.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    log = ["", f"## Stage 0 — human baseline ({datetime.now():%Y-%m-%d %H:%M})", "",
           *[f"- {k}: human macro-F1 {res[k]['macro_f1']:.3f} "
             f"(CI {res[k]['macro_f1_ci'][0]:.2f}–{res[k]['macro_f1_ci'][1]:.2f}), "
             f"κ {res[k]['kappa']:.3f}, n {res[k]['n']} → teacher gate {gate[k]:.3f}"
             for k in list(ENUMS) + list(MERGES)],
           f"- Teacher gate rule: human macro-F1 − {GATE_MARGIN} on the tune set (replaces the fixed 0.70)."]
    if a.promise_exclude:
        log.append(f"- Planned robustness check (decided before any model results): final gold-test scores "
                   f"will also be reported excluding {a.promise_exclude}'s single-labelled test rows.")
    with open(gd / "decision_log.md", "a", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")

    print("\n".join(md[:6 + len(ENUMS) + len(MERGES) + 1]))
    print(f"\nWrote {gd / 'human_baseline.md'}, human_baseline.json, and a decision_log.md entry.")


if __name__ == "__main__":
    main()
