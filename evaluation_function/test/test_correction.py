"""
Tests for FSA Correction Module.

Uses make_fsa from schemas.utils for all FSA construction.
Tests the simplified correction module that leverages validation.are_isomorphic().
"""

import pytest
from evaluation_function.schemas import FSA, ValidationError, ErrorCode
from evaluation_function.schemas.utils import make_fsa
from evaluation_function.schemas.result import FSAFeedback, LanguageComparison
from evaluation_function.correction import (
    CorrectionResult,
    analyze_fsa_correction,
    get_correction_feedback,
    get_fsa_feedback,
    check_fsa_properties,
    check_minimality,
    quick_equivalence_check,
)


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


@pytest.fixture
def dfa_with_unreachable():
    """DFA with unreachable state."""
    return make_fsa(
        states=["q0", "q1", "unreachable"],
        alphabet=["a"],
        transitions=[
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            {"from_state": "unreachable", "to_state": "q1", "symbol": "a"},
        ],
        initial="q0",
        accept=["q1"]
    )


# =============================================================================
# Test CorrectionResult
# =============================================================================

class TestCorrectionResult:
    """Test CorrectionResult model."""

    def test_model_dump(self):
        result = CorrectionResult()
        d = result.model_dump()
        assert "is_equivalent" in d
        assert "is_minimal" in d
        assert "equivalence_errors" in d

    def test_get_all_errors(self):
        result = CorrectionResult(
            validation_errors=[ValidationError(message="test", code=ErrorCode.INVALID_INITIAL, severity="error")],
            equivalence_errors=[ValidationError(message="equiv", code=ErrorCode.LANGUAGE_MISMATCH, severity="error")]
        )
        errors = result.get_all_errors()
        assert len(errors) == 2

    def test_to_fsa_feedback(self):
        result = CorrectionResult(summary="Test summary", is_equivalent=False)
        feedback = result.to_fsa_feedback()
        assert isinstance(feedback, FSAFeedback)
        assert feedback.summary == "Test summary"


# =============================================================================
# Test Main Pipeline
# =============================================================================

class TestAnalyzeFsaCorrection:
    """Test the main analysis pipeline."""

    def test_equivalent_fsas(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert result.is_equivalent is True
        assert result.is_isomorphic is True
        assert len(result.equivalence_errors) == 0

    def test_different_fsas(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        assert result.is_equivalent is False
        assert result.is_isomorphic is False
        # Should have errors from are_isomorphic()
        assert len(result.equivalence_errors) > 0

    def test_structural_info(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert result.structural_info is not None
        assert result.structural_info.num_states == 3

    def test_to_fsa_feedback(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        feedback = result.to_fsa_feedback()
        assert isinstance(feedback, FSAFeedback)
        assert len(feedback.errors) > 0

    def test_get_language_comparison(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        comparison = result.get_language_comparison()
        assert isinstance(comparison, LanguageComparison)
        assert comparison.are_equivalent is True


# =============================================================================
# Test Convenience Functions
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_correction_feedback(self, dfa_accepts_a, equivalent_dfa):
        feedback = get_correction_feedback(dfa_accepts_a, equivalent_dfa)
        assert isinstance(feedback, dict)
        assert feedback["is_equivalent"] is True

    def test_get_fsa_feedback(self, dfa_accepts_a, equivalent_dfa):
        feedback = get_fsa_feedback(dfa_accepts_a, equivalent_dfa)
        assert isinstance(feedback, FSAFeedback)

    def test_check_fsa_properties(self, dfa_accepts_a):
        props = check_fsa_properties(dfa_accepts_a)
        assert props["is_valid"] is True
        assert props["is_deterministic"] is True
        assert props["is_complete"] is True

    def test_check_fsa_properties_unreachable(self, dfa_with_unreachable):
        props = check_fsa_properties(dfa_with_unreachable)
        assert "unreachable" in props["unreachable_states"]

    def test_quick_equivalence_check_equal(self, dfa_accepts_a, equivalent_dfa):
        is_equiv, hint, hint_type = quick_equivalence_check(dfa_accepts_a, equivalent_dfa)
        assert is_equiv is True

    def test_quick_equivalence_check_different(self, dfa_accepts_a, dfa_accepts_a_or_b):
        is_equiv, hint, hint_type = quick_equivalence_check(dfa_accepts_a, dfa_accepts_a_or_b)
        assert is_equiv is False
        assert hint is not None


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
        assert result.is_equivalent is False
        assert len(result.validation_errors) > 0

    def test_invalid_accept_state(self):
        invalid = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["invalid"]
        )
        result = analyze_fsa_correction(invalid, invalid)
        assert result.is_equivalent is False
        assert len(result.validation_errors) > 0


# =============================================================================
# Test Minimality
# =============================================================================

class TestCheckMinimality:
    """Test check_minimality function."""

    def test_minimal_dfa(self, dfa_accepts_a):
        assert check_minimality(dfa_accepts_a) is True

    def test_non_minimal_dfa_with_unreachable(self):
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
            ],
            initial="q0",
            accept=["q1"]
        )
        assert check_minimality(non_minimal) is False


class TestAnalyzeFsaCorrectionMinimality:
    """Test analyze_fsa_correction with minimality checking."""

    def test_minimal_fsa_passes_check(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa, check_minimality=True)
        assert result.is_minimal is True

    def test_minimality_not_checked_by_default(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert result.is_minimal is None


# =============================================================================
# Test that errors come from are_isomorphic
# =============================================================================

class TestIsomorphismErrors:
    """Test that equivalence errors have proper highlights from are_isomorphic."""

    def test_errors_have_highlights(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        # are_isomorphic provides errors with ElementHighlight
        for error in result.equivalence_errors:
            # Each error should have meaningful info
            assert error.message is not None
            assert error.code == ErrorCode.LANGUAGE_MISMATCH

    def test_errors_have_suggestions(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        # are_isomorphic provides suggestions
        for error in result.equivalence_errors:
            assert error.suggestion is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
