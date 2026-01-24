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
            diff = len(fsa.states) - len(minimized.states)
            return False, ValidationError(
                message=f"Your FSA works correctly, but it's not minimal! You have {len(fsa.states)} states, but only {len(minimized.states)} are needed. You could remove {diff} state(s).",
                code=ErrorCode.NOT_MINIMAL,
                severity="error",
                suggestion="Look for states that behave identically (same transitions and acceptance) - these can be merged into one"
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
            unreachable = ", ".join(structural_info.unreachable_states)
            hints.append(f"Tip: States {{{unreachable}}} can't be reached from your start state - you might want to remove them or add transitions to them")
        if structural_info.dead_states:
            dead = ", ".join(structural_info.dead_states)
            hints.append(f"Tip: States {{{dead}}} can never lead to acceptance - this might be intentional (trap states) or a bug")
    
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
            error_types.add("alphabet issue")
        elif "states" in msg and ("many" in msg or "few" in msg or "needed" in msg):
            error_types.add("incorrect number of states")
        elif "accepting" in msg or "accept" in msg:
            error_types.add("accepting states issue")
        elif "transition" in msg or "reading" in msg:
            error_types.add("transition issue")
    
    if len(error_types) == 1:
        issue = list(error_types)[0]
        return f"Almost there! Your FSA has an {issue}. Check the details below."
    elif error_types:
        return f"Your FSA doesn't quite match the expected language. Issues found: {', '.join(error_types)}"
    return f"Your FSA doesn't accept the correct language. Found {len(errors)} issue(s) to fix."


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
        num_errors = len(student_errors)
        if num_errors == 1:
            summary = "Your FSA has a structural problem that needs to be fixed first. See the details below."
        else:
            summary = f"Your FSA has {num_errors} structural problems that need to be fixed first. See the details below."
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
            feedback="Oops! There's an issue with the expected answer. Please contact your instructor."
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
        # Success message with some stats
        state_count = len(student_fsa.states)
        feedback = f"Correct! Your FSA with {state_count} state(s) accepts exactly the right language. Well done!"
        return Result(
            is_correct=True,
            feedback=feedback,
            fsa_feedback=_build_feedback("Your FSA is correct!", [], [], structural_info)
        )
    
    # Build result with errors
    is_correct = len(equivalence_errors) == 0 and len(validation_errors) == 0
    summary = _summarize_errors(equivalence_errors) if equivalence_errors else "Your FSA has some issues to address."
    
    return Result(
        is_correct=is_correct,
        feedback=summary,
        fsa_feedback=_build_feedback(summary, validation_errors, equivalence_errors, structural_info)
    )
