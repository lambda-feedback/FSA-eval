import unittest

from .evaluation import evaluation_function
from lf_toolkit.shared.params import Params


class TestEvaluationFunction(unittest.TestCase):
    """Tests for FSA evaluation function."""

    def test_correct_fsa(self):
        """Test that identical FSAs are marked correct."""
        fsa = {
            "states": ["q0", "q1"],
            "alphabet": ["a"],
            "transitions": [
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            ],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }
        result = evaluation_function(fsa, fsa, Params()).to_dict()
        self.assertEqual(result.get("is_correct"), True)

    def test_equivalent_fsas(self):
        """Test that equivalent FSAs with different state names are correct."""
        student = {
            "states": ["s0", "s1"],
            "alphabet": ["a"],
            "transitions": [
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
                {"from_state": "s1", "to_state": "s1", "symbol": "a"},
            ],
            "initial_state": "s0",
            "accept_states": ["s1"]
        }
        expected = {
            "states": ["q0", "q1"],
            "alphabet": ["a"],
            "transitions": [
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            ],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }
        result = evaluation_function(student, expected, Params()).to_dict()
        self.assertEqual(result.get("is_correct"), True)

    def test_incorrect_fsa(self):
        """Test that non-equivalent FSAs are marked incorrect."""
        # Student accepts: a+ (one or more a's)
        student = {
            "states": ["q0", "q1"],
            "alphabet": ["a"],
            "transitions": [
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            ],
            "initial_state": "q0",
            "accept_states": ["q1"]
        }
        # Expected accepts: a* (zero or more a's) - different because q0 is accepting
        expected = {
            "states": ["q0", "q1"],
            "alphabet": ["a"],
            "transitions": [
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            ],
            "initial_state": "q0",
            "accept_states": ["q0", "q1"]  # q0 also accepting
        }
        result = evaluation_function(student, expected, Params()).to_dict()
        self.assertEqual(result.get("is_correct"), False)

    def test_invalid_fsa_format(self):
        """Test that invalid FSA format is handled gracefully."""
        result = evaluation_function("not an fsa", {}, Params()).to_dict()
        self.assertEqual(result.get("is_correct"), False)
        self.assertIn("error", result.get("feedback", "").lower())
