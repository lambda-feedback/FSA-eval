"""
Result Schema

Extended result schema with structured feedback for UI highlighting.
"""

from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """
    Standardized error codes for FSA validation.
    
    These codes allow the frontend to programmatically handle specific error types.
    """
    # Structural errors - invalid elements
    INVALID_STATE = "INVALID_STATE"
    INVALID_INITIAL = "INVALID_INITIAL"
    INVALID_ACCEPT = "INVALID_ACCEPT"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    
    # Transition errors
    INVALID_TRANSITION_SOURCE = "INVALID_TRANSITION_SOURCE"
    INVALID_TRANSITION_DEST = "INVALID_TRANSITION_DEST"
    INVALID_TRANSITION_SYMBOL = "INVALID_TRANSITION_SYMBOL"
    MISSING_TRANSITION = "MISSING_TRANSITION"
    DUPLICATE_TRANSITION = "DUPLICATE_TRANSITION"
    
    # Reachability errors
    UNREACHABLE_STATE = "UNREACHABLE_STATE"
    DEAD_STATE = "DEAD_STATE"
    
    # Type errors
    WRONG_AUTOMATON_TYPE = "WRONG_AUTOMATON_TYPE"
    NOT_DETERMINISTIC = "NOT_DETERMINISTIC"
    NOT_COMPLETE = "NOT_COMPLETE"
    
    # Language errors
    LANGUAGE_MISMATCH = "LANGUAGE_MISMATCH"
    TEST_CASE_FAILED = "TEST_CASE_FAILED"
    
    # General errors
    EMPTY_STATES = "EMPTY_STATES"
    EMPTY_ALPHABET = "EMPTY_ALPHABET"
    EVALUATION_ERROR = "EVALUATION_ERROR"


class ElementHighlight(BaseModel):
    """
    Specifies which FSA element to highlight in the UI.
    
    The frontend can use this to visually indicate errors on specific
    states, transitions, or other FSA components.
    """
    type: Literal["state", "transition", "initial_state", "accept_state", "alphabet_symbol"] = Field(
        ...,
        description="Type of FSA element to highlight"
    )
    
    # For state-related highlights
    state_id: Optional[str] = Field(
        default=None,
        description="State identifier (for type='state', 'initial_state', 'accept_state')"
    )
    
    # For transition-related highlights
    from_state: Optional[str] = Field(
        default=None,
        description="Source state of transition (for type='transition')"
    )
    to_state: Optional[str] = Field(
        default=None,
        description="Destination state of transition (for type='transition')"
    )
    symbol: Optional[str] = Field(
        default=None,
        description="Transition symbol (for type='transition' or 'alphabet_symbol')"
    )


class ValidationError(BaseModel):
    """
    A validation error with precise location for UI highlighting.
    
    Example - Missing transition:
    {
        "message": "Missing transition from state 'q0' on symbol 'a'",
        "code": "MISSING_TRANSITION",
        "severity": "error",
        "highlight": {
            "type": "state",
            "state_id": "q0"
        },
        "suggestion": "Add a transition from 'q0' on input 'a'"
    }
    
    Example - Invalid transition:
    {
        "message": "Transition points to non-existent state 'q5'",
        "code": "INVALID_TRANSITION_DEST",
        "severity": "error",
        "highlight": {
            "type": "transition",
            "from_state": "q0",
            "to_state": "q5",
            "symbol": "a"
        },
        "suggestion": "Change destination to an existing state or add state 'q5'"
    }
    """
    message: str = Field(..., description="Human-readable error message")
    
    code: ErrorCode = Field(
        ..., 
        description="Standardized error code from ErrorCode enum"
    )
    
    severity: Literal["error", "warning", "info"] = Field(
        default="error",
        description="Severity level of the issue"
    )
    
    highlight: Optional[ElementHighlight] = Field(
        default=None,
        description="FSA element to highlight in the UI"
    )
    
    suggestion: Optional[str] = Field(
        default=None,
        description="Actionable suggestion for fixing the error"
    )


class TestResult(BaseModel):
    """
    Result of evaluating the FSA on a single test case.
    
    Shows whether the FSA correctly accepts/rejects a specific input string.
    """
    input: str = Field(..., description="The test input string")
    expected: bool = Field(..., description="Expected result: true=accept, false=reject")
    actual: bool = Field(..., description="Actual result from student's FSA")
    passed: bool = Field(..., description="Whether the test passed (actual == expected)")
    trace: Optional[List[str]] = Field(
        default=None,
        description="State sequence during FSA execution (for debugging)"
    )


class StructuralInfo(BaseModel):
    """
    Structural properties and analysis of the FSA.
    
    Includes information about determinism, completeness, and reachability.
    """
    is_deterministic: bool = Field(
        ...,
        description="True if FSA is deterministic (no epsilon transitions, single transition per (state, symbol))"
    )
    
    is_complete: bool = Field(
        ...,
        description="True if DFA has transitions defined for all (state, symbol) pairs"
    )
    
    num_states: int = Field(..., ge=0, description="Number of states in the FSA")
    num_transitions: int = Field(..., ge=0, description="Number of transitions in the FSA")
    
    unreachable_states: List[str] = Field(
        default_factory=list,
        description="States that cannot be reached from the initial state"
    )
    
    dead_states: List[str] = Field(
        default_factory=list,
        description="States from which no accepting state is reachable"
    )


class LanguageComparison(BaseModel):
    """
    Result of comparing the student's FSA language with the expected language.
    
    Indicates whether the languages are equivalent and provides a counterexample if not.
    """
    are_equivalent: bool = Field(
        ...,
        description="True if student FSA accepts the same language as expected"
    )
    
    counterexample: Optional[str] = Field(
        default=None,
        description="A string where student FSA differs from expected (if languages not equivalent)"
    )
    
    counterexample_type: Optional[Literal["should_accept", "should_reject"]] = Field(
        default=None,
        description="Whether the counterexample should be accepted or rejected"
    )


class FSAFeedback(BaseModel):
    """
    Structured feedback for FSA evaluation with UI highlighting support.
    
    Contains detailed analysis, errors with element references for highlighting,
    and hints for improvement.
    """
    summary: str = Field(
        default="",
        description="Brief summary of the evaluation result"
    )
    
    errors: List[ValidationError] = Field(
        default_factory=list,
        description="List of errors with element references for UI highlighting"
    )
    
    warnings: List[ValidationError] = Field(
        default_factory=list,
        description="List of non-critical warnings"
    )
    
    structural: Optional[StructuralInfo] = Field(
        default=None,
        description="Structural analysis of the FSA (determinism, completeness, etc.)"
    )
    
    language: Optional[LanguageComparison] = Field(
        default=None,
        description="Language equivalence comparison with counterexample if applicable"
    )
    
    test_results: List[TestResult] = Field(
        default_factory=list,
        description="Results of individual test cases"
    )
    
    hints: List[str] = Field(
        default_factory=list,
        description="Helpful hints for improving the FSA"
    )


class Result(BaseModel):
    """
    Complete evaluation result for FSA validation.
    
    Contains overall correctness, feedback message, optional score,
    and structured feedback for UI integration.
    
    Example response:
    {
        "is_correct": false,
        "feedback": "Your FSA rejects 'ab' but it should accept it.",
        "score": 0.75,
        "fsa_feedback": {
            "summary": "Language mismatch - incorrect behavior on some inputs",
            "errors": [
                {
                    "message": "Transition from q0 on 'a' goes to wrong state",
                    "code": "INCORRECT_TRANSITION",
                    "severity": "error",
                    "highlight": {
                        "type": "transition",
                        "from_state": "q0",
                        "to_state": "q2",
                        "symbol": "a"
                    },
                    "suggestion": "This transition should go to q1"
                }
            ],
            "language": {
                "are_equivalent": false,
                "counterexample": "ab",
                "counterexample_type": "should_accept"
            },
            "structural": {
                "is_deterministic": true,
                "is_complete": true,
                "num_states": 3,
                "num_transitions": 6,
                "unreachable_states": [],
                "dead_states": []
            },
            "test_results": [
                {"input": "ab", "expected": true, "actual": false, "passed": false}
            ],
            "hints": ["Try tracing through your FSA with the string 'ab'"]
        }
    }
    """
    is_correct: bool = Field(
        default=False,
        description="Overall correctness: true if FSA is correct, false otherwise"
    )
    
    feedback: str = Field(
        default="",
        description="Human-readable feedback message for the student"
    )
    
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized score (0.0-1.0) for partial credit, null if not using partial credit"
    )
    
    fsa_feedback: Optional[FSAFeedback] = Field(
        default=None,
        description="Detailed structured feedback with element highlighting for UI"
    )
