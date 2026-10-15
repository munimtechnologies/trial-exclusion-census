#!/bin/sh
# trial-exclusion-census v0.3.0 and v0.4.0 on the registry records cached by trial-exclusion-census-v2
# (fetched 2026-10-14), so both sit beside the pre-registered v0.1.1 run on the same data.
# Seeds 2027 and 2028 draw fresh sample_items.csv files for independent precision checks, and
# diff_rules.py samples the items that v0.4.0 flags and v0.3.0 does not (and the reverse).
# If the cache is gone, the first census fetches the registry again (about an hour).
set -u
cd "$(dirname "$0")"
mkdir -p /out/v0.3.0 /out/v0.4.0 /out/diff /data
CACHE=/data/ctgov-interventional.jsonl.gz
{
  python v030/exclusion_census.py --version
  python exclusion_census.py --version
  python diff_rules.py --version
  sha256sum v030/exclusion_census.py exclusion_census.py diff_rules.py test_exclusion_census.py test_web_check.py test_diff_rules.py
  ls -la /data
} > /out/code.txt 2>&1
python v030/exclusion_census.py census --out-dir /out/v0.3.0 --cache $CACHE --seed 2027 > /dev/null
python exclusion_census.py census --out-dir /out/v0.4.0 --cache $CACHE --seed 2028 > /dev/null
python diff_rules.py --old v030/exclusion_census.py --new exclusion_census.py --cache $CACHE --out-dir /out/diff
ls -la /out /out/v0.3.0 /out/v0.4.0 /out/diff
