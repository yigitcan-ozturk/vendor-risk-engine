import json
import tempfile
import unittest
from pathlib import Path

from main import compliance_risk, risk_level, score_csv, score_vendor


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

    def test_risk_level_thresholds(self):
        self.assertEqual(risk_level(24.99), "LOW")
        self.assertEqual(risk_level(25), "MEDIUM")
        self.assertEqual(risk_level(50), "HIGH")
        self.assertEqual(risk_level(75), "CRITICAL")

    def test_result_is_json_serializable(self):
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


if __name__ == "__main__":
    unittest.main()
