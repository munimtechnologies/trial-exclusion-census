"""va_matched: do VA trials still name disability more often within the same conditions?

sponsor_check found that VA-led trials name cognitive, hearing and visual disability in their
eligibility criteria 2 to 2.7 times as often as the registry, within no-phase trials. VA trials
study different conditions (PTSD, substance use, pain), so this compares VA-led and other
no-phase trials condition by condition. Five disjoint condition strata (each leaves out the
earlier ones and every trial whose own condition is cognitive, brain injury, stroke, hearing or
vision), a Mantel-Haenszel ratio of shares across them for each phrase, and the exact rank test
of trend_check: the three families against non-disability controls. Each control is counted
without the trials that study that condition. Fixed in results/sponsor-check/PREREG-VA-MATCHED.md
before any phrase was counted in these strata.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import math
import sys
import time

import sponsor_check as sc
import trend_check as tc

__version__ = "0.1.0"

COUNTS = "results/sponsor-check/va-matched-counts.json"
# Priority order: a trial goes to the first stratum whose condition it matches.
STRATA = [
    ("ptsd", "PTSD"),
    ("substance use", '"substance use" OR alcohol OR opioid OR smoking OR tobacco'),
    ("depression", "depression"),
    ("pain", "pain"),
    ("cardiometabolic", 'diabetes OR "heart failure" OR hypertension OR coronary'),
]
# Trials whose own condition is a family's are left out of every stratum (sponsor_check's terms,
# plus brain injury and stroke).
OWN = ('cognitive OR dementia OR alzheimer OR "brain injury" OR stroke OR hearing OR deafness OR '
       'tinnitus OR ear OR vision OR visual OR eye OR blindness OR retina OR retinal OR macular OR '
       'glaucoma')
# Controls: the trend-check controls named in at least 2,000 no-phase registry trials (all years,
# prereg-v0.3-counts.json), each with the condition whose own trials are left out of its count.
CONTROLS = {
    "pregnant": "pregnancy", "hepatitis": "hepatitis", "allergy": "allergy",
    "migraine": "migraine", "osteoporosis": "osteoporosis", "claustrophobia": "claustrophobia",
    "celiac": "celiac", "hernia": "hernia",
}
PHRASES = list(tc.FAMILIES) + list(CONTROLS) + tc.REFERENCE
MIN_EXPECTED = 5
MIN_CONTROLS = 4


def kind(phrase):
    if phrase in tc.FAMILIES:
        return "family"
    return "control" if phrase in CONTROLS else "reference"


def term(i, phrase=None, va=False):
    """The query.term for one count in stratum i (no-phase interventional trials, all years)."""
    parts = ["AREA[StudyType]INTERVENTIONAL", "AREA[Phase]NA"]
    if va:
        parts.append(sc.SPONSORS["va"])
    if phrase:
        parts.append("AREA[EligibilityCriteria]" + tc.criteria(phrase))
    parts.append("AREA[ConditionSearch](%s)" % STRATA[i][1])
    nots = [c for _, c in STRATA[:i]] + [OWN] + ([CONTROLS[phrase]] if phrase in CONTROLS else [])
    parts.append("NOT AREA[ConditionSearch](%s)" % " OR ".join(nots))
    return " AND ".join(parts)


def fetch_counts(phrases=PHRASES, fetch=None, pause=0.5):
    """Every count of the test: trials and matches, VA-led and registry, in each stratum."""
    def n(*args, **kw):
        c = tc.count(term(*args, **kw), fetch or tc.fetch_json)
        time.sleep(pause)
        return c

    data = {"fetched": time.strftime("%Y-%m-%d"), "strata": [s for s, _ in STRATA],
            "trials": {}, "phrases": {}}
    for i, (s, _) in enumerate(STRATA):
        data["trials"][s] = {"va": n(i, va=True), "registry": n(i)}
    for p in phrases:
        row = {"kind": kind(p)}
        for i, (s, _) in enumerate(STRATA):
            row[s] = {"va": n(i, p, va=True), "registry": n(i, p)}
        data["phrases"][p] = row
    return data


def cells(data, phrase):
    """(VA matches, VA trials, other matches, other trials) per stratum; other = registry - VA."""
    out = []
    for s in data["strata"]:
        t, c = data["trials"][s], data["phrases"][phrase][s]
        out.append((c["va"], t["va"], c["registry"] - c["va"], t["registry"] - t["va"]))
    return out


def mh(cs, z=1.96):
    """Mantel-Haenszel ratio of shares across strata, with the Greenland-Robins 95% interval."""
    r = s = v = 0.0
    for a, n1, b, n0 in cs:
        big = n1 + n0
        if not n1 or not n0:
            continue
        r += a * n0 / big
        s += b * n1 / big
        v += (n1 * n0 * (a + b) - a * b * big) / big ** 2
    if not r or not s:
        return (0.0 if s else None), None, None
    est = r / s
    se = math.sqrt(v / (r * s))
    return (round(est, 2), round(math.exp(math.log(est) - z * se), 2),
            round(math.exp(math.log(est) + z * se), 2))


def crude(cs):
    """The same ratio with the strata pooled (no matching), for comparison."""
    a, n1, b, n0 = (sum(c[i] for c in cs) for i in range(4))
    return sc.share_ratio(a, n1, b, n0)


def expected(cs):
    """VA matches expected if VA trials named the phrase as often as the others in each stratum."""
    return round(sum(n1 * b / n0 for _, n1, b, n0 in cs if n0), 1)


def rows(data):
    out = []
    for p, c in data["phrases"].items():
        cs = cells(data, p)
        est, lo, hi = mh(cs)
        e = expected(cs)
        out.append({"phrase": p, "kind": c["kind"], "mh": est, "low": lo, "high": hi,
                    "crude": crude(cs), "va": sum(x[0] for x in cs), "expected": e,
                    "kept": c["kind"] != "control" or e >= MIN_EXPECTED,
                    "strata": {s: sc.share_ratio(*x) for s, x in zip(data["strata"], cs)}})
    return out


def test(rs):
    """HV1's test: the families' MH ratios against the kept controls' (exact one-sided rank sum)."""
    xs = [r["mh"] for r in rs if r["kind"] == "family" and r["mh"] is not None]
    controls = [r for r in rs if r["kind"] == "control" and r["mh"] is not None]
    ys = [r["mh"] for r in controls if r["kept"]]
    rank_sum, p = tc.rank_test(xs, ys)
    return {"families": len(xs), "controls": len(ys),
            "left_out": [r["phrase"] for r in controls if not r["kept"]],
            "testable": len(ys) >= MIN_CONTROLS, "control_max": max(ys) if ys else None,
            "rank_sum": rank_sum, "p": p}


def verdicts(rs, t):
    """HV1: testable and p < 0.05. HV2: the cognitive family's interval lies above 1."""
    cog = next((r for r in rs if r["phrase"] == "cognitive (all wordings)"), None)
    return {"HV1": bool(t["testable"] and t["p"] is not None and t["p"] < 0.05),
            "HV2": bool(cog and cog["low"] is not None and cog["low"] > 1)}


def markdown(data):
    def f(v):
        return "" if v is None else str(v)

    rs = rows(data)
    lines = ["| Stratum | VA trials | Other trials |", "|---|---|---|"]
    for s in data["strata"]:
        t = data["trials"][s]
        lines.append("| %s | %s | %s |" % (s, t["va"], t["registry"] - t["va"]))
    lines += ["", "Times as often in VA-led trials as in other trials of the same condition "
              "(* = control left out, fewer than %d VA matches expected):" % MIN_EXPECTED, "",
              "| Phrase | Kind | VA matches | Expected | Matched (MH) | 95% interval | Unmatched | "
              + " | ".join(data["strata"]) + " |",
              "|---|---|---|---|---|---|---|" + "---|" * len(data["strata"])]
    for r in rs:
        lines.append("| %s | %s | %s | %s | %s%s | %s-%s | %s | %s |" % (
            r["phrase"], r["kind"], r["va"], r["expected"], f(r["mh"]), "" if r["kept"] else "*",
            f(r["low"]), f(r["high"]), f(r["crude"]),
            " | ".join(f(r["strata"][s]) for s in data["strata"])))
    t = test(rs)
    v = verdicts(rs, t)
    lines += ["", "| Test | Families | Controls | Largest control | Rank sum | p |",
              "|---|---|---|---|---|---|",
              "| HV1: families against controls, matched | %s | %s | %s | %s | %s |" % (
                  t["families"], t["controls"], f(t["control_max"]), f(t["rank_sum"]), f(t["p"])),
              "", "HV1 (p < 0.05 with at least %d controls): %s. HV2 (cognitive interval above 1): %s." % (
                  MIN_CONTROLS, "holds" if v["HV1"] else ("does not hold" if t["testable"] else "not testable"),
                  "holds" if v["HV2"] else "does not hold")]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--counts", default=COUNTS, help="the saved counts (JSON)")
    ap.add_argument("--fetch", action="store_true",
                    help="count live from the registry (about 130 small requests) into --counts first")
    ap.add_argument("--json", help="also write the ratios and the test to this file")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args(argv)
    if args.fetch:
        data = fetch_counts(pause=args.pause)
        with open(args.counts, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    with open(args.counts, encoding="utf-8") as f:
        data = json.load(f)
    if args.json:
        rs = rows(data)
        t = test(rs)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "rows": rs, "test": t, "verdicts": verdicts(rs, t)},
                      f, indent=1)
    print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
