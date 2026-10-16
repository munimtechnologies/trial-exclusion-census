"""phone_requirement: within telephone trials, does naming a phone go with naming hearing loss?

phone_matched found that telephone-delivered no-phase trials name a hearing wording 2.45 times as
often as other trials of the same condition, and the S2 reading found that 13 of 20 non-VA
telephone trials that name hearing also name a phone somewhere in their criteria. This compares,
among non-VA telephone trials only, those whose criteria name a phone with those whose criteria
don't, in phone_matched's six strata, with va_matched's Mantel-Haenszel ratio. HP1: the hearing
family's interval lies above 1. HP2: hearing's ratio is above visual's and every kept control's.
Fixed in results/phone-check/PREREG-PHONE-REQUIREMENT.md before any phrase was counted.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import sys
import time

import phone_matched as pm
import trend_check as tc
import va_matched as vm

__version__ = "0.1.0"

COUNTS = "results/phone-check/phone-requirement-counts.json"
# The sponsor clause of the S2 reading (test_phone_hearing_read.NOT_VA).
NOT_VA = "NOT AREA[LeadSponsorName](VA OR Veteran OR Veterans)"
# The registry search treats phone and telephone as one word here too (1,890 of 7,420 base trials
# for each wording on 2026-10-16), so this also finds phone follow-up and app access.
REQUIREMENT = "AREA[EligibilityCriteria](phone OR telephone)"
WORDINGS = ["phone", "telephone", "(phone OR telephone)"]
STRATA = pm.STRATA
PHRASES = pm.PHRASES
HEARING = pm.HEARING
VISUAL = pm.VISUAL


def term(i, phrase=None, required=False):
    """The query.term for one count in stratum i: non-VA no-phase telephone trials, all years.

    With required=True, only those whose criteria name a phone (the phone arm).
    """
    parts = [pm.term(i, phrase, phone=True), NOT_VA]
    if required:
        parts.append(REQUIREMENT)
    return " AND ".join(parts)


def wording_term(wording=None):
    """The whole base (every stratum at once), with one wording of the requirement if given."""
    parts = ["AREA[StudyType]INTERVENTIONAL", "AREA[Phase]NA", pm.PHONE,
             "NOT AREA[ConditionSearch](%s)" % vm.OWN, NOT_VA]
    if wording:
        parts.append("AREA[EligibilityCriteria]" + wording)
    return " AND ".join(parts)


def reading_term():
    """S2's query: phone-arm trials of the whole base that name a hearing wording, in API order."""
    return wording_term("(phone OR telephone)") + " AND AREA[EligibilityCriteria]" + tc.criteria(HEARING)


def fetch_counts(phrases=PHRASES, fetch=None, pause=0.5):
    """Every count of the test: the wording check, then trials and matches, phone named and all,
    in each stratum. "registry" is every base trial of the stratum, as in phone_matched's layout."""
    def n(t):
        c = tc.count(t, fetch or tc.fetch_json)
        time.sleep(pause)
        return c

    data = {"fetched": time.strftime("%Y-%m-%d"), "strata": [s for s, _ in STRATA],
            "wordings": {"base": n(wording_term())}, "trials": {}, "phrases": {}}
    for w in WORDINGS:
        data["wordings"][w] = n(wording_term(w))
    for i, (s, _) in enumerate(STRATA):
        data["trials"][s] = {"phone": n(term(i, required=True)), "registry": n(term(i))}
    for p in phrases:
        row = {"kind": vm.kind(p)}
        for i, (s, _) in enumerate(STRATA):
            row[s] = {"phone": n(term(i, p, required=True)), "registry": n(term(i, p))}
        data["phrases"][p] = row
    return data


def checks(data):
    """Sums that must hold on the counting day: the strata cover the base and the phone arm, and
    no count is larger than a count that contains it. Equal wordings are reported, not required."""
    w, t = data["wordings"], data["trials"]
    return {
        "strata_add_up_to_base": sum(t[s]["registry"] for s in data["strata"]) == w["base"],
        "strata_add_up_to_phone_arm":
            sum(t[s]["phone"] for s in data["strata"]) == w["(phone OR telephone)"],
        "wordings_equal": len({w[x] for x in WORDINGS}) == 1,
        "nested": all(c[s]["phone"] <= c[s]["registry"] <= t[s]["registry"]
                      and c[s]["phone"] <= t[s]["phone"]
                      for c in data["phrases"].values() for s in data["strata"]),
    }


def rows(data):
    return pm.rows(data)


def verdicts(rs):
    """HP1 and HP2, defined as in phone_matched."""
    return pm.verdicts(rs)


def markdown(data):
    def f(v):
        return "" if v is None else str(v)

    rs = rows(data)
    lines = ["| Stratum | Phone named | Not named |", "|---|---|---|"]
    for s in data["strata"]:
        t = data["trials"][s]
        lines.append("| %s | %s | %s |" % (s, t["phone"], t["registry"] - t["phone"]))
    lines += ["", "Times as often in telephone trials whose criteria name a phone as in those whose "
              "criteria don't, same condition (* = control left out, fewer than %d phone-arm "
              "matches expected):" % vm.MIN_EXPECTED, "",
              "| Phrase | Kind | Phone-arm matches | Expected | Matched (MH) | 95% interval | Unmatched | "
              + " | ".join(data["strata"]) + " |",
              "|---|---|---|---|---|---|---|" + "---|" * len(data["strata"])]
    for r in rs:
        lines.append("| %s | %s | %s | %s | %s%s | %s-%s | %s | %s |" % (
            r["phrase"], r["kind"], r["va"], r["expected"], f(r["mh"]), "" if r["kept"] else "*",
            f(r["low"]), f(r["high"]), f(r["crude"]),
            " | ".join(f(r["strata"][s]) for s in data["strata"])))
    v = verdicts(rs)
    t = vm.test(rs)
    lines += ["", "HP1 (hearing interval above 1): %s. HP2 (hearing above visual and every kept "
              "control, %d rivals, chance 1 in %d): %s." % (
                  "holds" if v["HP1"] else "does not hold", v["rivals"], v["rivals"] + 1,
                  "holds" if v["HP2"] else "does not hold"),
              "", "S1 (families against %d kept controls): rank sum %s, p = %s." % (
                  t["controls"], f(t["rank_sum"]), f(t["p"]))]
    if "wordings" in data:
        c = checks(data)
        lines += ["", "Checks: " + ", ".join("%s %s" % (k, "yes" if ok else "NO") for k, ok in c.items())
                  + "."]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--counts", default=COUNTS, help="the saved counts (JSON)")
    ap.add_argument("--fetch", action="store_true",
                    help="count live from the registry (160 small requests) into --counts first")
    ap.add_argument("--json", help="also write the ratios, the checks and the verdicts to this file")
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
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "rows": rs, "verdicts": verdicts(rs),
                       "s1": vm.test(rs), "checks": checks(data) if "wordings" in data else None},
                      f, indent=1)
    print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
