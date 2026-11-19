/**
 * Disagreement Review — Apps Script web app for the rule-making session.
 *
 * Needs the tabs created by prepare_disagreement_review.py:  Items, Emails, Rules.
 *
 * Setup (once):
 *   1. Open the Google Sheet. File → Import → Upload disagreement_review.xlsx
 *      → "Replace spreadsheet" → Import data.
 *   2. Extensions → Apps Script. Replace Code.gs with this file.
 *   3. + → HTML → name it exactly "Index" → paste Index.html. Save.
 *   4. Deploy → New deployment → ⚙ Web app
 *        Execute as: User accessing the web app
 *        Who has access: Anyone with Google account
 *      → Deploy → authorise → open the /exec link.
 *
 * Verdicts and rules are written straight into the Items and Rules tabs.
 * Nothing here can change a gold label: those live in your local gold files.
 */

const ENUMS = {
  type: ['Task', 'Info', 'Credentials', 'Meeting', 'Approval'],
  urgency: ['Critical', 'High', 'Medium', 'Low'],
  sentiment: ['Positive', 'Neutral', 'Negative', 'Frustrated'],
};
const VERDICT_EXTRA = ['Ambiguous'];          // "both readings are defensible"
const RULE_STATUS = ['draft', 'agreed', 'rejected'];
const ITEM_EDITABLE = ['verdict', 'rule_id', 'comment'];
const RULE_COLS = ['rule_id', 'head', 'pair', 'status', 'rule', 'updated_by', 'updated_at'];

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Disagreement Review')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ------------------------------------------------------------------ helpers
function ss_() { return SpreadsheetApp.getActiveSpreadsheet(); }

function sheet_(name) {
  const sh = ss_().getSheetByName(name);
  if (!sh) throw new Error('Tab "' + name + '" not found. Import disagreement_review.xlsx first.');
  return sh;
}

function header_(sh) {
  return sh.getRange(1, 1, 1, sh.getLastColumn()).getDisplayValues()[0].map(function (h) { return String(h).trim(); });
}

/** Make sure every column we need exists (adds missing ones at the end). */
function ensureCols_(sh, cols) {
  let hdr = header_(sh);
  cols.forEach(function (c) {
    if (hdr.indexOf(c) < 0) {
      sh.getRange(1, hdr.length + 1).setValue(c);
      hdr.push(c);
    }
  });
  return hdr;
}

function readTable_(sh) {
  const hdr = header_(sh);
  const n = sh.getLastRow() - 1;
  if (n < 1) return [];
  return sh.getRange(2, 1, n, hdr.length).getDisplayValues().map(function (v, i) {
    const o = { _row: i + 2 };
    hdr.forEach(function (h, j) { o[h] = v[j]; });
    return o;
  });
}

function who_() {
  try { return Session.getActiveUser().getEmail() || 'someone'; } catch (e) { return 'someone'; }
}

function asText_(v) {
  v = v == null ? '' : String(v);
  return /^[=+\-@]/.test(v) ? "'" + v : v;     // keep free text from becoming a formula
}

// ------------------------------------------------------------------ read
function getData() {
  const items = sheet_('Items');
  ensureCols_(items, ['verdict', 'rule_id', 'comment', 'decided_by', 'decided_at']);
  ensureCols_(sheet_('Rules'), RULE_COLS);
  return {
    enums: ENUMS, verdictExtra: VERDICT_EXTRA, ruleStatus: RULE_STATUS,
    items: readTable_(items),
    emails: readTable_(sheet_('Emails')),
    rules: readTable_(sheet_('Rules')),
    sheetName: ss_().getName(),
  };
}

// ------------------------------------------------------------------ write
function saveItem(itemId, field, value) {
  if (ITEM_EDITABLE.indexOf(field) < 0) throw new Error('Not editable: ' + field);
  const lock = LockService.getDocumentLock();
  lock.waitLock(15000);
  try {
    const sh = sheet_('Items');
    const hdr = ensureCols_(sh, ['verdict', 'rule_id', 'comment', 'decided_by', 'decided_at']);
    const ids = sh.getRange(2, hdr.indexOf('item_id') + 1, Math.max(sh.getLastRow() - 1, 1), 1).getDisplayValues();
    let row = -1;
    for (let i = 0; i < ids.length; i++) if (ids[i][0] === itemId) { row = i + 2; break; }
    if (row < 0) throw new Error('Item ' + itemId + ' not found. Press Reload.');
    sh.getRange(row, hdr.indexOf(field) + 1).setValue(asText_(value));
    sh.getRange(row, hdr.indexOf('decided_by') + 1).setValue(who_());
    sh.getRange(row, hdr.indexOf('decided_at') + 1).setValue(new Date());
    return { ok: true };
  } finally {
    lock.releaseLock();
  }
}

/** Create (no rule_id) or update a rule. Returns the saved rule. */
function saveRule(rule) {
  if (rule.status && RULE_STATUS.indexOf(rule.status) < 0) throw new Error('Bad status');
  const lock = LockService.getDocumentLock();
  lock.waitLock(15000);
  try {
    const sh = sheet_('Rules');
    const hdr = ensureCols_(sh, RULE_COLS);
    const rows = readTable_(sh);
    let target = null;
    if (rule.rule_id) {
      target = rows.filter(function (r) { return r.rule_id === rule.rule_id; })[0];
      if (!target) throw new Error('Rule ' + rule.rule_id + ' not found. Press Reload.');
    } else {
      let max = 0;
      rows.forEach(function (r) { const m = /^R(\d+)$/.exec(r.rule_id); if (m) max = Math.max(max, +m[1]); });
      rule.rule_id = 'R' + (max + 1);
      sh.appendRow(hdr.map(function () { return ''; }));
      target = { _row: sh.getLastRow() };
      rule.status = rule.status || 'draft';
    }
    rule.updated_by = who_();
    rule.updated_at = new Date();
    ['rule_id', 'head', 'pair', 'status', 'rule', 'updated_by', 'updated_at'].forEach(function (k) {
      if (rule[k] !== undefined) {
        sh.getRange(target._row, hdr.indexOf(k) + 1).setValue(k === 'updated_at' ? rule[k] : asText_(rule[k]));
      }
    });
    const saved = readTable_(sh).filter(function (r) { return r.rule_id === rule.rule_id; })[0];
    return saved;
  } finally {
    lock.releaseLock();
  }
}

/** Builds the agreed ruleset as Markdown and also writes it to a "Ruleset" tab. */
function exportRuleset() {
  const rules = readTable_(sheet_('Rules')).filter(function (r) { return r.status === 'agreed'; });
  const items = readTable_(sheet_('Items'));
  const emails = {};
  readTable_(sheet_('Emails')).forEach(function (e) { emails[e.email_uid] = e; });
  const heads = ['type', 'urgency', 'sentiment'];
  const lines = ['# Labelling guide — rules agreed from the disagreement review', '',
    '_Generated ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm') +
    ' from "' + ss_().getName() + '". These rules feed the teacher prompt; they do not change gold labels._', ''];
  heads.forEach(function (h) {
    const rs = rules.filter(function (r) { return r.head === h; });
    if (!rs.length) return;
    lines.push('## ' + h.charAt(0).toUpperCase() + h.slice(1), '');
    rs.forEach(function (r) {
      const linked = items.filter(function (it) { return it.rule_id === r.rule_id; });
      lines.push('**' + r.rule_id + (r.pair && r.pair !== '(any)' ? ' · ' + r.pair : '') + '** — ' + r.rule);
      const ex = linked.filter(function (it) { return it.verdict && it.verdict !== 'Ambiguous'; }).slice(0, 3);
      ex.forEach(function (it) {
        const e = emails[it.email_uid] || {};
        lines.push('  - e.g. "' + (e.subject || '(no subject)') + '" → ' + it.verdict +
          (it.comment ? ' (' + it.comment + ')' : ''));
      });
      lines.push('  - linked disagreements: ' + linked.length, '');
    });
  });
  const amb = items.filter(function (it) { return it.verdict === 'Ambiguous'; }).length;
  const open = items.filter(function (it) { return !it.verdict; }).length;
  lines.push('---', 'Disagreements judged genuinely ambiguous: ' + amb + '. Still undecided: ' + open + '.');
  const md = lines.join('\n');

  let out = ss_().getSheetByName('Ruleset');
  if (!out) out = ss_().insertSheet('Ruleset');
  out.clear();
  out.getRange(1, 1).setValue(md).setWrap(true);
  out.setColumnWidth(1, 900);
  return md;
}
