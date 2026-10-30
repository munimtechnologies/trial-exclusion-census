"""Tests for consent_permission (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import csv
import io
import unittest

import consent_permission as cp


def row(nct, path, nci, washu, year="2021"):
    return {"nct_id": nct, "start_year": year, "stock_exact": "True", "adult_only": "True",
            "adult_path": str(path), "lead_sponsor": "X", "lead_class": "OTHER",
            "nci_linked": str(nci), "washu_led": str(washu)}


def table(rows):
    f = io.StringIO()
    w = csv.writer(f, lineterminator="\r\n")
    w.writerow(cp.SPONSOR_HEADER)
    for r in rows:
        w.writerow([r[h] for h in cp.SPONSOR_HEADER])
    return f.getvalue().encode("utf-8")


def synthetic():
    """A table with the published group counts: 5,436 trials."""
    rows, n = [], 0

    def add(k, total, nci, washu):
        nonlocal n
        for i in range(total):
            n += 1
            rows.append(row("NCT%08d" % n, i < k, nci, washu))
    add(260, 1546, True, False)    # NCI-linked only
    add(18, 24, True, True)        # both
    add(147, 200, False, True)     # WashU-led only
    add(241, 3666, False, False)   # Neither
    return rows


class Fake:
    """Stands in for the API: returns every requested id with a path in its text."""

    def __init__(self, drop=()):
        self.drop = set(drop)
        self.calls = 0

    def __call__(self, url):
        self.calls += 1
        ids = url.split("filter.ids=")[1].split("&")[0].replace("%2C", ",").split(",")
        return {"studies": [{"protocolSection": {
            "identificationModule": {"nctId": i, "briefTitle": "A trial"},
            "eligibilityModule": {
                "eligibilityCriteria": "Inclusion Criteria:\n\n* Age >= 18\n* Ability to "
                "understand and the willingness to sign a written informed consent document. "
                "Legally authorized representatives may sign.\n\nExclusion Criteria:\n\n* None",
                "minimumAge": "18 Years", "stdAges": ["ADULT", "OLDER_ADULT"]}}}
            for i in ids if i not in self.drop]}


class Constants(unittest.TestCase):
    def test_preregistered_values(self):
        self.assertEqual(cp.SEED, 20261030)
        self.assertEqual(cp.GROUPS, (("nci", 40), ("washu", 20), ("neither", 40)))
        self.assertEqual((cp.MIN_FETCHED, cp.MIN_STILL_PRESENT, cp.EXCERPT_CAP), (98, 95, 4000))
        self.assertEqual((cp.R1_MIN_DIFF, cp.R2_MIN_NCI, cp.R3_MAX_NEITHER, cp.R4_MIN_WASHU,
                          cp.R5_MIN_OWNER_SHARE), (0.15, 0.70, 0.60, 0.80, 0.70))
        self.assertEqual(cp.LABELS, ("adult_permission", "physical_only", "minor_only", "unclear",
                                     "not_a_permission", "path_gone"))
        self.assertIn(cp.SPONSOR_COMMIT, cp.SPONSOR_URL)
        self.assertEqual(len(cp.SPONSOR_COMMIT), 40)

    def test_expected_counts_add_up(self):
        e = cp.EXPECTED
        self.assertEqual(e["nci_linked"][1] + e["washu_led"][1] - e["both"][1] + e["neither"][1],
                         e["rows"])
        self.assertEqual(e["nci_linked"][0] + e["washu_led"][0] - e["both"][0] + e["neither"][0],
                         666)


class Patterns(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(cp.path_terms("or their legally authorized representative"),
                         ["representative"])
        self.assertEqual(cp.path_terms("a LAR may sign"), ["representative"])
        self.assertEqual(cp.path_terms("octreotide lar"), [])
        self.assertEqual(cp.path_terms("parent or legal guardian"), ["guardian"])
        self.assertEqual(cp.path_terms("health care proxy"), ["surrogate"])
        self.assertEqual(cp.path_terms("signed by the patient"), [])

    def test_excerpt_sections_and_gaps(self):
        text = ("Inclusion Criteria:\n* a\n* b\n* c\n* signs informed consent\n* d\n* e\n"
                "Exclusion Criteria:\n* f\n* g\n* has a guardian\n")
        ex = cp.excerpt(text)
        self.assertIn("[inclusion] * signs informed consent", ex)
        self.assertIn("[exclusion] * * has a guardian", ex)
        self.assertIn("    ...", ex)
        self.assertNotIn("* a", ex)

    def test_excerpt_cap(self):
        ex = cp.excerpt("consent " * 2000, cap=100)
        self.assertTrue(ex.endswith("[cut at 100 characters]"))

    def test_years(self):
        self.assertEqual(cp.years("18 Years"), 18.0)
        self.assertAlmostEqual(cp.years("6 Months"), 0.5)
        self.assertIsNone(cp.years(""))


class Sampling(unittest.TestCase):
    def test_gates_pass_on_published_counts(self):
        rows = synthetic()
        header, back = cp.read_csv(table(rows))
        g, got = cp.sample_gates(header, back)
        self.assertTrue(all(g.values()), got)

    def test_gate_fails_on_wrong_count(self):
        rows = synthetic()[:-1]
        header, back = cp.read_csv(table(rows))
        g, _ = cp.sample_gates(header, back)
        self.assertFalse(g["S1_table"])
        self.assertFalse(g["S2_counts"])

    def test_draw_is_seeded_and_in_group(self):
        rows = synthetic()
        a, b = cp.draw(rows), cp.draw(list(reversed(rows)))
        self.assertEqual(a, b)
        by = {r["nct_id"]: r for r in rows}
        for g, n in cp.GROUPS:
            self.assertEqual(len(set(a[g])), n)
            for i in a[g]:
                self.assertEqual(cp.group_of(by[i]), g)
                self.assertTrue(cp.truthy(by[i]["adult_path"]))
        self.assertNotEqual(cp.draw(rows, seed=1), a)

    def test_blind_order(self):
        ids = ["NCT%08d" % i for i in range(100)]
        o = cp.blind_order(ids)
        self.assertEqual(sorted(o.values()), ["R%03d" % i for i in range(1, 101)])
        self.assertNotEqual([o[i] for i in ids], sorted(o.values()))

    def test_run_sample_writes_blind_reading(self):
        fake = Fake()
        result, reading, key = cp.run_sample(table(synthetic()), fetch=fake)
        self.assertTrue(all(result["gates"].values()), result["gates"])
        self.assertEqual(len(key), 100)
        self.assertEqual(fake.calls, 1)
        self.assertNotIn("NCT", reading)
        self.assertEqual(reading.count("\n## R"), 100)
        self.assertIn("adult-only: yes", reading)
        self.assertEqual({k[2] for k in key}, {"nci", "washu", "neither"})
        self.assertEqual(result["reading_sha256"], cp.sha256(reading.encode("utf-8")))

    def test_run_sample_gate_on_missing(self):
        rows = synthetic()
        drop = cp.draw(rows)["nci"][:3]
        result, reading, _ = cp.run_sample(table(rows), fetch=Fake(drop))
        self.assertFalse(result["gates"]["S3_fetched"])
        self.assertEqual(reading.count("Not returned by the API."), 3)


class Grading(unittest.TestCase):
    def key(self):
        rows, n = [], 0
        for g, size in cp.GROUPS:
            for i in range(size):
                n += 1
                rows.append({"blind_id": "R%03d" % n, "nct_id": "N%d" % n, "group": g})
        return rows

    def labels(self, key, yes):
        """yes: {group: number labelled adult_permission}; the rest minor_only."""
        seen, out = {}, []
        for k in key:
            seen[k["group"]] = seen.get(k["group"], 0) + 1
            lab = "adult_permission" if seen[k["group"]] <= yes[k["group"]] else "minor_only"
            out.append({"blind_id": k["blind_id"], "label": lab, "reason": ""})
        return out

    def test_newcombe_published_example(self):
        d, lo, hi = cp.newcombe(56, 70, 48, 80)
        self.assertAlmostEqual(d, 0.2, places=6)
        self.assertAlmostEqual(lo, 0.0524, places=4)
        self.assertAlmostEqual(hi, 0.3339, places=4)

    def test_all_hold(self):
        key = self.key()
        r = cp.grade(key, ["blind_id", "label", "reason"],
                     self.labels(key, {"nci": 34, "washu": 18, "neither": 20}))
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["groups"]["nci"]["share"], 0.85)
        self.assertEqual(r["predictions"], {"R1": True, "R2": True, "R3": True, "R4": True,
                                            "R5": True})
        e = r["estimated_permissions"]
        self.assertAlmostEqual(e["owners"], round(278 * 0.85 + 147 * 0.9, 1))
        self.assertAlmostEqual(e["neither"], round(241 * 0.5, 1))

    def test_all_fail(self):
        key = self.key()
        r = cp.grade(key, ["blind_id", "label", "reason"],
                     self.labels(key, {"nci": 24, "washu": 12, "neither": 30}))
        self.assertEqual(r["predictions"], {"R1": False, "R2": False, "R3": False, "R4": False,
                                            "R5": False})

    def test_path_gone_left_out_of_shares(self):
        key = self.key()
        labs = self.labels(key, {"nci": 40, "washu": 20, "neither": 40})
        labs[0]["label"] = "path_gone"
        r = cp.grade(key, ["blind_id", "label", "reason"], labs)
        g = r["groups"][key[0]["group"]]
        self.assertEqual(g["read"], g["adult_permission"])
        self.assertEqual(g["labels"]["path_gone"], 1)

    def test_label_gates(self):
        key = self.key()
        labs = self.labels(key, {"nci": 1, "washu": 1, "neither": 1})
        self.assertIsNone(cp.grade(key, ["blind_id", "label"], labs[1:])["predictions"])
        labs[0]["label"] = "permission"
        self.assertFalse(cp.grade(key, ["blind_id", "label"], labs)["gates"]["L3_valid"])


if __name__ == "__main__":
    unittest.main()
