"""
Comprehensive tests for FSA validation, analysis, and comparison.

Covers validation rules, determinism, completeness, reachability,
dead states, string acceptance, language equivalence, and DFA isomorphism.
"""

import pytest

from evaluation_function.validation.validation import *
from evaluation_function.schemas.utils import make_fsa
from evaluation_function.schemas import ErrorCode


class TestFSAValidation:
    """Tests for basic FSA validation rules."""

    def test_valid_fsa_basic(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        assert is_valid_fsa(fsa).ok

    def test_invalid_initial_state(self):
        fsa = make_fsa(
            states=["q1"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=[],
        )
        result = is_valid_fsa(fsa)
        assert not result.ok
        assert ErrorCode.INVALID_INITIAL in [e.code for e in result.errors]

    def test_invalid_accept_state(self):
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["q1"],
        )
        result = is_valid_fsa(fsa)
        assert not result.ok
        assert ErrorCode.INVALID_ACCEPT in [e.code for e in result.errors]

    def test_invalid_transition_source(self):
        fsa = make_fsa(
            states=["q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q1",
            accept=[],
        )
        result = is_valid_fsa(fsa)
        assert ErrorCode.INVALID_TRANSITION_SOURCE in [e.code for e in result.errors]

    def test_invalid_transition_destination(self):
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=[],
        )
        result = is_valid_fsa(fsa)
        assert ErrorCode.INVALID_TRANSITION_DEST in [e.code for e in result.errors]

    def test_invalid_transition_symbol(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "b"}],
            initial="q0",
            accept=["q1"],
        )
        result = is_valid_fsa(fsa)
        assert ErrorCode.INVALID_SYMBOL in [e.code for e in result.errors]


class TestDeterminism:
    """Tests for determinism checking."""

    def test_deterministic_fsa(self):
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
        assert is_deterministic(fsa).ok

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
        result = is_deterministic(fsa)
        assert not result.ok
        assert ErrorCode.DUPLICATE_TRANSITION in [e.code for e in result.errors]


class TestCompleteness:
    """Tests for DFA completeness."""

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
        assert is_complete(fsa).ok

    def test_incomplete_dfa(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        result = is_complete(fsa)
        assert not result.ok
        assert ErrorCode.MISSING_TRANSITION in [e.code for e in result.errors]

    def test_complete_requires_deterministic(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"},
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            ],
            initial="q0",
            accept=["q1"],
        )
        result = is_complete(fsa)
        codes = [e.code for e in result.errors]
        assert ErrorCode.NOT_DETERMINISTIC in codes
        assert ErrorCode.DUPLICATE_TRANSITION in codes


class TestReachabilityAndDeadStates:
    """Tests for unreachable and dead states."""

    def test_find_unreachable_states(self):
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        result = find_unreachable_states(fsa)
        assert not result.ok
        assert ErrorCode.UNREACHABLE_STATE in [e.code for e in result.errors]

    def test_find_dead_states(self):
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q2", "symbol": "b"},
                {"from_state": "q2", "to_state": "q2", "symbol": "a"},
                {"from_state": "q2", "to_state": "q2", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],
        )
        result = find_dead_states(fsa)
        assert not result.ok
        assert ErrorCode.DEAD_STATE in [e.code for e in result.errors]

    def test_dead_states_no_accept_states(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q0", "symbol": "a"},
            ],
            initial="q0",
            accept=[],
        )
        result = find_dead_states(fsa)
        assert len(result.errors) == 2


class TestStringAcceptance:
    """Tests for string acceptance."""

    def test_accepts_string(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        assert accepts_string(fsa, "a").ok

    def test_rejected_no_transition(self):
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        result = accepts_string(fsa, "aa")
        assert ErrorCode.TEST_CASE_FAILED in [e.code for e in result.errors]

    def test_empty_string(self):
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"],
        )
        assert accepts_string(fsa, "").ok


class TestLanguageEquivalence:
    """Tests for language equivalence."""

    def test_accept_same_string(self):
        fsa1 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        fsa2 = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[{"from_state": "s0", "to_state": "s1", "symbol": "a"}],
            initial="s0",
            accept=["s1"],
        )
        assert fsas_accept_same_string(fsa1, fsa2, "a").ok

    def test_language_mismatch(self):
        fsa1 = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"],
        )
        fsa2 = make_fsa(
            states=["s0"],
            alphabet=["b"],
            transitions=[{"from_state": "s0", "to_state": "s0", "symbol": "b"}],
            initial="s0",
            accept=["s0"],
        )
        result = fsas_accept_same_language(fsa1, fsa2)
        assert not result.ok
        assert ErrorCode.LANGUAGE_MISMATCH in [e.code for e in result.errors]


class TestIsomorphism:
    """Tests for DFA isomorphism checking."""

    def test_isomorphic_dfas(self):
        fsa_user = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
                {"from_state": "q1", "to_state": "q0", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],
        )
        fsa_sol = make_fsa(
            states=["s0", "s1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
                {"from_state": "s0", "to_state": "s0", "symbol": "b"},
                {"from_state": "s1", "to_state": "s0", "symbol": "a"},
                {"from_state": "s1", "to_state": "s1", "symbol": "b"},
            ],
            initial="s0",
            accept=["s1"],
        )
        assert are_isomorphic(fsa_user, fsa_sol).ok


class TestEpsilonTransitions:
    """Tests for epsilon transition handling across the validation pipeline."""

    def test_valid_fsa_with_epsilon_unicode(self):
        """ε-NFA with Unicode ε should pass structural validation."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        assert is_valid_fsa(fsa).ok

    def test_valid_fsa_with_epsilon_string(self):
        """ε-NFA with 'epsilon' string should pass structural validation."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "epsilon"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        assert is_valid_fsa(fsa).ok

    def test_valid_fsa_with_empty_string_epsilon(self):
        """ε-NFA with empty string epsilon should pass structural validation."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": ""},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        assert is_valid_fsa(fsa).ok

    def test_epsilon_nfa_is_not_deterministic(self):
        """ε-NFA should be flagged as non-deterministic."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
            ],
            initial="q0",
            accept=["q1"],
        )
        result = is_deterministic(fsa)
        assert not result.ok
        assert ErrorCode.NOT_DETERMINISTIC in [e.code for e in result.errors]

    def test_accepts_string_via_epsilon_closure(self):
        """ε-NFA should accept 'a' by following q0 --ε--> q1 --a--> q2."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        assert accepts_string(fsa, "a").ok

    def test_rejects_string_with_epsilon_nfa(self):
        """ε-NFA that accepts 'a' should reject empty string."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        result = accepts_string(fsa, "")
        assert not result.ok

    def test_accepts_empty_string_via_epsilon(self):
        """ε-NFA should accept empty string when initial reaches accept via ε."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
            ],
            initial="q0",
            accept=["q1"],
        )
        assert accepts_string(fsa, "").ok

    def test_epsilon_nfa_equivalent_to_dfa(self):
        """ε-NFA and DFA accepting the same language should be equivalent."""
        enfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
            ],
            initial="s0",
            accept=["s1"],
        )
        assert fsas_accept_same_language(enfa, dfa).ok

    def test_epsilon_nfa_not_equivalent_to_different_dfa(self):
        """ε-NFA and DFA accepting different languages should not be equivalent."""
        enfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "b"},
            ],
            initial="s0",
            accept=["s1"],
        )
        result = fsas_accept_same_language(enfa, dfa)
        assert not result.ok

    def test_multi_epsilon_nfa_equivalent_to_dfa(self):
        """ε-NFA for (a|b) with branching epsilons should match equivalent DFA."""
        # q0 --ε--> q1, q0 --ε--> q2, q1 --a--> q3, q2 --b--> q3
        enfa = make_fsa(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q0", "to_state": "q2", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q3", "symbol": "a"},
                {"from_state": "q2", "to_state": "q3", "symbol": "b"},
            ],
            initial="q0",
            accept=["q3"],
        )
        dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
                {"from_state": "s0", "to_state": "s1", "symbol": "b"},
            ],
            initial="s0",
            accept=["s1"],
        )
        assert fsas_accept_same_language(enfa, dfa).ok


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
