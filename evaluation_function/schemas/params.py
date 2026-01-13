"""
Evaluation Parameters Schema

Configuration options for how the FSA evaluation is performed.
"""

from typing import Literal
from pydantic import BaseModel, Field


class Params(BaseModel):
    """
    Evaluation parameters.
    
    Example:
    {
        "evaluation_mode": "lenient",
        "expected_type": "DFA",
        "feedback_verbosity": "standard"
    }
    """
    # Evaluation mode
    evaluation_mode: Literal["strict", "lenient", "partial"] = Field(
        default="lenient",
        description="strict: exact match, lenient: language equivalence, partial: partial credit"
    )
    
    # Expected automaton type
    expected_type: Literal["DFA", "NFA", "any"] = Field(
        default="any",
        description="Expected automaton type"
    )
    
    # Feedback level
    feedback_verbosity: Literal["minimal", "standard", "detailed"] = Field(
        default="standard",
        description="Level of feedback detail"
    )
    
    # Validation options
    check_minimality: bool = Field(default=False, description="Check if FSA is minimal")
    check_completeness: bool = Field(default=False, description="Check if DFA is complete")
    
    # UI options
    highlight_errors: bool = Field(default=True, description="Include element IDs for UI highlighting")
    show_counterexample: bool = Field(default=True, description="Show counterexample if languages differ")
    
    # Test generation
    max_test_length: int = Field(default=10, ge=1, le=50, description="Max length for generated test strings")
