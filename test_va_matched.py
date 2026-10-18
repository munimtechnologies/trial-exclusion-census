"""Offline tests for va_matched (no network). Apache-2.0."""

import json
import os
import tempfile
import unittest
from unittest import mock

import sponsor_check as sc
import trend_check as tc
import va_matched as vm

HERE = os.path.dirname(os.path.abspath(__file__))
# Two strata. F is twice as common in VA trials in both (matched 2.0, unmatched 5.5 because the
# VA has more trials in stratum a, where everything is common). C is as common in both (matched
# 1.0, unmatched 2.75). X is too rare to test (1.04 VA matches expected).
SMALL = {
    "strata": ["a", "b"],
    "trials": {"a": {"va": 100, "registry": 200}, "b": {"va": 20, "registry": 1020}},
    "phrases": {
        "F": {"kind": "family", "a": {"va": 40, "registry": 60}, "b": {"va": 2, "registry": 52}},
        "C": {"kind": "control", "a": {"va": 20, "registry": 40}, "b": {"va": 1, "registry": 51}},
        "X": {"kind": "control", "a": {"va": 0, "registry": 1}, "b": {"va": 0, "registry": 2}},
    },
}


class TermTests(unittest.TestCase):
    def test_first_stratum(self):
        self.assertEqual(vm.term(0), "AREA[StudyType]INTERVENTIONAL AND AREA[Phase]NA AND "
                         "AREA[ConditionSearch](PTSD) AND NOT AREA[ConditionSearch](%s)" % vm.OWN)

    def test_control_leaves_out_earlier_strata_and_its_own_condition(self):
        t = vm.term(1, "hernia", va=True)
        self.assertIn(sc.SPONSORS["va"], t)
        self.assertIn('AREA[EligibilityCriteria]"hernia"', t)
        self.assertIn('AREA[ConditionSearch]("substance use" OR alcohol', t)
        self.assertTrue(t.endswith("NOT AREA[ConditionSearch](PTSD OR %s OR hernia)" % vm.OWN))

    def test_family_and_last_stratum(self):
        t = vm.term(4, "visual (all wordings)")
        self.assertIn("AREA[EligibilityCriteria]" + tc.criteria("visual (all wordings)"), t)
        self.assertNotIn("FED", t)
        self.assertTrue(t.endswith("depression OR pain OR %s)" % vm.OWN))

    def test_phrases(self):
        self.assertEqual(len(vm.PHRASES), 12)
        self.assertEqual([vm.kind(p) for p in vm.PHRASES].count("control"), 8)
        self.assertEqual(vm.kind("informed consent"), "reference")


class MathTests(unittest.TestCase):
    def test_one_table(self):
        # 10/100 against 20/400; var(log) = 1/10 - 1/100 + 1/20 - 1/400 = 0.1375.
        self.assertEqual(vm.mh([(10, 100, 20, 400)]), (2.0, 0.97, 4.14))

    def test_matching_removes_the_mix(self):
        f, c, x = vm.rows(SMALL)
        self.assertEqual((f["mh"], f["low"], f["high"], f["crude"]), (2.0, 1.29, 3.09, 5.5))
        self.assertEqual((c["mh"], c["crude"]), (1.0, 2.75))
        self.assertEqual(f["strata"], {"a": 2.0, "b": 2.0})
        self.assertEqual((f["va"], f["expected"], f["kept"]), (42, 21.0, True))

    def test_rare_control_left_out(self):
        x = vm.rows(SMALL)[2]
        self.assertEqual((x["mh"], x["low"], x["expected"], x["kept"]), (0.0, None, 1.0, False))
        t = vm.test(vm.rows(SMALL))
        self.assertEqual((t["families"], t["controls"], t["left_out"], t["p"]), (1, 1, ["X"], 0.5))
        self.assertFalse(t["testable"])
        self.assertFalse(vm.verdicts(vm.rows(SMALL), t)["HV1"])

    def test_verdicts(self):
        rs = [{"phrase": "cognitive (all wordings)", "kind": "family", "mh": 2.7, "low": 1.8, "kept": True},
              {"phrase": "hearing (all wordings)", "kind": "family", "mh": 2.0, "low": 0.9, "kept": True},
              {"phrase": "visual (all wordings)", "kind": "family", "mh": 1.9, "low": 0.8, "kept": True}]
        rs += [{"phrase": "c%d" % i, "kind": "control", "mh": m, "low": None, "kept": True}
               for i, m in enumerate([0.5, 0.6, 0.9, 1.2])]
        t = vm.test(rs)
        self.assertEqual((t["controls"], t["rank_sum"], t["p"], t["testable"]), (4, 18.0, 0.0286, True))
        self.assertEqual(vm.verdicts(rs, t), {"HV1": True, "HV2": True})
        rs[0]["low"] = 0.95
        self.assertFalse(vm.verdicts(rs, t)["HV2"])


class RunTests(unittest.TestCase):
    def test_fetch_counts(self):
        urls = []

        def fake(u):
            urls.append(u)
            return {"totalCount": 7}

        data = vm.fetch_counts(["pregnant"], fetch=fake, pause=0)
        self.assertEqual(len(urls), 20)
        self.assertEqual(data["strata"], [s for s, _ in vm.STRATA])
        self.assertEqual(data["trials"]["ptsd"], {"va": 7, "registry": 7})
        self.assertEqual(data["phrases"]["pregnant"]["kind"], "control")
        self.assertEqual(data["phrases"]["pregnant"]["cardiometabolic"], {"va": 7, "registry": 7})

    def test_markdown(self):
        md = vm.markdown(SMALL)
        self.assertIn("| a | 100 | 100 |", md)
        self.assertIn("| F | family | 42 | 21.0 | 2.0 | 1.29-3.09 | 5.5 | 2.0 | 2.0 |", md)
        self.assertIn("| X | control | 0 | 1.0 | 0.0* | - | 0.0 | 0.0 | 0.0 |", md)
        self.assertIn("HV1 (p < 0.05 with at least 4 controls): not testable.", md)

    def test_main_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            counts, out = os.path.join(d, "counts.json"), os.path.join(d, "out.json")
            with open(counts, "w", encoding="utf-8") as f:
                json.dump(SMALL, f)
            with mock.patch("builtins.print"):
                rc = vm.main(["--counts", counts, "--json", out])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["test"]["left_out"], ["X"])
            self.assertEqual(data["verdicts"], {"HV1": False, "HV2": False})


class PublishedTests(unittest.TestCase):
    def load(self, name):
        path = os.path.join(HERE, "results", "sponsor-check", name)
        if not os.path.exists(path):
            self.skipTest("%s not present" % name)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def test_counts_file(self):
        data = self.load("va-matched-counts.json")
        self.assertEqual(data["strata"], [s for s, _ in vm.STRATA])
        self.assertEqual(list(data["phrases"]), vm.PHRASES)
        for p, c in data["phrases"].items():
            self.assertEqual(c["kind"], vm.kind(p))
            for s in data["strata"]:
                self.assertLessEqual(c[s]["va"], c[s]["registry"])
                self.assertLessEqual(c[s]["registry"], data["trials"][s]["registry"])

    def test_stratum_sizes_match_the_preregistration(self):
        data = self.load("va-matched-counts.json")
        prereg = self.load("prereg-va-matched.json")
        self.assertEqual(data["trials"], prereg["stratum_sizes_known_before"])

    def test_result(self):
        data = self.load("va-matched-counts.json")
        rs = {r["phrase"]: r for r in vm.rows(data)}
        # First worked out outside the code by AI agents working for MV2 on 2026-10-15
        # (VA-MATCHED-RESULT.md, as corrected the same day); no person has checked them yet.
        for phrase, est, low, high in [("cognitive (all wordings)", 2.21, 1.99, 2.45),
                                       ("hearing (all wordings)", 1.77, 1.24, 2.52),
                                       ("visual (all wordings)", 1.55, 0.92, 2.62),
                                       ("pregnant", 0.68, 0.59, 0.77),
                                       ("claustrophobia", 1.02, 0.62, 1.66),
                                       ("informed consent", 0.72, 0.63, 0.83)]:
            r = rs[phrase]
            self.assertAlmostEqual(r["mh"], est, delta=0.011)
            self.assertAlmostEqual(r["low"], low, delta=0.011)
            self.assertAlmostEqual(r["high"], high, delta=0.011)
        # The first version of the write-up said 263 and 2.90; the counts give 255 and 2.81.
        self.assertEqual(rs["cognitive (all wordings)"]["va"], 255)
        self.assertAlmostEqual(rs["cognitive (all wordings)"]["crude"], 2.81, delta=0.011)
        self.assertEqual((rs["osteoporosis"]["mh"], rs["osteoporosis"]["kept"]), (0.0, True))
        self.assertAlmostEqual(rs["osteoporosis"]["expected"], 5.4, delta=0.05)
        t = vm.test(list(rs.values()))
        self.assertEqual(t["left_out"], ["migraine", "celiac", "hernia"])
        self.assertEqual((t["families"], t["controls"], t["rank_sum"], t["p"], t["testable"]),
                         (3, 5, 21.0, 0.0179, True))
        self.assertEqual(vm.verdicts(list(rs.values()), t), {"HV1": True, "HV2": True})


if __name__ == "__main__":
    unittest.main()
