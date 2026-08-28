import csv
import json
import tempfile
import unittest
from pathlib import Path

from main import (
    DEFAULT_THRESHOLDS,
    DEFAULT_TREND_TOLERANCE,
    DEFAULT_WEIGHTS,
    compliance_risk,
    rank_results,
    parse_review_date,
    risk_level,
    score_csv,
    score_history_csv,
    score_vendor,
    trend_direction,
    validate_thresholds,
    validate_trend_tolerance,
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
        self.assertEqual(result["meta"]["engine_version"], "0.5.0")
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
        self.assertEqual(results[1]["meta"]["engine_version"], "0.5.0")

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

    def test_trend_direction_uses_tolerance(self):
        self.assertEqual(trend_direction(2.0), "STABLE")
        self.assertEqual(trend_direction(2.01), "DETERIORATING")
        self.assertEqual(trend_direction(-2.01), "IMPROVING")
        self.assertEqual(
            trend_direction(4.0, tolerance=5.0),
            "STABLE",
        )

    def test_trend_tolerance_validation(self):
        self.assertEqual(
            validate_trend_tolerance(DEFAULT_TREND_TOLERANCE),
            2.0,
        )
        with self.assertRaisesRegex(ValueError, "between 0 and 100"):
            validate_trend_tolerance(-1)

    def test_parse_review_date_requires_iso_format(self):
        self.assertEqual(
            parse_review_date("2026-08-28").isoformat(),
            "2026-08-28",
        )
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            parse_review_date("28/08/2026")

    def test_score_history_csv_detects_deterioration(self):
        csv_text = (
            "as_of_date,vendor,on_time_delivery,defect_rate,"
            "prepayment_exposure,compliance_incidents,dependency_share\n"
            "2026-06-30,Supplier Trend,98,0.5,0,0,20\n"
            "2026-07-31,Supplier Trend,90,2,20,0,30\n"
            "2026-08-31,Supplier Trend,80,4,40,1,50\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "history.csv"
            path.write_text(csv_text, encoding="utf-8")
            trends = score_history_csv(path)

        self.assertEqual(len(trends), 1)
        trend = trends[0]
        self.assertEqual(trend["vendor"], "Supplier Trend")
        self.assertEqual(trend["observations"], 3)
        self.assertEqual(trend["direction"], "DETERIORATING")
        self.assertGreater(trend["latest_delta"], 2.0)
        self.assertGreater(trend["change_from_first"], 0)
        self.assertEqual(trend["current_as_of_date"], "2026-08-31")
        self.assertEqual(trend["meta"]["engine_version"], "0.5.0")
        self.assertEqual(trend["meta"]["model_version"], "vendor-risk-trend-v1")
        self.assertEqual(len(trend["history"]), 3)

    def test_score_history_csv_detects_improvement(self):
        csv_text = (
            "as_of_date,vendor,on_time_delivery,defect_rate,"
            "prepayment_exposure,compliance_incidents,dependency_share\n"
            "2026-06-30,Supplier Improve,75,5,60,1,60\n"
            "2026-07-31,Supplier Improve,90,2,20,0,30\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "history.csv"
            path.write_text(csv_text, encoding="utf-8")
            trends = score_history_csv(path)

        self.assertEqual(trends[0]["direction"], "IMPROVING")
        self.assertLess(trends[0]["latest_delta"], -2.0)

    def test_score_history_csv_single_observation_is_insufficient(self):
        csv_text = (
            "as_of_date,vendor,on_time_delivery,defect_rate,"
            "prepayment_exposure,compliance_incidents,dependency_share\n"
            "2026-08-31,Supplier New,95,1,0,0,20\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "history.csv"
            path.write_text(csv_text, encoding="utf-8")
            trends = score_history_csv(path)

        self.assertEqual(trends[0]["direction"], "INSUFFICIENT_HISTORY")
        self.assertIsNone(trends[0]["latest_delta"])

    def test_score_history_csv_rejects_duplicate_vendor_date(self):
        csv_text = (
            "as_of_date,vendor,on_time_delivery,defect_rate,"
            "prepayment_exposure,compliance_incidents,dependency_share\n"
            "2026-08-31,Supplier Dup,95,1,0,0,20\n"
            "2026-08-31,Supplier Dup,90,2,10,0,25\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "history.csv"
            path.write_text(csv_text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate as_of_date"):
                score_history_csv(path)

    def test_score_history_csv_rejects_missing_date_column(self):
        csv_text = (
            "vendor,on_time_delivery,defect_rate,prepayment_exposure,"
            "compliance_incidents,dependency_share\n"
            "Supplier A,98,0.5,0,0,20\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "history.csv"
            path.write_text(csv_text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "as_of_date"):
                score_history_csv(path)

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
