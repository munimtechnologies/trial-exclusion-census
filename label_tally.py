"""Label-only tally for the recall sample of trial-exclusion-census.

How many labelled trials have a disability barrier only in their inclusion
criteria (an i mark and no x mark in any of the six core categories), and in
which categories those i marks fall. It reads the label files alone, with the
same reading of the marks as `recall_sample.py score`, and runs no rules, so
the counts do not depend on any census version.

The counts cover every labelled trial in each file, from both the random and
the broad sample. The broad sample was chosen for loose wording, so these are
counts of what the labels record, not estimates for the registry. The labels
were made by AI agents working for MV2, one reader per trial, and no person
has checked them yet. They do not record whether a representative is named.

    python label_tally.py results/recall/labels-heldout.csv [more files...]

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import sys

import recall_sample as rs

__version__ = "0.1.0"

CORE = rs.CORE


def tally(labels):
    """Counts over labelled rows (done = 1): trials, trials with an i and no x,
    and those trials' i marks per category."""
    rows = list(labels.values())
    only = []
    for lab in rows:
        excl = [c for c in CORE if rs.marks(lab.get(c))[0]]
        incl = [c for c in CORE if rs.marks(lab.get(c))[1]]
        if incl and not excl:
            only.append(incl)
    return {"labelled": len(rows), "inclusion_only": len(only),
            "inclusion_only_by_category": {c: sum(c in incl for incl in only) for c in CORE}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("labels", nargs="+", help="labels.csv files (rows with done = 1 are counted)")
    args = ap.parse_args(argv)
    out = {"version": __version__, "files": {}}
    merged = {}
    for path in args.labels:
        labels = rs.read_labels(path)
        out["files"][path] = tally(labels)
        merged.update(labels)
    if len(args.labels) > 1:
        out["all"] = tally(merged)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
