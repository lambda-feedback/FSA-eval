from typing import Any
from lf_toolkit.evaluation import Result as LFResult
from .schemas import FSA
from .schemas.result import Result
from .correction import analyze_fsa_correction

def validate_fsa(value: str | dict) -> FSA:
    """Parse a FSA from JSON string or dict."""
    if isinstance(value, str):
        return FSA.model_validate_json(value)
    return FSA.model_validate(value)

def evaluation_function(
    response: Any = None,
    answer: Any = None,
    params: Any = None  # Temp workaround: treat params as Any
) -> LFResult:
    """
    Temporary FSA evaluation function.
    
    Args:
        response: Student's FSA (may be None if frontend wraps everything in params)
        answer: Expected FSA (may be None)
        params: Additional parameters (or full payload if frontend wraps everything here)
    
    Returns:
        LFResult with is_correct and feedback_items
    """
    try:
        # Extract student and expected FSAs from whatever is present
        raw_response = response or getattr(params, "response", None) or params.get("response", None)
        raw_answer = answer or getattr(params, "answer", None) or params.get("answer", None)
        extra_params = params.get("params") or params

        if raw_response is None or raw_answer is None:
            raise ValueError("Missing FSA data: response or answer is None")

        # Parse FSAs
        student_fsa = validate_fsa(raw_response)
        expected_fsa = validate_fsa(raw_answer)

        require_minimal = extra_params.get("require_minimal", False) if isinstance(extra_params, dict) else False

        # Run correction pipeline
        result: Result = analyze_fsa_correction(student_fsa, expected_fsa, require_minimal)

        # Return LFResult
        return LFResult(
            is_correct=result.is_correct,
            feedback_items=[("feedback", result.feedback)]
        )

    except Exception as e:
        # Always return LFResult with raw payload for debugging
        return LFResult(
            is_correct=False,
            feedback_items=[(
                "error",
                f"Invalid FSA format: {str(e)}\n\n"
                f"response: {response}\nanswer: {answer}\nparams: {params}"
            )]
        )
