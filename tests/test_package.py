import unittest

import vendor_risk_engine


class PackageTests(unittest.TestCase):
    def test_public_version(self):
        self.assertEqual(vendor_risk_engine.__version__, "0.4.0")
        self.assertEqual(vendor_risk_engine.VERSION, "0.4")

    def test_public_scoring_api(self):
        result = vendor_risk_engine.score_vendor(
            "Supplier A",
            on_time_delivery=90,
            defect_rate=1,
            prepayment_exposure=20,
            compliance_incidents=0,
            dependency_share=25,
        )
        self.assertEqual(result["vendor"], "Supplier A")
        self.assertIn(result["risk"], {"LOW", "MEDIUM", "HIGH", "CRITICAL"})
        self.assertEqual(result["meta"]["engine_version"], "0.4.0")

    def test_public_policy_api(self):
        thresholds = vendor_risk_engine.validate_thresholds(
            {"medium": 20, "high": 40, "critical": 60}
        )
        self.assertEqual(thresholds["high"], 40.0)


if __name__ == "__main__":
    unittest.main()
