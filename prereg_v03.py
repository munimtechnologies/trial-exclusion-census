"""prereg_v03: the pre-registered trend check v0.3, worked out from its saved counts.

results/trend-check/prereg-v0.3.json fixed the test before anything was counted: the 2025/2008
share ratios of three disability families against 23 controls that are not about disability, in
no-phase trials (H1) and in the other trials (H2), with the exact one-sided rank-sum test of
trend_check, leaving out of a stratum any control with fewer than 20 matches there in 2008.
This reads the counts fetched for it (results/trend-check/prereg-v0.3-counts.json), applies
that rule and runs the tests. It also runs the secondary VA test (VA-led trials against the
registry, no-phase trials only, all 23 controls) and, as a sensitivity check that was not
pre-registered, the trend tests with every control kept.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import sys

import trend_check as tc

__version__ = "0.1.0"

COUNTS = "results/trend-check/prereg-v0.3-counts.json"
STRATA = ("all", "no_phase", "other")
MIN_FIRST = 20


def split(c):
    """Counts for all and no-phase trials, plus the other trials (all minus no-phase)."""
    return {"all": c["all"], "no_phase": c["no_phase"], "other": c["all"] - c["no_phase"]}


def trend_rows(data, min_first=MIN_FIRST):
    """One row per phrase: its last/first share ratio in each stratum, and whether it is kept."""
    first, last = str(data["first"]), str(data["last"])
    t0, t1 = split(data["trials"][first]), split(data["trials"][last])
    rows = []
    for phrase, c in data["phrases"].items():
        a, b = split(c[first]), split(c[last])
        row = {"phrase": phrase, "kind": c["kind"]}
        for s in STRATA:
            row[s] = tc.ratio({"k": a[s], "n": t0[s]}, {"k": b[s], "n": t1[s]}, "k", "n")
            row[s + "_first"] = a[s]
            row[s + "_kept"] = c["kind"] != "control" or a[s] >= min_first
        rows.append(row)
    return rows


def va_rows(data):
    """One row per phrase: how many times larger the VA's no-phase share is than the registry's."""
    va = data["va_no_phase"]
    n_s, n_r = va["trials"]["va"], va["trials"]["registry"]
    rows = []
    for phrase, c in va["phrases"].items():
        r = round((c["va"] / n_s) / (c["registry"] / n_r), 2) if c["registry"] else None
        rows.append({"phrase": phrase, "kind": c["kind"], "va": c["va"],
                     "registry": c["registry"], "ratio": r})
    return rows


def test(rows, key, floor=True):
    """The families against the controls on one column of ratios (exact one-sided rank-sum test)."""
    xs = [r[key] for r in rows if r["kind"] == "family" and r[key] is not None]
    controls = [r for r in rows if r["kind"] == "control" and r[key] is not None]
    kept = [r for r in controls if not floor or r.get(key + "_kept", True)]
    ys = [r[key] for r in kept]
    rank_sum, p = tc.rank_test(xs, ys)
    return {"column": key, "floor": floor, "families": len(xs), "controls": len(ys),
            "left_out": [r["phrase"] for r in controls if r not in kept],
            "control_max": max(ys) if ys else None, "rank_sum": rank_sum, "p": p}


def results(data):
    rows = trend_rows(data)
    return {"H1": test(rows, "no_phase"), "H2": test(rows, "other"), "all": test(rows, "all"),
            "no_phase_every_control": test(rows, "no_phase", floor=False),
            "other_every_control": test(rows, "other", floor=False),
            "va_no_phase": test(va_rows(data), "ratio", floor=False)}


def verdicts(res):
    """H1 holds if no-phase p < 0.05; H2 holds if other-trials p >= 0.05."""
    return {"H1": res["H1"]["p"] is not None and res["H1"]["p"] < 0.05,
            "H2": res["H2"]["p"] is not None and res["H2"]["p"] >= 0.05}


def markdown(data):
    def f(v):
        return "" if v is None else str(v)

    rows = trend_rows(data)
    lines = ["Times larger in %s than in %s (* = left out of that stratum's test, fewer than %d "
             "matches in %s):" % (data["last"], data["first"], MIN_FIRST, data["first"]), "",
             "| Phrase | Kind | All trials | No-phase | Other |", "|---|---|---|---|---|"]
    for r in rows:
        cells = [f(r[s]) + ("" if r[s + "_kept"] else "*") for s in STRATA]
        lines.append("| %s | %s | %s |" % (r["phrase"], r["kind"], " | ".join(cells)))
    res = results(data)
    lines += ["", "| Test | Families | Controls | Largest control | Rank sum | p |",
              "|---|---|---|---|---|---|"]
    for name, key in [("H1: no-phase", "H1"), ("H2: other", "H2"), ("All trials", "all"),
                      ("No-phase, every control", "no_phase_every_control"),
                      ("Other, every control", "other_every_control"),
                      ("VA against registry, no-phase", "va_no_phase")]:
        t = res[key]
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            name, t["families"], t["controls"], f(t["control_max"]), f(t["rank_sum"]), f(t["p"])))
    v = verdicts(res)
    lines += ["", "H1 (no-phase p < 0.05): %s. H2 (other p >= 0.05): %s." % (
        "holds" if v["H1"] else "does not hold", "holds" if v["H2"] else "does not hold")]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--counts", default=COUNTS, help="the saved counts (JSON)")
    ap.add_argument("--json", help="also write the ratios and tests to this file")
    args = ap.parse_args(argv)
    with open(args.counts, encoding="utf-8") as f:
        data = json.load(f)
    if args.json:
        res = results(data)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "trend": trend_rows(data), "va_no_phase": va_rows(data),
                       "tests": res, "verdicts": verdicts(res)}, f, indent=1)
    print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
