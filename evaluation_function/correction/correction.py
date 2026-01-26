"""
FSA Correction Module

Compares student FSAs against expected FSAs.
Returns Result with FSAFeedback for UI highlighting.

All detailed "why" feedback comes from are_isomorphic() in validation module.
"""

from typing import List, Optional, Tuple

# Schema imports
from ..schemas import FSA, ValidationError, ErrorCode
from ..schemas.result import Result, FSAFeedback, StructuralInfo, LanguageComparison

# Validation imports
from ..validation.validation import (
    is_valid_fsa,
    fsas_accept_same_language,
    get_structured_info_of_fsa,
)

# Algorithm imports for minimality check
from ..algorithms.minimization import hopcroft_minimization


# =============================================================================
# Minimality Check
# =============================================================================

def _check_minimality(fsa: FSA) -> Tuple[bool, Optional[ValidationError]]:
    """Check if FSA is minimal by comparing with its minimized version."""
    try:
        minimized = hopcroft_minimization(fsa)
        if len(minimized.states) < len(fsa.states):
            return False, ValidationError(
                message=f"FSA is not minimal: has {len(fsa.states)} states but can be reduced to {len(minimized.states)}",
                code=ErrorCode.NOT_MINIMAL,
                severity="error",
                suggestion="Minimize your FSA by merging equivalent states"
            )
        return True, None
    except Exception:
        return True, None


def check_minimality(fsa: FSA) -> bool:
    """Check if FSA is minimal."""
    is_min, _ = _check_minimality(fsa)
    return is_min


# =============================================================================
# Helper Functions
# =============================================================================

def _build_feedback(
    summary: str,
    validation_errors: List[ValidationError],
    equivalence_errors: List[ValidationError],
    structural_info: Optional[StructuralInfo]
) -> FSAFeedback:
    """Build FSAFeedback from errors and analysis."""
    all_errors = validation_errors + equivalence_errors
    errors = [e for e in all_errors if e.severity == "error"]
    warnings = [e for e in all_errors if e.severity in ("warning", "info")]
    
    # Build hints from all error suggestions
    hints = [e.suggestion for e in all_errors if e.suggestion]
    if structural_info:
        if structural_info.unreachable_states:
            hints.append("Consider removing unreachable states")
        if structural_info.dead_states:
            hints.append("Dead states can never lead to acceptance")
    
    # Build language comparison
    language = LanguageComparison(are_equivalent=len(equivalence_errors) == 0)
    
    return FSAFeedback(
        summary=summary,
        errors=errors,
        warnings=warnings,
        structural=structural_info,
        language=language,
        hints=hints
    )


def _summarize_errors(errors: List[ValidationError]) -> str:
    """Generate summary from error messages."""
    error_types = set()
    for error in errors:
        msg = error.message.lower()
        if "alphabet" in msg:
            error_types.add("alphabet mismatch")
        elif "state" in msg and "count" in msg:
            error_types.add("state count mismatch")
        elif "accepting" in msg or "incorrectly marked" in msg:
            error_types.add("acceptance error")
        elif "transition" in msg:
            error_types.add("transition error")
    
    if error_types:
        return f"Languages differ: {', '.join(error_types)}"
    return f"Languages differ: {len(errors)} issue(s)"


# =============================================================================
# Main Pipeline
# =============================================================================

def analyze_fsa_correction(
    student_fsa: FSA,
    expected_fsa: FSA,
    require_minimal: bool = False
) -> Result:
    """
    Compare student FSA against expected FSA.
    
    Returns Result with:
    - is_correct: True if FSAs accept same language
    - feedback: Human-readable summary
    - fsa_feedback: Structured feedback with ElementHighlight for UI
    
    Args:
        student_fsa: The student's FSA
        expected_fsa: The reference/expected FSA  
        require_minimal: Whether to require student FSA to be minimal
    """
    validation_errors: List[ValidationError] = []
    equivalence_errors: List[ValidationError] = []
    structural_info: Optional[StructuralInfo] = None
    
    # Step 1: Validate student FSA structure
    student_errors = is_valid_fsa(student_fsa)
    if student_errors:
        summary = "FSA has structural errors"
        return Result(
            is_correct=False,
            feedback=summary,
            fsa_feedback=_build_feedback(summary, student_errors, [], None)
        )
    
    # Step 2: Validate expected FSA (should not fail)
    expected_errors = is_valid_fsa(expected_fsa)
    if expected_errors:
        return Result(
            is_correct=False,
            feedback="Internal error: expected FSA is invalid"
        )
    
    # Step 3: Check minimality if required
    if require_minimal:
        is_min, min_error = _check_minimality(student_fsa)
        if not is_min and min_error:
            validation_errors.append(min_error)
    
    # Step 4: Structural analysis
    structural_info = get_structured_info_of_fsa(student_fsa)
    
    # Step 5: Language equivalence (with detailed feedback from are_isomorphic)
    equivalence_errors = fsas_accept_same_language(student_fsa, expected_fsa)
    
    if not equivalence_errors and not validation_errors:
        return Result(
            is_correct=True,
            feedback="Correct! FSA accepts the expected language.",
            fsa_feedback=_build_feedback("FSA is correct", [], [], structural_info)
        )
    
    # Build result with errors
    is_correct = len(equivalence_errors) == 0 and len(validation_errors) == 0
    summary = _summarize_errors(equivalence_errors) if equivalence_errors else "FSA has issues"
    
    return Result(
        is_correct=is_correct,
        feedback=summary,
        fsa_feedback=_build_feedback(summary, validation_errors, equivalence_errors, structural_info)
    )
