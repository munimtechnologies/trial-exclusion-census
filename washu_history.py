"""washu_history: did WashU's trials carry the representative-consent sentence before CTEP's template?

The pre-registered test in results/washu-history/PREREG.md. results/ctep-template dated when NCI
CTEP's protocol templates gained the sentence "Legally authorized representatives may sign and give
informed consent on behalf of study participants": not in any archived copy up to 2022-07-09, in
every copy from 2023-11-15 on. Three Washington University-led trials registered in 2020-2022 carry
the sentence in today's registry text. This script reads the Internet Archive's copies of the
ClinicalTrials.gov study pages of all 224 WashU-led trials in results/washu-switch:

  1. waits until results/washu-history/PREREG.md is on the repository's main branch and main's
     washu_history.py is byte for byte this file (gives up after about an hour);
  2. reads the washu-switch per-trial table from main;
  3. for each trial, lists its archived study pages, reads the newest one captured on or before
     2022-07-09 that shows the trial's consent line, and, for the nine trials at the edges of the
     WashU switch, reads every distinct archived copy; then grades H1-H3.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import base64
import csv
import gzip
import hashlib
import html
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"

REPO_RAW = "https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/main/"
PREREG_PATH = "results/washu-history/PREREG.md"
SCRIPT_PATH = "washu_history.py"
TABLE_PATH = "results/washu-switch/washu-switch-trials.csv"
CDX = "https://web.archive.org/cdx/search/cdx"
CDX_FIELDS = "timestamp,original,statuscode,digest,mimetype"
CDX_LIMIT = 5000
MAX_CDX_PAGES = 5
WAYBACK = "https://web.archive.org/web/%sid_/%s"
USER_AGENT = "washu_history/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__

# Pre-registered (PREREG.md). Changing any of these after the fetch voids the test.
TABLE_ROWS = 224
EARLY_SENTENCE = ("NCT04462328", "NCT04852328", "NCT05521984")
LATE_CLAUSE_COUNT = 6
HOSTS = ("clinicaltrials.gov",)
BOUNDARY_HOSTS = ("clinicaltrials.gov", "classic.clinicaltrials.gov")
PATHS = ("/ct2/show/%s", "/ct2/show/record/%s")
CUTOFF_DAY = "20220709"
PRE_TRIES = 3
BOUNDARY_MAX = 25
MIN_PRE_USABLE = 30
H2_MIN_GRADED = 2
H3_KEPT = (9, 10)  # at least 9 in 10
DEADLINE_SECONDS = 150 * 60

TRIES = 40
PAUSE = 90
CDX_PAUSE = 2
DOWNLOAD_PAUSE = 4

# The stock line and the two wordings, exactly as in ctep_template.py 0.1.0 (the clause and the
# sentence are washu_switch.py 0.1.0's).
STOCK = re.compile(r"\bability\s+to\s+understand\s+and\s+(?:the\s+)?willingness\s+to\s+sign\s+"
                   r"an?\s+(?:[\w-]+\s+){0,3}?informed\s+consent\s+document", re.I)
CLAUSE = re.compile(r"\bor\s+that\s+of\s+(?:[\w'/]+\s+){0,3}?legal(?:ly)?[\s-]+"
                    r"(?:authori[sz]ed|acceptable)[\s-]+representatives?\b", re.I)
SENTENCE = re.compile(r"\blegal(?:ly)?[\s-]+authori[sz]ed[\s-]+representatives?\s+"
                      r"(?:\(LARs?\)\s+)?may\s+sign\s+and\s+give\s+(?:written\s+)?"
                      r"informed\s+consent\b", re.I)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def wayback_digest(data):
    """The Internet Archive's digest of a payload: base32 of its SHA-1."""
    return base64.b32encode(hashlib.sha1(data).digest()).decode("ascii")


def normalize(data):
    """Bytes with CRLF turned into LF, so a line-ending change does not count as a difference."""
    return data.replace(b"\r\n", b"\n")


def fetch_bytes(url, tries=4, timeout=120):
    """GET a URL, retrying with a growing pause (longer for the Internet Archive)."""
    base = 15 if "web.archive.org" in url else 2
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                       "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            err = e
            time.sleep(base * (i + 1))
    raise err


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def page_text(data):
    """Visible text of an HTML page: scripts, styles and tags dropped, entities decoded."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    s = data.decode("utf-8", "replace")
    s = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    return clean(html.unescape(re.sub(r"<[^>]+>", " ", s)))


def classify(data, nct):
    """Marks of one archived study page. Usable = it names the trial and shows the stock line."""
    try:
        text = page_text(data)
    except Exception:  # a broken payload is reported, never graded
        text = ""
    return {"usable": bool(STOCK.search(text)) and nct.lower() in text.lower(),
            "clause": bool(CLAUSE.search(text)), "sentence": bool(SENTENCE.search(text)),
            "chars": len(text), "bytes": len(data), "sha256": sha256(data)}


def truthy(v):
    return str(v).strip() == "True"


def read_table(data):
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    for r in rows:
        for k in ("seen", "nci_linked", "path_2026_10_16", "fetched", "clause", "sentence"):
            r[k] = truthy(r.get(k))
    return rows


def table_ok(trials):
    by_id = {t["nct_id"]: t for t in trials}
    late_clause = [t for t in trials if t["period"] == "late" and t["clause"]]
    return (len(trials) == TABLE_ROWS and len(by_id) == TABLE_ROWS
            and all(n in by_id and by_id[n]["period"] == "early" and by_id[n]["sentence"]
                    for n in EARLY_SENTENCE)
            and len(late_clause) == LATE_CLAUSE_COUNT)


def boundary_ids(trials):
    return sorted(set(EARLY_SENTENCE) | {t["nct_id"] for t in trials
                                         if t["period"] == "late" and t["clause"]})


def prefixes(nct, boundary):
    return [h + p % nct for h in (BOUNDARY_HOSTS if boundary else HOSTS) for p in PATHS]


def cdx_rows(prefix, fetch):
    """All CDX rows under a URL prefix, following resume keys; (rows, complete)."""
    rows, key = [], None
    for _ in range(MAX_CDX_PAGES):
        params = {"url": prefix, "matchType": "prefix", "output": "json", "fl": CDX_FIELDS,
                  "limit": CDX_LIMIT, "showResumeKey": "true"}
        if key:
            params["resumeKey"] = key
        data = fetch(CDX + "?" + urllib.parse.urlencode(params))
        page = json.loads(data.decode("utf-8")) if data.strip() else []
        header, key = None, None
        for i, r in enumerate(page):
            if header is None:
                header = r
            elif not r:  # a blank row: the next one holds the resume key
                if i + 1 < len(page) and page[i + 1]:
                    key = page[i + 1][0]
                break
            else:
                rows.append(dict(zip(header, r)))
        if not key:
            return rows, True
    return rows, False


def captures(rows):
    """Downloadable captures (status 200), oldest first."""
    out = [{"ts": r["timestamp"], "original": r["original"], "digest": r.get("digest", "")}
           for r in rows if r.get("statuscode") == "200"]
    return sorted(out, key=lambda c: (c["ts"], c["original"]))


def pre_candidates(caps):
    """Up to PRE_TRIES distinct pages captured on or before CUTOFF_DAY, newest first."""
    newest = {}
    for c in caps:
        if c["ts"][:8] <= CUTOFF_DAY:
            newest[c["digest"]] = c  # caps are oldest first, so the last one wins
    return sorted(newest.values(), key=lambda c: (c["ts"], c["original"]),
                  reverse=True)[:PRE_TRIES]


def boundary_plan(caps):
    """Up to BOUNDARY_MAX distinct pages, each at its earliest capture, oldest first."""
    first = {}
    for c in caps:
        first.setdefault(c["digest"], c)
    return sorted(first.values(), key=lambda c: (c["ts"], c["original"]))[:BOUNDARY_MAX]


def wording(m):
    if m["clause"] and m["sentence"]:
        return "both"
    return "clause" if m["clause"] else "sentence" if m["sentence"] else "neither"


def today(t):
    return wording({"clause": t["clause"], "sentence": t["sentence"]})


def grade(trials, pre, first, complete):
    """Gates A2-A3 and H1-H3 from the pre-template marks and the early trials' first pages."""
    usable = [t for t in trials if pre.get(t["nct_id"])]
    clause_today = [t for t in usable if t["clause"]]
    kept = [t for t in clause_today if pre[t["nct_id"]]["clause"]]
    graded2 = [n for n in EARLY_SENTENCE if first.get(n)]
    g = {"A2_coverage": len(usable) >= MIN_PRE_USABLE, "A3_complete": bool(complete)}
    r = {"gates": g, "pre_usable": len(usable),
         "pre_with_sentence": sorted(t["nct_id"] for t in usable
                                     if pre[t["nct_id"]]["sentence"]),
         "clause_today": len(clause_today), "clause_kept": len(kept),
         "h2_graded": graded2,
         "h2_sentence_first": [n for n in graded2 if first[n]["sentence"]],
         "predictions": None}
    if not all(g.values()):
        return r
    r["predictions"] = {
        "H1": not r["pre_with_sentence"],
        "H2": (not r["h2_sentence_first"]) if len(graded2) >= H2_MIN_GRADED else None,
        "H3": (H3_KEPT[1] * len(kept) >= H3_KEPT[0] * len(clause_today))
        if clause_today else None,
    }
    return r


def described(trials, pre, pages):
    """Not graded: today's wording against the pre-template page, and the boundary timelines."""
    cross = {}
    for t in trials:
        m = pre.get(t["nct_id"])
        if m:
            key = "%s->%s" % (wording(m), today(t))
            cross[key] = cross.get(key, 0) + 1
    timelines = {}
    for nct, rows in sorted(pages.items()):
        timelines[nct] = [[p["ts"][:8], wording(p) if p["usable"] else "unusable"]
                          for p in sorted(rows, key=lambda p: p["ts"])]
    with_s = [p for rows in pages.values() for p in rows if p["usable"] and p["sentence"]]
    earliest = min(with_s, key=lambda p: p["ts"]) if with_s else None
    return {"pre_to_today": dict(sorted(cross.items())), "boundary_timelines": timelines,
            "earliest_sentence_page": [earliest["nct_id"], earliest["ts"]] if earliest else None}


def wait_for_prereg(local_script, fetch=fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md and this exact script, else (False, tries)."""
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            script = fetch(REPO_RAW + SCRIPT_PATH + "?n=%d" % i)
            if b"H1" in prereg and normalize(script) == normalize(local_script):
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


PAGE_COLS = ["nct_id", "role", "ts", "original", "digest", "downloaded", "digest_match",
             "usable", "clause", "sentence", "chars", "bytes", "sha256", "error"]


def write_pages(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(PAGE_COLS)
        for r in rows:
            w.writerow([r.get(k, "") for k in PAGE_COLS])


def result_text(result):
    lines = ["washu_history %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    if "trials" in result:
        lines.append("trials %d, boundary %d, cdx queries %d (errors %d), pages downloaded %d "
                     "(errors %d), elapsed %ss" % (
                         result["trials"], len(result["boundary"]), result["cdx_queries"],
                         result["cdx_errors"], result["downloaded"], result["download_errors"],
                         result["elapsed_seconds"]))
    if "pre_usable" in result:
        lines.append("pre-template pages (on or before %s): usable %d, with sentence %s" % (
            CUTOFF_DAY, result["pre_usable"], result["pre_with_sentence"] or "none"))
        lines.append("clause today with a usable pre-template page %d, clause then %d" % (
            result["clause_today"], result["clause_kept"]))
        lines.append("H2 graded on %s; sentence on first page: %s" % (
            result["h2_graded"] or "none", result["h2_sentence_first"] or "none"))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        lines.append("pre -> today: %s" % ", ".join("%s %d" % kv
                                                    for kv in d["pre_to_today"].items()))
        lines.append("earliest page with the sentence: %s" % (d["earliest_sentence_page"]
                                                              or "none"))
        for nct, tl in d["boundary_timelines"].items():
            lines.append("  %s: %s" % (nct, "; ".join("%s %s" % tuple(x) for x in tl) or
                                       "no pages"))
    return "\n".join(lines)


def main(argv=None, fetch=fetch_bytes, sleep=time.sleep, clock=time.monotonic):
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
        print("washu_history: %s" % status)
        return 0 if status == "graded" else 2

    ok, polls = wait_for_prereg(local, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    result["polls"] = polls
    if not ok:
        return finish("pre-registration not public; nothing fetched")
    result["fetched_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        table = fetch(REPO_RAW + TABLE_PATH)
        result["table_sha256"] = sha256(table)
        trials = read_table(table)
    except Exception as e:  # reported; gate A1 fails
        result["table_error"] = repr(e)[:200]
        trials = []
    result["gates"]["A1_table"] = table_ok(trials)
    if not result["gates"]["A1_table"]:
        return finish("gate failed; nothing fetched from the archive")

    boundary = boundary_ids(trials)
    start = clock()
    complete = True
    pre, first, pages, page_rows, cache = {}, {}, {}, [], {}
    counts = {"cdx_queries": 0, "cdx_errors": 0, "downloaded": 0, "download_errors": 0}
    cdx_info = {}

    def late():
        return clock() - start > DEADLINE_SECONDS

    def page(nct, role, c):
        """Marks of one capture (downloaded once), recorded in the page table."""
        key = (c["ts"], c["original"])
        if key not in cache:
            if counts["downloaded"] + counts["download_errors"]:
                sleep(DOWNLOAD_PAUSE)
            try:
                data = fetch(WAYBACK % (c["ts"], c["original"]))
                m = classify(data, nct)
                m["digest_match"] = wayback_digest(data) == c["digest"]
                counts["downloaded"] += 1
            except Exception as e:  # a failed download is listed and left out
                m = {"error": repr(e)[:200]}
                counts["download_errors"] += 1
            cache[key] = m
        m = cache[key]
        row = dict(c, nct_id=nct, role=role, downloaded="error" not in m, **m)
        page_rows.append(row)
        return None if "error" in m else dict(m, ts=c["ts"], nct_id=nct)

    for t in trials:
        nct = t["nct_id"]
        rows, info = [], []
        for p in prefixes(nct, nct in boundary):
            if late():
                complete = False
                break
            if counts["cdx_queries"]:
                sleep(CDX_PAUSE)
            counts["cdx_queries"] += 1
            try:
                got, done = cdx_rows(p, fetch)
                rows.extend(got)
                info.append(len(got))
                complete = complete and done
            except Exception as e:  # an unanswered query makes the run incomplete
                counts["cdx_errors"] += 1
                info.append(repr(e)[:100])
                complete = False
        caps = captures(rows)
        cdx_info[nct] = {"rows": info, "captures_200": len(caps)}
        pre[nct] = None
        for c in pre_candidates(caps):
            if late():
                complete = False
                break
            m = page(nct, "pre", c)
            if m and m["usable"]:
                pre[nct] = m
                break
        if nct in boundary:
            got = []
            for c in boundary_plan(caps):
                if late():
                    complete = False
                    break
                m = page(nct, "boundary", c)
                if m:
                    got.append(m)
            pages[nct] = got
            usable = [m for m in got if m["usable"]]
            first[nct] = min(usable, key=lambda m: m["ts"]) if usable else None

    write_pages(os.path.join(args.out_dir, "washu-history-pages.csv"), page_rows)
    result.update(counts)
    result.update({"trials": len(trials), "boundary": boundary, "cdx": cdx_info,
                   "elapsed_seconds": int(clock() - start),
                   "pre_pages": {n: [m["ts"], wording(m)] for n, m in sorted(pre.items()) if m}})
    graded = grade(trials, pre, first, complete)
    result["gates"].update(graded.pop("gates"))
    result.update(graded)
    result["described"] = described(trials, pre, pages)
    if result["predictions"] is None:
        return finish("gate failed; not graded")
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
