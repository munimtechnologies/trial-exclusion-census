"""trend_check: is the rise in disability exclusions more than longer criteria?

Asks the ClinicalTrials.gov API v2 search itself, not the census rules, how many
interventional studies that started in a given year name a phrase in their
eligibility criteria. It does this for disability phrases and for control
phrases that are not about disability. If criteria had only grown longer, the
control phrases would rise as fast as the disability phrases. Each count is
split into no-phase trials (Phase NA) and the rest, because the share of
no-phase trials grew, and for some phrases it is repeated without the trials
that study that condition themselves.

Since 0.2.0 there are rare controls, which start as rare as the disability
phrases (a phrase in half of all trials cannot triple), pooled families that
count every wording of a disability at once (so a change of wording cancels
out), and an exact rank test of the families against the controls.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import itertools
import json
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.2.0"

API = "https://clinicaltrials.gov/api/v2/studies"
DISABILITY = ["cognitive impairment", "dementia", "hearing loss", "wheelchair"]
CONTROLS = ["pregnant", "hepatitis", "allergy"]
RARE_CONTROLS = ["gout", "psoriasis", "tattoo", "migraine", "osteoporosis", "claustrophobia",
                 "lactose intolerance", "sickle cell"]
# Not a control: it measures how full criteria are, and consent capacity is itself a category.
REFERENCE = ["informed consent"]
# Every wording of one kind of disability, searched as one OR query. Bare "blind" is left out
# because it also matches "double-blind" and "blind loop".
FAMILIES = {
    "cognitive (all wordings)": ["cognitive impairment", "dementia", "mental retardation",
                                 "intellectual disability", "cognitively impaired",
                                 "cognitive deficit", "cognitive dysfunction"],
    "hearing (all wordings)": ["hearing loss", "deaf", "deafness", "hearing impairment",
                               "hard of hearing", "hearing impaired"],
    "visual (all wordings)": ["visual impairment", "low vision", "vision loss",
                              "visually impaired", "legally blind"],
}
YEARS = [2008, 2012, 2016, 2020, 2025]
# Trials whose own condition matches are left out of the "not own condition" count.
NOT_OWN_CONDITION = {
    "cognitive impairment": "cognitive OR dementia OR alzheimer",
    "dementia": "cognitive OR dementia OR alzheimer",
    "hearing loss": "hearing OR deafness OR tinnitus OR ear",
}
# share name -> (numerator field, denominator field)
SHARES = {
    "pct": ("matches", "trials"),
    "no_phase_pct": ("no_phase_matches", "no_phase_trials"),
    "other_pct": ("other_matches", "other_trials"),
    "not_own_condition_pct": ("not_own_condition_matches", "trials"),
}
ALL_PHRASES = DISABILITY + list(FAMILIES) + CONTROLS + RARE_CONTROLS + REFERENCE


def kind(phrase):
    if phrase in FAMILIES:
        return "family"
    if phrase in CONTROLS:
        return "control"
    if phrase in RARE_CONTROLS:
        return "rare control"
    if phrase in REFERENCE:
        return "reference"
    return "disability"


def criteria(phrase):
    """The search for one phrase, or for every wording of a family."""
    if phrase in FAMILIES:
        return "(%s)" % " OR ".join('"%s"' % w for w in FAMILIES[phrase])
    return '"%s"' % phrase


def term(year, phrase=None, no_phase=False, not_condition=None):
    """The query.term for one count, in the registry's search syntax."""
    parts = ["AREA[StudyType]INTERVENTIONAL",
             "AREA[StartDate]RANGE[%d-01-01,%d-12-31]" % (year, year)]
    if no_phase:
        parts.append("AREA[Phase]NA")
    if phrase:
        parts.append("AREA[EligibilityCriteria]" + criteria(phrase))
    if not_condition:
        parts.append("NOT AREA[ConditionSearch](%s)" % not_condition)
    return " AND ".join(parts)


def url(t):
    return API + "?" + urllib.parse.urlencode(
        {"query.term": t, "countTotal": "true", "pageSize": 1, "fields": "NCTId"})


def fetch_json(u, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "trend-check/%s (Munim, Inc.)" % __version__})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def count(t, fetch=fetch_json):
    return int(fetch(url(t))["totalCount"])


def pct(k, n):
    return round(100.0 * k / n, 3) if n else None


def run(years=YEARS, phrases=ALL_PHRASES, fetch=None, pause=0.5):
    """One row per year and phrase, with the counts and shares."""
    def n(**kw):
        c = count(term(**kw), fetch or fetch_json)
        time.sleep(pause)
        return c

    rows = []
    for y in years:
        tot, na = n(year=y), n(year=y, no_phase=True)
        for p in phrases:
            k, k_na = n(year=y, phrase=p), n(year=y, phrase=p, no_phase=True)
            row = {"year": y, "phrase": p, "kind": kind(p),
                   "trials": tot, "matches": k,
                   "no_phase_trials": na, "no_phase_matches": k_na,
                   "other_trials": tot - na, "other_matches": k - k_na}
            if p in NOT_OWN_CONDITION:
                row["not_own_condition_matches"] = n(year=y, phrase=p, not_condition=NOT_OWN_CONDITION[p])
            for share, (num, den) in SHARES.items():
                if num in row:
                    row[share] = pct(row[num], row[den])
            rows.append(row)
    return rows


def ratio(a, b, num, den):
    if not a[den] or not b[den] or not a[num]:
        return None
    return round((b[num] / b[den]) / (a[num] / a[den]), 2)


def ratios(rows, first, last):
    """How many times larger each share is in the last year than in the first."""
    by = {(r["year"], r["phrase"]): r for r in rows}
    out = []
    for p in dict.fromkeys(r["phrase"] for r in rows):
        a, b = by.get((first, p)), by.get((last, p))
        if not a or not b:
            continue
        row = {"phrase": p, "kind": a["kind"], "first": first, "last": last}
        for share, (num, den) in SHARES.items():
            if num in a and num in b:
                row[share] = ratio(a, b, num, den)
        out.append(row)
    return out


def midranks(values):
    """Ranks from 1, with tied values sharing their mean rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return ranks


def rank_test(xs, ys):
    """Exact one-sided rank-sum test that xs tend to be larger than ys.

    Returns (rank sum of xs, p): p is the share of all ways to pick len(xs) of the pooled
    values whose rank sum is at least that large. Fine for the dozen or so values here.
    """
    if not xs or not ys:
        return None, None
    ranks = midranks(list(xs) + list(ys))
    observed = sum(ranks[:len(xs)])
    combos = hits = 0
    for c in itertools.combinations(ranks, len(xs)):
        combos += 1
        if sum(c) >= observed - 1e-9:
            hits += 1
    return observed, round(hits / combos, 4)


def family_test(ratio_rows, share):
    """The families against all controls (common and rare), on one share's ratios."""
    xs = [r[share] for r in ratio_rows if r["kind"] == "family" and r.get(share) is not None]
    ys = [r[share] for r in ratio_rows
          if r["kind"] in ("control", "rare control") and r.get(share) is not None]
    rank_sum, p = rank_test(xs, ys)
    return {"share": share, "families": len(xs), "controls": len(ys),
            "control_max": max(ys) if ys else None, "rank_sum": rank_sum, "p": p}


def markdown(rows, first, last):
    def f(v):
        return "" if v is None else str(v)

    lines = ["| Start year | Phrase | Kind | All trials % | No-phase % | Other % | Not own condition % |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["year"], r["phrase"], r["kind"], f(r.get("pct")), f(r.get("no_phase_pct")),
            f(r.get("other_pct")), f(r.get("not_own_condition_pct"))))
    rs = ratios(rows, first, last)
    lines += ["", "Times larger in %d than in %d:" % (last, first), "",
              "| Phrase | Kind | All trials | No-phase | Other | Not own condition |",
              "|---|---|---|---|---|---|"]
    for r in rs:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["phrase"], r["kind"], f(r.get("pct")), f(r.get("no_phase_pct")),
            f(r.get("other_pct")), f(r.get("not_own_condition_pct"))))
    tests = [family_test(rs, s) for s in ("pct", "no_phase_pct", "other_pct")]
    if any(t["families"] and t["controls"] for t in tests):
        lines += ["", "Families against controls (exact one-sided rank-sum test on the ratios):", "",
                  "| Share | Families | Controls | Largest control | Rank sum | p |",
                  "|---|---|---|---|---|---|"]
        for t in tests:
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                t["share"], t["families"], t["controls"], f(t["control_max"]),
                f(t["rank_sum"]), f(t["p"])))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--years", default=",".join(map(str, YEARS)), help="comma-separated start years")
    ap.add_argument("--phrases", default=",".join(ALL_PHRASES),
                    help="comma-separated phrases (family names count every wording)")
    ap.add_argument("--json", help="also write the rows to this file")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args(argv)
    years = [int(y) for y in args.years.split(",")]
    phrases = [p.strip() for p in args.phrases.split(",") if p.strip()]
    rows = run(years, phrases, pause=args.pause)
    if args.json:
        rs = ratios(rows, years[0], years[-1])
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "fetched": time.strftime("%Y-%m-%d"), "rows": rows,
                       "ratios": rs,
                       "family_tests": [family_test(rs, s) for s in ("pct", "no_phase_pct", "other_pct")]},
                      f, indent=1)
    print(markdown(rows, years[0], years[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
