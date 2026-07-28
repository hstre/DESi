import unittest

from desi_validation.models import CandidateUpdate
from desi_validation.validator import validate_candidate


BASE = {
    "candidate_id": "msce-l3-001",
    "claim": "Tool X is reliable for bounded task class Y.",
    "items": [
        {
            "item_id": "obs-1",
            "item_type": "observation",
            "text": "Tool X completed 18 of 20 verified episodes.",
            "evidence_ids": ["ev-1"],
        },
        {
            "item_id": "inf-1",
            "item_type": "inference",
            "text": "Tool X is operationally reliable under the tested conditions.",
            "evidence_ids": ["ev-1"],
        },
    ],
    "evidence": [
        {
            "anchor_id": "ev-1",
            "source_id": "trace-batch-7",
            "content_hash": "sha256:abc",
            "locator": "episodes:1-20",
            "polarity": "support",
        }
    ],
    "source_trace_ids": ["trace-1", "trace-2"],
    "policy_ids": ["policy-9"],
    "applicability_boundary": "Only for task class Y under configuration C.",
    "proposed_target": "L3",
}


class ValidationApiTests(unittest.TestCase):
    def test_supported_candidate_is_admissible(self):
        result = validate_candidate(CandidateUpdate.from_dict(BASE))
        self.assertEqual(result.decision.value, "admissible")

    def test_assumption_is_retained_as_hypothesis(self):
        payload = dict(BASE)
        payload["items"] = BASE["items"] + [
            {
                "item_id": "asm-1",
                "item_type": "assumption",
                "text": "The observed effect is causal.",
                "evidence_ids": [],
            }
        ]
        result = validate_candidate(CandidateUpdate.from_dict(payload))
        self.assertEqual(result.decision.value, "retained_as_hypothesis")

    def test_counterevidence_blocks_promotion(self):
        payload = dict(BASE)
        payload["evidence"] = BASE["evidence"] + [
            {
                "anchor_id": "ev-counter",
                "source_id": "trace-21",
                "content_hash": "sha256:def",
                "polarity": "counter",
            }
        ]
        result = validate_candidate(CandidateUpdate.from_dict(payload))
        self.assertEqual(result.decision.value, "contradicted")

    def test_identical_input_has_identical_result(self):
        candidate = CandidateUpdate.from_dict(BASE)
        first = validate_candidate(candidate).to_dict()
        second = validate_candidate(candidate).to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
