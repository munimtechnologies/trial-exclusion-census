"""consent_missed: how many consent paths does consent_phrase_check miss?

consent_phrase_check counts a trial as naming another path to consent when its eligibility text
names a representative, guardian or surrogate. A path named only as a caregiver, family member,
relative, spouse or partner is missed. This script fetches the same trials, keeps those with the
exact stock line and no path found, and looks for those words in the same sentence as "consent"
or "sign". It counts them, by start year, and draws a seeded sample of 40 snippets to read by eye,
so the miss can be stated as a number instead of a guess.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import os
import random
import re
import sys

import consent_phrase_check as cpc

__version__ = "0.1.0"

OTHER = re.compile(r"\bcare[\s-]?givers?\b|\bfamily\s+members?\b|\brelatives?\b|\bspouses?\b"
                   r"|\bpartners?\b|\bcare\s+partners?\b|\bstudy\s+partners?\b", re.I)
CONSENT = re.compile(r"\bconsent\w*|\bsign(?:ed|ing|ature|s)?\b", re.I)
SENTENCE = re.compile(r"[^.;\n]+")
SEED = 20261016


def other_path(text):
    """Snippets of every sentence that names another person and consent or signing."""
    out = []
    for m in SENTENCE.finditer(text or ""):
        s = m.group(0)
        if OTHER.search(s) and CONSENT.search(s):
            out.append(" ".join(s.split())[:240])
    return out


def run(found):
    rows = []
    for st in found:
        r = cpc.classify(st)
        if not r["stock_exact"] or r["adult_path"]:
            continue
        text = cpc.get(st.get("protocolSection", {}), "eligibilityModule", "eligibilityCriteria") or ""
        hits = other_path(text)
        rows.append({"nct_id": r["nct_id"], "start_year": r["start_year"], "adult_only": r["adult_only"],
                     "other_path": bool(hits), "snippets": hits})
    with_hits = sorted((r for r in rows if r["other_path"]), key=lambda r: r["nct_id"])
    sample = random.Random(SEED).sample(with_hits, min(40, len(with_hits)))
    by_year = {}
    for r in rows:
        y = by_year.setdefault(r["start_year"], [0, 0])
        y[0] += 1
        y[1] += r["other_path"]
    return {"version": __version__,
            "exact_no_path": len(rows),
            "other_path": len(with_hits),
            "other_path_adult_only": sum(1 for r in with_hits if r["adult_only"]),
            "by_year": [{"start_year": y, "trials": by_year[y][0], "with": by_year[y][1]}
                        for y in sorted(by_year, key=lambda v: (v is None, v or 0))],
            "reading_sample": [{"nct_id": r["nct_id"], "adult_only": r["adult_only"], "snippets": r["snippets"]}
                               for r in sample]}


def markdown(s):
    lines = ["# Paths the patterns miss", "",
             "Trials with the exact stock line and no representative, guardian or surrogate named: %d." % s["exact_no_path"],
             "Of these, %d name a caregiver, family member, relative, spouse or partner in a sentence about"
             " consent or signing (%d in adult-only trials)." % (s["other_path"], s["other_path_adult_only"]),
             "", "A mention is not a permission: read reading_sample in consent-missed.json.", "",
             "| Start year | Trials | Other person named |", "|---|---|---|"]
    for r in s["by_year"]:
        lines.append("| %s | %d | %d |" % ("unknown" if r["start_year"] is None else r["start_year"],
                                          r["trials"], r["with"]))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--pause", type=float, default=0.5)
    args = ap.parse_args(argv)
    found, _ = cpc.studies(pause=args.pause)
    s = run(found)
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "consent-missed.json"), "w", encoding="utf-8") as f:
        json.dump(s, f, indent=1)
    md = markdown(s)
    with open(os.path.join(args.out_dir, "CONSENT-MISSED.md"), "w", encoding="utf-8") as f:
        f.write(md + "\n")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
