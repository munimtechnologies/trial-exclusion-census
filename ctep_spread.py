"""ctep_spread: who uses CTEP's representative-consent sentence, registry-wide?

The pre-registered test in results/ctep-spread/PREREG.md. results/ctep-template dated the sentence
"Legally authorized representatives may sign and give informed consent on behalf of study
participants" into NCI CTEP's protocol templates between June 13, 2022 and August 4, 2023. This
script finds every ClinicalTrials.gov trial whose eligibility text carries it today, whoever
sponsors it, and asks whether it spread beyond NCI-linked and Washington University-led trials:

  1. waits until results/ctep-spread/PREREG.md is on the repository's main branch and main's
     ctep_spread.py is byte for byte this file (gives up after about an hour);
  2. reads the consent-phrase table (commit c4c0ded) for the trials it marked with the sentence on
     2026-10-16: the recall anchors;
  3. runs three eligibility-text searches on the ClinicalTrials.gov API v2, keeps the trials whose
     text matches the sentence, fetches the anchors by id, and grades R1-R5.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"

REPO_RAW = "https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/main/"
PREREG_PATH = "results/ctep-spread/PREREG.md"
SCRIPT_PATH = "ctep_spread.py"
PHRASE_COMMIT = "c4c0ded776cdb43101b881c88f7de31fde2facdc"
PHRASE_URL = ("https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/%s/"
              "results/consent-phrase/consent-phrase-trials.csv" % PHRASE_COMMIT)
API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = ("NCTId,EligibilityCriteria,StudyFirstSubmitDate,LeadSponsorName,LeadSponsorClass,"
          "CollaboratorName")
USER_AGENT = "ctep_spread/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__
SEARCHES = (
    'AREA[EligibilityCriteria]("may sign and give informed consent")',
    'AREA[EligibilityCriteria]("legally authorized representatives may sign")',
    'AREA[EligibilityCriteria]("legally authorized representative" AND "sign and give")',
)
NCI_NAME = "national cancer institute (nci)"
WASHU_NAME = "washington university school of medicine"

# Pre-registered (PREREG.md). Changing any of these after the fetch voids the test.
PHRASE_ROWS = 5473
ANCHOR_COLUMN = "nci_lar_may_sign"
MIN_ANCHORS = 90
MIN_CURRENT_ANCHORS = 80
MIN_RECALL = 0.95
MIN_POST = 40
MIN_NEITHER = 15
LAST_WITHOUT = "2022-07-09"
FIRST_WITH = "2023-08-04"
R1_MIN_NEITHER_POST = 0.25
R2_MAX_NEITHER_PRE = 0.10
R3_MAX_INDUSTRY = 0.05
R4_MIN_NEITHER_STOCK = 0.80
R5_MIN_NEITHER_SPONSORS = 10

TRIES = 40
PAUSE = 90

# The three patterns of ctep_template.py 0.1.0 (CLAUSE and SENTENCE as in washu_switch.py 0.1.0).
STOCK = re.compile(r"\bability\s+to\s+understand\s+and\s+(?:the\s+)?willingness\s+to\s+sign\s+"
                   r"an?\s+(?:[\w-]+\s+){0,3}?informed\s+consent\s+document", re.I)
CLAUSE = re.compile(r"\bor\s+that\s+of\s+(?:[\w'/]+\s+){0,3}?legal(?:ly)?[\s-]+"
                    r"(?:authori[sz]ed|acceptable)[\s-]+representatives?\b", re.I)
SENTENCE = re.compile(r"\blegal(?:ly)?[\s-]+authori[sz]ed[\s-]+representatives?\s+"
                      r"(?:\(LARs?\)\s+)?may\s+sign\s+and\s+give\s+(?:written\s+)?"
                      r"informed\s+consent\b", re.I)


def truthy(v):
    return str(v).strip() == "True"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(data):
    """Bytes with CRLF turned into LF, so a line-ending change does not count as a difference."""
    return data.replace(b"\r\n", b"\n")


def fetch_bytes(url, tries=4, timeout=60):
    """GET a URL, retrying with a growing pause; raises the last error."""
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                       "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            err = e
            time.sleep(2 * (i + 1))
    raise err


def fetch_json(url):
    return json.loads(fetch_bytes(url).decode("utf-8"))


def clean(text):
    """Eligibility text with the API's Markdown backslash escapes removed and spaces collapsed."""
    return re.sub(r"\s+", " ", (text or "").replace("\\", ""))


def marks(text):
    t = clean(text)
    return {"sentence": bool(SENTENCE.search(t)), "clause": bool(CLAUSE.search(t)),
            "stock": bool(STOCK.search(t))}


def read_anchors(data):
    """(rows, has the anchor column, all ids, sorted anchor ids) of the consent-phrase table."""
    reader = csv.reader(io.StringIO(data.decode("utf-8")))
    header = next(reader)
    rows = [dict(zip(header, r)) for r in reader if r]
    ids = {r["nct_id"] for r in rows}
    if ANCHOR_COLUMN not in header:
        return len(rows), False, ids, []
    return len(rows), True, ids, sorted(r["nct_id"] for r in rows if truthy(r[ANCHOR_COLUMN]))


def study_record(s):
    ps = s.get("protocolSection", {})
    nct = ps.get("identificationModule", {}).get("nctId")
    sc = ps.get("sponsorCollaboratorsModule", {})
    lead = sc.get("leadSponsor", {})
    return nct, {"text": ps.get("eligibilityModule", {}).get("eligibilityCriteria", ""),
                 "submitted": ps.get("statusModule", {}).get("studyFirstSubmitDate", ""),
                 "lead": lead.get("name", ""), "lead_class": lead.get("class", ""),
                 "collaborators": [c.get("name", "") for c in sc.get("collaborators", [])]}


def search(term, fetch=None, pause=1.0, sleep=time.sleep):
    """All studies matching one search: (records, totalCount, studies received)."""
    fetch = fetch or fetch_json
    params = {"query.term": term, "fields": FIELDS, "pageSize": 1000, "countTotal": "true",
              "format": "json"}
    out, total, got, token = {}, None, 0, None
    while True:
        if token:
            params["pageToken"] = token
        page = fetch(API + "?" + urllib.parse.urlencode(params))
        if total is None:
            total = page.get("totalCount")
        for s in page.get("studies", []):
            got += 1
            nct, rec = study_record(s)
            if nct:
                out[nct] = rec
        token = page.get("nextPageToken")
        if not token:
            return out, total, got
        if pause:
            sleep(pause)


def fetch_ids(ids, fetch=None, batch=100, pause=1.0, sleep=time.sleep):
    """The same fields for a list of NCT ids, 100 ids per request."""
    fetch = fetch or fetch_json
    out = {}
    for i in range(0, len(ids), batch):
        params = {"filter.ids": ",".join(ids[i:i + batch]), "fields": FIELDS,
                  "pageSize": 1000, "format": "json"}
        token = None
        while True:
            if token:
                params["pageToken"] = token
            page = fetch(API + "?" + urllib.parse.urlencode(params))
            for s in page.get("studies", []):
                nct, rec = study_record(s)
                if nct:
                    out[nct] = rec
            token = page.get("nextPageToken")
            if not token:
                break
        if pause:
            sleep(pause)
    return out


def nci_linked(rec):
    return any(n.strip().casefold() == NCI_NAME for n in [rec["lead"]] + rec["collaborators"])


def washu_led(rec):
    return rec["lead"].strip().casefold() == WASHU_NAME


def period(date):
    d = (date or "")[:10]
    if len(d) != 10:
        return "none"
    if d <= LAST_WITHOUT:
        return "pre"
    if d >= FIRST_WITH:
        return "post"
    return "gap"


def build(found, frame_ids, anchors):
    """One row per trial whose current eligibility text carries the sentence."""
    rows = []
    for nct in sorted(found):
        rec, hits = found[nct]
        m = marks(rec["text"])
        if not m["sentence"]:
            continue
        nci, washu = nci_linked(rec), washu_led(rec)
        rows.append({"nct_id": nct, "submitted": rec["submitted"][:10],
                     "period": period(rec["submitted"]),
                     "group": "neither" if not (nci or washu) else
                              "both" if nci and washu else "nci" if nci else "washu",
                     "nci_linked": nci, "washu_led": washu, "lead_sponsor": rec["lead"].strip(),
                     "lead_class": rec["lead_class"].strip().upper(), "stock": m["stock"],
                     "clause": m["clause"], "in_frame": nct in frame_ids,
                     "anchor": nct in anchors, "searches": "+".join(str(h) for h in hits)})
    return rows


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def share(k, n):
    return [k, n, round(k / n, 4) if n else None, wilson(k, n)]


def recall(anchors, anchor_recs, sentence_ids):
    current = [a for a in anchors if a in anchor_recs and marks(anchor_recs[a]["text"])["sentence"]]
    found = [a for a in current if a in sentence_ids]
    return {"anchors": len(anchors), "anchors_fetched": sum(1 for a in anchors if a in anchor_recs),
            "anchors_current": len(current), "anchors_found": len(found),
            "missed": [a for a in current if a not in sentence_ids],
            "recall": round(len(found) / len(current), 4) if current else None}


def grade(rows):
    post = [r for r in rows if r["period"] == "post"]
    neither = [r for r in rows if r["group"] == "neither"]
    dated = [r for r in neither if r["period"] != "none"]
    n_post = sum(1 for r in post if r["group"] == "neither")
    n_pre = sum(1 for r in dated if r["period"] == "pre")
    industry = sum(1 for r in rows if r["lead_class"] == "INDUSTRY")
    stock = sum(1 for r in neither if r["stock"])
    sponsors = {r["lead_sponsor"].casefold() for r in neither}
    measures = {"R1_neither_of_post": share(n_post, len(post)),
                "R2_pre_of_dated_neither": share(n_pre, len(dated)),
                "R3_industry_of_all": share(industry, len(rows)),
                "R4_stock_of_neither": share(stock, len(neither)),
                "R5_neither_lead_sponsors": len(sponsors)}
    big = len(dated) >= MIN_NEITHER
    preds = {"R1": n_post / len(post) >= R1_MIN_NEITHER_POST if len(post) >= MIN_POST else None,
             "R2": n_pre / len(dated) <= R2_MAX_NEITHER_PRE if big else None,
             "R3": industry / len(rows) <= R3_MAX_INDUSTRY if rows else None,
             "R4": stock / len(neither) >= R4_MIN_NEITHER_STOCK if big else None,
             "R5": len(sponsors) >= R5_MIN_NEITHER_SPONSORS if big else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    groups = ("nci", "washu", "both", "neither")
    periods = ("pre", "gap", "post", "none")
    by_period = {p: {g: sum(1 for r in rows if r["period"] == p and r["group"] == g)
                     for g in groups} for p in periods}
    years = sorted({r["submitted"][:4] for r in rows if r["submitted"]})
    by_year = {y: {g: sum(1 for r in rows if r["submitted"][:4] == y and r["group"] == g)
                   for g in groups} for y in years}
    counts = {}
    for r in rows:
        if r["group"] == "neither" and r["lead_class"] != "INDIV":
            counts[r["lead_sponsor"]] = counts.get(r["lead_sponsor"], 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    first = {g: min((r["submitted"] for r in rows if r["group"] == g and r["submitted"]),
                    default=None) for g in groups}
    return {"by_group": {g: sum(1 for r in rows if r["group"] == g) for g in groups},
            "by_period": by_period, "by_submit_year": by_year, "top_neither_sponsors": top,
            "first_submitted": first,
            "outside_frame": sum(1 for r in rows if not r["in_frame"]),
            "with_stock": sum(1 for r in rows if r["stock"]),
            "with_clause": sum(1 for r in rows if r["clause"]),
            "by_lead_class": {c: sum(1 for r in rows if r["lead_class"] == c)
                              for c in sorted({r["lead_class"] for r in rows})}}


def wait_for_prereg(local_script, fetch=fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md and this exact script, else (False, tries)."""
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            script = fetch(REPO_RAW + SCRIPT_PATH + "?n=%d" % i)
            if b"R1" in prereg and normalize(script) == normalize(local_script):
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


def result_text(result):
    lines = ["ctep_spread %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    if result.get("searches"):
        lines.append("searches (total, received, kept with sentence): %s" % "; ".join(
            "%d %s/%s/%s" % (i + 1, s["total"], s["received"], s["sentence"])
            for i, s in enumerate(result["searches"])))
    rc = result.get("recall")
    if rc:
        lines.append("anchors %d, fetched %d, still with sentence %d, found %d, recall %s" % (
            rc["anchors"], rc["anchors_fetched"], rc["anchors_current"], rc["anchors_found"],
            rc["recall"]))
    if "sentence_trials" in result:
        lines.append("trials with the sentence: %d" % result["sentence_trials"])
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        lines.append("by group: %s" % d["by_group"])
        for k in ("pre", "gap", "post", "none"):
            lines.append("  %s: %s" % (k, d["by_period"][k]))
        lines.append("outside the 2026-10-16 frame %d, with stock line %d, with WashU clause %d" % (
            d["outside_frame"], d["with_stock"], d["with_clause"]))
    return "\n".join(lines)


TRIAL_COLUMNS = ["nct_id", "submitted", "period", "group", "nci_linked", "washu_led",
                 "lead_sponsor", "lead_class", "stock", "clause", "in_frame", "anchor", "searches"]


def write_trials(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(TRIAL_COLUMNS)
        for r in rows:
            w.writerow([r[c] for c in TRIAL_COLUMNS])


def main(argv=None, fetch=fetch_bytes, fetch_api=None, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    with open(os.path.abspath(__file__), "rb") as f:
        local = f.read()
    result = {"version": __version__, "script_sha256": sha256(local), "gates": {}}

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("ctep_spread: %s" % status)
        return 0 if status == "graded" else 2

    ok, polls = wait_for_prereg(local, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    result["polls"] = polls
    if not ok:
        return finish("pre-registration not public; nothing fetched")
    table = fetch(PHRASE_URL)
    result["phrase_sha256"] = sha256(table)
    n, has_col, frame_ids, anchors = read_anchors(table)
    result["phrase_rows"], result["anchors"] = n, len(anchors)
    result["gates"]["A1_table"] = n == PHRASE_ROWS and has_col and len(anchors) >= MIN_ANCHORS
    if not result["gates"]["A1_table"]:
        return finish("consent-phrase table gate failed; nothing searched")
    result["fetched_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    found, complete, result["searches"] = {}, True, []
    for i, term in enumerate(SEARCHES, 1):
        recs, total, got = search(term, fetch=fetch_api, sleep=sleep)
        complete = complete and total is not None and got == total
        for nct, rec in recs.items():
            found.setdefault(nct, (rec, []))[1].append(i)
        result["searches"].append({"term": term, "total": total, "received": got,
                                   "sentence": sum(1 for r in recs.values()
                                                   if marks(r["text"])["sentence"])})
    anchor_recs = fetch_ids(anchors, fetch=fetch_api, sleep=sleep)
    rows = build(found, frame_ids, set(anchors))
    rc = recall(anchors, anchor_recs, {r["nct_id"] for r in rows})
    result["recall"] = rc
    result["gates"]["A2_searches_complete"] = complete
    result["gates"]["A3_recall"] = (rc["anchors_current"] >= MIN_CURRENT_ANCHORS
                                    and rc["recall"] is not None and rc["recall"] >= MIN_RECALL)
    result["sentence_trials"] = len(rows)
    write_trials(os.path.join(args.out_dir, "ctep-spread-trials.csv"), rows)
    result["described"] = described(rows)
    if not all(result["gates"].values()):
        return finish("search gate failed; not graded")
    result["measures"], result["predictions"] = grade(rows)
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
