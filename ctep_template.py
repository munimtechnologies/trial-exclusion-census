"""ctep_template: when did NCI CTEP's protocol template add the representative-consent sentence?

The pre-registered test in results/ctep-template/PREREG.md. The Generic Protocol Template that NCI's
Cancer Therapy Evaluation Program (CTEP) posts for its Experimental Therapeutics Clinical Trials
Network (updated 2026-07-16) ends its inclusion criteria with the stock consent line followed by
"Legally authorized representatives may sign and give informed consent on behalf of study
participants", the sentence results/washu-switch looks for in Washington University's trials. This
script dates when the template gained that sentence from the Internet Archive's copies:

  1. waits until results/ctep-template/PREREG.md is on the repository's main branch and main's
     ctep_template.py is byte for byte this file (gives up after about an hour);
  2. fetches today's template as a positive control for the text extraction;
  3. lists every archived capture of a Word protocol template under CTEP's two document folders,
     downloads each distinct file once, marks the wordings, and grades T1-T4.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import base64
import csv
import datetime
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
import zipfile

__version__ = "0.1.0"

REPO_RAW = "https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/main/"
PREREG_PATH = "results/ctep-template/PREREG.md"
SCRIPT_PATH = "ctep_template.py"
LIVE_URL = ("https://dctd.cancer.gov/research/ctep-trials/trial-development/"
            "etctn-protocol-template.docx")
CDX = "https://web.archive.org/cdx/search/cdx"
CDX_FIELDS = "timestamp,original,statuscode,digest,mimetype"
CDX_LIMIT = 20000
MAX_CDX_PAGES = 20
WAYBACK = "https://web.archive.org/web/%sid_/%s"
USER_AGENT = "ctep_template/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__

# Pre-registered (PREREG.md). Changing any of these after the fetch voids the test.
PREFIXES = ("ctep.cancer.gov/protocoldevelopment/docs/",
            "dctd.cancer.gov/research/ctep-trials/trial-development/")
EXCLUDE_WORDS = ("consent", "icd", "worksheet")
MAX_DOWNLOADS = 150
MIN_USABLE = 4
MAX_BRACKET_DAYS = 730
T1_EARLIEST = "20200101"
T1_LATEST = "20231231"
ADJACENT_CHARS = 300
NEAR_CHARS = 500

TRIES = 40
PAUSE = 90
DOWNLOAD_PAUSE = 5
OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
DOCX_PART = re.compile(r"word/(?:document|header\d*|footer\d*)\.xml")

# The stock line: "Ability to understand and the willingness to sign a written informed consent
# document".
STOCK = re.compile(r"\bability\s+to\s+understand\s+and\s+(?:the\s+)?willingness\s+to\s+sign\s+"
                   r"an?\s+(?:[\w-]+\s+){0,3}?informed\s+consent\s+document", re.I)
# The WashU clause and the sentence, exactly as in washu_switch.py 0.1.0.
CLAUSE = re.compile(r"\bor\s+that\s+of\s+(?:[\w'/]+\s+){0,3}?legal(?:ly)?[\s-]+"
                    r"(?:authori[sz]ed|acceptable)[\s-]+representatives?\b", re.I)
SENTENCE = re.compile(r"\blegal(?:ly)?[\s-]+authori[sz]ed[\s-]+representatives?\s+"
                      r"(?:\(LARs?\)\s+)?may\s+sign\s+and\s+give\s+(?:written\s+)?"
                      r"informed\s+consent\b", re.I)
# Any named representative: "legally authorized/acceptable representative(s)" or "LAR(s)".
LAR = re.compile(r"(?i:\blegal(?:ly)?[\s-]+(?:authori[sz]ed|acceptable)[\s-]+representatives?\b)"
                 r"|\bLARs?\b")
VERSION_DATE = re.compile(r"Version\s+Date:?\s*([A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4})")


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


def xml_text(xml):
    """Visible text of a WordprocessingML part: deleted text and field codes dropped."""
    xml = re.sub(r"<w:(delText|instrText)\b[^>]*>.*?</w:\1>", "", xml, flags=re.S)
    xml = re.sub(r"</w:p>|<w:br\b[^>]*/>|<w:tab\b[^>]*/>|<w:cr\b[^>]*/>", " ", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml))


def docx_text(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = sorted(n for n in z.namelist() if DOCX_PART.fullmatch(n))
        return clean(" ".join(xml_text(z.read(n).decode("utf-8", "replace")) for n in names))


def doc_text(data):
    """Text runs of a legacy .doc: its bytes read as UTF-16 (both alignments) and as cp1252."""
    return clean(" | ".join((data.decode("utf-16-le", "ignore"),
                             data[1:].decode("utf-16-le", "ignore"),
                             data.decode("cp1252", "ignore"))))


def classify(data):
    if data[:2] == b"PK":
        kind = "docx"
        try:
            text = docx_text(data)
        except Exception:  # a broken or truncated archive is reported, never graded
            kind, text = "bad-docx", ""
    elif data[:8] == OLE:
        kind, text = "doc", doc_text(data)
    else:
        kind, text = "other", ""
    stocks = [m.end() for m in STOCK.finditer(text)]
    sents = [m.start() for m in SENTENCE.finditer(text)]
    return {"kind": kind, "chars": len(text), "usable": bool(stocks),
            "sentence": bool(sents), "clause": bool(CLAUSE.search(text)),
            "adjacent": any(0 <= s - e <= ADJACENT_CHARS for e in stocks for s in sents),
            "lar_near": any(bool(LAR.search(text, e, e + NEAR_CHARS)) for e in stocks),
            "version_dates": sorted(set(VERSION_DATE.findall(text)))[:5],
            "sha256": sha256(data), "bytes": len(data)}


def template_name(original):
    """The lower-case file name if the URL is a Word protocol template, else None."""
    path = urllib.parse.urlsplit(original).path
    name = urllib.parse.unquote(path.rsplit("/", 1)[-1]).lower()
    if (name.endswith((".doc", ".docx")) and "protocol" in name and "template" in name
            and not any(w in name for w in EXCLUDE_WORDS)):
        return name
    return None


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
    out = []
    for r in rows:
        if not template_name(r.get("original", "")):
            continue
        status, mime = r.get("statuscode"), r.get("mimetype")
        if status == "200" or mime == "warc/revisit":
            out.append({"ts": r["timestamp"], "original": r["original"], "digest": r["digest"],
                        "fetchable": status == "200"})
    return sorted(out, key=lambda c: (c["ts"], c["original"]))


def plan(caps):
    """One capture per distinct file: the earliest downloadable capture of each digest."""
    first = {}
    for c in caps:
        if c["fetchable"] and c["digest"] not in first:
            first[c["digest"]] = c
    return sorted(first.values(), key=lambda c: (c["ts"], c["original"]))


def day(ts):
    return datetime.date(int(ts[:4]), int(ts[4:6]), int(ts[6:8]))


def bracket(caps, files):
    """(last capture without the sentence before the first with it, first with it, usable)."""
    usable = [c for c in caps if c["digest"] in files and files[c["digest"]]["usable"]]
    with_ts = [c["ts"] for c in usable if files[c["digest"]]["sentence"]]
    if not with_ts:
        return None, None, usable
    first_with = min(with_ts)
    before = [c["ts"] for c in usable
              if not files[c["digest"]]["sentence"] and c["ts"] < first_with]
    return (max(before) if before else None), first_with, usable


def grade(caps, files, live):
    last_without, first_with, usable = bracket(caps, files)
    used = sorted({c["digest"] for c in usable})
    g = {"G1_live_control": bool(live and live["usable"] and live["sentence"]
                                 and live["adjacent"]),
         "G2_usable": len(used) >= MIN_USABLE,
         "G3_both_sides": bool(first_with and last_without)}
    r = {"gates": g, "usable_files": len(used), "usable_captures": len(usable),
         "last_without": last_without, "first_with": first_with,
         "bracket_days": (day(first_with) - day(last_without)).days
         if g["G3_both_sides"] else None,
         "without_after_first_with": sorted({c["original"] for c in usable if first_with
                                             and c["ts"] > first_with
                                             and not files[c["digest"]]["sentence"]}),
         "predictions": None}
    if not all(g.values()):
        return r
    narrow = r["bracket_days"] <= MAX_BRACKET_DAYS
    g["G4_bracket_narrow"] = narrow
    with_s = [files[d] for d in used if files[d]["sentence"]]
    without = [files[d] for d in used if not files[d]["sentence"]]
    r["predictions"] = {
        "T1": (last_without[:8] >= T1_EARLIEST and first_with[:8] <= T1_LATEST)
        if narrow else None,
        "T2": not any(files[d]["clause"] for d in used) and not live["clause"],
        "T3": all(f["adjacent"] for f in with_s),
        "T4": not any(f["lar_near"] for f in without),
    }
    return r


def wait_for_prereg(local_script, fetch=fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md and this exact script, else (False, tries)."""
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            script = fetch(REPO_RAW + SCRIPT_PATH + "?n=%d" % i)
            if b"T1" in prereg and normalize(script) == normalize(local_script):
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


def file_rows(todo, caps, files):
    out = []
    for c in todo:
        f = files.get(c["digest"])
        seen = [x["ts"] for x in caps if x["digest"] == c["digest"]]
        row = {"digest": c["digest"], "first_ts": min(seen), "last_ts": max(seen),
               "captures": len(seen), "original": c["original"], "downloaded": f is not None}
        if f:
            row.update(f)
        out.append(row)
    return out


def result_text(result):
    lines = ["ctep_template %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    live = result.get("live")
    if live:
        lines.append("live (%s): kind %s, usable %s, sentence %s, adjacent %s, clause %s, "
                     "lar_near %s" % (result.get("live_source"), live["kind"], live["usable"],
                                      live["sentence"], live["adjacent"], live["clause"],
                                      live["lar_near"]))
    for p, c in sorted((result.get("cdx") or {}).items()):
        lines.append("cdx %s: %s" % (p, c))
    if "template_captures" in result:
        lines.append("template captures %d, distinct files %d, downloaded %d, usable files %s, "
                     "usable captures %s" % (result["template_captures"],
                                             result["distinct_files"], result["downloaded"],
                                             result.get("usable_files"),
                                             result.get("usable_captures")))
        lines.append("bracket: last without %s, first with %s, days %s; without after first "
                     "with: %d urls" % (result.get("last_without"), result.get("first_with"),
                                        result.get("bracket_days"),
                                        len(result.get("without_after_first_with") or [])))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    for f in (result.get("files") or [])[:80]:
        name = f["original"].rsplit("/", 1)[-1]
        if f["downloaded"]:
            lines.append("  %s..%s x%d %s %s usable=%s sentence=%s clause=%s lar_near=%s %s" % (
                f["first_ts"][:8], f["last_ts"][:8], f["captures"], name, f["kind"],
                f["usable"], f["sentence"], f["clause"], f["lar_near"],
                "; ".join(f["version_dates"])))
        else:
            lines.append("  %s..%s x%d %s not downloaded" % (
                f["first_ts"][:8], f["last_ts"][:8], f["captures"], name))
    return "\n".join(lines)


def write_captures(path, caps, files):
    cols = ["ts", "original", "digest", "fetchable", "downloaded", "kind", "usable", "sentence",
            "clause", "adjacent", "lar_near"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for c in caps:
            got = files.get(c["digest"]) or {}
            row = dict(c, downloaded=bool(got), **{k: got.get(k, "") for k in cols[5:]})
            w.writerow([row[k] for k in cols])


def main(argv=None, fetch=fetch_bytes, sleep=time.sleep):
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
        print("ctep_template: %s" % status)
        return 0 if status == "graded" else 2

    ok, polls = wait_for_prereg(local, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    result["polls"] = polls
    if not ok:
        return finish("pre-registration not public; nothing fetched")
    result["fetched_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    live = None
    for source, url in (("direct", LIVE_URL), ("archive", WAYBACK % ("2026", LIVE_URL))):
        try:
            live = classify(fetch(url))
            result["live_source"] = source
            break
        except Exception as e:  # the archived copy is the fallback control
            result.setdefault("live_errors", []).append(repr(e)[:200])
    result["live"] = live
    rows, result["cdx"] = [], {}
    for p in PREFIXES:
        try:
            got, complete = cdx_rows(p, fetch)
            result["cdx"][p] = {"rows": len(got), "complete": complete}
            rows.extend(got)
        except Exception as e:  # reported; the gates decide whether enough is left
            result["cdx"][p] = {"error": repr(e)[:200]}
    caps = captures(rows)
    todo = plan(caps)
    files, errors = {}, []
    for i, c in enumerate(todo[:MAX_DOWNLOADS]):
        if i:
            sleep(DOWNLOAD_PAUSE)
        try:
            data = fetch(WAYBACK % (c["ts"], c["original"]))
        except Exception as e:  # a failed download is listed and left out
            errors.append([c["ts"], c["original"], repr(e)[:200]])
            continue
        f = classify(data)
        f["digest_match"] = wayback_digest(data) == c["digest"]
        files[c["digest"]] = f
    result.update({"template_captures": len(caps), "distinct_files": len(todo),
                   "downloaded": len(files), "download_errors": errors,
                   "files": file_rows(todo, caps, files)})
    write_captures(os.path.join(args.out_dir, "ctep-template-captures.csv"), caps, files)
    graded = grade(caps, files, live)
    result["gates"].update(graded.pop("gates"))
    result.update(graded)
    if result["predictions"] is None:
        return finish("gate failed; not graded")
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
