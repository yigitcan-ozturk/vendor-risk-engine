import unittest

from main import compliance_risk, risk_level, score_vendor


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


if __name__ == "__main__":
    unittest.main()
