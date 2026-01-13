"""
Result Schema

Extended result schema with structured feedback for UI highlighting.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """A validation error with location info for UI highlighting."""
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Error code for programmatic handling")
    severity: Literal["error", "warning", "info"] = Field(default="error")
    
    # Element reference for UI highlighting
    element_type: Optional[Literal["state", "transition", "initial", "accept", "alphabet"]] = None
    element_id: Optional[str] = Field(default=None, description="State name or transition ID")
    
    # For transitions
    from_state: Optional[str] = None
    to_state: Optional[str] = None
    symbol: Optional[str] = None
    
    suggestion: Optional[str] = Field(default=None, description="Suggested fix")


class TestResult(BaseModel):
    """Result of a single test case."""
    input: str
    expected: bool
    actual: bool
    passed: bool
    trace: Optional[List[str]] = Field(default=None, description="State trace")


class StructuralInfo(BaseModel):
    """Structural analysis of the FSA."""
    is_deterministic: bool = True
    is_complete: bool = False
    num_states: int = 0
    num_transitions: int = 0
    unreachable_states: List[str] = Field(default_factory=list)
    dead_states: List[str] = Field(default_factory=list)


class LanguageComparison(BaseModel):
    """Result of comparing FSA languages."""
    are_equivalent: bool = False
    counterexample: Optional[str] = None
    counterexample_type: Optional[Literal["should_accept", "should_reject"]] = None


class FSAFeedback(BaseModel):
    """Structured feedback for FSA evaluation."""
    summary: str = ""
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    structural: Optional[StructuralInfo] = None
    language: Optional[LanguageComparison] = None
    test_results: List[TestResult] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)


class Result(BaseModel):
    """
    Complete evaluation result.
    
    Example response:
    {
        "is_correct": false,
        "feedback": "Your FSA rejects 'ab' but it should accept.",
        "score": 0.8,
        "fsa_feedback": {
            "summary": "Language mismatch",
            "errors": [...],
            "language": {
                "are_equivalent": false,
                "counterexample": "ab",
                "counterexample_type": "should_accept"
            }
        }
    }
    """
    is_correct: bool = False
    feedback: str = ""
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Score for partial credit")
    fsa_feedback: Optional[FSAFeedback] = Field(default=None, description="Structured feedback for UI")
