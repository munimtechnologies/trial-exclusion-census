"""diff_rules: what a rule change adds and removes, across the whole registry.

Reads the census cache and runs every exclusion item through classify() and
every inclusion item through requirements() of two versions of
exclusion_census.py. It counts, per core category, the items and trials each
version flags that the other does not, and keeps a seeded random sample of up
to 40 changed items per category and direction, so the precision of just the
new rules can be checked by hand (changes.csv, changed_items.csv).

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import csv
import importlib.util
import json
import os
import random
import sys

__version__ = "0.1.0"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def diff(records, old, new, per_key=40, seed=2029):
    """Counts and samples of the core-category flags that differ between two rule modules."""
    core = set(new.CORE)
    rng = random.Random(seed)
    items, trials, seen = collections.Counter(), collections.Counter(), collections.Counter()
    samples = collections.defaultdict(list)
    n = any_old = any_new = 0
    for rec in records:
        crit = rec.get("criteria") or ""
        excl = new.exclusion_section(crit)
        if excl is None:
            continue
        n += 1
        parts = (("exclusion", new.split_items(excl), old.classify, new.classify),
                 ("inclusion", new.split_items(new.inclusion_section(crit)), old.requirements, new.requirements))
        for kind, its, old_fn, new_fn in parts:
            t_old, t_new = set(), set()
            for item in its:
                a, b = old_fn(item) & core, new_fn(item) & core
                t_old |= a
                t_new |= b
                for direction, cats in (("added", b - a), ("removed", a - b)):
                    for c in cats:
                        key = (kind, c, direction)
                        items[key] += 1
                        seen[key] += 1
                        s = samples[key]
                        if len(s) < per_key:
                            s.append((rec.get("nct"), item))
                        else:
                            j = rng.randrange(seen[key])
                            if j < per_key:
                                s[j] = (rec.get("nct"), item)
            for c in t_new - t_old:
                trials[(kind, c, "added")] += 1
            for c in t_old - t_new:
                trials[(kind, c, "removed")] += 1
            if kind == "exclusion":
                any_old += bool(t_old)
                any_new += bool(t_new)
    return {"trials": n, "any_core_old": any_old, "any_core_new": any_new,
            "items": items, "trial_counts": trials, "samples": samples}


def write(res, out_dir, old, new):
    os.makedirs(out_dir, exist_ok=True)
    keys = sorted(set(res["items"]) | set(res["trial_counts"]))
    with open(os.path.join(out_dir, "changes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section", "category", "direction", "items", "trials"])
        for k in keys:
            w.writerow(list(k) + [res["items"][k], res["trial_counts"][k]])
    with open(os.path.join(out_dir, "changed_items.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section", "category", "direction", "nct", "item", "correct"])
        for k in keys:
            for nct, item in res["samples"][k]:
                w.writerow(list(k) + [nct, item, ""])
    n = res["trials"]
    summary = {"old": old.__version__, "new": new.__version__, "trials_with_exclusion_section": n,
               "any_core_old": res["any_core_old"], "any_core_new": res["any_core_new"],
               "any_core_old_pct": round(100.0 * res["any_core_old"] / n, 2) if n else None,
               "any_core_new_pct": round(100.0 * res["any_core_new"] / n, 2) if n else None}
    with open(os.path.join(out_dir, "diff_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--old", required=True, help="path to the older exclusion_census.py")
    ap.add_argument("--new", required=True, help="path to the newer exclusion_census.py")
    ap.add_argument("--cache", required=True, help="the census jsonl.gz cache")
    ap.add_argument("--out-dir", default="diff")
    ap.add_argument("--per-key", type=int, default=40)
    ap.add_argument("--seed", type=int, default=2029)
    args = ap.parse_args(argv)
    old, new = load(args.old, "ec_old"), load(args.new, "ec_new")
    res = diff(new.load_records(args.cache), old, new, args.per_key, args.seed)
    print(json.dumps(write(res, args.out_dir, old, new), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
