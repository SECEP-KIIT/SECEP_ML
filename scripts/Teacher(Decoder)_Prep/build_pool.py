#!/usr/bin/env python3
"""
build_pool.py — Phase A: the unlabelled training pool (6k uniform + 4k enriched).

Run from  C:\\Dev\\SECEP_ML\\ML_Training :
    python scripts\\build_pool.py

Defaults (change with flags if your folders differ):
    --maildir   Data\\raw\\maildir
    --manifest  Data\\labelling\\manifest.csv     (the gold manifest from build_gold_sheet.py)
    --gold-dir  Data\\gold_final                  (gold_test/dev/calib.csv, decision_log.md)
    --out-dir   Data\\pool

What it does
  1. Scans EVERY custodian's received folders (inbox, own subfolders, deleted_items),
     with the same folder rules as the gold sheet; sent folders are only used to
     learn each custodian's own address (for To/Cc/Bcc position).
     First scan takes a while; the result is cached in Data\\pool\\_scan_cache.pkl.
  2. Maps every custodian to a role with common/roles.py (gold's 19 exactly; others
     from public titles; unknown -> Other).
  3. Removes leakage. An email is dropped if it is a gold email or in a gold thread:
       same Message-ID | same gold email_uid (same text, any mailbox) |
       same gold thread_id | same subject AND shares >=2 participants with a gold email |
       same cleaned text as any gold email (checked after cleaning).
     Then de-duplicates (Message-ID and text), and keeps at most 2 emails per thread.
  4. Samples 6,000 uniformly at random (used later for the role prior) and 4,000
     enriched ones (rare-class keywords: credentials / approval / meeting; tense wording;
     Oct–Dec 2001), each tagged with why it was picked.
  5. Cleans every chosen email with common/text.py (the one recipe).
  6. GATE: re-checks zero overlap with gold (Message-ID, uid, thread, text) and zero
     duplicates inside the pool. If the gate fails, pool.parquet is NOT written.
  7. Writes Data\\pool\\pool.parquet, pool_report.md, roles_used.csv, leakage_check.json,
     a runs\\<date>-build_pool\\ record (config, metrics, fingerprints) and a
     decision_log.md entry.
"""
import argparse
import hashlib
import json
import math
import os
import pickle
import random
import re
import shutil
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from email.parser import Parser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

# ML_Training = the nearest folder above this script that contains common\text.py,
# so the script works from scripts\ or any subfolder of it.
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "common" / "text.py").exists())
sys.path.insert(0, str(ROOT))

from common.roles import ROLES_VERSION, role_for     # noqa: E402
from common.text import TEXT_VERSION, process        # noqa: E402

SCAN_VERSION = "2"            # bump if the scan logic changes (invalidates the cache)

# ---------------------------------------------------------------- same rules as the gold sheet
SENT = {"sent", "sent_items", "_sent_mail", "sent_mail"}
INBOX = {"inbox", "notes_inbox"}
DELETED = {"deleted_items"}
SKIP = {"all_documents", "discussion_threads", "contacts", "calendar", "notes",
        "_americas", "calendar_items"}
BROADCAST_MIN = 15
MIN_BODY_RAW, MAX_BODY_RAW = 25, 30000
MIN_BODY_CLEAN = 20

SUBJ_PREFIX = re.compile(r"^\s*((re|fw|fwd)\s*:\s*)+", re.I)
# Legacy quote split — used ONLY to compute email_uid exactly as build_gold_sheet.py did,
# so pool emails can be matched against gold uids. The text itself comes from common/text.py.
LEGACY_QUOTE_SPLIT = re.compile(
    r"(-{3,}\s*Original Message\s*-{3,}"
    r"|-{3,}\s*Original Appointment\s*-{3,}"
    r"|\n[^\n]{1,80}\n?\s*\d{1,2}/\d{1,2}/\d{2,4} \d{1,2}:\d{2} [AP]M\s*\n\s*To:"
    r"|\nFrom:\s[^\n]+\n\s*Sent:\s)",
    re.I,
)
TENSION = re.compile(
    r"\b(urgent|asap|immediately|unacceptable|frustrat\w*|disappoint\w*|still waiting|"
    r"as soon as possible|escalat\w*|deadline|critical|not acceptable|upset|angry|"
    r"concerned|again\?|why (?:has|have|did|is)n'?t)\b", re.I)
HINTS = {
    "credentials": re.compile(r"\b(password|passcode|log ?in|user ?(?:id|name)|pin\b|"
                              r"access code|credentials?|reset your)\b", re.I),
    "approval": re.compile(r"\b(approv\w*|sign[- ]?off|authori[sz]\w*|consent|"
                           r"please (?:review and )?sign)\b", re.I),
    "meeting": re.compile(r"\b(meeting|conference call|con ?call|agenda|"
                          r"resched\w*|calendar|invit\w*)\b", re.I),
}
# Enriched slice: filled in this order (rarest first) up to these counts, then topped up
# with any email carrying at least one tag.
ENRICH_QUOTAS = {"credentials": 700, "approval": 700, "meeting": 600, "tension": 1200, "q4": 1200}

_parser = Parser()


# ---------------------------------------------------------------- helpers
def win_long(path: str) -> str:
    """Enron files are named '1.', '2.' … and Windows drops a trailing dot from
    normal paths. The \\\\?\\ prefix stops that."""
    if os.name != "nt":
        return path
    path = os.path.abspath(path)
    if path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def rel_parts(rel: str):
    return [p for p in re.split(r"[\\/]", rel) if p]


def folder_category(name):
    n = name.lower()
    if n in SENT:
        return "sent"
    if n in INBOX:
        return "inbox"
    if n in DELETED:
        return "deleted"
    if n in SKIP:
        return None
    return "custom"


def addr_list(value):
    return [a.lower() for _, a in getaddresses([value or ""]) if "@" in a]


def legacy_split(body):
    m = LEGACY_QUOTE_SPLIT.search(body)
    new = body[: m.start()] if m else body
    lines = [ln for ln in new.splitlines() if not ln.lstrip().startswith(">")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def norm(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def text_hash(input_text):
    return hashlib.sha1(norm(input_text).encode("utf-8")).hexdigest()


def thread_id_of(nsubj, parts, mid):
    if nsubj and len(parts) <= BROADCAST_MIN:
        return hashlib.sha1((nsubj + "|" + ",".join(sorted(parts))).encode()).hexdigest()[:12]
    return hashlib.sha1(mid.encode()).hexdigest()[:12]


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_msg(path):
    with open(win_long(path), encoding="latin-1") as fh:
        return _parser.parse(fh)


def wkey(rng, w):
    """Efraimidis–Spirakis key for weighted sampling without replacement."""
    return rng.random() ** (1.0 / max(w, 1e-6))


# ---------------------------------------------------------------- pass 1: scan (one custodian per worker)
def scan_custodian(args):
    maildir, custodian, gold_loose = args
    cdir = os.path.join(maildir, custodian)
    sent_from, recs, seen, n_files = Counter(), [], set(), 0
    for folder in sorted(os.listdir(win_long(cdir))):
        cat = folder_category(folder)
        fpath = os.path.join(cdir, folder)
        if cat is None or not os.path.isdir(win_long(fpath)):
            continue
        for dirpath, _, files in os.walk(win_long(fpath)):
            for fn in files:
                n_files += 1
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, encoding="latin-1") as fh:
                        msg = _parser.parse(fh)
                except Exception:
                    continue
                if cat == "sent":
                    frm = addr_list(msg.get("From"))
                    if frm:
                        sent_from[frm[0]] += 1
                    continue
                mid = (msg.get("Message-ID") or "").strip()
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                body = msg.get_payload()
                if not isinstance(body, str) or len(body) > MAX_BODY_RAW:
                    continue
                new = legacy_split(body)
                if len(new) < MIN_BODY_RAW:
                    continue
                subj = (msg.get("Subject") or "").strip()
                nsubj = SUBJ_PREFIX.sub("", subj).strip().lower()
                frm = (addr_list(msg.get("From")) or [""])[0]
                to, cc, bcc = addr_list(msg.get("To")), addr_list(msg.get("Cc")), addr_list(msg.get("Bcc"))
                parts = set(to + cc + [frm])
                try:
                    dt = parsedate_to_datetime(msg.get("Date"))
                    q4 = dt.year == 2001 and dt.month >= 10
                except Exception:
                    q4 = False
                # loose thread match (mass mail excluded, as in the gold thread rule):
                # same subject and at least 2 shared participants with a gold email
                loose = (bool(nsubj) and len(parts) <= BROADCAST_MIN and
                         any(len(parts & gp) >= 2 for gp in gold_loose.get(nsubj, ())))
                text = subj + "\n" + new
                rel = os.path.relpath(path, win_long(maildir))
                recs.append({
                    "mid": mid, "custodian": custodian, "cat": cat,
                    "folder": os.path.relpath(dirpath, win_long(cdir)).lower(),
                    "path": rel, "q4": q4, "to": to, "cc": cc, "bcc": bcc,
                    "n_recipients": len(set(to + cc + bcc)),
                    "broadcast": len(parts) > BROADCAST_MIN,
                    "thread_id": thread_id_of(nsubj, parts, mid),
                    "h": hashlib.sha1(norm(nsubj + " " + new).encode()).hexdigest(),
                    "tension": bool(TENSION.search(text)),
                    "hints": [k for k, rx in HINTS.items() if rx.search(text)],
                    "leak_loose": loose,
                })

    # custodian's own address: most frequent From in their sent mail (as in the gold sheet);
    # fallback for mailboxes with no sent folder: the most common To address of their mail.
    own, own_src = "", "none"
    if sent_from:
        own, own_src = sent_from.most_common(1)[0][0], "sent"
    elif recs:
        top = Counter(a for r in recs for a in set(r["to"])).most_common(1)
        if top and top[0][1] >= 0.3 * len(recs):
            own, own_src = top[0][0], "to-fallback"
    for r in recs:
        r["recipient"] = own
        r["position"] = ("To" if own and own in r["to"] else
                         "Cc" if own and own in r["cc"] else
                         "Bcc" if own and own in r["bcc"] else "List/Unknown")
        del r["to"], r["cc"], r["bcc"]
    return custodian, own, own_src, recs, n_files


# ---------------------------------------------------------------- pass 2: clean with the recipe
def clean_one(args):
    maildir, rel = args
    try:
        with open(win_long(os.path.join(maildir, *rel_parts(rel))), "rb") as fh:
            return process(fh.read())
    except Exception:
        return None


# ---------------------------------------------------------------- gold
def load_gold(manifest_path, gold_dir, maildir):
    import pandas as pd
    man = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
    need = {"email_uid", "thread_id", "message_id", "source_path"}
    if need - set(man.columns):
        sys.exit(f"{manifest_path} is missing columns {sorted(need - set(man.columns))}")
    gold = {
        "mids": set(man["message_id"].str.strip()) - {""},
        "uids": set(man["email_uid"].str.strip()) - {""},
        "tids": set(man["thread_id"].str.strip()) - {""},
        "loose": defaultdict(list), "text": set(), "missing_files": 0, "n": len(man),
    }
    for rel in man["source_path"]:
        try:
            msg = read_msg(os.path.join(maildir, *rel_parts(rel)))
        except OSError:
            gold["missing_files"] += 1
            continue
        nsubj = SUBJ_PREFIX.sub("", (msg.get("Subject") or "").strip()).strip().lower()
        parts = set(addr_list(msg.get("To")) + addr_list(msg.get("Cc")) +
                    (addr_list(msg.get("From")) or [""])[:1])
        if nsubj and len(parts) <= BROADCAST_MIN:
            gold["loose"][nsubj].append(frozenset(parts))
    text_files = []
    for sp in ("test", "dev", "calib"):
        f = Path(gold_dir) / f"gold_{sp}.csv"
        if not f.exists():
            print(f"  ! {f} not found — text-level leakage check skips gold_{sp}", file=sys.stderr)
            continue
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        if "input_text" not in df.columns:
            print(f"  ! {f.name} has no input_text (rebuild_gold_text.py not run?) — skipped", file=sys.stderr)
            continue
        gold["text"].update(text_hash(t) for t in df["input_text"])
        text_files.append(f)
    gold["loose"] = dict(gold["loose"])
    gold["text_files"] = text_files
    return gold


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maildir", default=str(ROOT / "Data" / "raw" / "maildir"))
    ap.add_argument("--manifest", default=str(ROOT / "Data" / "labelling" / "manifest.csv"))
    ap.add_argument("--gold-dir", default=str(ROOT / "Data" / "gold_final"))
    ap.add_argument("--out-dir", default=str(ROOT / "Data" / "pool"))
    ap.add_argument("--runs-dir", default=str(ROOT / "runs"))
    ap.add_argument("--uniform", type=int, default=6000)
    ap.add_argument("--enriched", type=int, default=4000)
    ap.add_argument("--max-per-thread", type=int, default=2)
    ap.add_argument("--enriched-cust-cap", type=float, default=0.04,
                    help="max share of the enriched slice from one mailbox (default 4%%)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--rescan", action="store_true", help="ignore the scan cache")
    ap.add_argument("--force", action="store_true", help="replace an existing pool.parquet")
    a = ap.parse_args()
    t0 = time.time()

    try:
        import pandas as pd
        import pyarrow  # noqa: F401
    except ImportError:
        sys.exit("Needs pandas and pyarrow:  pip install pandas pyarrow")

    maildir, out_dir = a.maildir, Path(a.out_dir)
    if not os.path.isdir(win_long(maildir)):
        sys.exit(f"maildir not found: {maildir}  (pass --maildir <path>)")
    if not Path(a.manifest).exists():
        sys.exit(f"Gold manifest not found: {a.manifest}  (pass --manifest <path>)")
    out_dir.mkdir(parents=True, exist_ok=True)
    pool_path = out_dir / "pool.parquet"
    if pool_path.exists() and not a.force:
        sys.exit(f"{pool_path} already exists. Re-run with --force to replace it (the old one is backed up).")

    # ---- gold
    print("Loading gold manifest and gold text …", file=sys.stderr)
    gold = load_gold(a.manifest, a.gold_dir, maildir)
    print(f"  {gold['n']} gold emails · {len(gold['tids'])} gold threads · "
          f"{len(gold['text'])} gold texts · {gold['missing_files']} gold files not found", file=sys.stderr)
    if gold["missing_files"]:
        print("  ! some gold source files are missing — check --maildir; the subject+participants"
              " thread check is weaker for those", file=sys.stderr)
    if not gold["text"]:
        sys.exit("No gold input_text found in --gold-dir; the text-level leakage check needs it.")
    manifest_fp = sha256(a.manifest)

    # ---- pass 1 (cached)
    cache = out_dir / "_scan_cache.pkl"
    key = {"scan_version": SCAN_VERSION, "maildir": os.path.abspath(maildir), "manifest": manifest_fp}
    scan = None
    if cache.exists() and not a.rescan:
        with open(cache, "rb") as fh:
            c = pickle.load(fh)
        if c.get("key") == key:
            scan = c["scan"]
            print(f"Using cached scan ({cache.name}); --rescan to redo it.", file=sys.stderr)
    if scan is None:
        custodians = sorted(d for d in os.listdir(win_long(maildir))
                            if os.path.isdir(win_long(os.path.join(maildir, d))))
        print(f"Scanning {len(custodians)} custodians with {a.workers} workers "
              "(first run: roughly 10–25 min on a laptop) …", file=sys.stderr)
        scan = []
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            jobs = [(maildir, c, gold["loose"]) for c in custodians]
            for i, res in enumerate(ex.map(scan_custodian, jobs), 1):
                scan.append(res)
                print(f"  [{i}/{len(custodians)}] {res[0]}: {res[4]} files, {len(res[3])} received",
                      file=sys.stderr)
        with open(cache, "wb") as fh:
            pickle.dump({"key": key, "scan": scan}, fh, protocol=pickle.HIGHEST_PROTOCOL)

    # ---- roles + flatten
    roles, recs = {}, []
    for cust, own, own_src, rs, n_files in scan:
        role, src = role_for(cust)
        roles[cust] = {"custodian": cust, "role": role, "role_source": src, "own_address": own,
                       "own_address_source": own_src, "files_scanned": n_files, "received": len(rs)}
        for r in rs:
            r["role"], r["role_source"] = role, src
        recs.extend(rs)
    thread_size = Counter(r["thread_id"] for r in recs)
    print(f"{len(recs)} received emails scanned", file=sys.stderr)

    # ---- leakage removal + dedup
    rng = random.Random(a.seed)
    recs.sort(key=lambda r: r["path"])
    rng.shuffle(recs)
    removed, seen_mid, seen_h, eligible = Counter(), set(), set(), []
    for r in recs:
        r["uid"] = r["h"][:16]
        if r["mid"] in gold["mids"]:
            removed["leak: gold Message-ID"] += 1
        elif r["uid"] in gold["uids"]:
            removed["leak: gold email (same text, any mailbox)"] += 1
        elif r["thread_id"] in gold["tids"]:
            removed["leak: gold thread_id"] += 1
        elif r["leak_loose"]:
            removed["leak: gold subject + shared participants"] += 1
        elif r["mid"] in seen_mid:
            removed["duplicate Message-ID"] += 1
        elif r["h"] in seen_h:
            removed["duplicate text"] += 1
        else:
            seen_mid.add(r["mid"])
            seen_h.add(r["h"])
            eligible.append(r)
    print(f"{len(eligible)} eligible after leakage removal and dedup", file=sys.stderr)

    # ---- sampling with on-the-fly cleaning
    chosen, chosen_uid, chosen_text = [], set(), set()
    per_thread, per_cust_enr = Counter(), Counter()
    post_reject = Counter()
    ex = ProcessPoolExecutor(max_workers=a.workers)

    def fill(cands, n, slice_name, tag="", cust_cap=None, tag_needed=None):
        got, i = 0, 0
        while got < n and i < len(cands):
            batch, need = [], n - got
            while i < len(cands) and len(batch) < int(need * 1.15) + 20:
                r = cands[i]
                i += 1
                if r["uid"] in chosen_uid or per_thread[r["thread_id"]] >= a.max_per_thread:
                    continue
                if cust_cap and per_cust_enr[r["custodian"]] >= cust_cap:
                    continue
                if tag_needed and not tag_needed(r):
                    continue
                per_thread[r["thread_id"]] += 1
                if cust_cap:
                    per_cust_enr[r["custodian"]] += 1
                chosen_uid.add(r["uid"])
                batch.append(r)
            results = list(ex.map(clean_one, [(maildir, r["path"]) for r in batch], chunksize=25))
            for r, p in zip(batch, results):
                th = text_hash(p["input_text"]) if p else None
                why = ("unreadable" if p is None else
                       "body too short after cleaning" if len(p["body"]) < MIN_BODY_CLEAN else
                       "leak: same cleaned text as gold" if th in gold["text"] else
                       "duplicate cleaned text" if th in chosen_text else
                       "Message-ID changed between passes" if p["message_id"].strip() != r["mid"] else
                       "quota full" if got >= n else "")
                if why:
                    post_reject[why] += why != "quota full"
                    per_thread[r["thread_id"]] -= 1
                    if cust_cap:
                        per_cust_enr[r["custodian"]] -= 1
                    chosen_uid.discard(r["uid"])
                    continue
                chosen_text.add(th)
                chosen.append({**r, "slice": slice_name, "pick_reason": tag, "p": p, "text_hash": th})
                got += 1
        return got

    try:
        print(f"Sampling {a.uniform} uniform …", file=sys.stderr)
        got_u = fill(eligible, a.uniform, "uniform", "uniform")

        def tags_of(r):
            return set(r["hints"]) | ({"tension"} if r["tension"] else set()) | ({"q4"} if r["q4"] else set())

        for r in eligible:
            r["tags"] = tags_of(r)
            w = (3.0 if r["q4"] else 1) * (2.0 if r["tension"] else 1) * (1.5 if r["hints"] else 1)
            w *= (0.5 if r["broadcast"] else 1) * (1.3 if thread_size[r["thread_id"]] > 1 else 1)
            r["w"] = w
        n_cust = len({r["custodian"] for r in eligible}) or 1
        cap = max(math.ceil(a.enriched_cust_cap * a.enriched), math.ceil(2 * a.enriched / n_cust))
        tagged = sorted((r for r in eligible if r["tags"]), key=lambda r: wkey(rng, r["w"]), reverse=True)
        print(f"Sampling {a.enriched} enriched from {len(tagged)} tagged candidates "
              f"(≤{cap} per mailbox) …", file=sys.stderr)
        got_e, shortfalls = 0, {}
        for tag, quota in ENRICH_QUOTAS.items():
            have = sum(tag in c["tags"] for c in chosen if c["slice"] == "enriched")
            want = min(quota, a.enriched - got_e) - have
            if want > 0:
                got = fill(tagged, want, "enriched", tag, cap, lambda r, t=tag: t in r["tags"])
                got_e += got
                if got < want:
                    shortfalls[tag] = f"{have + got}/{quota}"
        if got_e < a.enriched:
            got_e += fill(tagged, a.enriched - got_e, "enriched", "any-tag", cap)
    finally:
        ex.shutdown()
    print(f"Chose {got_u} uniform + {got_e} enriched", file=sys.stderr)

    # ---- dataframe
    rows = []
    for c in chosen:
        p = c["p"]
        rows.append({
            "pool_uid": c["uid"], "slice": c["slice"], "pick_reason": c["pick_reason"],
            "enrich_tags": "|".join(sorted(c["tags"])) if c["slice"] == "enriched" else
                           "|".join(sorted(tags_of(c))),
            "message_id": c["mid"], "custodian": c["custodian"], "folder_category": c["cat"],
            "folder": c["folder"], "source_path": c["path"],
            "recipient_role": c["role"], "role_source": c["role_source"], "recipient": c["recipient"],
            "recipient_position": c["position"], "date": p["date"], "q4_2001": c["q4"],
            "tension": c["tension"], "hints": "|".join(c["hints"]), "broadcast": c["broadcast"],
            "n_recipients": c["n_recipients"], "thread_id": c["thread_id"],
            "thread_size": thread_size[c["thread_id"]],
            "subject": p["subject"], "body": p["body"], "quoted": p["quoted"],
            "input_text": p["input_text"], "masked_kinds": "|".join(p["masked_kinds"]),
            "body_chars": len(p["body"]), "truncated": p["truncated"],
            "text_version": TEXT_VERSION, "roles_version": ROLES_VERSION, "text_hash": c["text_hash"],
        })
    df = pd.DataFrame(rows).sample(frac=1, random_state=a.seed).reset_index(drop=True)
    df.insert(0, "pool_idx", range(len(df)))

    # ---- GATE
    gate = {
        "gold_message_id_overlap": int(df["message_id"].isin(gold["mids"]).sum()),
        "gold_uid_overlap": int(df["pool_uid"].isin(gold["uids"]).sum()),
        "gold_thread_overlap": int(df["thread_id"].isin(gold["tids"]).sum()),
        "gold_text_overlap": int(df["text_hash"].isin(gold["text"]).sum()),
        "dup_message_id": int(df["message_id"].duplicated().sum()),
        "dup_uid": int(df["pool_uid"].duplicated().sum()),
        "dup_text": int(df["text_hash"].duplicated().sum()),
        "max_per_thread": int(df["thread_id"].value_counts().max()) if len(df) else 0,
    }
    passed = all(v == 0 for k, v in gate.items() if k != "max_per_thread") \
        and gate["max_per_thread"] <= a.max_per_thread
    gate["passed"] = passed
    gate["gold_files_missing"] = gold["missing_files"]
    (out_dir / "leakage_check.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    if not passed:
        bad = out_dir / "_failed_pool.parquet"
        df.to_parquet(bad, index=False)
        sys.exit(f"GATE FAILED — pool.parquet NOT written. Details: {out_dir / 'leakage_check.json'} "
                 f"(candidate saved as {bad.name} for inspection)")

    # ---- write
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if pool_path.exists():
        shutil.move(str(pool_path), str(out_dir / f"_old_pool_{stamp}.parquet"))
    df.to_parquet(pool_path, index=False)
    pool_fp = sha256(pool_path)
    roles_df = pd.DataFrame(sorted(roles.values(), key=lambda r: (r["role_source"], r["custodian"])))
    roles_df["in_pool"] = roles_df["custodian"].map(df["custodian"].value_counts()).fillna(0).astype(int)
    roles_df.to_csv(out_dir / "roles_used.csv", index=False)

    def tab(title, s):
        vc = s.value_counts()
        tot = vc.sum() or 1
        return [f"\n**{title}**", "", "| value | n | share |", "|---|---:|---:|"] + \
               [f"| {k} | {v} | {v / tot:.1%} |" for k, v in vc.items()]

    uni, enr = df[df["slice"] == "uniform"], df[df["slice"] == "enriched"]
    tag_counts = pd.Series([t for s in enr["enrich_tags"] for t in s.split("|") if t])
    rpt = [f"# Training pool report ({stamp})", "",
           f"- **{len(df)} emails**: {len(uni)} uniform + {len(enr)} enriched "
           f"(targets {a.uniform} + {a.enriched}); {df['custodian'].nunique()} mailboxes",
           f"- Text recipe `common/text.py` v{TEXT_VERSION}; roles `common/roles.py` v{ROLES_VERSION}",
           f"- pool.parquet sha256 `{pool_fp}`",
           f"- **Leakage gate: PASSED** — 0 gold Message-IDs, 0 gold uids, 0 gold threads, "
           f"0 gold texts, 0 duplicates; ≤{gate['max_per_thread']} per thread",
           f"- Received emails scanned: {len(recs)}; eligible after removal: {len(eligible)}",
           f"- Median body {int(df['body_chars'].median()) if len(df) else 0} chars; "
           f"{int((df['masked_kinds'] != '').sum())} with secrets masked; "
           f"{int(df['broadcast'].sum())} broadcasts (>15 recipients)",
           "", "## Removed before sampling", "", "| reason | n |", "|---|---:|"] + \
          [f"| {k} | {v} |" for k, v in removed.most_common()] + \
          ["", "## Rejected after cleaning", "", "| reason | n |", "|---|---:|"] + \
          [f"| {k} | {v} |" for k, v in post_reject.most_common() if v] + \
          ["", "## Uniform slice (use this alone for the role prior)"] + \
          tab("Role", uni["recipient_role"]) + tab("Position", uni["recipient_position"]) + \
          tab("Folder", uni["folder_category"]) + \
          ["", "## Enriched slice"] + tab("Picked for", enr["pick_reason"]) + \
          tab("Tags carried (an email can carry several)", tag_counts) + \
          tab("Role", enr["recipient_role"]) + \
          ["", "## Roles", "",
           f"- From gold mapping: {int((roles_df.role_source == 'gold').sum())} mailboxes; "
           f"approximate titles: {int((roles_df.role_source == 'approx').sum())}; "
           f"unknown → Other: {int((roles_df.role_source == 'default').sum())}. See roles_used.csv.",
           f"- Mailboxes with no own address found (position = List/Unknown): "
           f"{int((roles_df.own_address_source == 'none').sum())}"]
    if shortfalls:
        rpt += ["", "## Enriched quotas not met", ""] + [f"- {k}: {v}" for k, v in shortfalls.items()]
    (out_dir / "pool_report.md").write_text("\n".join(rpt) + "\n", encoding="utf-8")

    # ---- run record
    run_dir = Path(a.runs_dir) / f"{datetime.now():%Y-%m-%d}-build_pool"
    if run_dir.exists():
        run_dir = run_dir.with_name(run_dir.name + f"-{stamp[-6:]}")
    run_dir.mkdir(parents=True)
    cfg = {k: v for k, v in vars(a).items()}
    cfg.update({"enrich_quotas": ENRICH_QUOTAS, "text_version": TEXT_VERSION,
                "roles_version": ROLES_VERSION, "scan_version": SCAN_VERSION,
                "min_body_raw": MIN_BODY_RAW, "min_body_clean": MIN_BODY_CLEAN})
    metrics = {"n_pool": len(df), "n_uniform": len(uni), "n_enriched": len(enr),
               "received_scanned": len(recs), "eligible": len(eligible),
               "removed": dict(removed), "rejected_after_cleaning": {k: v for k, v in post_reject.items() if v},
               "enriched_shortfalls": shortfalls, "gate": gate,
               "seconds": round(time.time() - t0, 1)}
    fps = {"pool.parquet": pool_fp, "manifest.csv": manifest_fp,
           **{f.name: sha256(f) for f in gold["text_files"]},
           "common/text.py": sha256(ROOT / "common" / "text.py"),
           "common/roles.py": sha256(ROOT / "common" / "roles.py"),
           "scripts/build_pool.py": sha256(Path(__file__).resolve())}
    for name, obj in (("config.json", cfg), ("metrics.json", metrics), ("fingerprints.json", fps)):
        (run_dir / name).write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    shutil.copy2(out_dir / "pool_report.md", run_dir / "pool_report.md")

    log = Path(a.gold_dir) / "decision_log.md"
    entry = ["", f"## Phase A — training pool built ({stamp})", "",
             f"- {len(df)} emails: {len(uni)} uniform + {len(enr)} enriched (Q4-2001, tension, "
             "credentials/approval/meeting keywords), received folders only, all mailboxes",
             "- Cut for the 14-hour plan: 10k pool instead of 25k",
             "- Leakage removed: gold Message-IDs, gold uids (any mailbox), gold thread_ids, "
             "same subject with ≥2 shared participants, same cleaned text. Gate passed (0 overlap).",
             f"- Roles: common/roles.py v{ROLES_VERSION} — gold's 19 exact; other mailboxes from "
             "approximate public titles; unknown → Other. Role prior must use the uniform slice only.",
             f"- pool.parquet sha256 `{pool_fp}`; run record {run_dir.name}/"]
    if log.exists():
        with open(log, "a", encoding="utf-8") as fh:
            fh.write("\n".join(entry) + "\n")

    print("\n" + "\n".join(rpt[:8]))
    print(f"\nWrote {pool_path}\n      {out_dir / 'pool_report.md'}\n      {run_dir}")
    print(f"Done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
