"""Blind recall sample for trial-exclusion-census: what do the word rules miss?

The census measures its precision from flagged items (sample_items.csv), but
not its recall: how many disability-related exclusions the word rules miss.
That needs trials drawn without looking at the flags. `draw` takes two seeded
random samples of interventional trials that have an exclusion section:

- random: any such trial, for unbiased precision and recall per category;
- broad: trials with no core flag whose criteria still use a loose word
  (walk, hearing, understand, reading...), to find misses quickly. It is
  reported as a list of misses, never as an estimate.

It writes blind.md (each trial's full eligibility criteria, no flags, in
shuffled order), labels.csv (an empty row per trial to fill in by hand),
flags.csv (what the rules flagged, kept apart so labelling stays blind) and
sample.jsonl (the records, so `score` can re-run newer rules on the same
trials).

Labelling: for each core category write x if the exclusion criteria exclude
people for that kind of disability, i if the inclusion criteria require an
ability that shuts them out (for example "able to walk 100 m unaided"), xi
for both, and blank for neither; set done to 1. The census reads only the
exclusion section, so i-only trials show what an exclusion-only count cannot
see.

`score` reports, per category, trial-level precision and recall of the rules
on the random sample with Wilson 95% intervals, the share of trials whose
only barrier is in the inclusion criteria, and every miss in both samples.
Since 0.2.0 it scores the census's inclusion-criteria requirement rules
against the i marks the same way.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import csv
import json
import math
import os
import random
import re
import sys

import exclusion_census as ec

__version__ = "0.2.0"

CORE = ec.CORE
BROAD = re.compile(
    r"\b(?:cognit\w*|memory|comprehen\w*|understand\w*|decision\w*|vision|visual\w*|sight\w*|"
    r"eyesight|hearing|deaf\w*|speak\w*|speech|literac\w*|literate|communicat\w*|walk\w*|"
    r"ambulat\w*|mobility|wheel\w*|sensory|reading|writing)\b", re.I)

BLIND_HEAD = """# Blind recall sample, trial-exclusion-census

recall_sample %(version)s, seed %(seed)d, %(n)d trials. Rules version not shown on purpose.

For each trial, fill in its row in labels.csv. For each category (%(cats)s) write
x if the exclusion criteria exclude people for that kind of disability, i if the
inclusion criteria require an ability that shuts them out, xi for both, blank for
neither. Then set done to 1. Judge what the text says, not whether it is justified.

"""


def draw(records, n_random=150, n_broad=75, seed=2026):
    """Seeded reservoir samples (see the module docstring) in shuffled order,
    labelled R001, R002...; and how many trials each sample was drawn from."""
    rng = random.Random(seed)
    want = {"random": n_random, "broad": n_broad}
    pools = {"random": [], "broad": []}
    seen = {"random": 0, "broad": 0}
    for rec in records:
        a = ec.analyze(rec)
        if not a["has_exclusion"]:
            continue
        names = ["random"]
        if not set(a["hits"]) & set(CORE) and BROAD.search(rec.get("criteria") or ""):
            names.append("broad")
        for name in names:
            seen[name] += 1
            pool = pools[name]
            if len(pool) < want[name]:
                pool.append(rec)
            else:
                j = rng.randrange(seen[name])
                if j < want[name]:
                    pool[j] = rec
    # A trial drawn in both samples keeps only its random place.
    ids = {r.get("nct") for r in pools["random"]}
    rows = [dict(r, stratum="random") for r in pools["random"]]
    rows += [dict(r, stratum="broad") for r in pools["broad"] if r.get("nct") not in ids]
    rng.shuffle(rows)
    for i, r in enumerate(rows, 1):
        r["label"] = "R%03d" % i
    return rows, seen


def write_sample(rows, seen, out_dir, seed=2026):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sample.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "blind.md"), "w", encoding="utf-8") as f:
        f.write(BLIND_HEAD % {"version": __version__, "seed": seed, "n": len(rows), "cats": ", ".join(CORE)})
        for r in rows:
            f.write("## %s (%s)\n\n" % (r["label"], r.get("nct")))
            f.write("Title: %s\n\nConditions: %s\n\n" % (r.get("title") or "", "; ".join(r.get("conditions") or [])))
            f.write("~~~~\n%s\n~~~~\n\n" % (r.get("criteria") or "").strip())
    with open(os.path.join(out_dir, "labels.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("label", "nct", "done") + CORE + ("notes",))
        for r in rows:
            w.writerow([r["label"], r.get("nct"), ""] + [""] * len(CORE) + [""])
    with open(os.path.join(out_dir, "flags.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("label", "nct", "stratum") + CORE + ("related", "required"))
        for r in rows:
            a = ec.analyze(r)
            w.writerow([r["label"], r.get("nct"), r["stratum"]] + [int(c in a["hits"]) for c in CORE]
                       + ["|".join(sorted(a["related"] & set(CORE), key=CORE.index)),
                          "|".join(sorted(a["requires"], key=CORE.index))])
    with open(os.path.join(out_dir, "sample_info.json"), "w", encoding="utf-8") as f:
        json.dump({"version": __version__, "census_version": ec.__version__, "seed": seed,
                   "drawn_from": seen, "trials": len(rows),
                   "random": sum(r["stratum"] == "random" for r in rows),
                   "broad": sum(r["stratum"] == "broad" for r in rows)}, f, indent=1)


def read_sample(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def read_labels(path):
    """Labelled rows (done = 1) by label."""
    with open(path, newline="", encoding="utf-8") as f:
        return {row["label"]: row for row in csv.DictReader(f) if (row.get("done") or "").strip() == "1"}


def marks(value):
    """(excluded, required by inclusion) from a label cell such as 'x', 'i' or 'xi'."""
    v = (value or "").strip().lower()
    return "x" in v, "i" in v


def wilson(k, n, z=1.96):
    """Wilson score 95% interval for k of n, or None when n is 0."""
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def _tally(counts, got, want):
    """Add one trial's flagged (got) and labelled (want) categories to per-category counts."""
    for c, g, w in [(c, c in got, c in want) for c in CORE] + [("any", bool(got), bool(want))]:
        if g and w:
            counts[c]["tp"] += 1
        elif g:
            counts[c]["fp"] += 1
        elif w:
            counts[c]["fn"] += 1


def score(rows, labels):
    """Trial-level counts of the current rules against hand labels: the exclusion rules
    against the x marks, and the inclusion-criteria requirement rules against the i marks."""
    counts = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CORE + ("any",)}
    req_counts = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CORE + ("any",)}
    n = {"random": 0, "broad": 0}
    misses, req_misses = [], []
    inclusion_any = inclusion_only = 0
    for r in rows:
        lab = labels.get(r["label"])
        if not lab:
            continue
        n[r["stratum"]] += 1
        a = ec.analyze(r)
        flagged = set(a["hits"]) & set(CORE)
        required = set(a["requires"]) & set(CORE)
        excl = {c for c in CORE if marks(lab.get(c))[0]}
        incl = {c for c in CORE if marks(lab.get(c))[1]}
        for c in sorted(excl - flagged, key=CORE.index):
            misses.append({"label": r["label"], "nct": r.get("nct"), "stratum": r["stratum"],
                           "category": c, "notes": lab.get("notes") or ""})
        for c in sorted(incl - required, key=CORE.index):
            req_misses.append({"label": r["label"], "nct": r.get("nct"), "stratum": r["stratum"],
                               "category": c, "notes": lab.get("notes") or ""})
        if r["stratum"] != "random":
            continue
        inclusion_any += bool(incl)
        inclusion_only += bool(incl) and not excl
        _tally(counts, flagged, excl)
        _tally(req_counts, required, incl)
    return {"labelled": n, "counts": counts, "misses": misses,
            "req_counts": req_counts, "req_misses": req_misses,
            "inclusion_any": inclusion_any, "inclusion_only": inclusion_only}


def _rate(k, n):
    if not n:
        return "n/a"
    lo, hi = wilson(k, n)
    return "%d/%d = %.0f%% (%.0f-%.0f%%)" % (k, n, 100.0 * k / n, 100 * lo, 100 * hi)


def _table(counts, labelled):
    lines = ["| Category | %s | Flagged | Precision | Recall |" % labelled, "|---|---|---|---|---|"]
    for c in CORE + ("any",):
        k = counts[c]
        lines.append("| %s | %d | %d | %s | %s |" % (
            c, k["tp"] + k["fn"], k["tp"] + k["fp"], _rate(k["tp"], k["tp"] + k["fp"]), _rate(k["tp"], k["tp"] + k["fn"])))
    return lines


def _miss_lines(misses):
    lines = ["- %s %s (%s) %s: %s" % (m["label"], m["nct"], m["stratum"], m["category"], m["notes"])
             for m in misses]
    return lines or ["None."]


def score_md(res):
    n = res["labelled"]["random"]
    lines = ["# Recall and precision of the word rules (hand-labelled sample)", "",
             "census rules %s; labelled trials: %d random, %d broad." % (ec.__version__, n, res["labelled"]["broad"]),
             "Trial level: a trial counts once per category. Wilson 95% intervals.", ""]
    lines += _table(res["counts"], "Labelled excluded")
    lines += ["", "Random-sample trials with a disability barrier in the inclusion criteria: %s; "
              "with one only there (invisible to an exclusion-only count): %s." % (
                  _rate(res["inclusion_any"], n), _rate(res["inclusion_only"], n)),
              "", "## Inclusion-criteria requirement rules against the i marks", ""]
    lines += _table(res["req_counts"], "Labelled required")
    lines += ["", "## Misses (labelled excluded, not flagged)", ""]
    lines += _miss_lines(res["misses"])
    lines += ["", "## Requirement misses (labelled i, not flagged)", ""]
    lines += _miss_lines(res["req_misses"])
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draw", help="draw the blind samples from the census cache")
    d.add_argument("--cache", required=True, help="the census jsonl.gz cache (fetched first if missing)")
    d.add_argument("--out-dir", default="recall")
    d.add_argument("--n-random", type=int, default=150)
    d.add_argument("--n-broad", type=int, default=75)
    d.add_argument("--seed", type=int, default=2026)
    s = sub.add_parser("score", help="compare hand labels with the current rules")
    s.add_argument("--sample", required=True, help="sample.jsonl from draw")
    s.add_argument("--labels", required=True, help="labels.csv with done = 1 rows")
    s.add_argument("--out", default="", help="write the report here as well")
    args = ap.parse_args(argv)
    if args.cmd == "draw":
        rows, seen = draw(ec.load_records(args.cache), args.n_random, args.n_broad, args.seed)
        write_sample(rows, seen, args.out_dir, args.seed)
        print("%d trials drawn (from %d with an exclusion section; %d in the broad pool)"
              % (len(rows), seen["random"], seen["broad"]))
        return 0
    report = score_md(score(read_sample(args.sample), read_labels(args.labels)))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
