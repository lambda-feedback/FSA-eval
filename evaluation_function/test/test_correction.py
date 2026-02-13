"""
Tests for FSA Correction Module.

Tests the correction module that returns Result with FSAFeedback.
"""

import pytest
from evaluation_function.schemas import ValidationError, ErrorCode
from evaluation_function.schemas.utils import make_fsa
from evaluation_function.schemas.result import Result, FSAFeedback
from evaluation_function.schemas.params import Params
from evaluation_function.correction import analyze_fsa_correction


# =============================================================================
# Fixtures - DFAs
# =============================================================================

@pytest.fixture
def dfa_accepts_a():
    """DFA that accepts exactly 'a'."""
    return make_fsa(
        states=["q0", "q1", "q2"],
        alphabet=["a", "b"],
        transitions=[
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q0", "to_state": "q2", "symbol": "b"},
            {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            {"from_state": "q1", "to_state": "q2", "symbol": "b"},
            {"from_state": "q2", "to_state": "q2", "symbol": "a"},
            {"from_state": "q2", "to_state": "q2", "symbol": "b"},
        ],
        initial="q0",
        accept=["q1"]
    )


@pytest.fixture
def dfa_accepts_a_or_b():
    """DFA that accepts 'a' or 'b'."""
    return make_fsa(
        states=["q0", "q1", "q2"],
        alphabet=["a", "b"],
        transitions=[
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q0", "to_state": "q1", "symbol": "b"},
            {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            {"from_state": "q1", "to_state": "q2", "symbol": "b"},
            {"from_state": "q2", "to_state": "q2", "symbol": "a"},
            {"from_state": "q2", "to_state": "q2", "symbol": "b"},
        ],
        initial="q0",
        accept=["q1"]
    )


@pytest.fixture
def equivalent_dfa():
    """DFA equivalent to dfa_accepts_a with different state names."""
    return make_fsa(
        states=["s0", "s1", "s2"],
        alphabet=["a", "b"],
        transitions=[
            {"from_state": "s0", "to_state": "s1", "symbol": "a"},
            {"from_state": "s0", "to_state": "s2", "symbol": "b"},
            {"from_state": "s1", "to_state": "s2", "symbol": "a"},
            {"from_state": "s1", "to_state": "s2", "symbol": "b"},
            {"from_state": "s2", "to_state": "s2", "symbol": "a"},
            {"from_state": "s2", "to_state": "s2", "symbol": "b"},
        ],
        initial="s0",
        accept=["s1"]
    )


# =============================================================================
# Helper: Default Params
# =============================================================================

@pytest.fixture
def default_params():
    """Default Params object for analyze_fsa_correction."""
    return Params(
        expected_type="DFA",
        check_completeness=True,
        check_minimality=True,
        evaluation_mode="strict",
        highlight_errors=True,
        feedback_verbosity="detailed"
    )


# =============================================================================
# Test Main Pipeline - Returns Result
# =============================================================================

class TestAnalyzeFsaCorrection:
    """Test the main analysis pipeline returns Result."""

    def test_equivalent_fsas_correct(self, dfa_accepts_a, equivalent_dfa, default_params):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa, default_params)
        print(result)
        assert isinstance(result, Result)
        assert result.is_correct is True
        assert "Correct" in result.feedback

    def test_different_fsas_incorrect(self, dfa_accepts_a, dfa_accepts_a_or_b, default_params):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b, default_params)
        assert isinstance(result, Result)
        assert result.is_correct is False

    def test_result_has_fsa_feedback(self, dfa_accepts_a, equivalent_dfa, default_params):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa, default_params)
        assert result.fsa_feedback is not None
        assert isinstance(result.fsa_feedback, FSAFeedback)

    def test_fsa_feedback_has_structural_info(self, dfa_accepts_a, equivalent_dfa, default_params):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa, default_params)
        assert result.fsa_feedback.structural is not None
        assert result.fsa_feedback.structural.num_states == 3

    def test_different_fsas_have_errors(self, dfa_accepts_a, dfa_accepts_a_or_b, default_params):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b, default_params)
        assert result.fsa_feedback is not None
        assert len(result.fsa_feedback.errors) > 0


# =============================================================================
# Test Invalid FSAs
# =============================================================================

class TestInvalidFsas:
    """Test handling of invalid FSAs."""

    def test_invalid_initial_state(self, default_params):
        invalid = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="invalid",
            accept=[]
        )
        result = analyze_fsa_correction(invalid, invalid, default_params)
        assert result.is_correct is False
        assert result.fsa_feedback is not None
        assert len(result.fsa_feedback.errors) > 0

    def test_invalid_accept_state(self, default_params):
        invalid = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["invalid"]
        )
        result = analyze_fsa_correction(invalid, invalid, default_params)
        assert result.is_correct is False


# =============================================================================
# Test Minimality
# =============================================================================

class TestAnalyzeFsaCorrectionMinimality:
    """Test analyze_fsa_correction with minimality checking."""

    def test_minimal_fsa_passes(self, dfa_accepts_a, equivalent_dfa):
        params = Params(
            expected_type="DFA",
            check_completeness=True,
            check_minimality=True,
            evaluation_mode="strict",
            highlight_errors=True,
            feedback_verbosity="detailed"
        )
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa, params)
        assert result.is_correct is True

    def test_non_minimal_fsa_fails_when_required(self, equivalent_dfa):
        non_minimal = make_fsa(
            states=["q0", "q1", "q2", "unreachable"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "b"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
                {"from_state": "q1", "to_state": "q2", "symbol": "b"},
                {"from_state": "q2", "to_state": "q2", "symbol": "a"},
                {"from_state": "q2", "to_state": "q2", "symbol": "b"},
                {"from_state": "unreachable", "to_state": "unreachable", "symbol": "a"},
                {"from_state": "unreachable", "to_state": "unreachable", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"]
        )
        params = Params(
            expected_type="DFA",
            check_completeness=True,
            check_minimality=True,
            evaluation_mode="strict",
            highlight_errors=True,
            feedback_verbosity="detailed"
        )
        result = analyze_fsa_correction(non_minimal, equivalent_dfa, params)
        # Should have minimality error
        assert result.fsa_feedback is not None
        assert any(e.code == ErrorCode.NOT_MINIMAL for e in result.fsa_feedback.errors)


# =============================================================================
# Test Epsilon Transitions (End-to-End)
# =============================================================================

class TestEpsilonTransitionCorrection:
    """Test the full correction pipeline with ε-NFA inputs."""

    @pytest.fixture
    def nfa_params(self):
        """Params that allow NFA/ε-NFA student submissions."""
        return Params(
            expected_type="any",
            check_completeness=False,
            check_minimality=False,
            evaluation_mode="lenient",
            highlight_errors=True,
            feedback_verbosity="detailed",
        )

    def test_epsilon_nfa_vs_equivalent_dfa_correct(self, nfa_params):
        """ε-NFA student answer equivalent to DFA expected should be correct."""
        # ε-NFA accepts exactly "a": q0 --ε--> q1 --a--> q2
        student_enfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        # DFA accepts exactly "a": s0 --a--> s1
        expected_dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
            ],
            initial="s0",
            accept=["s1"],
        )
        result = analyze_fsa_correction(student_enfa, expected_dfa, nfa_params)
        assert isinstance(result, Result)
        assert result.is_correct is True

    def test_epsilon_nfa_vs_different_dfa_incorrect(self, nfa_params):
        """ε-NFA accepting 'a' vs DFA accepting 'b' should be incorrect."""
        student_enfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        expected_dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "b"},
            ],
            initial="s0",
            accept=["s1"],
        )
        result = analyze_fsa_correction(student_enfa, expected_dfa, nfa_params)
        assert isinstance(result, Result)
        assert result.is_correct is False
        assert result.fsa_feedback is not None
        assert len(result.fsa_feedback.errors) > 0

    def test_multi_epsilon_nfa_vs_dfa_correct(self, nfa_params):
        """ε-NFA for (a|b) with branching epsilons should match equivalent DFA."""
        student_enfa = make_fsa(
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
        expected_dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
                {"from_state": "s0", "to_state": "s1", "symbol": "b"},
            ],
            initial="s0",
            accept=["s1"],
        )
        result = analyze_fsa_correction(student_enfa, expected_dfa, nfa_params)
        assert isinstance(result, Result)
        assert result.is_correct is True

    def test_epsilon_nfa_structural_info_reports_nondeterministic(self, nfa_params):
        """ε-NFA should have structural info reporting non-deterministic."""
        student_enfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "ε"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q2"],
        )
        expected_dfa = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
            ],
            initial="s0",
            accept=["s1"],
        )
        result = analyze_fsa_correction(student_enfa, expected_dfa, nfa_params)
        assert result.fsa_feedback is not None
        assert result.fsa_feedback.structural is not None
        assert result.fsa_feedback.structural.is_deterministic is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
