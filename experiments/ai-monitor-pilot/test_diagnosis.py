import unittest
import diagnosis as d

class DiagnosisTests(unittest.TestCase):
    def test_unrelated_disconnect_is_not_cause(self):
        p=d.context_rules({"context":[{"id":"E0","component":"other_monitor","event":"disconnected"}]})
        self.assertEqual(p["candidate"],"unknown")

    def test_conflicting_evidence_requires_abstention(self):
        p=d.context_rules({"context":[{"id":"E0","component":"output","selection_stride":8},
            {"id":"E1","component":"output","queue_fraction":.99,"discarded_delta":5}]})
        self.assertEqual(p["candidate"],"unknown")
        self.assertEqual(set(p["evidence_ids"]),{"E0","E1"})

    def test_unknown_evidence_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            d.validate({"candidate":"unknown","evidence_ids":["E9"],
                        "checks":["collect_missing_context"]},{"context":[]})

    def test_missing_context_means_unknown(self):
        p=d.context_rules({"context":[]})
        self.assertEqual(p["candidate"],"unknown")
        self.assertIn("collect_missing_context",p["checks"])
