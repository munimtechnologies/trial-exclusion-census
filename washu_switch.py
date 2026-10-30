"""washu_switch: did Washington University's trials switch consent wording, and when?

The pre-registered test in results/washu-switch/PREREG.md. While grading results/consent-permission,
all 13 sampled WashU-led trials with NCT ids before NCT06 carried the WashU clause ("or that of
legally authorized representative, if applicable") and all 7 from NCT06 on carried the sentence
"Legally authorized representatives may sign and give informed consent on behalf of study
participants" instead. This script tests that on the other 204 WashU-led trials of the sponsor
table, which no one has read for this question:

  1. waits until results/washu-switch/PREREG.md is on the repository's main branch and main's
     washu_switch.py is byte for byte this file (gives up after about an hour);
  2. checks the sponsor table (commit dfa8206) against its published counts;
  3. fetches the current eligibility text of all 224 WashU-led trials from the ClinicalTrials.gov
     API v2 in one request, marks each for the two wordings, and grades W1-W5 on the 204 unseen.

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
PREREG_PATH = "results/washu-switch/PREREG.md"
SCRIPT_PATH = "washu_switch.py"
SPONSOR_COMMIT = "dfa820661d6c06ec4eddee5e0ce1513c069a4dc6"
SPONSOR_URL = ("https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/%s/"
               "results/consent-sponsor/consent-sponsor-trials.csv" % SPONSOR_COMMIT)
API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = "NCTId,EligibilityCriteria,StartDate"
USER_AGENT = "washu_switch/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__

SPONSOR_HEADER = ["nct_id", "start_year", "stock_exact", "adult_only", "adult_path",
                  "lead_sponsor", "lead_class", "nci_linked", "washu_led"]
TABLE_ROWS = 5436
WASHU_COUNTS = (165, 224)  # (naming a path, trials), CONSENT-SPONSOR-RESULT.md

# The 20 WashU-led trials read in results/consent-permission (its key.csv, group washu). They
# are left out of every graded share.
SEEN = ("NCT01913951", "NCT02630823", "NCT02683148", "NCT02747537", "NCT03166254",
        "NCT03532217", "NCT03623373", "NCT03655080", "NCT03916796", "NCT04318717",
        "NCT04379505", "NCT05410418", "NCT05618301", "NCT06582849", "NCT06926634",
        "NCT06957431", "NCT07101666", "NCT07620548", "NCT07756593", "NCT07842172")

# Pre-registered (PREREG.md). Changing any of these after the fetch voids the test.
CUTOFF = "NCT06000000"
MIN_FETCHED = 218
MIN_EARLY = 40
MIN_LATE = 15
W1_MIN_DIFF = 0.40
W2_MIN_LATE_SENTENCE = 0.60
W3_MAX_LATE_CLAUSE = 0.10
W4_MAX_EARLY_SENTENCE = 0.10
W5_MIN_EARLY_CLAUSE = 0.50

TRIES = 40
PAUSE = 90

# The WashU clause: "(or that of legally authorized representative, if applicable)".
CLAUSE = re.compile(r"\bor\s+that\s+of\s+(?:[\w'/]+\s+){0,3}?legal(?:ly)?[\s-]+"
                    r"(?:authori[sz]ed|acceptable)[\s-]+representatives?\b", re.I)
# The sentence: "Legally authorized representatives may sign and give informed consent ...".
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


def read_csv(data):
    reader = csv.reader(io.StringIO(data.decode("utf-8")))
    header = next(reader)
    return header, [dict(zip(header, r)) for r in reader if r]


def clean(text):
    """Eligibility text with the API's Markdown backslash escapes removed and spaces collapsed."""
    return re.sub(r"\s+", " ", (text or "").replace("\\", ""))


def wordings(text):
    t = clean(text)
    return bool(CLAUSE.search(t)), bool(SENTENCE.search(t))


def period(nct):
    return "early" if nct < CUTOFF else "late"


def table_gates(header, rows):
    washu = [r for r in rows if truthy(r["washu_led"])]
    by = {r["nct_id"]: r for r in washu}
    got = (sum(1 for r in washu if truthy(r["adult_path"])), len(washu))
    seen_ok = (len(set(SEEN)) == 20 and all(
        i in by and truthy(by[i]["adult_path"]) and not truthy(by[i]["nci_linked"])
        for i in SEEN))
    return {"S1_table": header == SPONSOR_HEADER and len(rows) == TABLE_ROWS,
            "S2_washu_counts": got == WASHU_COUNTS,
            "S3_seen": seen_ok}, washu


def fetch_studies(ids, fetch=None):
    fetch = fetch or fetch_json
    params = {"filter.ids": ",".join(ids), "fields": FIELDS, "pageSize": 1000, "format": "json"}
    out, token = {}, None
    while True:
        if token:
            params["pageToken"] = token
        page = fetch(API + "?" + urllib.parse.urlencode(params))
        for s in page.get("studies", []):
            ps = s.get("protocolSection", {})
            nct = ps.get("identificationModule", {}).get("nctId")
            if nct:
                out[nct] = ps.get("eligibilityModule", {}).get("eligibilityCriteria", "")
        token = page.get("nextPageToken")
        if not token:
            return out


def records(washu, studies):
    out = []
    for r in sorted(washu, key=lambda r: r["nct_id"]):
        nct = r["nct_id"]
        clause, sentence = wordings(studies.get(nct, ""))
        out.append({"nct_id": nct, "period": period(nct), "start_year": r["start_year"],
                    "seen": nct in SEEN, "nci_linked": truthy(r["nci_linked"]),
                    "path_2026_10_16": truthy(r["adult_path"]), "fetched": nct in studies,
                    "clause": clause and nct in studies, "sentence": sentence and nct in studies})
    return out


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def newcombe(k1, n1, k2, n2):
    """Difference k1/n1 - k2/n2 with Newcombe's hybrid score 95% interval (method 10)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def tally(rows):
    n = len(rows)
    out = {"trials": n}
    for w in ("clause", "sentence"):
        k = sum(1 for r in rows if r[w])
        ci = wilson(k, n)
        out[w] = [k, round(k / n, 4) if n else None,
                  [round(ci[0], 4), round(ci[1], 4)] if ci else None]
    out["both_wordings"] = sum(1 for r in rows if r["clause"] and r["sentence"])
    out["neither_wording"] = sum(1 for r in rows if not r["clause"] and not r["sentence"])
    return out


def grade(recs):
    result = {"version": __version__}
    graded = [r for r in recs if r["fetched"] and not r["seen"]]
    early = [r for r in graded if r["period"] == "early"]
    late = [r for r in graded if r["period"] == "late"]
    g = {"S4_fetched": sum(1 for r in recs if r["fetched"]) >= MIN_FETCHED,
         "S5_enough": len(early) >= MIN_EARLY and len(late) >= MIN_LATE}
    result["gates"] = g
    result["unseen"] = {"early": tally(early), "late": tally(late)}
    result["predictions"] = None
    if not all(g.values()):
        return result
    ke, kl = result["unseen"]["early"]["clause"][0], result["unseen"]["late"]["clause"][0]
    d, lo, hi = newcombe(ke, len(early), kl, len(late))
    result["diff_clause_early_minus_late"] = [round(d, 4), round(lo, 4), round(hi, 4)]
    se = result["unseen"]["early"]["sentence"][0] / len(early)
    sl = result["unseen"]["late"]["sentence"][0] / len(late)
    result["predictions"] = {
        "W1": d >= W1_MIN_DIFF and lo > 0,
        "W2": sl >= W2_MIN_LATE_SENTENCE,
        "W3": kl / len(late) <= W3_MAX_LATE_CLAUSE,
        "W4": se <= W4_MAX_EARLY_SENTENCE,
        "W5": ke / len(early) >= W5_MIN_EARLY_CLAUSE,
    }
    return result


def described(recs):
    """Reported, not graded: by NCT prefix, by start year, the 24 NCI-linked, and the boundary."""
    got = [r for r in recs if r["fetched"]]
    prefixes = sorted({r["nct_id"][:5] for r in got})
    years = sorted({r["start_year"] for r in got})
    clause_ids = [r["nct_id"] for r in got if r["clause"]]
    sentence_ids = [r["nct_id"] for r in got if r["sentence"]]
    last_clause = max(clause_ids) if clause_ids else None
    first_sentence = min(sentence_ids) if sentence_ids else None
    overlap = []
    if last_clause and first_sentence and first_sentence < last_clause:
        overlap = [r["nct_id"] for r in got if first_sentence <= r["nct_id"] <= last_clause
                   and (r["clause"] or r["sentence"])]
    return {"by_prefix": {p: tally([r for r in got if r["nct_id"][:5] == p]) for p in prefixes},
            "by_start_year": {y: tally([r for r in got if r["start_year"] == y]) for y in years},
            "nci_linked": tally([r for r in got if r["nci_linked"]]),
            "seen": tally([r for r in got if r["seen"]]),
            "last_clause_id": last_clause, "first_sentence_id": first_sentence,
            "ids_in_overlap": len(overlap)}


def wait_for_prereg(local_script, fetch=fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md and this exact script, else (False, tries)."""
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            script = fetch(REPO_RAW + SCRIPT_PATH + "?n=%d" % i)
            if b"W1" in prereg and normalize(script) == normalize(local_script):
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


def result_text(result):
    lines = ["washu_switch %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for p in ("early", "late"):
        t = (result.get("unseen") or {}).get(p)
        if t:
            lines.append("unseen %s: %d trials, clause %s, sentence %s, both %d, neither %d" % (
                p, t["trials"], t["clause"], t["sentence"], t["both_wordings"],
                t["neither_wording"]))
    if result.get("diff_clause_early_minus_late"):
        lines.append("diff clause early - late: %s" % result["diff_clause_early_minus_late"])
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        lines.append("last clause id %s, first sentence id %s, ids in overlap %d" % (
            d["last_clause_id"], d["first_sentence_id"], d["ids_in_overlap"]))
        for k, t in d["by_prefix"].items():
            lines.append("  %s: %d trials, clause %d, sentence %d" % (
                k, t["trials"], t["clause"][0], t["sentence"][0]))
    return "\n".join(lines)


def write_trials(path, recs):
    cols = ["nct_id", "period", "start_year", "seen", "nci_linked", "path_2026_10_16",
            "fetched", "clause", "sentence"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in recs:
            w.writerow([r[c] for c in cols])


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
        print("washu_switch: %s" % status)
        return 0 if status == "graded" else 2

    ok, polls = wait_for_prereg(local, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    result["polls"] = polls
    if not ok:
        return finish("pre-registration not public; nothing fetched")
    table = fetch(SPONSOR_URL)
    result["sponsor_sha256"] = sha256(table)
    header, rows = read_csv(table)
    g, washu = table_gates(header, rows)
    result["gates"].update(g)
    if not all(g.values()):
        return finish("sponsor table gate failed; nothing fetched")
    result["fetched_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    studies = fetch_studies([r["nct_id"] for r in washu], fetch=fetch_api)
    recs = records(washu, studies)
    write_trials(os.path.join(args.out_dir, "washu-switch-trials.csv"), recs)
    graded = grade(recs)
    result["gates"].update(graded.pop("gates"))
    result.update(graded)
    result["fetched"] = sum(1 for r in recs if r["fetched"])
    result["described"] = described(recs)
    if result["predictions"] is None:
        return finish("fetch gate failed; not graded")
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
