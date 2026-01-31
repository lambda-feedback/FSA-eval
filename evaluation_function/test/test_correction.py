"""
Tests for FSA Correction Module.

Tests the correction module that returns Result with FSAFeedback.
"""

import pytest
from evaluation_function.schemas import ValidationError, ErrorCode
from evaluation_function.schemas.utils import make_fsa
from evaluation_function.schemas.result import Result, FSAFeedback
from evaluation_function.correction import analyze_fsa_correction


# =============================================================================
# Fixtures
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
# Test Main Pipeline - Returns Result
# =============================================================================

class TestAnalyzeFsaCorrection:
    """Test the main analysis pipeline returns Result."""

    def test_equivalent_fsas_correct(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert isinstance(result, Result)
        assert result.is_correct is True
        assert "Correct" in result.feedback

    def test_different_fsas_incorrect(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        assert isinstance(result, Result)
        assert result.is_correct is False

    def test_result_has_fsa_feedback(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert result.fsa_feedback is not None
        assert isinstance(result.fsa_feedback, FSAFeedback)

    def test_fsa_feedback_has_structural_info(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert result.fsa_feedback.structural is not None
        assert result.fsa_feedback.structural.num_states == 3

    def test_different_fsas_have_errors(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        assert result.fsa_feedback is not None
        assert len(result.fsa_feedback.errors) > 0


# =============================================================================
# Test Invalid FSAs
# =============================================================================

class TestInvalidFsas:
    """Test handling of invalid FSAs."""

    def test_invalid_initial_state(self):
        invalid = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="invalid",
            accept=[]
        )
        result = analyze_fsa_correction(invalid, invalid)
        assert result.is_correct is False
        assert result.fsa_feedback is not None
        assert len(result.fsa_feedback.errors) > 0

    def test_invalid_accept_state(self):
        invalid = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["invalid"]
        )
        result = analyze_fsa_correction(invalid, invalid)
        assert result.is_correct is False


class TestAnalyzeFsaCorrectionMinimality:
    """Test analyze_fsa_correction with minimality checking."""

    def test_minimal_fsa_passes(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa, require_minimal=True)
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
        result = analyze_fsa_correction(non_minimal, equivalent_dfa, require_minimal=True)
        # Should have minimality error
        assert result.fsa_feedback is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
