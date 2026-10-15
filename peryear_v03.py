"""peryear_v03: the per-year secondary of the pre-registered trend check v0.3.

results/trend-check/prereg-v0.3.json named, as a secondary analysis, the share of trials naming
each phrase in every start year from 2008 to 2025 and the least-squares slope of log(share) on
year, with the families' slopes ranked among the controls' by the exact test of trend_check.
This reads the counts fetched for it (results/trend-check/prereg-v0.3-peryear-counts.json: a
reduced set, no-phase trials only, the three families and the controls that the 20-match rule
keeps there) and works out the slopes and the test. Unlike the 2025/2008 ratio of H1, a slope
uses every year, so one odd first or last year moves it less.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import math
import sys

import trend_check as tc

__version__ = "0.1.0"

COUNTS = "results/trend-check/prereg-v0.3-peryear-counts.json"


def slope(years, ks, ns):
    """Least-squares slope of log(k/n) on year; None if a year has no match or no trial."""
    if any(not k for k in ks) or any(not n for n in ns):
        return None
    ys = [math.log(k / n) for k, n in zip(ks, ns)]
    mx, my = sum(years) / len(years), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in years)
    return sum((x - mx) * (y - my) for x, y in zip(years, ys)) / sxx


def rows(data):
    """One row per phrase: its log-share slope and the yearly change it means, in percent."""
    out = []
    for phrase, c in data["phrases"].items():
        b = slope(data["years"], c["counts"], data["trials"])
        out.append({"phrase": phrase, "kind": c["kind"],
                    "slope": None if b is None else round(b, 4),
                    "per_year_pct": None if b is None else round(100 * (math.exp(b) - 1), 1),
                    "shares_pct": [tc.pct(k, n) for k, n in zip(c["counts"], data["trials"])]})
    return out


def test(rs):
    """The families' slopes against the controls' (exact one-sided rank-sum test)."""
    xs = [r["slope"] for r in rs if r["kind"] == "family" and r["slope"] is not None]
    ys = [r["slope"] for r in rs if r["kind"] == "control" and r["slope"] is not None]
    rank_sum, p = tc.rank_test(xs, ys)
    return {"families": len(xs), "controls": len(ys), "control_max": max(ys) if ys else None,
            "rank_sum": rank_sum, "p": p}


def markdown(data):
    def f(v):
        return "" if v is None else str(v)

    rs = sorted(rows(data), key=lambda r: -(r["slope"] if r["slope"] is not None else -1e9))
    lines = ["Slope of log(share) on start year, %d-%d, %s trials (steepest first):" % (
        data["years"][0], data["years"][-1], data.get("stratum", "")), "",
        "| Phrase | Kind | Slope | Change per year | Share %d | Share %d |" % (
            data["years"][0], data["years"][-1]),
        "|---|---|---|---|---|---|"]
    for r in rs:
        lines.append("| %s | %s | %s | %s%% | %s%% | %s%% |" % (
            r["phrase"], r["kind"], f(r["slope"]), f(r["per_year_pct"]),
            f(r["shares_pct"][0]), f(r["shares_pct"][-1])))
    t = test(rs)
    lines += ["", "| Test | Families | Controls | Largest control | Rank sum | p |",
              "|---|---|---|---|---|---|",
              "| Families against controls, slopes | %s | %s | %s | %s | %s |" % (
                  t["families"], t["controls"], f(t["control_max"]), f(t["rank_sum"]), f(t["p"]))]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--counts", default=COUNTS, help="the saved counts by year (JSON)")
    ap.add_argument("--json", help="also write the slopes and the test to this file")
    args = ap.parse_args(argv)
    with open(args.counts, encoding="utf-8") as f:
        data = json.load(f)
    if args.json:
        rs = rows(data)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"version": __version__, "rows": rs, "test": test(rs)}, f, indent=1)
    print(markdown(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
