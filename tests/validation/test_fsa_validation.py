import unittest

from evaluation_function.validation.validation import *
from evaluation_function.schemas.utils import make_fsa


class TestFSAValidation(unittest.TestCase):
    
    def test_valid_fsa_basic(self):
        """A valid FSA should return an empty error list."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}
            ],
            initial="q0",
            accept=["q1"],
        )
        
        errors = is_valid_fsa(fsa)
        self.assertEqual(errors, [])
    
    def test_invalid_initial_state(self):
        """An FSA with an undefined initial state should return an error."""
        fsa = make_fsa(
            states=["q1"],
            alphabet=["a"],
            transitions=[],
            initial="q0",  # q0 is not in states
            accept=[],
        )
        
        errors = is_valid_fsa(fsa)
        self.assertGreater(len(errors), 0)
        
        # Check that we have the right error code
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.INVALID_INITIAL, error_codes)
    
    def test_invalid_accept_state(self):
        """An FSA with undefined accept states should return errors."""
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["q1"],  # q1 is not in states
        )
        
        errors = is_valid_fsa(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.INVALID_ACCEPT, error_codes)
    
    def test_invalid_transition_source(self):
        """An FSA with transitions from undefined states should return errors."""
        fsa = make_fsa(
            states=["q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}  # q0 not in states
            ],
            initial="q1",
            accept=[],
        )
        
        errors = is_valid_fsa(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.INVALID_TRANSITION_SOURCE, error_codes)
    
    def test_invalid_transition_destination(self):
        """An FSA with transitions to undefined states should return errors."""
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}  # q1 not in states
            ],
            initial="q0",
            accept=[],
        )
        
        errors = is_valid_fsa(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.INVALID_TRANSITION_DEST, error_codes)
    
    def test_invalid_transition_symbol(self):
        """An FSA with transitions using symbols not in alphabet should return errors."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "b"}  # b not in alphabet
            ],
            initial="q0",
            accept=["q1"],
        )
        
        errors = is_valid_fsa(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.INVALID_SYMBOL, error_codes)

    # seems that be the pydantic model def, these are impossible
    # def test_empty_states(self):
    #     """An FSA with no states should return an error."""
    #     fsa = make_fsa(
    #         states=[],  # Empty states
    #         alphabet=["a"],
    #         transitions=[],
    #         initial="q0",
    #         accept=[],
    #     )
        
    #     errors = is_valid_fsa(fsa)
    #     self.assertGreater(len(errors), 0)
        
    #     error_codes = [err.code for err in errors]
    #     self.assertIn(ErrorCode.EMPTY_STATES, error_codes)
    
    # def test_empty_alphabet(self):
    #     """An FSA with empty alphabet should return an error."""
    #     fsa = make_fsa(
    #         states=["q0"],
    #         alphabet=[],  # Empty alphabet
    #         transitions=[],
    #         initial="q0",
    #         accept=[],
    #     )
        
    #     errors = is_valid_fsa(fsa)
    #     self.assertGreater(len(errors), 0)
        
    #     error_codes = [err.code for err in errors]
    #     self.assertIn(ErrorCode.EMPTY_ALPHABET, error_codes)
    
    def test_deterministic_fsa(self):
        """A deterministic FSA should return an empty error list from is_deterministic."""
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
        
        errors = is_deterministic(fsa)
        self.assertEqual(errors, [])
    
    def test_nondeterministic_fsa(self):
        """A non-deterministic FSA should return errors from is_deterministic."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "a"},  # Two transitions on 'a' from q0
            ],
            initial="q0",
            accept=["q2"],
        )
        
        errors = is_deterministic(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.DUPLICATE_TRANSITION, error_codes)
    
    def test_complete_dfa(self):
        """A complete DFA should return an empty error list from is_complete."""
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
        
        errors = is_complete(fsa)
        self.assertEqual(errors, [])
    
    def test_incomplete_dfa(self):
        """An incomplete DFA should return errors from is_complete."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                # Missing: q0 on b, q1 on a, q1 on b
            ],
            initial="q0",
            accept=["q1"],
        )
        
        errors = is_complete(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.MISSING_TRANSITION, error_codes)
        
        # Should have 3 missing transitions (q0-b, q1-a, q1-b)
        self.assertEqual(len(errors), 3)
    
    def test_is_complete_requires_deterministic(self):
        """is_complete should return errors if FSA is non-deterministic."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"},
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},  # Non-deterministic
            ],
            initial="q0",
            accept=["q1"],
        )
        
        errors = is_complete(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.NOT_DETERMINISTIC, error_codes)
        self.assertIn(ErrorCode.DUPLICATE_TRANSITION, error_codes)
    
    def test_single_state_complete_fsa(self):
        """A single-state complete FSA should return no errors from is_complete."""
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"}
            ],
            initial="q0",
            accept=["q0"],
        )
        
        errors = is_complete(fsa)
        self.assertEqual(errors, [])
    
    def test_find_unreachable_states(self):
        """Should identify unreachable states."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],  # q2 is unreachable
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"}
            ],
            initial="q0",
            accept=["q1"],
        )
        
        errors = find_unreachable_states(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.UNREACHABLE_STATE, error_codes)
        
        # Check that q2 is in the error messages
        error_messages = [err.message for err in errors]
        self.assertTrue(any("q2" in msg for msg in error_messages))
    
    def test_find_dead_states(self):
        """Should identify dead states."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q2", "symbol": "b"},  # q2 is a sink/dead state
                {"from_state": "q2", "to_state": "q2", "symbol": "a"},
                {"from_state": "q2", "to_state": "q2", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],  # q2 cannot reach q1
        )
        
        errors = find_dead_states(fsa)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.DEAD_STATE, error_codes)
        
        # Check that q2 is in the error messages
        error_messages = [err.message for err in errors]
        self.assertTrue(any("q2" in msg for msg in error_messages))
    
    def test_find_dead_states_with_no_accept_states(self):
        """All states should be dead if there are no accept states."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q0", "symbol": "a"},
            ],
            initial="q0",
            accept=[],  # No accept states
        )
        
        errors = find_dead_states(fsa)
        self.assertGreater(len(errors), 0)
        
        # Both q0 and q1 should be dead
        self.assertEqual(len(errors), 2)
    
    def test_accepts_string_accepted(self):
        """A string that should be accepted returns empty error list."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]
        )
        
        errors = accepts_string(fsa, "a")
        self.assertEqual(errors, [])
    
    def test_accepts_string_rejected_no_transition(self):
        """A string that has no transition returns an error."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]
        )
        
        errors = accepts_string(fsa, "aa")
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.TEST_CASE_FAILED, error_codes)
    
    def test_accepts_string_rejected_non_accepting(self):
        """A string that ends in non-accepting state returns an error."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q0", "symbol": "a"}
            ],
            initial="q0",
            accept=["q1"]  # Only q1 is accepting
        )
        
        # "aa" goes q0->q1->q0, q0 is not accepting
        errors = accepts_string(fsa, "aa")
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.TEST_CASE_FAILED, error_codes)
    
    def test_accepts_string_empty_string_accepted(self):
        """Empty string should be accepted if initial state is accepting."""
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"]  # q0 is accepting
        )
        
        errors = accepts_string(fsa, "")
        self.assertEqual(errors, [])
    
    def test_accepts_string_empty_string_rejected(self):
        """Empty string should be rejected if initial state is not accepting."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]  # q0 is not accepting
        )
        
        errors = accepts_string(fsa, "")
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.TEST_CASE_FAILED, error_codes)
    
    def test_accepts_string_invalid_symbol(self):
        """String with symbol not in alphabet should return an error."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]
        )
        
        errors = accepts_string(fsa, "ab")  # 'b' not in alphabet
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.INVALID_SYMBOL, error_codes)
    
    def test_fsas_accept_same_string_agree(self):
        """Two FSAs that both accept a string should return empty list."""
        fsa1 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]
        )
        
        fsa2 = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[{"from_state": "s0", "to_state": "s1", "symbol": "a"}],
            initial="s0",
            accept=["s1"]
        )
        
        errors = fsas_accept_same_string(fsa1, fsa2, "a")
        self.assertEqual(errors, [])
    
    def test_fsas_accept_same_string_disagree(self):
        """Two FSAs that disagree on a string should return an error."""
        fsa1 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]  # Accepts "a"
        )
        
        fsa2 = make_fsa(
            states=["s0"],
            alphabet=["a"],
            transitions=[{"from_state": "s0", "to_state": "s0", "symbol": "a"}],
            initial="s0",
            accept=[]  # Rejects everything
        )
        
        errors = fsas_accept_same_string(fsa1, fsa2, "a")
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.LANGUAGE_MISMATCH, error_codes)
    
    def test_fsas_accept_same_language_equivalent(self):
        """Two equivalent FSAs should return empty list."""
        fsa1 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]
        )
        
        fsa2 = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[{"from_state": "s0", "to_state": "s1", "symbol": "a"}],
            initial="s0",
            accept=["s1"]
        )
        
        errors = fsas_accept_same_language(fsa1, fsa2, max_length=2)
        self.assertEqual(errors, [])
    
    def test_fsas_accept_same_language_different(self):
        """Two non-equivalent FSAs should return an error."""
        fsa1 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"]  # Accepts only "a"
        )
        
        fsa3 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q0"]  # Accepts only empty string
        )
        
        errors = fsas_accept_same_language(fsa1, fsa3, max_length=1)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.LANGUAGE_MISMATCH, error_codes)
    
    def test_fsas_accept_same_language_different_alphabet(self):
        """FSAs with different alphabets should return an error."""
        fsa1 = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"]
        )
        
        fsa2 = make_fsa(
            states=["s0"],
            alphabet=["b"],  # Different alphabet
            transitions=[{"from_state": "s0", "to_state": "s0", "symbol": "b"}],
            initial="s0",
            accept=["s0"]
        )
        
        errors = fsas_accept_same_language(fsa1, fsa2, max_length=1)
        self.assertGreater(len(errors), 0)
        
        error_codes = [err.code for err in errors]
        self.assertIn(ErrorCode.LANGUAGE_MISMATCH, error_codes)
    
    def test_get_structured_info_of_fsa(self):
        """get_structured_info_of_fsa should return a StructuralInfo object with correct fields."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "b"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q2", "symbol": "b"},
                {"from_state": "q2", "to_state": "q2", "symbol": "a"},
                {"from_state": "q2", "to_state": "q2", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"]  # q2 is dead state
        )
        
        info = get_structured_info_of_fsa(fsa)
        print(info, type(info))
        
        # Check basic properties
        self.assertIsInstance(info, StructuralInfo)
        self.assertTrue(info.is_deterministic)
        self.assertTrue(info.is_complete)
        self.assertEqual(info.num_states, 3)
        self.assertEqual(info.num_transitions, 6)
        
        # Check unreachable states (should be none in this FSA)
        self.assertEqual(len(info.unreachable_states), 0)
        
        # Check dead states (q2 is dead)
        self.assertEqual(len(info.dead_states), 1)
        self.assertIn("q2", info.dead_states)


if __name__ == "__main__":
    unittest.main()