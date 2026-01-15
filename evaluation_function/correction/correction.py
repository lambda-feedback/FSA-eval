"""
FSA Correction Module

Provides FSA comparison functionality by leveraging the validation module.
The validation module's are_isomorphic() already provides detailed feedback with:
- State acceptance errors (with ElementHighlight)
- Transition errors - missing, extra, wrong destination (with ElementHighlight)
- Alphabet mismatches
- State count mismatches

Pipeline:
1. Structural Validation (is_valid_fsa)
2. Minimality Check (if required)
3. Structural Analysis (get_structured_info_of_fsa)
4. Language Equivalence (fsas_accept_same_language -> are_isomorphic)

All detailed "why" feedback comes from are_isomorphic() in validation module.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

# Schema imports
from ..schemas import FSA, ValidationError, ErrorCode
from ..schemas.result import LanguageComparison, StructuralInfo, FSAFeedback

# Validation imports - these provide all the functionality we need
from ..validation.validation import (
    is_valid_fsa,
    is_deterministic,
    is_complete,
    find_unreachable_states,
    find_dead_states,
    fsas_accept_same_language,
    get_structured_info_of_fsa,
)

# Algorithm imports for minimality check
from ..algorithms.minimization import hopcroft_minimization


# =============================================================================
# Result Model
# =============================================================================

class CorrectionResult(BaseModel):
    """Result of FSA correction analysis."""
    is_equivalent: bool = True
    is_isomorphic: Optional[bool] = None
    is_minimal: Optional[bool] = None
    summary: str = ""
    validation_errors: List[ValidationError] = Field(default_factory=list)
    equivalence_errors: List[ValidationError] = Field(default_factory=list)
    structural_info: Optional[StructuralInfo] = None
    
    def get_all_errors(self) -> List[ValidationError]:
        """Get all errors for UI highlighting."""
        return list(self.validation_errors) + list(self.equivalence_errors)
    
    def get_language_comparison(self) -> LanguageComparison:
        """Convert to LanguageComparison schema."""
        # Extract counterexample from equivalence errors if available
        counterexample = None
        counterexample_type = None
        
        for error in self.equivalence_errors:
            if error.highlight:
                if error.highlight.state_id and "accepting" in error.message.lower():
                    # State acceptance error - can infer counterexample type
                    if "should be an accepting" in error.message.lower():
                        counterexample_type = "should_accept"
                    elif "should not" in error.message.lower() or "incorrectly marked" in error.message.lower():
                        counterexample_type = "should_reject"
                break
        
        return LanguageComparison(
            are_equivalent=self.is_equivalent,
            counterexample=counterexample,
            counterexample_type=counterexample_type
        )
    
    def to_fsa_feedback(self) -> FSAFeedback:
        """Convert to FSAFeedback schema for structured output."""
        all_errors = self.get_all_errors()
        errors = [e for e in all_errors if e.severity == "error"]
        warnings = [e for e in all_errors if e.severity in ("warning", "info")]
        
        hints = []
        for error in self.equivalence_errors:
            if error.suggestion:
                hints.append(error.suggestion)
        
        if self.structural_info:
            if self.structural_info.unreachable_states:
                hints.append("Consider removing unreachable states or adding transitions to reach them")
            if self.structural_info.dead_states:
                hints.append("Dead states can never lead to acceptance - add paths to accepting states")
        
        return FSAFeedback(
            summary=self.summary,
            errors=errors,
            warnings=warnings,
            structural=self.structural_info,
            language=self.get_language_comparison(),
            test_results=[],
            hints=hints[:5]  # Limit hints
        )


# =============================================================================
# Minimality Check
# =============================================================================

def _check_minimality(fsa: FSA) -> Tuple[bool, Optional[ValidationError]]:
    """
    Internal: Check if FSA is minimal by comparing with its minimized version.
    """
    try:
        minimized = hopcroft_minimization(fsa)
        if len(minimized.states) < len(fsa.states):
            return False, ValidationError(
                message=f"FSA is not minimal: has {len(fsa.states)} states but can be reduced to {len(minimized.states)}",
                code=ErrorCode.NOT_COMPLETE,
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
# Main Pipeline
# =============================================================================

def analyze_fsa_correction(
    student_fsa: FSA,
    expected_fsa: FSA,
    check_minimality: bool = False
) -> CorrectionResult:
    """
    Main pipeline: Analyze student FSA against expected FSA.
    
    Pipeline Steps:
    1. Structural Validation: is_valid_fsa()
    2. Minimality Check (if required): hopcroft_minimization comparison
    3. Structural Analysis: get_structured_info_of_fsa()
    4. Language Equivalence: fsas_accept_same_language() -> are_isomorphic()
       (are_isomorphic provides detailed WHY feedback with ElementHighlight)
    
    Args:
        student_fsa: The student's FSA
        expected_fsa: The reference/expected FSA
        check_minimality: Whether to check if student FSA is minimal
    
    Returns:
        CorrectionResult with analysis
    """
    result = CorrectionResult()
    
    # Step 1: Structural Validation
    student_errors = is_valid_fsa(student_fsa)
    if student_errors:
        result.validation_errors = student_errors
        result.is_equivalent = False
        result.summary = "Student FSA has structural errors that must be fixed first"
        return result
    
    expected_errors = is_valid_fsa(expected_fsa)
    if expected_errors:
        result.validation_errors = expected_errors
        result.is_equivalent = False
        result.summary = "Expected FSA has structural errors (internal error)"
        return result
    
    # Step 2: Minimality Check (if required)
    if check_minimality:
        is_min, minimality_error = _check_minimality(student_fsa)
        result.is_minimal = is_min
        if not is_min and minimality_error:
            result.validation_errors.append(minimality_error)
    
    # Step 3: Structural Analysis
    result.structural_info = get_structured_info_of_fsa(student_fsa)
    
    # Step 4: Language Equivalence
    # fsas_accept_same_language calls are_isomorphic which provides detailed feedback:
    # - State acceptance errors with ElementHighlight
    # - Missing/extra/wrong transitions with ElementHighlight
    # - Alphabet mismatches
    # - State count differences
    equiv_errors = fsas_accept_same_language(student_fsa, expected_fsa)
    
    if not equiv_errors:
        result.is_equivalent = True
        result.is_isomorphic = True
        result.summary = "FSAs accept the same language"
        return result
    
    result.is_equivalent = False
    result.is_isomorphic = False
    result.equivalence_errors = equiv_errors
    
    # Generate summary from errors
    error_types = set()
    for error in equiv_errors:
        if "alphabet" in error.message.lower():
            error_types.add("alphabet mismatch")
        elif "state" in error.message.lower() and "count" in error.message.lower():
            error_types.add("state count mismatch")
        elif "accepting" in error.message.lower() or "incorrectly marked" in error.message.lower():
            error_types.add("acceptance error")
        elif "transition" in error.message.lower():
            error_types.add("transition error")
    
    result.summary = f"Languages differ: {', '.join(error_types) if error_types else f'{len(equiv_errors)} issue(s)'}"
    return result


# =============================================================================
# Convenience Functions
# =============================================================================

def get_correction_feedback(
    student_fsa: FSA,
    expected_fsa: FSA,
    check_minimality: bool = False
) -> dict:
    """Returns correction analysis as dict."""
    result = analyze_fsa_correction(student_fsa, expected_fsa, check_minimality)
    return result.model_dump()


def get_fsa_feedback(
    student_fsa: FSA,
    expected_fsa: FSA,
    check_minimality: bool = False
) -> FSAFeedback:
    """Returns structured FSAFeedback schema (recommended for UI)."""
    result = analyze_fsa_correction(student_fsa, expected_fsa, check_minimality)
    return result.to_fsa_feedback()


def check_fsa_properties(fsa: FSA) -> dict:
    """Get FSA properties using validation functions."""
    result = {
        "is_valid": True,
        "is_deterministic": True,
        "is_complete": True,
        "is_minimal": True,
        "validation_errors": [],
        "determinism_errors": [],
        "completeness_errors": [],
        "unreachable_states": [],
        "dead_states": [],
        "structural_info": None
    }
    
    validation_errors = is_valid_fsa(fsa)
    if validation_errors:
        result["is_valid"] = False
        result["validation_errors"] = [e.model_dump() for e in validation_errors]
        return result
    
    det_errors = is_deterministic(fsa)
    result["is_deterministic"] = len(det_errors) == 0
    result["determinism_errors"] = [e.model_dump() for e in det_errors]
    
    if result["is_deterministic"]:
        comp_errors = is_complete(fsa)
        result["is_complete"] = len(comp_errors) == 0
        result["completeness_errors"] = [e.model_dump() for e in comp_errors]
        result["is_minimal"] = check_minimality(fsa)
    else:
        result["is_complete"] = False
        result["is_minimal"] = False
    
    result["unreachable_states"] = [
        e.highlight.state_id for e in find_unreachable_states(fsa)
        if e.highlight and e.highlight.state_id
    ]
    result["dead_states"] = [
        e.highlight.state_id for e in find_dead_states(fsa)
        if e.highlight and e.highlight.state_id
    ]
    result["structural_info"] = get_structured_info_of_fsa(fsa).model_dump()
    
    return result


def quick_equivalence_check(
    student_fsa: FSA,
    expected_fsa: FSA
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Quick equivalence check.
    
    Returns:
        (are_equivalent, counterexample_hint, hint_type)
    """
    if is_valid_fsa(student_fsa) or is_valid_fsa(expected_fsa):
        return False, None, None
    
    equiv_errors = fsas_accept_same_language(student_fsa, expected_fsa)
    if not equiv_errors:
        return True, None, None
    
    # Extract hint from first error
    first_error = equiv_errors[0]
    hint = first_error.message
    hint_type = None
    
    if "accepting" in hint.lower():
        hint_type = "acceptance_error"
    elif "transition" in hint.lower():
        hint_type = "transition_error"
    
    return False, hint, hint_type
