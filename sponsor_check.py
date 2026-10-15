"""sponsor_check: do one sponsor's trials name disability more often than the registry does?

Asks the ClinicalTrials.gov API v2 search how many interventional studies of one sponsor
group name each phrase of trend_check in their eligibility criteria, and how many in the
whole registry, and gives the ratio of the two shares. If a sponsor's criteria simply named
everything more often, the control phrases would show the same ratio as the disability
families. Each family is also counted in no-phase trials only (sponsors differ in how many
behavioural and device trials they run) and without the trials that study that condition.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import sys
import time

import trend_check as tc

__version__ = "0.1.0"

# Sponsor groups, in the registry's search syntax. "va" is every federal lead sponsor whose
# name has VA, Veteran or Veterans in it (the VA Office of Research and Development, the
# Department of Veterans Affairs and VA medical centers).
SPONSORS = {
    "va": "AREA[LeadSponsorClass]FED AND AREA[LeadSponsorName](VA OR Veteran OR Veterans)",
    "fed": "AREA[LeadSponsorClass]FED",
    "nih": "AREA[LeadSponsorClass]NIH",
    "industry": "AREA[LeadSponsorClass]INDUSTRY",
}
# Trials whose own condition matches a family are left out of its "not own condition" count.
FAMILY_NOT_OWN = {
    "cognitive (all wordings)": "cognitive OR dementia OR alzheimer",
    "hearing (all wordings)": "hearing OR deafness OR tinnitus OR ear",
    "visual (all wordings)": "vision OR visual OR eye OR blindness OR retina OR retinal OR macular OR glaucoma",
}
PHRASES = list(tc.FAMILIES) + tc.CONTROLS + tc.RARE_CONTROLS + tc.REFERENCE


def term(sponsor=None, phrase=None, no_phase=False, not_condition=None):
    """The query.term for one count over all start years."""
    parts = ["AREA[StudyType]INTERVENTIONAL"]
    if sponsor:
        parts.append(SPONSORS.get(sponsor, sponsor))
    if no_phase:
        parts.append("AREA[Phase]NA")
    if phrase:
        parts.append("AREA[EligibilityCriteria]" + tc.criteria(phrase))
    if not_condition:
        parts.append("NOT AREA[ConditionSearch](%s)" % not_condition)
    return " AND ".join(parts)


def share_ratio(k_s, n_s, k_r, n_r):
    """How many times larger the sponsor's share is than the registry's."""
    if not n_s or not n_r or not k_r:
        return None
    return round((k_s / n_s) / (k_r / n_r), 2)


def run(sponsor, phrases=PHRASES, fetch=None, pause=0.5):
    """One row per phrase: the sponsor's and the registry's counts, shares and their ratio."""
    def n(**kw):
        c = tc.count(term(**kw), fetch or tc.fetch_json)
        time.sleep(pause)
        return c

    tot_s, tot_r = n(sponsor=sponsor), n()
    na_s, na_r = n(sponsor=sponsor, no_phase=True), n(no_phase=True)
    rows = []
    for p in phrases:
        k_s, k_r = n(sponsor=sponsor, phrase=p), n(phrase=p)
        row = {"phrase": p, "kind": tc.kind(p),
               "sponsor_trials": tot_s, "sponsor_matches": k_s,
               "registry_trials": tot_r, "registry_matches": k_r,
               "sponsor_pct": tc.pct(k_s, tot_s), "registry_pct": tc.pct(k_r, tot_r),
               "ratio": share_ratio(k_s, tot_s, k_r, tot_r)}
        if p in tc.FAMILIES:
            j_s, j_r = n(sponsor=sponsor, phrase=p, no_phase=True), n(phrase=p, no_phase=True)
            row.update({"sponsor_no_phase_trials": na_s, "sponsor_no_phase_matches": j_s,
                        "registry_no_phase_trials": na_r, "registry_no_phase_matches": j_r,
                        "no_phase_ratio": share_ratio(j_s, na_s, j_r, na_r)})
            if p in FAMILY_NOT_OWN:
                o_s = n(sponsor=sponsor, phrase=p, not_condition=FAMILY_NOT_OWN[p])
                o_r = n(phrase=p, not_condition=FAMILY_NOT_OWN[p])
                row.update({"sponsor_not_own_condition_matches": o_s,
                            "registry_not_own_condition_matches": o_r,
                            "not_own_condition_ratio": share_ratio(o_s, tot_s, o_r, tot_r)})
        rows.append(row)
    return rows


def family_test(rows):
    """The families against all controls (common and rare), on the sponsor/registry ratios."""
    return tc.family_test(rows, "ratio")


def markdown(rows, sponsor):
    def f(v):
        return "" if v is None else str(v)

    lines = ["Sponsor group: %s (%s trials; registry %s)" % (
        sponsor, rows[0]["sponsor_trials"] if rows else "", rows[0]["registry_trials"] if rows else ""),
        "",
        "| Phrase | Kind | Sponsor % | Registry % | Times larger | No-phase only | Not own condition |",
        "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["phrase"], r["kind"], f(r["sponsor_pct"]), f(r["registry_pct"]), f(r["ratio"]),
            f(r.get("no_phase_ratio")), f(r.get("not_own_condition_ratio"))))
    t = family_test(rows)
    if t["families"] and t["controls"]:
        lines += ["", "Families against controls (exact one-sided rank-sum test on the ratios):", "",
                  "| Families | Controls | Largest control | Rank sum | p |", "|---|---|---|---|---|",
                  "| %s | %s | %s | %s | %s |" % (t["families"], t["controls"], f(t["control_max"]),
                                                 f(t["rank_sum"]), f(t["p"]))]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--sponsor", default="va",
                    help="a group (%s) or any search fragment" % ", ".join(SPONSORS))
    ap.add_argument("--phrases", default=",".join(PHRASES),
                    help="comma-separated phrases (family names count every wording)")
    ap.add_argument("--json", help="also write the rows to this file")
    ap.add_argument("--pause", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args(argv)
    phrases = [p.strip() for p in args.phrases.split(",") if p.strip()]
    rows = run(args.sponsor, phrases, pause=args.pause)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "fetched": time.strftime("%Y-%m-%d"),
                       "sponsor": args.sponsor, "rows": rows, "family_test": family_test(rows)},
                      f, indent=1)
    print(markdown(rows, args.sponsor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
