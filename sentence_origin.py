"""sentence_origin: was the representative-consent sentence in registry text before CTEP's template?

The pre-registered test in results/sentence-origin/PREREG.md. results/ctep-spread found 30 trials
whose eligibility text carries "Legally authorized representatives may sign and give informed
consent on behalf of study participants" today and that were first submitted before August 4, 2023,
the date of the first NCI CTEP template version known to carry it. This script reads the Internet
Archive's copies of their ClinicalTrials.gov study pages from before that date:

  1. waits until results/sentence-origin/PREREG.md, results/ctep-spread/ctep-spread-trials.csv and
     main's sentence_origin.py (byte for byte this file) are on the repository's main branch;
  2. for each of the 30 trials (the three early WashU-led trials first, then SWOG-led, then the
     rest), lists its archived study pages and reads its oldest, its newest up to 2022-07-09 and
     its newest up to 2023-08-03 usable pages;
  3. grades S1-S4.

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
PREREG_PATH = "results/sentence-origin/PREREG.md"
SCRIPT_PATH = "sentence_origin.py"
TABLE_PATH = "results/ctep-spread/ctep-spread-trials.csv"
CDX = "https://web.archive.org/cdx/search/cdx"
CDX_FIELDS = "timestamp,original,statuscode,digest"
CDX_LIMIT = 5000
MAX_CDX_PAGES = 5
WAYBACK = "https://web.archive.org/web/%sid_/%s"
USER_AGENT = "sentence_origin/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__
PATHS = ("clinicaltrials.gov/ct2/show/%s", "clinicaltrials.gov/ct2/show/record/%s")
SWOG = "swog cancer research network"

# Pre-registered (PREREG.md). Changing any of these after the fetch voids the test.
TABLE_ROWS = 147
COHORT_SIZE = 30
EARLY_WASHU = ("NCT04462328", "NCT04852328", "NCT05521984")
SWOG_IN_COHORT = 10
CUTOFF_PRE = "20220709"    # last archived date CTEP's template is known to lack the sentence
CUTOFF_EARLY = "20230803"  # the day before the first template version date with it
TRIES = 3
MIN_TEXT = 2000
MIN_USABLE_TRIALS = 15     # A2
MIN_COMPLETE_TRIALS = 27   # A3
DEADLINE_SECONDS = 200 * 60
S1_MIN_GRADED = 6
S2_MIN_GRADED = 4
S3_MIN_GRADED = 4
S4_MIN_GRADED = 2

POLLS = 40
PAUSE = 90
CDX_PAUSE = 2
DOWNLOAD_PAUSE = 4

# The patterns of ctep_template.py 0.1.0 / washu_switch.py 0.1.0, unchanged.
STOCK = re.compile(r"\bability\s+to\s+understand\s+and\s+(?:the\s+)?willingness\s+to\s+sign\s+"
                   r"an?\s+(?:[\w-]+\s+){0,3}?informed\s+consent\s+document", re.I)
CLAUSE = re.compile(r"\bor\s+that\s+of\s+(?:[\w'/]+\s+){0,3}?legal(?:ly)?[\s-]+"
                    r"(?:authori[sz]ed|acceptable)[\s-]+representatives?\b", re.I)
SENTENCE = re.compile(r"\blegal(?:ly)?[\s-]+authori[sz]ed[\s-]+representatives?\s+"
                      r"(?:\(LARs?\)\s+)?may\s+sign\s+and\s+give\s+(?:written\s+)?"
                      r"informed\s+consent\b", re.I)
ELIGIBILITY = re.compile(r"eligibility\s+criteria|inclusion\s+criteria|ages\s+eligible\s+for\s+"
                         r"study|sexes\s+eligible\s+for\s+study", re.I)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def wayback_digest(data):
    """The Internet Archive's digest of a payload: base32 of its SHA-1."""
    return base64.b32encode(hashlib.sha1(data).digest()).decode("ascii")


def normalize(data):
    """Bytes with CRLF turned into LF, so a line-ending change does not count as a difference."""
    return data.replace(b"\r\n", b"\n")


def fetch_bytes(url, tries=3, timeout=90):
    """GET a URL, retrying with a growing pause (longer for the Internet Archive)."""
    base = 10 if "web.archive.org" in url else 2
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                       "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            err = e
            if i + 1 < tries:
                time.sleep(base * (i + 1))
    raise err


def page_text(data):
    """Visible text of an HTML page: scripts, styles and tags dropped, entities decoded."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    s = data.decode("utf-8", "replace")
    s = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def classify(data, nct):
    """Marks of one archived study page. Usable = it names the trial and shows its eligibility."""
    try:
        text = page_text(data)
    except Exception:  # a broken payload is reported, never graded
        text = ""
    usable = (len(text) >= MIN_TEXT and nct.lower() in text.lower()
              and bool(ELIGIBILITY.search(text)))
    return {"usable": usable, "sentence": bool(SENTENCE.search(text)),
            "clause": bool(CLAUSE.search(text)), "stock": bool(STOCK.search(text)),
            "chars": len(text), "bytes": len(data), "sha256": sha256(data)}


def truthy(v):
    return str(v).strip() == "True"


def read_table(data):
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    for r in rows:
        for k in ("nci_linked", "washu_led", "stock", "clause", "in_frame", "anchor"):
            r[k] = truthy(r.get(k))
    return rows


def kind(r):
    """washu, swog or nci (the only groups in the cohort), as the PREREG names them."""
    if r["nct_id"] in EARLY_WASHU or r["group"] == "washu":
        return "washu"
    if r["lead_sponsor"].strip().casefold() == SWOG:
        return "swog"
    return "nci" if r["nci_linked"] else "other"


def cohort(rows):
    """The pre and gap trials, in reading order: early WashU, then SWOG, then the rest."""
    sel = [r for r in rows if r["period"] in ("pre", "gap")]
    rank = {"washu": 0, "swog": 1, "nci": 2, "other": 3}
    return sorted(sel, key=lambda r: (rank[kind(r)], r["nct_id"]))


def table_ok(rows, trials):
    ids = [r["nct_id"] for r in trials]
    return (len(rows) == TABLE_ROWS and len({r["nct_id"] for r in rows}) == TABLE_ROWS
            and len(trials) == COHORT_SIZE and ids[:3] == list(EARLY_WASHU)
            and sum(1 for r in trials if kind(r) == "swog") == SWOG_IN_COHORT
            and all(kind(r) in ("washu", "swog", "nci") for r in trials))


def cdx_rows(prefix, fetch):
    """All status-200 CDX rows under a URL prefix up to CUTOFF_EARLY; (rows, complete)."""
    rows, key = [], None
    for _ in range(MAX_CDX_PAGES):
        params = {"url": prefix, "matchType": "prefix", "output": "json", "fl": CDX_FIELDS,
                  "filter": "statuscode:200", "to": CUTOFF_EARLY, "limit": CDX_LIMIT,
                  "showResumeKey": "true"}
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
    """Status-200 captures on or before CUTOFF_EARLY, oldest first."""
    out = [{"ts": r["timestamp"], "original": r["original"], "digest": r.get("digest", "")}
           for r in rows if r.get("statuscode") == "200" and r["timestamp"][:8] <= CUTOFF_EARLY]
    return sorted(out, key=lambda c: (c["ts"], c["original"]))


def distinct_first(caps):
    """Each distinct page (by digest) at its earliest capture, oldest first."""
    first = {}
    for c in caps:
        first.setdefault(c["digest"], c)
    return sorted(first.values(), key=lambda c: (c["ts"], c["original"]))


def distinct_last(caps, day):
    """Each distinct page at its latest capture on or before day, newest first."""
    last = {}
    for c in caps:
        if c["ts"][:8] <= day:
            last[c["digest"]] = c  # caps are oldest first, so the last one wins
    return sorted(last.values(), key=lambda c: (c["ts"], c["original"]), reverse=True)


def plans(caps):
    """The three page lists tried for a trial, at most TRIES pages each."""
    return {"oldest": distinct_first(caps)[:TRIES],
            "newest_pre": distinct_last(caps, CUTOFF_PRE)[:TRIES],
            "newest_early": distinct_last(caps, CUTOFF_EARLY)[:TRIES]}


def frac_ok(k, n, num, den, at_least):
    return (den * k >= num * n) if at_least else (den * k <= num * n)


def grade(trials, marks, complete):
    """Gates A2-A4 and S1-S4 from each trial's usable pages ({role: page marks or None})."""
    usable = [t for t in trials if any(marks.get(t["nct_id"], {}).values())]
    pages = [p for t in trials for p in marks.get(t["nct_id"], {}).values() if p]
    g = {"A2_usable": len(usable) >= MIN_USABLE_TRIALS,
         "A3_complete": sum(1 for t in trials if complete.get(t["nct_id"])) >= MIN_COMPLETE_TRIALS,
         "A4_stock_seen": any(p["stock"] for p in pages)}

    def pre_pages(n):
        m = marks.get(n, {})
        return [p for p in (m.get("oldest"), m.get("newest_pre"))
                if p and p["ts"][:8] <= CUTOFF_PRE]

    s1_trials = [t["nct_id"] for t in trials if pre_pages(t["nct_id"])]
    s1_hits = [n for n in s1_trials if any(p["sentence"] for p in pre_pages(n))]

    def oldest_share(k):
        sel = [t["nct_id"] for t in trials if kind(t) == k and marks.get(t["nct_id"], {}).get(
            "oldest")]
        hit = [n for n in sel if marks[n]["oldest"]["sentence"]]
        return sel, hit

    s2, s2_hit = oldest_share("swog")
    s3, s3_hit = oldest_share("nci")
    s4 = [n for n in EARLY_WASHU if marks.get(n, {}).get("oldest")]
    s4_hit = [n for n in s4 if marks[n]["oldest"]["sentence"]]
    r = {"gates": g, "usable_trials": len(usable),
         "complete_trials": sum(1 for t in trials if complete.get(t["nct_id"])),
         "S1": {"graded_on": s1_trials, "with_sentence": s1_hits},
         "S2": {"graded_on": s2, "with_sentence": s2_hit},
         "S3": {"graded_on": s3, "with_sentence": s3_hit},
         "S4": {"graded_on": s4, "with_sentence": s4_hit},
         "predictions": None}
    if not all(g.values()):
        return r
    r["predictions"] = {
        "S1": bool(s1_hits) if len(s1_trials) >= S1_MIN_GRADED else None,
        "S2": frac_ok(len(s2_hit), len(s2), 1, 2, True) if len(s2) >= S2_MIN_GRADED else None,
        "S3": frac_ok(len(s3_hit), len(s3), 1, 2, False) if len(s3) >= S3_MIN_GRADED else None,
        "S4": (not s4_hit) if len(s4) >= S4_MIN_GRADED else None,
    }
    return r


def wording(p):
    if not p:
        return "-"
    return "sentence" if p["sentence"] else "clause" if p["clause"] else "neither"


def described(trials, marks):
    """Not graded: per trial, the three pages read; and the earliest page with the sentence."""
    per = {}
    for t in trials:
        m = marks.get(t["nct_id"], {})
        per[t["nct_id"]] = {"kind": kind(t), "submitted": t["submitted"],
                            "pages": {k: [m[k]["ts"][:8], wording(m[k])] if m.get(k) else None
                                      for k in ("oldest", "newest_pre", "newest_early")}}
    with_s = [(p["ts"], n) for n, m in marks.items() for p in m.values() if p and p["sentence"]]
    earliest = min(with_s) if with_s else None
    switched = [n for n, m in sorted(marks.items())
                if m.get("oldest") and m.get("newest_early") and not m["oldest"]["sentence"]
                and m["newest_early"]["sentence"]]
    return {"trials": per, "earliest_sentence_page": [earliest[1], earliest[0]] if earliest
            else None, "gained_before_cutoff": switched}


def wait_for_prereg(local_script, fetch=fetch_bytes, sleep=time.sleep, tries=POLLS, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md, the table and this exact script."""
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            script = fetch(REPO_RAW + SCRIPT_PATH + "?n=%d" % i)
            table = fetch(REPO_RAW + TABLE_PATH + "?n=%d" % i)
            if (b"S1" in prereg and normalize(script) == normalize(local_script)
                    and table.startswith(b"nct_id,")):
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


PAGE_COLS = ["nct_id", "role", "ts", "original", "digest", "downloaded", "digest_match",
             "usable", "sentence", "clause", "stock", "chars", "bytes", "sha256", "error"]


def write_pages(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(PAGE_COLS)
        for r in rows:
            w.writerow([r.get(k, "") for k in PAGE_COLS])


def result_text(result):
    lines = ["sentence_origin %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    if "trials" in result:
        lines.append("trials %d, complete %d, with a usable page %d; cdx queries %d (errors %d), "
                     "pages downloaded %d (errors %d), elapsed %ss" % (
                         result["trials"], result["complete_trials"], result["usable_trials"],
                         result["cdx_queries"], result["cdx_errors"], result["downloaded"],
                         result["download_errors"], result["elapsed_seconds"]))
        for k in ("S1", "S2", "S3", "S4"):
            lines.append("  %s graded on %d, with the sentence %d: %s" % (
                k, len(result[k]["graded_on"]), len(result[k]["with_sentence"]),
                " ".join(result[k]["with_sentence"]) or "-"))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        lines.append("earliest page with the sentence: %s" % (d["earliest_sentence_page"]
                                                              or "none"))
        lines.append("gained it between oldest and newest early page: %s" % (
            " ".join(d["gained_before_cutoff"]) or "none"))
        for n, x in d["trials"].items():
            lines.append("  %s %s %s: %s" % (n, x["kind"], x["submitted"], "; ".join(
                "%s %s" % (k, " ".join(v) if v else "-") for k, v in x["pages"].items())))
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
        print("sentence_origin: %s" % status)
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
        rows = read_table(table)
    except Exception as e:  # reported; gate A1 fails
        result["table_error"] = repr(e)[:200]
        rows = []
    trials = cohort(rows)
    result["gates"]["A1_table"] = table_ok(rows, trials)
    if not result["gates"]["A1_table"]:
        return finish("gate failed; nothing fetched from the archive")

    start = clock()
    marks, complete, page_rows, cdx_info = {}, {}, [], {}
    counts = {"cdx_queries": 0, "cdx_errors": 0, "downloaded": 0, "download_errors": 0}

    def late():
        return clock() - start > DEADLINE_SECONDS

    cache = {}

    def page(nct, role, c):
        """Marks of one capture; a page with a digest already read is not downloaded again."""
        key = (nct, c["digest"]) if c["digest"] else (c["ts"], c["original"])
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
        page_rows.append(dict(c, nct_id=nct, role=role, downloaded="error" not in m, **m))
        return None if "error" in m else dict(m, ts=c["ts"])

    for t in trials:
        nct = t["nct_id"]
        marks[nct] = {"oldest": None, "newest_pre": None, "newest_early": None}
        if late():
            complete[nct] = False
            continue
        rows_, info, done = [], [], True
        for p in PATHS:
            if counts["cdx_queries"]:
                sleep(CDX_PAUSE)
            counts["cdx_queries"] += 1
            try:
                got, whole = cdx_rows(p % nct, fetch)
                rows_.extend(got)
                info.append(len(got))
                done = done and whole
            except Exception as e:  # an unanswered query leaves the trial incomplete
                counts["cdx_errors"] += 1
                info.append(repr(e)[:100])
                done = False
        caps = captures(rows_)
        cdx_info[nct] = {"rows": info, "captures": len(caps)}
        for role, todo in plans(caps).items():
            for c in todo:
                if late():
                    done = False
                    break
                m = page(nct, role, c)
                if m and m["usable"]:
                    marks[nct][role] = m
                    break
        complete[nct] = done and not late()

    write_pages(os.path.join(args.out_dir, "sentence-origin-pages.csv"), page_rows)
    result.update(counts)
    result.update({"trials": len(trials), "order": [t["nct_id"] for t in trials],
                   "cdx": cdx_info, "elapsed_seconds": int(clock() - start),
                   "complete": complete})
    graded = grade(trials, marks, complete)
    result["gates"].update(graded.pop("gates"))
    result.update(graded)
    result["described"] = described(trials, marks)
    if result["predictions"] is None:
        return finish("gate failed; not graded")
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
