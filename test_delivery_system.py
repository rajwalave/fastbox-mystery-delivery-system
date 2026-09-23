"""Tests for the FastBox Mystery Delivery System."""

import json
import tempfile
import unittest
from pathlib import Path

from delivery_system import (
    assign_packages,
    build_report,
    euclidean_distance,
    load_data,
)


ROOT = Path(__file__).parent
TEST_CASES = ROOT / "test_cases"


class DeliverySystemTests(unittest.TestCase):
    def test_euclidean_distance(self):
        self.assertAlmostEqual(euclidean_distance((0, 0), (3, 4)), 5.0)

    def test_base_case_supports_list_format(self):
        warehouses, agents, packages = load_data(ROOT / "base_case.json")
        report = build_report(warehouses, agents, packages)
        self.assertEqual(report["summary"]["total_packages"], 5)
        self.assertEqual(report["summary"]["packages_delivered"], 5)
        self.assertTrue(report["summary"]["all_packages_delivered"])

    def test_test_cases_support_dictionary_format(self):
        for case_file in sorted(TEST_CASES.glob("test_case_*.json")):
            with self.subTest(case_file=case_file.name):
                warehouses, agents, packages = load_data(case_file)
                report = build_report(warehouses, agents, packages)
                self.assertEqual(report["summary"]["total_packages"], len(packages))
                self.assertEqual(report["summary"]["packages_delivered"], len(packages))
                self.assertTrue(report["summary"]["all_packages_delivered"])
                self.assertIsNotNone(report["best_agent"])

    def test_nearest_agent_assignment(self):
        warehouses = {"W1": (0.0, 0.0)}
        agents = {"A1": (1.0, 1.0), "A2": (10.0, 10.0)}
        packages = [{"id": "P1", "warehouse_id": "W1", "destination": (2.0, 2.0)}]
        assignments = assign_packages(warehouses, agents, packages)
        self.assertEqual([p["id"] for p in assignments["A1"]], ["P1"])
        self.assertEqual(assignments["A2"], [])

    def test_tie_break_is_deterministic(self):
        warehouses = {"W1": (0.0, 0.0)}
        agents = {"A2": (1.0, 0.0), "A1": (-1.0, 0.0)}
        packages = [{"id": "P1", "warehouse_id": "W1", "destination": (0.0, 1.0)}]
        assignments = assign_packages(warehouses, agents, packages)
        self.assertEqual([p["id"] for p in assignments["A1"]], ["P1"])

    def test_invalid_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_data(path)


if __name__ == "__main__":
    unittest.main()
