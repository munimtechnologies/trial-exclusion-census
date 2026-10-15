#!/bin/sh
# Recall and precision of three rule versions on the same blind sample (225 trials drawn by
# recall_sample.py from the 2026-10-14 registry, results/v0.1.1/recall/), labelled by hand blind
# to the flags. R001-R114 (dev) were labelled first and the v0.4.0 rules were written from their
# misses. R115-R225 (held-out) were labelled after the v0.4.0 rules were fixed, so only the
# held-out scores measure v0.4.0 fairly.
set -u
cd "$(dirname "$0")"
mkdir -p /out
cp results/recall/labels-dev.csv labels-all.csv
tail -n +2 results/recall/labels-heldout.csv >> labels-all.csv
{
  for d in v020 v030 .; do (cd $d && python exclusion_census.py --version && python recall_sample.py --version); done
  sha256sum v020/*.py v030/*.py exclusion_census.py recall_sample.py sample.jsonl labels-all.csv results/recall/*.csv
} > /out/code.txt 2>&1
for v in v020 v030 v040; do
  d=$v
  [ "$v" = v040 ] && d=.
  python $d/recall_sample.py score --sample sample.jsonl --labels results/recall/labels-dev.csv --out /out/$v-dev.md > /dev/null
  python $d/recall_sample.py score --sample sample.jsonl --labels results/recall/labels-heldout.csv --out /out/$v-heldout.md > /dev/null
  python $d/recall_sample.py score --sample sample.jsonl --labels labels-all.csv --out /out/$v-all.md > /dev/null
done
cp labels-all.csv /out/labels.csv
ls -la /out
