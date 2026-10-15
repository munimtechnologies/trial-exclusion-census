"""phone_matched: do telephone-delivered trials name hearing loss more often?

VA-HEARING-READ.md found that VA trials often exclude people with hearing loss because the study
runs by telephone. This asks whether that holds across all sponsors: it compares no-phase trials
whose interventions mention the telephone with other no-phase trials of the same condition, in
the five strata of va_matched plus one stratum for every other condition, with va_matched's
Mantel-Haenszel ratio. HP1: the hearing family's interval lies above 1. HP2: hearing's ratio is
above visual's and every kept control's. Fixed in results/phone-check/PREREG-PHONE-MATCHED.md
before any phrase was counted.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import sys
import time

import trend_check as tc
import va_matched as vm

__version__ = "0.1.0"

COUNTS = "results/phone-check/phone-matched-counts.json"
# The registry search treats telephone and phone as one word (8,657 no-phase trials either way on
# 2026-10-15), so this also finds phone follow-up and mobile-phone apps.
PHONE = "AREA[InterventionSearch]telephone"
# va_matched's five strata, then every trial that matches none of them.
STRATA = vm.STRATA + [("other", None)]
PHRASES = vm.PHRASES
HEARING = "hearing (all wordings)"
VISUAL = "visual (all wordings)"


def term(i, phrase=None, phone=False):
    """The query.term for one count in stratum i (no-phase interventional trials, all years)."""
    parts = ["AREA[StudyType]INTERVENTIONAL", "AREA[Phase]NA"]
    if phone:
        parts.append(PHONE)
    if phrase:
        parts.append("AREA[EligibilityCriteria]" + tc.criteria(phrase))
    if STRATA[i][1]:
        parts.append("AREA[ConditionSearch](%s)" % STRATA[i][1])
    nots = ([c for _, c in STRATA[:i]] + [vm.OWN]
            + ([vm.CONTROLS[phrase]] if phrase in vm.CONTROLS else []))
    parts.append("NOT AREA[ConditionSearch](%s)" % " OR ".join(nots))
    return " AND ".join(parts)


def fetch_counts(phrases=PHRASES, fetch=None, pause=0.5):
    """Every count of the test: trials and matches, telephone and all, in each stratum."""
    def n(*args, **kw):
        c = tc.count(term(*args, **kw), fetch or tc.fetch_json)
        time.sleep(pause)
        return c

    data = {"fetched": time.strftime("%Y-%m-%d"), "strata": [s for s, _ in STRATA],
            "trials": {}, "phrases": {}}
    for i, (s, _) in enumerate(STRATA):
        data["trials"][s] = {"phone": n(i, phone=True), "registry": n(i)}
    for p in phrases:
        row = {"kind": vm.kind(p)}
        for i, (s, _) in enumerate(STRATA):
            row[s] = {"phone": n(i, p, phone=True), "registry": n(i, p)}
        data["phrases"][p] = row
    return data


def as_vm(data):
    """The same counts in va_matched's layout, so its ratios and test apply unchanged."""
    def cell(c):
        return {"va": c["phone"], "registry": c["registry"]}

    out = {"strata": data["strata"], "trials": {s: cell(data["trials"][s]) for s in data["strata"]},
           "phrases": {}}
    for p, row in data["phrases"].items():
        out["phrases"][p] = dict({"kind": row["kind"]}, **{s: cell(row[s]) for s in data["strata"]})
    return out


def rows(data):
    return vm.rows(as_vm(data))


def verdicts(rs):
    """HP1: hearing's interval lies above 1. HP2: hearing's ratio is above visual's and every kept
    control's; by chance it would come first 1 time in (rivals + 1)."""
    by = {r["phrase"]: r for r in rs}
    h = by[HEARING]
    rivals = [by[VISUAL]] + [r for r in rs if r["kind"] == "control" and r["kept"]]
    rivals = [r for r in rivals if r["mh"] is not None]
    return {"HP1": bool(h["low"] is not None and h["low"] > 1),
            "HP2": bool(h["mh"] is not None and rivals and all(h["mh"] > r["mh"] for r in rivals)),
            "rivals": len(rivals)}


def markdown(data):
    def f(v):
        return "" if v is None else str(v)

    rs = rows(data)
    lines = ["| Stratum | Telephone trials | Other trials |", "|---|---|---|"]
    for s in data["strata"]:
        t = data["trials"][s]
        lines.append("| %s | %s | %s |" % (s, t["phone"], t["registry"] - t["phone"]))
    lines += ["", "Times as often in telephone trials as in other trials of the same condition "
              "(* = control left out, fewer than %d telephone matches expected):" % vm.MIN_EXPECTED, "",
              "| Phrase | Kind | Telephone matches | Expected | Matched (MH) | 95% interval | Unmatched | "
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
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--counts", default=COUNTS, help="the saved counts (JSON)")
    ap.add_argument("--fetch", action="store_true",
                    help="count live from the registry (156 small requests) into --counts first")
    ap.add_argument("--json", help="also write the ratios and the verdicts to this file")
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
                       "s1": vm.test(rs)}, f, indent=1)
    print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
