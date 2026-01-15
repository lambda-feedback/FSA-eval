"""
Tests for FSA Correction Module.

Uses make_fsa from schemas.utils for all FSA construction.
Tests leverage validation functions where applicable.
"""

import pytest
from evaluation_function.schemas import FSA, ValidationError, ErrorCode
from evaluation_function.schemas.utils import make_fsa
from evaluation_function.schemas.result import FSAFeedback, LanguageComparison, TestResult
from evaluation_function.correction.correction import (
    DifferenceString,
    TransitionError,
    StateError,
    CorrectionResult,
    trace_string,
    fsa_accepts,
    generate_difference_strings,
    identify_state_errors,
    identify_transition_errors,
    analyze_fsa_correction,
    get_correction_feedback,
    get_fsa_feedback,
    check_fsa_properties,
    quick_equivalence_check,
)


# =============================================================================
# Fixtures using make_fsa
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
def dfa_even_as():
    """DFA accepting strings with even number of 'a's."""
    return make_fsa(
        states=["even", "odd"],
        alphabet=["a", "b"],
        transitions=[
            {"from_state": "even", "to_state": "odd", "symbol": "a"},
            {"from_state": "even", "to_state": "even", "symbol": "b"},
            {"from_state": "odd", "to_state": "even", "symbol": "a"},
            {"from_state": "odd", "to_state": "odd", "symbol": "b"},
        ],
        initial="even",
        accept=["even"]
    )


@pytest.fixture
def dfa_odd_as():
    """DFA accepting strings with odd number of 'a's."""
    return make_fsa(
        states=["even", "odd"],
        alphabet=["a", "b"],
        transitions=[
            {"from_state": "even", "to_state": "odd", "symbol": "a"},
            {"from_state": "even", "to_state": "even", "symbol": "b"},
            {"from_state": "odd", "to_state": "even", "symbol": "a"},
            {"from_state": "odd", "to_state": "odd", "symbol": "b"},
        ],
        initial="even",
        accept=["odd"]
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


@pytest.fixture
def dfa_with_dead():
    """DFA with dead state."""
    return make_fsa(
        states=["q0", "q1", "dead"],
        alphabet=["a", "b"],
        transitions=[
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q0", "to_state": "dead", "symbol": "b"},
            {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            {"from_state": "dead", "to_state": "dead", "symbol": "a"},
            {"from_state": "dead", "to_state": "dead", "symbol": "b"},
        ],
        initial="q0",
        accept=["q1"]
    )


@pytest.fixture
def incomplete_dfa():
    """DFA missing transitions."""
    return make_fsa(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
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
# Test Pydantic Models (use model_dump)
# =============================================================================

class TestPydanticModels:
    """Test Pydantic model functionality."""

    def test_difference_string_model_dump(self):
        diff = DifferenceString(string="a", student_accepts=True, expected_accepts=False)
        d = diff.model_dump()
        assert d["string"] == "a"
        assert d["difference_type"] == "should_reject"

    def test_transition_error_model_dump(self):
        err = TransitionError(from_state="q0", symbol="a", error_type="missing")
        d = err.model_dump()
        assert d["from_state"] == "q0"
        assert d["error_type"] == "missing"

    def test_state_error_model_dump(self):
        err = StateError(state_id="q1", error_type="unreachable")
        d = err.model_dump()
        assert d["state_id"] == "q1"

    def test_correction_result_model_dump(self):
        result = CorrectionResult()
        d = result.model_dump()
        assert "is_equivalent" in d
        assert "difference_strings" in d

    def test_to_validation_error(self):
        err = StateError(state_id="q1", error_type="dead")
        val_err = err.to_validation_error()
        assert isinstance(val_err, ValidationError)
        assert val_err.code == ErrorCode.DEAD_STATE


# =============================================================================
# Test Helper Functions
# =============================================================================

class TestHelperFunctions:
    """Test trace_string and fsa_accepts."""

    def test_trace_accepted(self, dfa_accepts_a):
        accepted, trace = trace_string(dfa_accepts_a, "a")
        assert accepted is True
        assert trace == ["q0", "q1"]

    def test_trace_rejected(self, dfa_accepts_a):
        accepted, trace = trace_string(dfa_accepts_a, "b")
        assert accepted is False

    def test_fsa_accepts(self, dfa_accepts_a):
        assert fsa_accepts(dfa_accepts_a, "a") is True
        assert fsa_accepts(dfa_accepts_a, "b") is False

    def test_empty_string(self, dfa_even_as):
        assert fsa_accepts(dfa_even_as, "") is True


# =============================================================================
# Test Core Analysis Functions
# =============================================================================

class TestGenerateDifferenceStrings:
    """Test generate_difference_strings."""

    def test_no_differences_equivalent(self, dfa_accepts_a, equivalent_dfa):
        diffs = generate_difference_strings(dfa_accepts_a, equivalent_dfa)
        assert len(diffs) == 0

    def test_finds_differences(self, dfa_accepts_a, dfa_accepts_a_or_b):
        diffs = generate_difference_strings(dfa_accepts_a, dfa_accepts_a_or_b)
        assert len(diffs) > 0
        assert any(d.string == "b" for d in diffs)

    def test_max_limit(self, dfa_even_as, dfa_odd_as):
        diffs = generate_difference_strings(dfa_even_as, dfa_odd_as, max_differences=3)
        assert len(diffs) <= 3


class TestIdentifyErrors:
    """Test error identification functions."""

    def test_unreachable_states(self, dfa_with_unreachable, dfa_accepts_a):
        diffs = generate_difference_strings(dfa_with_unreachable, dfa_accepts_a)
        errors = identify_state_errors(dfa_with_unreachable, dfa_accepts_a, diffs)
        assert any(e.state_id == "unreachable" and e.error_type == "unreachable" for e in errors)

    def test_dead_states(self, dfa_with_dead, dfa_accepts_a):
        diffs = generate_difference_strings(dfa_with_dead, dfa_accepts_a)
        errors = identify_state_errors(dfa_with_dead, dfa_accepts_a, diffs)
        assert any(e.state_id == "dead" and e.error_type == "dead" for e in errors)


# =============================================================================
# Test Main Pipeline
# =============================================================================

class TestAnalyzeFsaCorrection:
    """Test main pipeline."""

    def test_equivalent_fsas(self, dfa_accepts_a, equivalent_dfa):
        result = analyze_fsa_correction(dfa_accepts_a, equivalent_dfa)
        assert result.is_equivalent is True

    def test_different_fsas(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        assert result.is_equivalent is False
        assert len(result.difference_strings) > 0

    def test_structural_info(self, dfa_with_unreachable, dfa_accepts_a):
        result = analyze_fsa_correction(dfa_with_unreachable, dfa_accepts_a)
        assert result.structural_info is not None
        assert "unreachable" in result.structural_info.unreachable_states

    def test_to_fsa_feedback(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        feedback = result.to_fsa_feedback()
        assert isinstance(feedback, FSAFeedback)

    def test_get_language_comparison(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        lang = result.get_language_comparison()
        assert isinstance(lang, LanguageComparison)
        assert lang.are_equivalent is False

    def test_get_test_results(self, dfa_accepts_a, dfa_accepts_a_or_b):
        result = analyze_fsa_correction(dfa_accepts_a, dfa_accepts_a_or_b)
        tests = result.get_test_results()
        assert all(isinstance(t, TestResult) for t in tests)


# =============================================================================
# Test Convenience Functions
# =============================================================================

class TestConvenienceFunctions:
    """Test get_correction_feedback, get_fsa_feedback, etc."""

    def test_get_correction_feedback(self, dfa_accepts_a, dfa_accepts_a_or_b):
        feedback = get_correction_feedback(dfa_accepts_a, dfa_accepts_a_or_b)
        assert isinstance(feedback, dict)
        assert "is_equivalent" in feedback

    def test_get_fsa_feedback(self, dfa_accepts_a, dfa_accepts_a_or_b):
        feedback = get_fsa_feedback(dfa_accepts_a, dfa_accepts_a_or_b)
        assert isinstance(feedback, FSAFeedback)
        assert feedback.language.are_equivalent is False

    def test_check_fsa_properties(self, dfa_accepts_a):
        props = check_fsa_properties(dfa_accepts_a)
        assert props["is_valid"] is True
        assert props["is_deterministic"] is True
        assert props["is_complete"] is True

    def test_check_fsa_properties_incomplete(self, incomplete_dfa):
        props = check_fsa_properties(incomplete_dfa)
        assert props["is_complete"] is False

    def test_check_fsa_properties_unreachable(self, dfa_with_unreachable):
        props = check_fsa_properties(dfa_with_unreachable)
        assert "unreachable" in props["unreachable_states"]

    def test_quick_equivalence_check_equal(self, dfa_accepts_a, equivalent_dfa):
        is_eq, ce, ce_type = quick_equivalence_check(dfa_accepts_a, equivalent_dfa)
        assert is_eq is True

    def test_quick_equivalence_check_different(self, dfa_accepts_a, dfa_accepts_a_or_b):
        is_eq, ce, ce_type = quick_equivalence_check(dfa_accepts_a, dfa_accepts_a_or_b)
        assert is_eq is False


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
        valid = make_fsa(states=["q0"], alphabet=["a"], transitions=[], initial="q0", accept=[])
        result = analyze_fsa_correction(invalid, valid)
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
        valid = make_fsa(states=["q0"], alphabet=["a"], transitions=[], initial="q0", accept=[])
        result = analyze_fsa_correction(invalid, valid)
        assert len(result.validation_errors) > 0


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases."""

    def test_empty_language(self):
        """Test FSA accepting nothing."""
        empty = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=[]
        )
        props = check_fsa_properties(empty)
        assert props["is_valid"] is True

    def test_all_accepting(self):
        """Test FSA accepting everything."""
        all_accept = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"]
        )
        props = check_fsa_properties(all_accept)
        assert props["is_valid"] is True

    def test_nondeterministic(self):
        """Test NFA detection."""
        nfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "a"},
            ],
            initial="q0",
            accept=["q1"]
        )
        props = check_fsa_properties(nfa)
        assert props["is_deterministic"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
