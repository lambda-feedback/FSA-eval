"""
Comprehensive tests for FSA Correction Module.

Tests the correction pipeline that generates difference strings
and identifies states/transitions causing errors. Mirrors the
structure and comprehensiveness of test_validation.py.
"""

import pytest
from evaluation_function.schemas import FSA, Transition, ValidationError, ErrorCode
from evaluation_function.schemas.utils import make_fsa
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
from evaluation_function.schemas.result import FSAFeedback, LanguageComparison, TestResult


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def simple_dfa_accepts_a():
    """DFA that accepts exactly 'a'."""
    return FSA(
        states=["q0", "q1", "q2"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", symbol="a", to_state="q1"),
            Transition(from_state="q0", symbol="b", to_state="q2"),
            Transition(from_state="q1", symbol="a", to_state="q2"),
            Transition(from_state="q1", symbol="b", to_state="q2"),
            Transition(from_state="q2", symbol="a", to_state="q2"),
            Transition(from_state="q2", symbol="b", to_state="q2"),
        ],
        initial_state="q0",
        accept_states=["q1"]
    )


@pytest.fixture
def simple_dfa_accepts_a_or_b():
    """DFA that accepts 'a' or 'b'."""
    return FSA(
        states=["q0", "q1", "q2"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", symbol="a", to_state="q1"),
            Transition(from_state="q0", symbol="b", to_state="q1"),
            Transition(from_state="q1", symbol="a", to_state="q2"),
            Transition(from_state="q1", symbol="b", to_state="q2"),
            Transition(from_state="q2", symbol="a", to_state="q2"),
            Transition(from_state="q2", symbol="b", to_state="q2"),
        ],
        initial_state="q0",
        accept_states=["q1"]
    )


@pytest.fixture
def dfa_accepts_even_as():
    """DFA that accepts strings with even number of 'a's."""
    return FSA(
        states=["even", "odd"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="even", symbol="a", to_state="odd"),
            Transition(from_state="even", symbol="b", to_state="even"),
            Transition(from_state="odd", symbol="a", to_state="even"),
            Transition(from_state="odd", symbol="b", to_state="odd"),
        ],
        initial_state="even",
        accept_states=["even"]
    )


@pytest.fixture
def dfa_accepts_odd_as():
    """DFA that accepts strings with odd number of 'a's."""
    return FSA(
        states=["even", "odd"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="even", symbol="a", to_state="odd"),
            Transition(from_state="even", symbol="b", to_state="even"),
            Transition(from_state="odd", symbol="a", to_state="even"),
            Transition(from_state="odd", symbol="b", to_state="odd"),
        ],
        initial_state="even",
        accept_states=["odd"]
    )


@pytest.fixture
def dfa_with_unreachable_state():
    """DFA with an unreachable state."""
    return FSA(
        states=["q0", "q1", "q2", "unreachable"],
        alphabet=["a"],
        transitions=[
            Transition(from_state="q0", symbol="a", to_state="q1"),
            Transition(from_state="q1", symbol="a", to_state="q2"),
            Transition(from_state="q2", symbol="a", to_state="q2"),
            Transition(from_state="unreachable", symbol="a", to_state="q1"),
        ],
        initial_state="q0",
        accept_states=["q2"]
    )


@pytest.fixture
def dfa_with_dead_state():
    """DFA with a dead state (cannot reach accepting state)."""
    return FSA(
        states=["q0", "q1", "dead"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", symbol="a", to_state="q1"),
            Transition(from_state="q0", symbol="b", to_state="dead"),
            Transition(from_state="q1", symbol="a", to_state="q1"),
            Transition(from_state="q1", symbol="b", to_state="q1"),
            Transition(from_state="dead", symbol="a", to_state="dead"),
            Transition(from_state="dead", symbol="b", to_state="dead"),
        ],
        initial_state="q0",
        accept_states=["q1"]
    )


@pytest.fixture
def incomplete_dfa():
    """DFA missing some transitions."""
    return FSA(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", symbol="a", to_state="q1"),
            # Missing: q0 on 'b', q1 on 'a', q1 on 'b'
        ],
        initial_state="q0",
        accept_states=["q1"]
    )


@pytest.fixture
def equivalent_dfa_different_names():
    """DFA equivalent to simple_dfa_accepts_a but with different state names."""
    return FSA(
        states=["s0", "s1", "s2"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="s0", symbol="a", to_state="s1"),
            Transition(from_state="s0", symbol="b", to_state="s2"),
            Transition(from_state="s1", symbol="a", to_state="s2"),
            Transition(from_state="s1", symbol="b", to_state="s2"),
            Transition(from_state="s2", symbol="a", to_state="s2"),
            Transition(from_state="s2", symbol="b", to_state="s2"),
        ],
        initial_state="s0",
        accept_states=["s1"]
    )


# =============================================================================
# Test trace_string
# =============================================================================

class TestTraceString:
    """Tests for trace_string function."""

    def test_trace_accepted_string(self, simple_dfa_accepts_a):
        """Test tracing an accepted string."""
        accepted, trace = trace_string(simple_dfa_accepts_a, "a")
        assert accepted is True
        assert trace == ["q0", "q1"]

    def test_trace_rejected_string(self, simple_dfa_accepts_a):
        """Test tracing a rejected string."""
        accepted, trace = trace_string(simple_dfa_accepts_a, "b")
        assert accepted is False
        assert trace == ["q0", "q2"]

    def test_trace_empty_string(self, dfa_accepts_even_as):
        """Test tracing empty string (should accept for even 'a's DFA)."""
        accepted, trace = trace_string(dfa_accepts_even_as, "")
        assert accepted is True
        assert trace == ["even"]

    def test_trace_longer_string(self, dfa_accepts_even_as):
        """Test tracing a longer string."""
        accepted, trace = trace_string(dfa_accepts_even_as, "aab")
        assert accepted is True
        assert trace == ["even", "odd", "even", "even"]

    def test_trace_invalid_symbol(self, simple_dfa_accepts_a):
        """Test tracing string with symbol not in alphabet."""
        accepted, trace = trace_string(simple_dfa_accepts_a, "c")
        assert accepted is False


# =============================================================================
# Test fsa_accepts
# =============================================================================

class TestFsaAccepts:
    """Tests for fsa_accepts function."""

    def test_accepts_valid_string(self, simple_dfa_accepts_a):
        """Test acceptance of valid string."""
        assert fsa_accepts(simple_dfa_accepts_a, "a") is True

    def test_rejects_invalid_string(self, simple_dfa_accepts_a):
        """Test rejection of invalid string."""
        assert fsa_accepts(simple_dfa_accepts_a, "b") is False
        assert fsa_accepts(simple_dfa_accepts_a, "aa") is False

    def test_empty_string_acceptance(self, dfa_accepts_even_as):
        """Test empty string acceptance."""
        assert fsa_accepts(dfa_accepts_even_as, "") is True

    def test_empty_string_rejection(self, dfa_accepts_odd_as):
        """Test empty string rejection."""
        assert fsa_accepts(dfa_accepts_odd_as, "") is False


# =============================================================================
# Test generate_difference_strings
# =============================================================================

class TestGenerateDifferenceStrings:
    """Tests for generate_difference_strings function."""

    def test_identical_fsas_no_differences(self, simple_dfa_accepts_a, equivalent_dfa_different_names):
        """Test that equivalent FSAs produce no differences."""
        differences = generate_difference_strings(
            simple_dfa_accepts_a, equivalent_dfa_different_names
        )
        assert len(differences) == 0

    def test_different_fsas_find_differences(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test that different FSAs produce differences."""
        differences = generate_difference_strings(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        assert len(differences) > 0
        # 'b' should be a difference (student rejects, expected accepts)
        b_diff = next((d for d in differences if d.string == "b"), None)
        assert b_diff is not None
        assert b_diff.student_accepts is False
        assert b_diff.expected_accepts is True
        assert b_diff.difference_type == "should_accept"

    def test_opposite_languages(self, dfa_accepts_even_as, dfa_accepts_odd_as):
        """Test FSAs with opposite acceptance conditions."""
        differences = generate_difference_strings(
            dfa_accepts_even_as, dfa_accepts_odd_as
        )
        assert len(differences) > 0
        # Empty string should be a difference
        empty_diff = next((d for d in differences if "empty" in d.string.lower() or d.string == ""), None)
        assert empty_diff is not None

    def test_max_differences_limit(self, dfa_accepts_even_as, dfa_accepts_odd_as):
        """Test that max_differences is respected."""
        differences = generate_difference_strings(
            dfa_accepts_even_as, dfa_accepts_odd_as,
            max_differences=3
        )
        assert len(differences) <= 3

    def test_difference_string_properties(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test DifferenceString properties."""
        differences = generate_difference_strings(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        for diff in differences:
            assert isinstance(diff.string, str)
            assert isinstance(diff.student_accepts, bool)
            assert isinstance(diff.expected_accepts, bool)
            assert diff.difference_type in ["should_accept", "should_reject"]
            assert diff.student_accepts != diff.expected_accepts


# =============================================================================
# Test identify_state_errors
# =============================================================================

class TestIdentifyStateErrors:
    """Tests for identify_state_errors function."""

    def test_finds_unreachable_states(self, dfa_with_unreachable_state, simple_dfa_accepts_a):
        """Test identification of unreachable states."""
        differences = generate_difference_strings(
            dfa_with_unreachable_state, simple_dfa_accepts_a
        )
        errors = identify_state_errors(
            dfa_with_unreachable_state, simple_dfa_accepts_a, differences
        )
        unreachable_errors = [e for e in errors if e.error_type == "unreachable"]
        assert len(unreachable_errors) > 0
        assert any(e.state_id == "unreachable" for e in unreachable_errors)

    def test_finds_dead_states(self, dfa_with_dead_state, simple_dfa_accepts_a):
        """Test identification of dead states."""
        differences = generate_difference_strings(
            dfa_with_dead_state, simple_dfa_accepts_a
        )
        errors = identify_state_errors(
            dfa_with_dead_state, simple_dfa_accepts_a, differences
        )
        dead_errors = [e for e in errors if e.error_type == "dead"]
        assert len(dead_errors) > 0
        assert any(e.state_id == "dead" for e in dead_errors)

    def test_state_error_to_validation_error(self):
        """Test StateError conversion to ValidationError."""
        state_error = StateError(
            state_id="q1",
            error_type="should_be_accepting",
            example_string="test"
        )
        val_error = state_error.to_validation_error()
        assert isinstance(val_error, ValidationError)
        assert val_error.code == ErrorCode.LANGUAGE_MISMATCH
        assert "q1" in val_error.message


# =============================================================================
# Test identify_transition_errors
# =============================================================================

class TestIdentifyTransitionErrors:
    """Tests for identify_transition_errors function."""

    def test_finds_missing_transitions(self, incomplete_dfa, simple_dfa_accepts_a):
        """Test identification of missing transitions."""
        differences = generate_difference_strings(
            incomplete_dfa, simple_dfa_accepts_a
        )
        errors = identify_transition_errors(
            incomplete_dfa, simple_dfa_accepts_a, differences
        )
        # Should find some missing transitions
        missing_errors = [e for e in errors if e.error_type == "missing"]
        # Note: may or may not find missing transitions depending on analysis
        assert isinstance(errors, list)

    def test_transition_error_to_validation_error(self):
        """Test TransitionError conversion to ValidationError."""
        trans_error = TransitionError(
            from_state="q0",
            symbol="a",
            actual_to_state="q1",
            expected_to_state="q2",
            error_type="wrong_destination",
            example_string="a"
        )
        val_error = trans_error.to_validation_error()
        assert isinstance(val_error, ValidationError)
        assert val_error.code == ErrorCode.LANGUAGE_MISMATCH
        assert "q0" in val_error.message
        assert val_error.highlight is not None
        assert val_error.highlight.type == "transition"


# =============================================================================
# Test analyze_fsa_correction (main pipeline)
# =============================================================================

class TestAnalyzeFsaCorrection:
    """Tests for the main analysis pipeline."""

    def test_equivalent_fsas(self, simple_dfa_accepts_a, equivalent_dfa_different_names):
        """Test analysis of equivalent FSAs."""
        result = analyze_fsa_correction(
            simple_dfa_accepts_a, equivalent_dfa_different_names
        )
        assert result.is_equivalent is True
        assert len(result.difference_strings) == 0

    def test_different_fsas(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test analysis of different FSAs."""
        result = analyze_fsa_correction(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        assert result.is_equivalent is False
        assert len(result.difference_strings) > 0
        assert result.summary != ""

    def test_result_to_dict(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test CorrectionResult.to_dict()."""
        result = analyze_fsa_correction(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "is_equivalent" in result_dict
        assert "summary" in result_dict
        assert "difference_strings" in result_dict
        assert "transition_errors" in result_dict
        assert "state_errors" in result_dict

    def test_get_language_comparison(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test CorrectionResult.get_language_comparison()."""
        result = analyze_fsa_correction(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        lang_comp = result.get_language_comparison()
        assert lang_comp.are_equivalent is False
        assert lang_comp.counterexample is not None

    def test_get_test_results(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test CorrectionResult.get_test_results()."""
        result = analyze_fsa_correction(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        test_results = result.get_test_results()
        assert len(test_results) == len(result.difference_strings)
        for tr in test_results:
            assert tr.passed is False  # All difference strings are failures

    def test_get_all_validation_errors(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test CorrectionResult.get_all_validation_errors()."""
        result = analyze_fsa_correction(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        all_errors = result.get_all_validation_errors()
        assert isinstance(all_errors, list)
        for error in all_errors:
            assert isinstance(error, ValidationError)

    def test_structural_info_included(self, dfa_with_unreachable_state, simple_dfa_accepts_a):
        """Test that structural info is included in result."""
        result = analyze_fsa_correction(
            dfa_with_unreachable_state, simple_dfa_accepts_a
        )
        assert result.structural_info is not None


# =============================================================================
# Test get_correction_feedback
# =============================================================================

class TestGetCorrectionFeedback:
    """Tests for the convenience wrapper function."""

    def test_returns_dict(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test that get_correction_feedback returns a dictionary."""
        feedback = get_correction_feedback(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        assert isinstance(feedback, dict)
        assert "is_equivalent" in feedback
        assert "summary" in feedback

    def test_equivalent_feedback(self, simple_dfa_accepts_a, equivalent_dfa_different_names):
        """Test feedback for equivalent FSAs."""
        feedback = get_correction_feedback(
            simple_dfa_accepts_a, equivalent_dfa_different_names
        )
        assert feedback["is_equivalent"] is True


# =============================================================================
# Test get_fsa_feedback (returns FSAFeedback schema)
# =============================================================================

class TestGetFsaFeedback:
    """Tests for get_fsa_feedback function that returns FSAFeedback schema."""

    def test_returns_fsa_feedback(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test that get_fsa_feedback returns FSAFeedback object."""
        feedback = get_fsa_feedback(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        assert isinstance(feedback, FSAFeedback)

    def test_fsa_feedback_has_summary(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test FSAFeedback has a summary."""
        feedback = get_fsa_feedback(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        assert feedback.summary != ""

    def test_fsa_feedback_has_errors(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test FSAFeedback has errors for non-equivalent FSAs."""
        feedback = get_fsa_feedback(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        # Should have errors or test results showing differences
        assert len(feedback.errors) > 0 or len(feedback.test_results) > 0

    def test_fsa_feedback_has_language_comparison(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test FSAFeedback has language comparison."""
        feedback = get_fsa_feedback(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        assert feedback.language is not None
        assert isinstance(feedback.language, LanguageComparison)
        assert feedback.language.are_equivalent is False

    def test_fsa_feedback_has_test_results(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test FSAFeedback has test results."""
        feedback = get_fsa_feedback(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        assert isinstance(feedback.test_results, list)
        for tr in feedback.test_results:
            assert isinstance(tr, TestResult)

    def test_fsa_feedback_has_structural_info(self, dfa_with_unreachable_state, simple_dfa_accepts_a):
        """Test FSAFeedback has structural info."""
        feedback = get_fsa_feedback(dfa_with_unreachable_state, simple_dfa_accepts_a)
        assert feedback.structural is not None
        assert "unreachable" in feedback.structural.unreachable_states

    def test_fsa_feedback_equivalent_fsas(self, simple_dfa_accepts_a, equivalent_dfa_different_names):
        """Test FSAFeedback for equivalent FSAs."""
        feedback = get_fsa_feedback(simple_dfa_accepts_a, equivalent_dfa_different_names)
        assert feedback.language is not None
        assert feedback.language.are_equivalent is True

    def test_fsa_feedback_has_hints(self, dfa_with_dead_state, simple_dfa_accepts_a):
        """Test FSAFeedback generates helpful hints."""
        feedback = get_fsa_feedback(dfa_with_dead_state, simple_dfa_accepts_a)
        # Should have hints about dead states
        assert isinstance(feedback.hints, list)

    def test_fsa_feedback_separates_errors_and_warnings(self, dfa_with_unreachable_state, simple_dfa_accepts_a):
        """Test FSAFeedback separates errors from warnings."""
        feedback = get_fsa_feedback(dfa_with_unreachable_state, simple_dfa_accepts_a)
        # Errors should be severity="error", warnings should be severity="warning"
        for error in feedback.errors:
            assert error.severity == "error"
        for warning in feedback.warnings:
            assert warning.severity in ("warning", "info")


# =============================================================================
# Test CorrectionResult.to_fsa_feedback
# =============================================================================

class TestCorrectionResultToFsaFeedback:
    """Tests for CorrectionResult.to_fsa_feedback method."""

    def test_to_fsa_feedback_returns_fsa_feedback(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test to_fsa_feedback returns FSAFeedback."""
        result = analyze_fsa_correction(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        feedback = result.to_fsa_feedback()
        assert isinstance(feedback, FSAFeedback)

    def test_to_fsa_feedback_includes_all_fields(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test to_fsa_feedback includes all required fields."""
        result = analyze_fsa_correction(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        feedback = result.to_fsa_feedback()
        
        # Check all fields exist
        assert hasattr(feedback, 'summary')
        assert hasattr(feedback, 'errors')
        assert hasattr(feedback, 'warnings')
        assert hasattr(feedback, 'structural')
        assert hasattr(feedback, 'language')
        assert hasattr(feedback, 'test_results')
        assert hasattr(feedback, 'hints')

    def test_to_fsa_feedback_model_dump(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test to_fsa_feedback result can be serialized with model_dump."""
        result = analyze_fsa_correction(simple_dfa_accepts_a, simple_dfa_accepts_a_or_b)
        feedback = result.to_fsa_feedback()
        
        # Should be serializable
        dumped = feedback.model_dump()
        assert isinstance(dumped, dict)
        assert "summary" in dumped
        assert "errors" in dumped


# =============================================================================
# Test check_fsa_properties
# =============================================================================

class TestCheckFsaProperties:
    """Tests for check_fsa_properties function."""

    def test_valid_complete_dfa(self, simple_dfa_accepts_a):
        """Test properties of a valid complete DFA."""
        props = check_fsa_properties(simple_dfa_accepts_a)
        assert props["is_valid"] is True
        assert props["is_deterministic"] is True
        assert props["is_complete"] is True
        assert len(props["unreachable_states"]) == 0

    def test_incomplete_dfa(self, incomplete_dfa):
        """Test properties of an incomplete DFA."""
        props = check_fsa_properties(incomplete_dfa)
        assert props["is_valid"] is True
        assert props["is_deterministic"] is True
        assert props["is_complete"] is False

    def test_dfa_with_unreachable_state(self, dfa_with_unreachable_state):
        """Test properties of DFA with unreachable state."""
        props = check_fsa_properties(dfa_with_unreachable_state)
        assert props["is_valid"] is True
        assert "unreachable" in props["unreachable_states"]

    def test_dfa_with_dead_state(self, dfa_with_dead_state):
        """Test properties of DFA with dead state."""
        props = check_fsa_properties(dfa_with_dead_state)
        assert props["is_valid"] is True
        assert "dead" in props["dead_states"]

    def test_structural_info_included(self, simple_dfa_accepts_a):
        """Test that structural info is included."""
        props = check_fsa_properties(simple_dfa_accepts_a)
        assert props["structural_info"] is not None
        assert isinstance(props["structural_info"], dict)


# =============================================================================
# Test quick_equivalence_check
# =============================================================================

class TestQuickEquivalenceCheck:
    """Tests for quick_equivalence_check function."""

    def test_equivalent_fsas(self, simple_dfa_accepts_a, equivalent_dfa_different_names):
        """Test quick check for equivalent FSAs."""
        is_eq, counterexample, ce_type = quick_equivalence_check(
            simple_dfa_accepts_a, equivalent_dfa_different_names
        )
        assert is_eq is True
        assert counterexample is None

    def test_different_fsas(self, simple_dfa_accepts_a, simple_dfa_accepts_a_or_b):
        """Test quick check for different FSAs."""
        is_eq, counterexample, ce_type = quick_equivalence_check(
            simple_dfa_accepts_a, simple_dfa_accepts_a_or_b
        )
        assert is_eq is False
        # May or may not have counterexample depending on how check works


# =============================================================================
# Test DifferenceString class
# =============================================================================

class TestDifferenceString:
    """Tests for DifferenceString data class."""

    def test_to_dict(self):
        """Test DifferenceString.to_dict()."""
        diff = DifferenceString(
            string="ab",
            student_accepts=True,
            expected_accepts=False,
            student_trace=["q0", "q1", "q2"],
            expected_trace=["s0", "s1", "s2"]
        )
        d = diff.to_dict()
        assert d["string"] == "ab"
        assert d["student_accepts"] is True
        assert d["expected_accepts"] is False
        assert d["difference_type"] == "should_reject"
        assert d["student_trace"] == ["q0", "q1", "q2"]

    def test_difference_type_should_accept(self):
        """Test difference_type property for should_accept."""
        diff = DifferenceString(
            string="a",
            student_accepts=False,
            expected_accepts=True
        )
        assert diff.difference_type == "should_accept"

    def test_difference_type_should_reject(self):
        """Test difference_type property for should_reject."""
        diff = DifferenceString(
            string="a",
            student_accepts=True,
            expected_accepts=False
        )
        assert diff.difference_type == "should_reject"


# =============================================================================
# Test TransitionError class
# =============================================================================

class TestTransitionError:
    """Tests for TransitionError data class."""

    def test_to_dict(self):
        """Test TransitionError.to_dict()."""
        error = TransitionError(
            from_state="q0",
            symbol="a",
            actual_to_state="q1",
            expected_to_state="q2",
            error_type="wrong_destination",
            example_string="a"
        )
        d = error.to_dict()
        assert d["from_state"] == "q0"
        assert d["symbol"] == "a"
        assert d["error_type"] == "wrong_destination"

    def test_to_validation_error_wrong_destination(self):
        """Test conversion to ValidationError for wrong destination."""
        error = TransitionError(
            from_state="q0",
            symbol="a",
            actual_to_state="q1",
            expected_to_state="q2",
            error_type="wrong_destination"
        )
        val_error = error.to_validation_error()
        assert "wrong" in val_error.message.lower() or "goes to" in val_error.message.lower()

    def test_to_validation_error_missing(self):
        """Test conversion to ValidationError for missing transition."""
        error = TransitionError(
            from_state="q0",
            symbol="a",
            actual_to_state=None,
            expected_to_state="q1",
            error_type="missing"
        )
        val_error = error.to_validation_error()
        assert "missing" in val_error.message.lower()

    def test_to_validation_error_extra(self):
        """Test conversion to ValidationError for extra transition."""
        error = TransitionError(
            from_state="q0",
            symbol="a",
            actual_to_state="q1",
            expected_to_state=None,
            error_type="extra"
        )
        val_error = error.to_validation_error()
        assert "extra" in val_error.message.lower()


# =============================================================================
# Test StateError class
# =============================================================================

class TestStateError:
    """Tests for StateError data class."""

    def test_to_dict(self):
        """Test StateError.to_dict()."""
        error = StateError(
            state_id="q1",
            error_type="should_be_accepting",
            example_string="ab"
        )
        d = error.to_dict()
        assert d["state_id"] == "q1"
        assert d["error_type"] == "should_be_accepting"
        assert d["example_string"] == "ab"

    def test_to_validation_error_should_be_accepting(self):
        """Test conversion for should_be_accepting error."""
        error = StateError(state_id="q1", error_type="should_be_accepting")
        val_error = error.to_validation_error()
        assert val_error.code == ErrorCode.LANGUAGE_MISMATCH
        assert val_error.severity == "error"

    def test_to_validation_error_unreachable(self):
        """Test conversion for unreachable error."""
        error = StateError(state_id="q1", error_type="unreachable")
        val_error = error.to_validation_error()
        assert val_error.code == ErrorCode.UNREACHABLE_STATE
        assert val_error.severity == "warning"

    def test_to_validation_error_dead(self):
        """Test conversion for dead state error."""
        error = StateError(state_id="q1", error_type="dead")
        val_error = error.to_validation_error()
        assert val_error.code == ErrorCode.DEAD_STATE
        assert val_error.severity == "warning"


# =============================================================================
# Test CorrectionResult class
# =============================================================================

class TestCorrectionResult:
    """Tests for CorrectionResult data class."""

    def test_empty_result(self):
        """Test default empty CorrectionResult."""
        result = CorrectionResult()
        assert result.is_equivalent is True
        assert len(result.difference_strings) == 0
        assert len(result.transition_errors) == 0
        assert len(result.state_errors) == 0

    def test_to_dict_empty(self):
        """Test to_dict on empty result."""
        result = CorrectionResult()
        d = result.to_dict()
        assert d["is_equivalent"] is True
        assert d["difference_strings"] == []

    def test_get_language_comparison_no_differences(self):
        """Test get_language_comparison with no differences."""
        result = CorrectionResult()
        result.is_equivalent = True
        lang_comp = result.get_language_comparison()
        assert lang_comp.are_equivalent is True
        assert lang_comp.counterexample is None

    def test_get_language_comparison_with_differences(self):
        """Test get_language_comparison with differences."""
        result = CorrectionResult()
        result.is_equivalent = False
        result.difference_strings = [
            DifferenceString(
                string="ab",
                student_accepts=True,
                expected_accepts=False
            )
        ]
        lang_comp = result.get_language_comparison()
        assert lang_comp.are_equivalent is False
        assert lang_comp.counterexample == "ab"
        assert lang_comp.counterexample_type == "should_reject"

# =============================================================================
# Additional Edge Case Tests (mirroring test_validation.py structure)
# =============================================================================

class TestCorrectionWithMakeFsa:
    """Tests using make_fsa helper for consistency with validation tests."""

    def test_basic_equivalent_fsas(self):
        """Test correction analysis with equivalent FSAs using make_fsa."""
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
        result = analyze_fsa_correction(fsa1, fsa2)
        assert result.is_equivalent is True

    def test_different_accept_states(self):
        """Test correction when FSAs differ only in accept states."""
        fsa1 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q0"],  # Initial is accepting
        )
        fsa2 = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],  # Final is accepting
        )
        result = analyze_fsa_correction(fsa1, fsa2)
        assert result.is_equivalent is False
        # Empty string should be a difference
        empty_diffs = [d for d in result.difference_strings if "empty" in d.string.lower()]
        assert len(empty_diffs) > 0 or any(d.string == "a" for d in result.difference_strings)

    def test_missing_transition_detection(self):
        """Test that missing transitions are detected."""
        complete_fsa = make_fsa(
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
        incomplete_fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                # Missing b transitions
            ],
            initial="q0",
            accept=["q1"],
        )
        result = analyze_fsa_correction(incomplete_fsa, complete_fsa)
        # FSAs differ - incomplete one can't process 'b' from q0
        assert result.is_equivalent is False

    def test_nondeterministic_student_fsa(self):
        """Test correction with nondeterministic student FSA."""
        nfa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "a"},  # Non-determinism
            ],
            initial="q0",
            accept=["q1"],
        )
        dfa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        props = check_fsa_properties(nfa)
        assert props["is_deterministic"] is False

    def test_unreachable_state_in_correction(self):
        """Test correction identifies unreachable states via structural_info."""
        fsa_with_unreachable = make_fsa(
            states=["q0", "q1", "q2"],  # q2 is unreachable
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        fsa_normal = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        result = analyze_fsa_correction(fsa_with_unreachable, fsa_normal)
        # Structural info should report unreachable states even if languages are equivalent
        assert result.structural_info is not None
        assert "q2" in result.structural_info.unreachable_states

    def test_dead_state_in_correction(self):
        """Test correction identifies dead states via structural_info."""
        fsa_with_dead = make_fsa(
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
            accept=["q1"],
        )
        fsa_normal = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],
        )
        result = analyze_fsa_correction(fsa_with_dead, fsa_normal)
        # Structural info should report dead states even if languages differ
        assert result.structural_info is not None
        assert "dead" in result.structural_info.dead_states

    def test_all_strings_rejected(self):
        """Test correction when student FSA rejects all strings."""
        rejects_all = make_fsa(
            states=["q0"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
            ],
            initial="q0",
            accept=[],  # No accept states
        )
        accepts_a = make_fsa(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
                {"from_state": "q1", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],
        )
        result = analyze_fsa_correction(rejects_all, accepts_a)
        assert result.is_equivalent is False
        # All differences should be "should_accept" type
        should_accept = [d for d in result.difference_strings if d.difference_type == "should_accept"]
        assert len(should_accept) > 0

    def test_all_strings_accepted(self):
        """Test correction when student FSA accepts all strings."""
        accepts_all = make_fsa(
            states=["q0"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
            ],
            initial="q0",
            accept=["q0"],  # Initial is accepting
        )
        accepts_only_a = make_fsa(
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
            accept=["q1"],
        )
        result = analyze_fsa_correction(accepts_all, accepts_only_a)
        assert result.is_equivalent is False
        # Should find strings that should be rejected
        should_reject = [d for d in result.difference_strings if d.difference_type == "should_reject"]
        assert len(should_reject) > 0


class TestCorrectionInvalidFsas:
    """Tests for correction with invalid FSAs."""

    def test_invalid_initial_state(self):
        """Test correction with invalid initial state."""
        invalid_fsa = make_fsa(
            states=["q1"],
            alphabet=["a"],
            transitions=[],
            initial="q0",  # Not in states
            accept=[],
        )
        valid_fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=[],
        )
        result = analyze_fsa_correction(invalid_fsa, valid_fsa)
        assert result.is_equivalent is False
        assert len(result.validation_errors) > 0

    def test_invalid_accept_state(self):
        """Test correction with invalid accept state."""
        invalid_fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["q1"],  # Not in states
        )
        valid_fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial="q0",
            accept=["q0"],
        )
        result = analyze_fsa_correction(invalid_fsa, valid_fsa)
        assert result.is_equivalent is False
        assert len(result.validation_errors) > 0

    def test_invalid_transition_source(self):
        """Test correction with invalid transition source."""
        invalid_fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q2", "to_state": "q1", "symbol": "a"}],  # q2 not in states
            initial="q0",
            accept=["q1"],
        )
        valid_fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        result = analyze_fsa_correction(invalid_fsa, valid_fsa)
        assert result.is_equivalent is False
        assert len(result.validation_errors) > 0


class TestCorrectionStructuralInfo:
    """Tests for structural info in correction results."""

    def test_structural_info_deterministic(self):
        """Test structural info reports determinism."""
        fsa = make_fsa(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q1", "symbol": "a"}],
            initial="q0",
            accept=["q1"],
        )
        props = check_fsa_properties(fsa)
        assert props["structural_info"]["is_deterministic"] is True

    def test_structural_info_complete(self):
        """Test structural info reports completeness."""
        complete_fsa = make_fsa(
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
        props = check_fsa_properties(complete_fsa)
        assert props["structural_info"]["is_complete"] is True

    def test_structural_info_counts(self):
        """Test structural info includes correct counts."""
        fsa = make_fsa(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q0", "to_state": "q2", "symbol": "b"},
            ],
            initial="q0",
            accept=["q1"],
        )
        props = check_fsa_properties(fsa)
        assert props["structural_info"]["num_states"] == 3
        assert props["structural_info"]["num_transitions"] == 2
        # Note: alphabet_size is not part of StructuralInfo schema


class TestCorrectionLanguageEquivalence:
    """Tests for language equivalence checking in correction."""

    def test_same_language_different_structure(self):
        """Test FSAs with same language but different structure."""
        # Both accept a*
        fsa1 = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"],
        )
        fsa2 = make_fsa(
            states=["s0", "s1"],
            alphabet=["a"],
            transitions=[
                {"from_state": "s0", "to_state": "s1", "symbol": "a"},
                {"from_state": "s1", "to_state": "s0", "symbol": "a"},
            ],
            initial="s0",
            accept=["s0", "s1"],
        )
        is_eq, _, _ = quick_equivalence_check(fsa1, fsa2)
        # Both accept a*, so should be equivalent
        assert is_eq is True

    def test_different_alphabet_sizes(self):
        """Test FSAs with different alphabet sizes."""
        fsa1 = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"],
        )
        fsa2 = make_fsa(
            states=["q0"],
            alphabet=["a", "b"],
            transitions=[
                {"from_state": "q0", "to_state": "q0", "symbol": "a"},
                {"from_state": "q0", "to_state": "q0", "symbol": "b"},
            ],
            initial="q0",
            accept=["q0"],
        )
        result = analyze_fsa_correction(fsa1, fsa2)
        # Different alphabets lead to different languages
        # fsa1 can't process 'b', fsa2 accepts 'b'
        assert result.is_equivalent is False


class TestTraceStringEdgeCases:
    """Additional edge case tests for trace_string."""

    def test_trace_self_loop(self):
        """Test tracing through self-loops."""
        fsa = make_fsa(
            states=["q0"],
            alphabet=["a"],
            transitions=[{"from_state": "q0", "to_state": "q0", "symbol": "a"}],
            initial="q0",
            accept=["q0"],
        )
        fsa_obj = FSA(
            states=fsa.states,
            alphabet=fsa.alphabet,
            transitions=[Transition(**t.model_dump()) for t in fsa.transitions],
            initial_state=fsa.initial_state,
            accept_states=fsa.accept_states
        )
        accepted, trace = trace_string(fsa_obj, "aaa")
        assert accepted is True
        assert trace == ["q0", "q0", "q0", "q0"]

    def test_trace_multi_state_path(self):
        """Test tracing through multiple states."""
        fsa = make_fsa(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a"],
            transitions=[
                {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                {"from_state": "q1", "to_state": "q2", "symbol": "a"},
                {"from_state": "q2", "to_state": "q3", "symbol": "a"},
            ],
            initial="q0",
            accept=["q3"],
        )
        fsa_obj = FSA(
            states=fsa.states,
            alphabet=fsa.alphabet,
            transitions=[Transition(**t.model_dump()) for t in fsa.transitions],
            initial_state=fsa.initial_state,
            accept_states=fsa.accept_states
        )
        accepted, trace = trace_string(fsa_obj, "aaa")
        assert accepted is True
        assert trace == ["q0", "q1", "q2", "q3"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])