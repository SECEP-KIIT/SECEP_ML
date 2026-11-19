#!/usr/bin/env python3
"""
prepare_disagreement_review.py — Stage 0, Job 5 (setup).

Builds  Data\\review\\disagreement_review.xlsx  for the team's rule-making session.
It READS gold_final\\disagreements.csv and the gold files; it never changes them.

Tabs in the workbook
  Items    one row per disagreement (email × head), plus empty columns the review
           page fills in: verdict, rule_id, comment, decided_by, decided_at
  Emails   one row per email: sender, recipients, date, recipient role/position,
           full cleaned body and the earlier thread
  Rules    starter rules (status "draft") for the team to agree, edit or reject
  README   what this is

Run from  C:\\Dev\\SECEP_ML\\ML_Training :
    python scripts\\prepare_disagreement_review.py

Then in Google Sheets: open your copy → File → Import → Upload this .xlsx →
"Replace spreadsheet". (Your original disagreements.csv stays untouched on disk.)
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import pandas as pd  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

# Starter rules, written from the definitions in the SRS and the disagreement
# patterns in your file. Status "draft": the team accepts, edits or rejects each.
SEED_RULES = [
    ("R0", "type", "(any)", "agreed",
     "Precedence when several types genuinely apply: Credentials > Approval / Meeting > Task > Info."),
    ("R1", "type", "Info ↔ Task", "draft",
     "Task only if the email asks THIS recipient to produce or do something (reply with content, send, "
     "prepare, review, fix). Newsletters, announcements, FYI forwards, confirmations and status reports "
     "are Info, even when they end with a generic 'let me know if…' or 'click here'."),
    ("R2", "type", "Approval ↔ Info / Approval ↔ Task", "draft",
     "Approval only when the recipient is asked for a yes/no decision or sign-off. A notice that something "
     "WAS approved, or an approval list sent for information, is Info. Asking someone to arrange or "
     "execute a deal is Task, not Approval."),
    ("R3", "type", "Info ↔ Meeting", "draft",
     "Meeting when the recipient is asked to attend, schedule, confirm or move a meeting or call. A broad "
     "event announcement (happy hour, brown bag, orientation) with no RSVP asked of the recipient is Info."),
    ("R4", "urgency", "Low ↔ Medium", "draft",
     "Medium if a reply or action is expected from the recipient, with no date or a date more than 3 days "
     "after the email's date. Low if nothing is expected (FYI, newsletters, confirmations, articles), "
     "however important the topic is to the business."),
    ("R5", "urgency", "High ↔ Medium / Critical ↔ High", "draft",
     "High only for a deadline within 3 days of the email's date, or an explicit same-day / ASAP request. "
     "Critical only for a deadline within 24 hours or an outage/loss under way. A subject saying 'critical' "
     "or 'urgent' does not count without a real deadline."),
    ("R6", "sentiment", "Neutral ↔ Positive", "draft",
     "Positive only when thanks, praise or good news is the point of the email. Routine courtesy "
     "('Thanks', 'Regards', 'Hope you are well') and marketing enthusiasm stay Neutral."),
    ("R7", "sentiment", "Negative ↔ Neutral / Frustrated ↔ Negative", "draft",
     "Negative = complaint, disappointment or bad news. Frustrated = irritation aimed at the recipient "
     "(repeated chasing, sharp tone). A news article reporting bad events in a neutral voice is Neutral."),
]


def pair_label(head, a, b):
    x, y = sorted([a, b])                 # alphabetical, same style as the agreement report
    return f"{x} ↔ {y}"


def clean(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return ILLEGAL_CHARACTERS_RE.sub("", str(v))


def write_sheet(wb, title, df, widths):
    ws = wb.create_sheet(title)
    head_font = Font(name="Arial", bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="1F3A5F")
    for ci, col in enumerate(df.columns, 1):
        c = ws.cell(row=1, column=ci, value=col)
        c.font, c.fill = head_font, head_fill
        ws.column_dimensions[get_column_letter(ci)].width = widths.get(col, 14)
    for ri, row in enumerate(df.itertuples(index=False), 2):
        for ci, v in enumerate(row, 1):
            c = ws.cell(row=ri, column=ci)
            c.value = clean(v)
            c.data_type = "s"                       # never let text become a formula
            c.font = Font(name="Arial", size=10)
            c.alignment = Alignment(vertical="top", wrap_text=False)
    ws.freeze_panes = "A2"
    return ws


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold-dir", default=str(ROOT / "Data" / "gold_final"))
    ap.add_argument("--out", default=str(ROOT / "Data" / "review" / "disagreement_review.xlsx"))
    a = ap.parse_args()
    gd = Path(a.gold_dir)

    dis = pd.read_csv(gd / "disagreements.csv", dtype=str, keep_default_na=False)
    gold = pd.concat([pd.read_csv(gd / f"gold_{s}.csv", dtype=str, keep_default_na=False)
                      for s in ("test", "dev", "calib")], ignore_index=True)
    if "body_sheet" not in gold.columns:
        print("Note: gold files have not been rebuilt (Job 3); using the sheet text.", file=sys.stderr)
    gold = gold.drop_duplicates("email_uid").set_index("email_uid")
    missing = sorted(set(dis["email_uid"]) - set(gold.index))
    if missing:
        # emails someone marked 'exclude' were removed from the gold files, so their
        # text is not available here — they are left out of the review
        print(f"Skipping {len(missing)} disagreement email(s) not in the gold files "
              f"(excluded during finalisation): {', '.join(missing)}", file=sys.stderr)
        dis = dis[~dis["email_uid"].isin(missing)]

    # ---- Items
    items = dis.copy()
    items.insert(0, "item_id", [f"{u}-{h}" for u, h in zip(items["email_uid"], items["head"])])
    items["pair"] = [pair_label(h, x, y) for h, x, y in zip(items["head"], items["label_a"], items["label_b"])]
    for col in ["verdict", "rule_id", "comment", "decided_by", "decided_at"]:
        items[col] = ""
    items = items[["item_id", "email_uid", "head", "pair", "labeller_a", "label_a", "labeller_b", "label_b",
                   "resolution", "final", "notes", "verdict", "rule_id", "comment", "decided_by", "decided_at"]]

    # ---- Emails
    uids = list(dict.fromkeys(dis["email_uid"]))
    g = gold.loc[uids]

    def col(name, fallback=""):
        return g[name] if name in g.columns else pd.Series([fallback] * len(g), index=g.index)
    emails = pd.DataFrame({
        "email_uid": uids,
        "subject": col("subject").values,
        "from": col("from").values,
        "to": col("to").values,
        "cc": col("cc").values,
        "date": col("date").values,
        "recipient_role": col("recipient_role").values,
        "recipient_position": col("recipient_position").values,
        "body": col("body").values,
        "earlier_thread": [q or c for q, c in zip(col("quoted").values, col("context").values)],
    })

    rules = pd.DataFrame(SEED_RULES, columns=["rule_id", "head", "pair", "status", "rule"])
    rules["updated_by"] = "draft"
    rules["updated_at"] = ""

    readme = pd.DataFrame({"About this workbook": [
        "Built by prepare_disagreement_review.py from gold_final/disagreements.csv (which is unchanged).",
        "Items: one row per disagreement. Emails: the full emails. Rules: the guide rules being agreed.",
        "Verdicts written here shape the labelling guide and the teacher prompt.",
        "They NEVER change a gold label.",
        f"{len(items)} disagreements across {len(uids)} emails.",
    ]})

    wb = Workbook()
    wb.remove(wb.active)
    write_sheet(wb, "Items", items, {"item_id": 22, "email_uid": 18, "pair": 22, "notes": 50, "comment": 40})
    write_sheet(wb, "Emails", emails, {"email_uid": 18, "subject": 40, "body": 80, "earlier_thread": 60,
                                       "to": 30, "cc": 30})
    write_sheet(wb, "Rules", rules, {"pair": 30, "rule": 100})
    write_sheet(wb, "README", readme, {"About this workbook": 100})
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)

    print(f"Wrote {out}")
    print(f"  {len(items)} disagreements across {len(uids)} emails")
    for (h, p), n in items.groupby(["head", "pair"]).size().sort_values(ascending=False).items():
        print(f"    {h:<9} {p:<26} {n}")


if __name__ == "__main__":
    main()
