"""
FSA Correction Module

Compares student FSAs against expected FSAs.
Returns Result with FSAFeedback for UI highlighting.

All detailed "why" feedback comes from are_isomorphic() in validation module.
"""

from typing import List, Optional

from evaluation_function.schemas.params import Params

# Schema imports
from ..schemas import FSA, ValidationError, ErrorCode, ValidationResult
from ..schemas.result import Result, FSAFeedback, StructuralInfo, LanguageComparison

# Validation imports
from ..validation.validation import (
    are_isomorphic,
    is_valid_fsa,
    is_deterministic,
    is_complete,
    is_minimal,
    fsas_accept_same_language,
    get_structured_info_of_fsa,
)


# =============================================================================
# Feedback Helpers
# =============================================================================

def _build_feedback(
    summary: str,
    validation_errors: List[ValidationError],
    equivalence_errors: List[ValidationError],
    structural_info: Optional[StructuralInfo],
    params: Params
) -> FSAFeedback:
    """Build FSAFeedback from errors and analysis."""
    all_errors = validation_errors + equivalence_errors

    errors = [e for e in all_errors if e.severity == "error"]
    warnings = [e for e in all_errors if e.severity in ("warning", "info")]

    # Remove UI highlights if disabled
    if not params.highlight_errors:
        for e in all_errors:
            e.highlight = None

    # Build hints
    hints: List[str] = []
    if params.feedback_verbosity != "minimal":
        hints.extend(e.suggestion for e in all_errors if e.suggestion)

        if params.feedback_verbosity == "detailed" and structural_info:
            if structural_info.unreachable_states:
                unreachable = ", ".join(structural_info.unreachable_states)
                hints.append(
                    f"Tip: States {{{unreachable}}} are unreachable from the start state"
                )
            if structural_info.dead_states:
                dead = ", ".join(structural_info.dead_states)
                hints.append(
                    f"Tip: States {{{dead}}} can never reach an accepting state"
                )
    else:
        structural_info = None
        hints = []

    language = LanguageComparison(
        are_equivalent=len(equivalence_errors) == 0
    )

    return FSAFeedback(
        summary=summary,
        errors=errors,
        warnings=warnings,
        structural=structural_info,
        language=language,
        hints=hints
    )


def _summarize_errors(errors: List[ValidationError]) -> str:
    """Generate a human-readable summary from error messages."""
    categories = set()

    for error in errors:
        msg = error.message.lower()
        if "alphabet" in msg:
            categories.add("alphabet issue")
        elif "accept" in msg:
            categories.add("accepting states issue")
        elif "transition" in msg:
            categories.add("transition issue")
        elif "state" in msg:
            categories.add("state structure issue")

    if len(categories) == 1:
        return f"Almost there! Your FSA has a {next(iter(categories))}."
    elif categories:
        return f"Your FSA has multiple issues: {', '.join(categories)}."
    return "Your FSA does not match the expected language."


# =============================================================================
# Main Pipeline
# =============================================================================

def analyze_fsa_correction(
    student_fsa: FSA,
    expected_fsa: FSA,
    params: Params
) -> Result:
    """
    Compare student FSA against expected FSA using configurable parameters.
    """

    validation_errors: List[ValidationError] = []
    equivalence_errors: List[ValidationError] = []
    structural_info: Optional[StructuralInfo] = None

    # -------------------------------------------------------------------------
    # Step 1: Validate student FSA structure
    # -------------------------------------------------------------------------
    student_result = is_valid_fsa(student_fsa)
    if not student_result.ok:
        summary = (
            "Your FSA has a structural problem that needs to be fixed first."
            if len(student_result.errors) == 1
            else f"Your FSA has {len(student_result.errors)} structural problems to fix."
        )
        return Result(
            is_correct=False,
            feedback=summary,
            fsa_feedback=_build_feedback(
                summary,
                student_result.errors,
                [],
                None,
                params
            )
        )

    # -------------------------------------------------------------------------
    # Step 2: Validate expected FSA (should never fail)
    # -------------------------------------------------------------------------
    expected_result = is_valid_fsa(expected_fsa)
    if not expected_result.ok:
        return Result(
            is_correct=False,
            feedback="Oops! There's an issue with the expected answer. Please contact your instructor."
        )

    # -------------------------------------------------------------------------
    # Step 3: Enforce expected automaton type
    # -------------------------------------------------------------------------
    if params.expected_type == "DFA":
        det_result = is_deterministic(student_fsa)
        if not det_result.ok:
            summary = "Your automaton must be deterministic (a DFA)."
            return Result(
                is_correct=False,
                feedback=summary,
                fsa_feedback=_build_feedback(
                    summary,
                    det_result.errors,
                    [],
                    None,
                    params
                )
            )

    # -------------------------------------------------------------------------
    # Step 4: Optional completeness check
    # -------------------------------------------------------------------------
    if params.check_completeness:
        comp_result = is_complete(student_fsa)
        if not comp_result.ok:
            validation_errors.extend(comp_result.errors)

    # -------------------------------------------------------------------------
    # Step 5: Optional minimality check
    # -------------------------------------------------------------------------
    validation_result = None
    if params.check_minimality:
        validation_result = is_minimal(student_fsa)
        if not validation_result.ok:
            validation_errors.extend(validation_result.errors)

    # -------------------------------------------------------------------------
    # Step 6: Structural analysis (for feedback only)
    # -------------------------------------------------------------------------
    structural_info = get_structured_info_of_fsa(student_fsa)

    # -------------------------------------------------------------------------
    # Step 7: Language equivalence
    # -------------------------------------------------------------------------
    equivalence_result = fsas_accept_same_language(
        student_fsa, expected_fsa
    )
    equivalence_errors.extend(equivalence_result.errors)

    # -------------------------------------------------------------------------
    # Step 8: Isomorphism
    # -------------------------------------------------------------------------
    iso_result = are_isomorphic(student_fsa, expected_fsa)
    equivalence_errors.extend(iso_result.errors)

    # -------------------------------------------------------------------------
    # Step 9: Decide correctness based on evaluation mode
    # -------------------------------------------------------------------------
    if params.evaluation_mode == "strict":
        is_correct = (
            (not params.check_minimality or validation_result.ok)
            and equivalence_result.ok
            and iso_result.ok
        )
    elif params.evaluation_mode == "lenient":
        is_correct = (
            (not params.check_minimality or validation_result.ok)
            and equivalence_result.ok
        )
    else:  # partial # I dont know what the partial is meant for, always mark as incorrect?
        is_correct = False

    # -------------------------------------------------------------------------
    # Step 10: Build summary
    # -------------------------------------------------------------------------
    if is_correct:
        feedback = (
            f"Correct! Your FSA with {len(student_fsa.states)} state(s) "
            "accepts exactly the right language. Well done!"
        )
        summary = "Your FSA is correct!"
    else:
        summary = (
            _summarize_errors(equivalence_errors)
            if len(equivalence_errors) > 0
            else "Your FSA has some issues to address."
        )
        feedback = summary

    # -------------------------------------------------------------------------
    # Step 11: Return result
    # -------------------------------------------------------------------------
    return Result(
        is_correct=is_correct,
        feedback=feedback,
        fsa_feedback=_build_feedback(
            summary,
            validation_errors,
            equivalence_errors,
            structural_info,
            params
        )
    )
