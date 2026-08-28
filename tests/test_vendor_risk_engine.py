import csv
import json
import tempfile
import unittest
from pathlib import Path

from main import (
    DEFAULT_THRESHOLDS,
    DEFAULT_WEIGHTS,
    compliance_risk,
    rank_results,
    risk_level,
    score_csv,
    score_vendor,
    validate_thresholds,
    validate_weights,
    write_results_csv,
)


class VendorRiskEngineTests(unittest.TestCase):
    def test_low_risk_vendor(self):
        result = score_vendor(
            vendor="Supplier A",
            on_time_delivery=98,
            defect_rate=0.5,
            prepayment_exposure=0,
            compliance_incidents=0,
            dependency_share=20,
        )

        self.assertEqual(result["risk"], "LOW")
        self.assertAlmostEqual(result["score"], 3.85)

    def test_medium_risk_vendor(self):
        result = score_vendor(
            vendor="Supplier B",
            on_time_delivery=85,
            defect_rate=3,
            prepayment_exposure=40,
            compliance_incidents=1,
            dependency_share=50,
        )

        self.assertEqual(result["risk"], "MEDIUM")
        self.assertAlmostEqual(result["score"], 31.0)

    def test_critical_risk_vendor(self):
        result = score_vendor(
            vendor="Supplier C",
            on_time_delivery=60,
            defect_rate=8,
            prepayment_exposure=100,
            compliance_incidents=3,
            dependency_share=100,
        )

        self.assertEqual(result["risk"], "CRITICAL")
        self.assertAlmostEqual(result["score"], 77.0)

    def test_quality_risk_is_capped_at_100(self):
        result = score_vendor(
            vendor="Supplier D",
            on_time_delivery=100,
            defect_rate=15,
            prepayment_exposure=0,
            compliance_incidents=0,
            dependency_share=0,
        )

        self.assertEqual(result["components"]["quality"], 100.0)
        self.assertAlmostEqual(result["score"], 25.0)

    def test_compliance_risk_scale(self):
        self.assertEqual(compliance_risk(0), 0.0)
        self.assertEqual(compliance_risk(1), 40.0)
        self.assertEqual(compliance_risk(2), 70.0)
        self.assertEqual(compliance_risk(3), 100.0)
        self.assertEqual(compliance_risk(8), 100.0)

    def test_invalid_percentage_rejected(self):
        with self.assertRaises(ValueError):
            score_vendor(
                vendor="Supplier E",
                on_time_delivery=101,
                defect_rate=1,
                prepayment_exposure=0,
                compliance_incidents=0,
                dependency_share=10,
            )

    def test_negative_incident_count_rejected(self):
        with self.assertRaises(ValueError):
            compliance_risk(-1)

    def test_default_risk_level_thresholds(self):
        self.assertEqual(risk_level(24.99), "LOW")
        self.assertEqual(risk_level(25), "MEDIUM")
        self.assertEqual(risk_level(50), "HIGH")
        self.assertEqual(risk_level(75), "CRITICAL")

    def test_custom_thresholds_change_classification_not_score(self):
        custom_thresholds = {
            "medium": 20.0,
            "high": 30.0,
            "critical": 40.0,
        }
        result = score_vendor(
            vendor="Supplier B",
            on_time_delivery=85,
            defect_rate=3,
            prepayment_exposure=40,
            compliance_incidents=1,
            dependency_share=50,
            thresholds=custom_thresholds,
        )

        self.assertAlmostEqual(result["score"], 31.0)
        self.assertEqual(result["risk"], "HIGH")
        self.assertEqual(result["thresholds"], custom_thresholds)
        self.assertEqual(result["policy"]["thresholds"], custom_thresholds)

    def test_default_thresholds_are_valid(self):
        self.assertEqual(validate_thresholds(DEFAULT_THRESHOLDS), DEFAULT_THRESHOLDS)

    def test_invalid_threshold_order_rejected(self):
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            validate_thresholds(
                {
                    "medium": 30,
                    "high": 30,
                    "critical": 75,
                }
            )

    def test_threshold_out_of_range_rejected(self):
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            validate_thresholds(
                {
                    "medium": -1,
                    "high": 50,
                    "critical": 75,
                }
            )

    def test_result_is_json_serializable_and_versioned(self):
        result = score_vendor(
            vendor="Supplier JSON",
            on_time_delivery=90,
            defect_rate=2,
            prepayment_exposure=10,
            compliance_incidents=0,
            dependency_share=20,
        )

        encoded = json.dumps(result)
        self.assertIn('"vendor": "Supplier JSON"', encoded)
        self.assertEqual(result["meta"]["engine"], "vendor-risk-engine")
        self.assertEqual(result["meta"]["engine_version"], "0.4.0")
        self.assertEqual(result["meta"]["model_version"], "vendor-risk-v1")
        self.assertEqual(result["meta"]["schema_version"], "1.0")
        self.assertEqual(result["policy"]["weights"], result["weights"])

    def test_score_csv_multiple_vendors(self):
        csv_text = (
            "vendor,on_time_delivery,defect_rate,prepayment_exposure,"
            "compliance_incidents,dependency_share\n"
            "Supplier A,98,0.5,0,0,20\n"
            "Supplier B,85,3,40,1,50\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vendors.csv"
            path.write_text(csv_text, encoding="utf-8")
            results = score_csv(path)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["risk"], "LOW")
        self.assertEqual(results[1]["risk"], "MEDIUM")
        self.assertAlmostEqual(results[1]["score"], 31.0)
        self.assertEqual(results[1]["meta"]["engine_version"], "0.4.0")

    def test_score_csv_missing_column_rejected(self):
        csv_text = (
            "vendor,on_time_delivery,defect_rate,prepayment_exposure,"
            "compliance_incidents\n"
            "Supplier A,98,0.5,0,0\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vendors.csv"
            path.write_text(csv_text, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "dependency_share"):
                score_csv(path)

    def test_score_csv_invalid_row_reports_row_number(self):
        csv_text = (
            "vendor,on_time_delivery,defect_rate,prepayment_exposure,"
            "compliance_incidents,dependency_share\n"
            "Supplier A,98,not-a-number,0,0,20\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vendors.csv"
            path.write_text(csv_text, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "CSV row 2"):
                score_csv(path)

    def test_default_weights_total_100_percent(self):
        validated = validate_weights(DEFAULT_WEIGHTS)
        self.assertAlmostEqual(sum(validated.values()), 1.0)

    def test_custom_weights_change_score(self):
        custom_weights = {
            "delivery": 0.40,
            "quality": 0.30,
            "commercial": 0.15,
            "compliance": 0.10,
            "dependency": 0.05,
        }
        result = score_vendor(
            vendor="Supplier B",
            on_time_delivery=85,
            defect_rate=3,
            prepayment_exposure=40,
            compliance_incidents=1,
            dependency_share=50,
            weights=custom_weights,
        )

        self.assertAlmostEqual(result["score"], 27.5)
        self.assertEqual(result["weights"], custom_weights)

    def test_invalid_weight_total_rejected(self):
        with self.assertRaisesRegex(ValueError, "total 100%"):
            validate_weights(
                {
                    "delivery": 0.40,
                    "quality": 0.30,
                    "commercial": 0.20,
                    "compliance": 0.10,
                    "dependency": 0.10,
                }
            )

    def test_negative_weight_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            validate_weights(
                {
                    "delivery": 0.40,
                    "quality": 0.30,
                    "commercial": 0.20,
                    "compliance": 0.15,
                    "dependency": -0.05,
                }
            )

    def test_score_csv_uses_custom_weights_and_thresholds(self):
        csv_text = (
            "vendor,on_time_delivery,defect_rate,prepayment_exposure,"
            "compliance_incidents,dependency_share\n"
            "Supplier B,85,3,40,1,50\n"
        )
        custom_weights = {
            "delivery": 0.40,
            "quality": 0.30,
            "commercial": 0.15,
            "compliance": 0.10,
            "dependency": 0.05,
        }
        custom_thresholds = {
            "medium": 20.0,
            "high": 25.0,
            "critical": 60.0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vendors.csv"
            path.write_text(csv_text, encoding="utf-8")
            results = score_csv(
                path,
                weights=custom_weights,
                thresholds=custom_thresholds,
            )

        self.assertAlmostEqual(results[0]["score"], 27.5)
        self.assertEqual(results[0]["risk"], "HIGH")

    def test_rank_results_highest_risk_first(self):
        results = [
            {"vendor": "Low", "score": 10.0},
            {"vendor": "Critical", "score": 80.0},
            {"vendor": "Medium", "score": 30.0},
        ]
        ranked = rank_results(results)

        self.assertEqual(
            [result["vendor"] for result in ranked],
            ["Critical", "Medium", "Low"],
        )

    def test_write_results_csv_includes_rank_and_breakdown(self):
        results = [
            score_vendor(
                vendor="Supplier A",
                on_time_delivery=98,
                defect_rate=0.5,
                prepayment_exposure=0,
                compliance_incidents=0,
                dependency_share=20,
            ),
            score_vendor(
                vendor="Supplier C",
                on_time_delivery=60,
                defect_rate=8,
                prepayment_exposure=100,
                compliance_incidents=3,
                dependency_share=100,
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.csv"
            ranked = write_results_csv(results, path)

            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(ranked[0]["vendor"], "Supplier C")
        self.assertEqual(rows[0]["rank"], "1")
        self.assertEqual(rows[0]["vendor"], "Supplier C")
        self.assertEqual(rows[0]["risk"], "CRITICAL")
        self.assertIn("delivery_weighted", rows[0])


if __name__ == "__main__":
    unittest.main()
