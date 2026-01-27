"""
Preview function for FSA validation.

The preview function validates student FSA responses BEFORE submission.
It catches clear structural errors early, preventing students from submitting
invalid FSAs for full evaluation.

Validation checks performed:
1. Parse check - Is the response a valid FSA structure?
2. Structural validation - Are states, initial, accept states, and transitions valid?
3. Warnings - Unreachable states, dead states, non-determinism (if applicable)
"""

from typing import Any, List, Dict
from lf_toolkit.preview import Result, Params, Preview

from .schemas import FSA, ValidationError
from .validation.validation import (
    is_valid_fsa,
    is_deterministic,
    find_unreachable_states,
    find_dead_states,
    get_structured_info_of_fsa,
)


def parse_fsa(value: Any) -> FSA:
    """
    Parse an FSA from various input formats.
    
    Args:
        value: FSA as dict or JSON string
        
    Returns:
        Parsed FSA object
        
    Raises:
        ValueError: If the input cannot be parsed as a valid FSA
    """
    if value is None:
        raise ValueError("No FSA provided")
    
    if isinstance(value, str):
        # Try to parse as JSON string
        return FSA.model_validate_json(value)
    elif isinstance(value, dict):
        return FSA.model_validate(value)
    else:
        raise ValueError(f"Expected FSA as dict or JSON string, got {type(value).__name__}")


def format_errors_for_preview(errors: List[ValidationError], max_errors: int = 5) -> str:
    """
    Format validation errors into a human-readable string for preview feedback.
    
    Args:
        errors: List of ValidationError objects
        max_errors: Maximum number of errors to show (to avoid overwhelming the user)
        
    Returns:
        Formatted error string
    """
    if not errors:
        return ""
    
    # Separate errors by severity
    critical_errors = [e for e in errors if e.severity == "error"]
    warnings = [e for e in errors if e.severity == "warning"]
    
    lines = []
    
    if critical_errors:
        if len(critical_errors) == 1:
            lines.append("There's an issue with your FSA that needs to be fixed:")
        else:
            lines.append(f"There are {len(critical_errors)} issues with your FSA that need to be fixed:")
        lines.append("")
        
        for i, err in enumerate(critical_errors[:max_errors], 1):
            lines.append(f"  {i}. {err.message}")
            if err.suggestion:
                lines.append(f"     >> {err.suggestion}")
            lines.append("")
        
        if len(critical_errors) > max_errors:
            lines.append(f"  ... and {len(critical_errors) - max_errors} more issue(s)")
    
    if warnings:
        if lines:
            lines.append("")
        lines.append("Some things to consider (not blocking, but worth checking):")
        lines.append("")
        for i, warn in enumerate(warnings[:max_errors], 1):
            lines.append(f"  - {warn.message}")
            if warn.suggestion:
                lines.append(f"    >> {warn.suggestion}")
        
        if len(warnings) > max_errors:
            lines.append(f"  ... and {len(warnings) - max_errors} more suggestion(s)")
    
    return "\n".join(lines)


def errors_to_dict_list(errors: List[ValidationError]) -> List[Dict]:
    """
    Convert ValidationError objects to dictionaries for JSON serialization.
    """
    return [
        {
            "message": e.message,
            "code": e.code.value if hasattr(e.code, 'value') else str(e.code),
            "severity": e.severity,
            "highlight": e.highlight.model_dump() if e.highlight else None,
            "suggestion": e.suggestion
        }
        for e in errors
    ]


def preview_function(response: Any, params: Params) -> Result:
    """
    Validate a student's FSA response before submission.
    
    This function performs structural validation to catch clear errors early,
    preventing students from submitting obviously invalid FSAs for evaluation.
    
    Args:
        response: Student's FSA response (dict or JSON string)
        params: Extra parameters:
            - require_deterministic (bool): Whether to require DFA (default: False)
            - show_warnings (bool): Whether to show warnings (default: True)
    
    Returns:
        Result with:
        - preview.latex: FSA summary if valid
        - preview.feedback: Error/warning messages if any
        - preview.sympy: Structured validation data (errors, warnings, info)
    """
    # Extract params with defaults
    require_deterministic = False
    show_warnings = True
    
    if hasattr(params, 'get'):
        require_deterministic = params.get("require_deterministic", False)
        show_warnings = params.get("show_warnings", True)
    elif isinstance(params, dict):
        require_deterministic = params.get("require_deterministic", False)
        show_warnings = params.get("show_warnings", True)
    
    try:
        # Step 1: Parse the FSA
        fsa = parse_fsa(response)
        
    except Exception as e:
        # Failed to parse - this is a critical error
        error_msg = str(e)
        
        # Make error message more user-friendly
        if "validation error" in error_msg.lower():
            if "states" in error_msg.lower():
                feedback = "Your FSA is missing the 'states' list. Every FSA needs a set of states to define!"
            elif "alphabet" in error_msg.lower():
                feedback = "Your FSA is missing the 'alphabet'. What symbols should your automaton recognize?"
            elif "initial_state" in error_msg.lower():
                feedback = "Your FSA needs an initial state - this is where processing begins!"
            elif "transitions" in error_msg.lower():
                feedback = "There's an issue with your transitions. Each transition needs a from_state, to_state, and symbol."
            else:
                feedback = f"Your FSA structure isn't quite right: {error_msg}"
        elif "json" in error_msg.lower():
            feedback = "Couldn't read your FSA data. Make sure it's properly formatted."
        elif "no fsa" in error_msg.lower() or "none" in error_msg.lower():
            feedback = "No FSA provided! Please build your automaton before checking."
        else:
            feedback = f"There's a problem with your FSA format: {error_msg}"
        
        return Result(
            preview=Preview(
                feedback=feedback,
                sympy={
                    "valid": False,
                    "parse_error": True,
                    "errors": [{"message": feedback, "code": "PARSE_ERROR", "severity": "error"}]
                }
            )
        )
    
    # Step 2: Structural validation
    all_errors: List[ValidationError] = []
    
    # Run structural validation (states, initial, accept, transitions)
    structural_errors = is_valid_fsa(fsa)
    all_errors.extend(structural_errors)
    
    # If there are structural errors, don't proceed with other checks
    if structural_errors:
        feedback = "Your FSA has some issues that need to be fixed before submission.\n\n"
        feedback += format_errors_for_preview(all_errors)
        return Result(
            preview=Preview(
                feedback=feedback,
                sympy={
                    "valid": False,
                    "errors": errors_to_dict_list(all_errors),
                    "num_states": len(fsa.states),
                    "num_transitions": len(fsa.transitions)
                }
            )
        )
    
    # Step 3: Additional checks (determinism, unreachable states, dead states)
    warnings: List[ValidationError] = []
    
    # Check determinism if required
    if require_deterministic:
        det_errors = is_deterministic(fsa)
        if det_errors:
            all_errors.extend(det_errors)
    
    # Check for warnings (unreachable/dead states)
    if show_warnings:
        unreachable = find_unreachable_states(fsa)
        dead = find_dead_states(fsa)
        warnings.extend(unreachable)
        warnings.extend(dead)
    
    # Get structural info
    try:
        info = get_structured_info_of_fsa(fsa)
        info_dict = info.model_dump()
    except Exception:
        info_dict = {
            "num_states": len(fsa.states),
            "num_transitions": len(fsa.transitions),
            "is_deterministic": len(is_deterministic(fsa)) == 0
        }
    
    # Step 4: Build response
    has_errors = len(all_errors) > 0
    has_warnings = len(warnings) > 0
    
    if has_errors:
        # Critical errors - cannot submit
        feedback = "Hold on! Your FSA has issues that need to be addressed.\n\n"
        feedback += format_errors_for_preview(all_errors + warnings)
        return Result(
            preview=Preview(
                feedback=feedback,
                sympy={
                    "valid": False,
                    "errors": errors_to_dict_list(all_errors),
                    "warnings": errors_to_dict_list(warnings),
                    **info_dict
                }
            )
        )
    
    # Build success message
    state_word = "state" if len(fsa.states) == 1 else "states"
    trans_word = "transition" if len(fsa.transitions) == 1 else "transitions"
    
    fsa_type = "DFA (Deterministic)" if info_dict.get("is_deterministic") else "NFA (Non-deterministic)"
    
    summary = f"{fsa_type} with {len(fsa.states)} {state_word} and {len(fsa.transitions)} {trans_word}"
    alphabet_str = ", ".join(f"'{s}'" for s in fsa.alphabet)
    
    if has_warnings:
        # Valid but with warnings
        warning_feedback = format_errors_for_preview(warnings)
        feedback = f"Looking good! Your FSA is structurally valid.\n\n"
        feedback += f"Summary: {summary}\n"
        feedback += f"Alphabet: {{{alphabet_str}}}\n\n"
        feedback += warning_feedback
    else:
        feedback = f"Great! Your FSA is structurally valid and ready for submission.\n\n"
        feedback += f"Summary: {summary}\n"
        feedback += f"Alphabet: {{{alphabet_str}}}"
    
    return Result(
        preview=Preview(
            latex=summary,  # Short summary for display
            feedback=feedback,
            sympy={
                "valid": True,
                "errors": [],
                "warnings": errors_to_dict_list(warnings),
                **info_dict
            }
        )
    )
