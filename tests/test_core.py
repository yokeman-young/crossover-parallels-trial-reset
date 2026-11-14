import datetime as dt
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trialreset import core  # noqa: E402
from trialreset.adapters import CROSSOVER, PARALLELS  # noqa: E402


NOW = dt.datetime(2026, 11, 14, 12, 0, 0)


class PlanTests(unittest.TestCase):
    def test_parallels_licence_keys_are_deleted(self):
        snapshot = {"License.Flags": 1, "License.Params.0": -11000,
                    "WiConfig": {"mode": "trial"}, "Unrelated": True}
        plan = core.plan_reset(PARALLELS, snapshot, NOW)
        self.assertEqual(sorted(plan.delete_keys),
                         ["License.Flags", "License.Params.0", "WiConfig"])
        self.assertNotIn("Unrelated", plan.delete_keys)

    def test_crossover_dates_are_shifted_three_hours(self):
        plan = core.plan_reset(CROSSOVER, {"FirstRunDate": "x", "SULastCheckTime": "y"}, NOW)
        self.assertEqual(plan.set_dates["FirstRunDate"], "2026-11-14T09:00:00Z")
        self.assertEqual(plan.set_dates["SULastCheckTime"], "2026-11-14T09:00:00Z")

    def test_unknown_schema_warns(self):
        plan = core.plan_reset(PARALLELS, {"SomethingElse": 1}, NOW)
        self.assertTrue(plan.warnings)
        self.assertFalse(plan.delete_keys)

    def test_kill_and_cache_are_planned(self):
        plan = core.plan_reset(PARALLELS, {"License.Flags": 1}, NOW)
        self.assertIn("prl_disp_service", plan.kill)
        self.assertTrue(all(p.startswith("/") for p in plan.caches))

    def test_spec_registry(self):
        from trialreset.adapters import SPECS
        self.assertIn("crossover", SPECS)
        self.assertIn("parallels", SPECS)
        for spec in SPECS.values():
            self.assertTrue(spec.app_paths)
            self.assertTrue(spec.bundle_id)


if __name__ == "__main__":
    unittest.main()
