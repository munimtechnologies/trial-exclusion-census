"""consent_phrase_check: does the stock consent line come with another way to consent?

Many trials copy the line "Ability to understand and the willingness to sign a
written informed consent document" into their inclusion criteria. Read alone, it
keeps out adults who could take part with help from a legally authorized
representative, guardian or surrogate. This script downloads, from the
ClinicalTrials.gov API v2, the eligibility text of every study the registry's
search finds for the line, checks the exact wording with a regular expression
(the search also matches near variants), and counts how many of those trials
name another path to consent anywhere in their eligibility text, by start year,
by phase and for adult-only trials.

A mention is not always a permission ("participants who need a legally
authorized representative are excluded" is a mention too), so it keeps a short
snippet around every mention, notes whether it comes before or after the
exclusion heading, and draws a seeded random sample for reading.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.2.0"

API = "https://clinicaltrials.gov/api/v2/studies"
SEARCH = ('AREA[EligibilityCriteria]("ability to understand and the willingness to sign"'
          ' OR "ability to understand and willingness to sign")')
FIELDS = "NCTId,EligibilityCriteria,StartDate,Phase,MinimumAge,StudyType"
STOCK = re.compile(r"\bability\s+to\s+understand\s+and\s+the\s+willingness\s+to\s+sign\b", re.I)
STOCK_LOOSE = re.compile(r"\bability\s+to\s+understand\s+and\s+(?:the\s+)?willingness\s+to\s+sign\b", re.I)
PATHS = {
    "representative": re.compile(
        r"\blegal(?:ly)?[\s-]+(?:authori[sz]ed\s+|acceptable\s+)?representatives?\b"
        r"|\bauthori[sz]ed\s+representatives?\b|\b(?-i:LARs?)\b", re.I),
    "guardian": re.compile(r"\bguardians?\b|\bconservators?\b", re.I),
    "surrogate": re.compile(
        r"\bsurrogates?\b|\bprox(?:y|ies)\b|\bnext\s+of\s+kin\b"
        r"|\bhealth\s*care\s+agents?\b|\bsubstitute\s+decision", re.I),
    "parent": re.compile(r"\bparents?\b", re.I),
    # NCI trials since about 2020 add "Participants with impaired decision-making capacity (IDMC)
    # who have a legally-authorized representative (LAR) ... will also be eligible" (NCT03983824).
    # Bare "IDMC" is left out: it also stands for an independent data monitoring committee.
    "idmc": re.compile(r"\bimpaired\s+decision[\s-]*making\s+capacity\b", re.I),
}
# "parent" and "idmc" are counted on their own: "parent" is the path for children, and the
# IDMC clause names a representative too, so it is already in the adult paths when it allows one.
ADULT_PATHS = ("representative", "guardian", "surrogate")
# Three wordings from NCI's protocol template, oldest to newest as far as known: "must have"
# (NCT03842228), "will also be eligible" (NCT03983824), and the line that follows the stock one
# in CTEP's Generic Protocol Template of 07-16-2026. Within one sentence, so a later
# "will also be eligible" about something else is not counted.
TEMPLATES = {
    "nci_idmc_must_have": re.compile(
        r"\bimpaired\s+decision[\s-]*making\s+capacity\b[^.;]{0,300}?\bcaregiver\s+who\s+gives\s+such\s+consent\b", re.I),
    "nci_idmc_also_eligible": re.compile(
        r"\bimpaired\s+decision[\s-]*making\s+capacity\b[^.;]{0,300}?\bwill\s+also\s+be\s+eligible\b", re.I),
    "nci_lar_may_sign": re.compile(
        r"\blegally\s+authori[sz]ed\s+representatives?\s+may\s+sign\s+and\s+give\s+informed\s+consent\b", re.I),
}
EXCLUSION_HEADING = re.compile(r"exclusion\s+criteria", re.I)
SEED = 20261016


def url(token=None, page_size=1000):
    q = {"query.term": SEARCH, "fields": FIELDS, "pageSize": page_size, "countTotal": "true"}
    if token:
        q["pageToken"] = token
    return API + "?" + urllib.parse.urlencode(q)


def fetch_json(u, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "consent-phrase-check/%s (Munim, Inc.)" % __version__})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def studies(fetch=None, pause=0.5, page_size=1000):
    """Every study the search finds, page by page, and the registry's own total."""
    fetch = fetch or fetch_json
    out, token, total = [], None, None
    while True:
        page = fetch(url(token, page_size))
        if total is None:
            total = page.get("totalCount")
        out.extend(page.get("studies", []))
        token = page.get("nextPageToken")
        if not token:
            return out, total
        time.sleep(pause)


def get(d, *path, default=None):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def years_from_age(text):
    """'18 Years' -> 18.0, '6 Months' -> 0.5; None when missing or not a number."""
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(year|month|week|day|hour|minute)s?\b", text or "", re.I)
    if not m:
        return None
    per_year = {"year": 1, "month": 12, "week": 52, "day": 365, "hour": 8760, "minute": 525600}
    return float(m.group(1)) / per_year[m.group(2).lower()]


def snippet(text, m, width=60):
    a, b = max(0, m.start() - width), min(len(text), m.end() + width)
    return " ".join(text[a:b].split())


def section(hits, cut):
    """Where the mentions are: before the exclusion heading, after it, both, or ''."""
    where = {"inclusion" if m.start() < cut else "exclusion" for m in hits}
    return "both" if len(where) == 2 else (where.pop() if where else "")


def classify(study):
    """One row of flags for one study."""
    p = study.get("protocolSection", {})
    text = get(p, "eligibilityModule", "eligibilityCriteria") or ""
    start = get(p, "statusModule", "startDateStruct", "date") or ""
    phases = get(p, "designModule", "phases") or []
    min_age = years_from_age(get(p, "eligibilityModule", "minimumAge"))
    h = EXCLUSION_HEADING.search(text)
    cut = h.start() if h else len(text)
    row = {"nct_id": get(p, "identificationModule", "nctId"),
           "start_year": int(start[:4]) if start[:4].isdigit() else None,
           "phase": "/".join(phases) or "NONE",
           "study_type": get(p, "designModule", "studyType"),
           "adult_only": None if min_age is None else min_age >= 18,
           "stock_exact": bool(STOCK.search(text)),
           "stock_loose": bool(STOCK_LOOSE.search(text)),
           "has_exclusion_heading": bool(h)}
    snippets = []
    for name, rx in PATHS.items():
        hits = list(rx.finditer(text))
        row[name] = bool(hits)
        row[name + "_section"] = section(hits, cut)
        snippets += ["%s: %s" % (name, snippet(text, m)) for m in hits[:2]]
    row["adult_path"] = any(row[n] for n in ADULT_PATHS)
    row["adult_path_inclusion"] = any(row[n + "_section"] in ("inclusion", "both") for n in ADULT_PATHS)
    for name, rx in TEMPLATES.items():
        row[name] = bool(rx.search(text))
    row["snippets"] = snippets
    return row


def pct(k, n):
    return round(100.0 * k / n, 3) if n else None


def share(rows, flag):
    k = sum(1 for r in rows if r.get(flag))
    return {"trials": len(rows), "with": k, "pct": pct(k, len(rows))}


def summarize(rows, registry_total):
    """Counts over the trials with the exact line, overall and by year and phase."""
    exact = [r for r in rows if r["stock_exact"]]

    def by(key, flag="adult_path"):
        groups = {}
        for r in exact:
            groups.setdefault(r[key], []).append(r)
        return [dict({key: g}, **share(groups[g], flag))
                for g in sorted(groups, key=lambda v: (v is None, str(v)))]

    return {"registry_total": registry_total,
            "downloaded": len(rows),
            "stock_exact": len(exact),
            "stock_loose_only": sum(1 for r in rows if r["stock_loose"] and not r["stock_exact"]),
            "neither": sum(1 for r in rows if not r["stock_loose"]),
            "adult_path": share(exact, "adult_path"),
            "adult_path_inclusion": share(exact, "adult_path_inclusion"),
            "adult_path_adult_only": share([r for r in exact if r["adult_only"]], "adult_path"),
            "paths": {n: share(exact, n)["with"] for n in PATHS},
            "by_year": by("start_year"),
            "by_phase": by("phase"),
            "idmc_by_year": by("start_year", "idmc"),
            "templates": {n: share(exact, n) for n in TEMPLATES},
            "template_by_year": {n: by("start_year", n) for n in TEMPLATES}}


def reading_sample(rows, k=50, seed=SEED):
    """A seeded random sample of trials with the exact line and an adult path, to read by eye."""
    pool = sorted((r for r in rows if r["stock_exact"] and r["adult_path"]), key=lambda r: r["nct_id"])
    return random.Random(seed).sample(pool, min(k, len(pool)))


def markdown(s):
    def f(v):
        return "unknown" if v is None else str(v)

    a, inc, ad = s["adult_path"], s["adult_path_inclusion"], s["adult_path_adult_only"]
    lines = ["# Stock consent line: is another path to consent named?", "",
             "Registry search: %s trials; downloaded %s; exact line in %s; near variant only %s; neither %s." % (
                 f(s["registry_total"]), s["downloaded"], s["stock_exact"], s["stock_loose_only"], s["neither"]),
             "",
             "Of %d trials with the exact line, %d (%s%%) name a legally authorized representative, guardian or"
             " surrogate anywhere in their eligibility text; %d (%s%%) do so before the exclusion heading." % (
                 a["trials"], a["with"], f(a["pct"]), inc["with"], f(inc["pct"])),
             "Adult-only trials (minimum age 18 or more): %d of %d (%s%%)." % (ad["with"], ad["trials"], f(ad["pct"])),
             "",
             "A mention is not always a permission: read the sample in consent-phrase.json before quoting"
             " these as trials that allow a representative.",
             "", "| Start year | Trials | Name another path | % |", "|---|---|---|---|"]
    for r in s["by_year"]:
        lines.append("| %s | %s | %s | %s |" % (f(r["start_year"]), r["trials"], r["with"], f(r["pct"])))
    lines += ["", "| Phase | Trials | Name another path | % |", "|---|---|---|---|"]
    for r in s["by_phase"]:
        lines.append("| %s | %s | %s | %s |" % (r["phase"], r["trials"], r["with"], f(r["pct"])))
    lines += ["", "| Start year | Trials | IDMC clause | % |", "|---|---|---|---|"]
    for r in s["idmc_by_year"]:
        lines.append("| %s | %s | %s | %s |" % (f(r["start_year"]), r["trials"], r["with"], f(r["pct"])))
    lines += ["", "NCI template wording: " + "; ".join(
        "%s %d" % (n, s["templates"][n]["with"]) for n in TEMPLATES) + ".",
        "", "| Start year | Trials | " + " | ".join(TEMPLATES) + " |", "|---|---|" + "---|" * len(TEMPLATES)]
    for i, r in enumerate(s["by_year"]):
        lines.append("| %s | %s | %s |" % (f(r["start_year"]), r["trials"], " | ".join(
            str(s["template_by_year"][n][i]["with"]) for n in TEMPLATES)))
    lines += ["", "Start year is when the trial began; the registry keeps only the current eligibility text,"
              " so a wording may have been added later."]
    return "\n".join(lines)


def write(out_dir, rows, total, sample_size=50):
    s = summarize(rows, total)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "consent-phrase.json"), "w", encoding="utf-8") as f:
        json.dump({"version": __version__, "fetched": time.strftime("%Y-%m-%d"), "search": SEARCH,
                   "summary": s,
                   "reading_sample": [{"nct_id": r["nct_id"], "snippets": r["snippets"]}
                                      for r in reading_sample(rows, sample_size)]}, f, indent=1)
    with open(os.path.join(out_dir, "consent-phrase-trials.csv"), "w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            for r in rows:
                w.writerow(dict(r, snippets=" | ".join(r["snippets"])))
    md = markdown(s)
    with open(os.path.join(out_dir, "CONSENT-PHRASE.md"), "w", encoding="utf-8") as f:
        f.write(md + "\n")
    return s, md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--out-dir", default=".", help="where to write the JSON, CSV and Markdown")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between pages")
    ap.add_argument("--sample", type=int, default=50, help="trials in the reading sample")
    args = ap.parse_args(argv)
    found, total = studies(pause=args.pause)
    _, md = write(args.out_dir, [classify(st) for st in found], total, args.sample)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
