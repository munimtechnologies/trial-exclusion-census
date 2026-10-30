"""grade_job: grade the consent-permission reading only after the labels are public.

results/consent-permission/PREREG.md says the labels are committed before the key is opened. This
job enforces that order in code, so no one (the reader included) sees the key first:

  1. waits until results/consent-permission/labels.csv on the repository's main branch matches
     the local labels.csv (gives up after about an hour);
  2. checks that the committed reading.txt is the one the sample run wrote (sha256 13c9e6d8b257);
  3. fetches consent_permission.py from main and checks it is byte for byte the 0.1.0 file the
     sample run tested (sha256 7674ee9f942d...);
  4. rebuilds the key from the same seed and sponsor table (the draw needs no trial text), writes
     key.csv, and runs that script's own grade step.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import urllib.request

__version__ = "0.1.0"

RAW = "https://raw.githubusercontent.com/munimtechnologies/trial-exclusion-census/main/"
LABELS_PATH = "results/consent-permission/labels.csv"
READING_PATH = "results/consent-permission/reading.txt"
SCRIPT_PATH = "consent_permission.py"
USER_AGENT = "grade_job/%s (MV2 of Munim, Inc.; mv2@munimtech.com)" % __version__

# Printed by the sample run (compete job consent-permission-v1, 2026-10-30 14:57 UTC).
SCRIPT_SHA256 = "7674ee9f942d4182ed4a1090db3a33ae418d94fb7a57115487d518c37701c24f"
READING_SHA12 = "13c9e6d8b257"

TRIES = 40
PAUSE = 90


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(data):
    """Bytes with CRLF turned into LF, so a line-ending change does not count as a difference."""
    return data.replace(b"\r\n", b"\n")


def fetch_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def wait_for_public(local, fetch=fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts, sha256 of the public copy) once main holds the same labels, else False."""
    last = None
    for i in range(tries):
        try:
            remote = fetch(RAW + LABELS_PATH + "?n=%d" % i)
            last = sha256(remote)
            if normalize(remote) == normalize(local):
                return True, i + 1, last
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries, last


def check_sha(data, want, prefix=False):
    got = sha256(data)
    return got.startswith(want) if prefix else got == want


def load_module(path, name="consent_permission"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def key_rows(cp, rows):
    """The key exactly as the sample step builds it: sorted (blind id, NCT id, group)."""
    picked = cp.draw(rows)
    ids = [i for grp, _ in cp.GROUPS for i in picked[grp]]
    order = cp.blind_order(ids)
    return sorted((order[i], i, grp) for grp, _ in cp.GROUPS for i in picked[grp])


def key_csv(key):
    """key.csv bytes, written the way consent_permission.main writes them."""
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["blind_id", "nct_id", "group"])
    w.writerows(key)
    return f.getvalue().encode("utf-8")


def main(argv=None, fetch=fetch_bytes, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--labels", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    with open(args.labels, "rb") as f:
        local = f.read()
    gate = {"version": __version__, "labels_sha256": sha256(local)}

    def finish(status):
        gate["status"] = status
        with open(os.path.join(args.out_dir, "gate.json"), "w", encoding="utf-8") as f:
            json.dump(gate, f, indent=1)
        print("gate: %s" % json.dumps(gate, sort_keys=True))
        print("grade_job: %s" % status)
        return 0 if status == "graded" else 2

    ok, tries, remote = wait_for_public(local, fetch=fetch, sleep=sleep)
    gate.update(labels_public=ok, polls=tries, public_sha256=remote)
    if not ok:
        return finish("labels not public; key not built")
    reading = fetch(RAW + READING_PATH)
    gate["reading_sha256"] = sha256(reading)
    gate["reading_matches"] = check_sha(reading, READING_SHA12, prefix=True)
    script = fetch(RAW + SCRIPT_PATH)
    gate["script_sha256"] = sha256(script)
    gate["script_matches"] = check_sha(script, SCRIPT_SHA256)
    if not (gate["reading_matches"] and gate["script_matches"]):
        return finish("pinned file mismatch; key not built")
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, SCRIPT_PATH)
    with open(path, "wb") as f:
        f.write(script)
    cp = load_module(path)
    header, rows = cp.read_csv(cp.fetch_bytes(cp.SPONSOR_URL))
    gates, _ = cp.sample_gates(header, rows)
    gate["sponsor_gates"] = gates
    if not all(gates.values()):
        return finish("sponsor table gate failed; key not built")
    data = key_csv(key_rows(cp, rows))
    key_path = os.path.join(args.out_dir, "key.csv")
    with open(key_path, "wb") as f:
        f.write(data)
    gate["key_sha256"] = sha256(data)
    cp.main(["grade", "--key", key_path, "--labels", args.labels, "--out-dir", args.out_dir])
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
