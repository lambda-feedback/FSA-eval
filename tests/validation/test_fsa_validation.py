import unittest

from evaluation_function.schemas.validation import (
    is_valid_fsa,
    is_deterministic,
    is_complete,
)

from evaluation_function.schemas.fsa import FSA, Transition
from .utils import make_fsa


class TestFSAValidation(unittest.TestCase):

    # a valid fsa should be identified as valid
    def test_valid_fsa_basic(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}
            ],
            initial="q0",
            accept=["q1"],
        )

        self.assertTrue(is_valid_fsa(fsa))

    # an invalid fsa should be identified as invalid
    def test_invalid_initial_state(self):
        fsa = make_fsa(
            states=["q1"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=[],
        )

        self.assertFalse(is_valid_fsa(fsa))

    # an fsa with unknown transition states is not a valid fsa
    def test_invalid_transition_state(self):
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}
            ],
            initial="q0",
            accept=[],
        )

        self.assertFalse(is_valid_fsa(fsa))

    # deterministic but incomplete
    def test_deterministic_but_incomplete(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}
            ],
            initial="q0",
            accept=["q1"],
        )

        self.assertTrue(is_deterministic(fsa))
        self.assertFalse(is_complete(fsa))

    # nondeterministic fsa
    def test_nondeterministic_fsa(self):
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )

        self.assertFalse(is_deterministic(fsa))
        self.assertFalse(is_complete(fsa))

    # complete dfa
    def test_complete_dfa(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q0", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],
        )

        self.assertTrue(is_valid_fsa(fsa))
        self.assertTrue(is_deterministic(fsa))
        self.assertTrue(is_complete(fsa))

    # edge case: single state complete fsa
    def test_single_state_complete_fsa(self):
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"}
            ],
            initial="q0",
            accept=["q0"],
        )

        self.assertTrue(is_complete(fsa))


if __name__ == "__main__":
    unittest.main()
