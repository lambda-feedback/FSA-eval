from typing import Any
from lf_toolkit.evaluation import Result as LFResult
from .schemas import FSA, FSAFrontend
from .schemas.result import Result
from .correction import analyze_fsa_correction

def validate_fsa(value: str | dict) -> FSA:
    """Parse a FSA from JSON string or dict."""
    if isinstance(value, str):
        return FSAFrontend.model_validate_json(value).toFSA()
    return FSAFrontend.model_validate(value).toFSA()

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
        # TEMPORARY WORKAROUND: Extract from params if not passed directly
        if params is None:
            params = {}

        if isinstance(params, dict):
            raw_response = response or params.get("response") or {}
            raw_answer = answer or params.get("answer") or {}
            extra_params = params.get("params") or {}
        else:
            # If params is not a dict, fallback to empty dict
            raw_response = response
            raw_answer = answer
            extra_params = {}

        if not raw_response or not raw_answer:
            raise ValueError(
                f"Missing FSA data: response or answer is None\n"
                f"raw_response: {raw_response}\nraw_answer: {raw_answer}"
            )

        # Parse FSAs
        student_fsa = validate_fsa(raw_response)
        expected_fsa = validate_fsa(raw_answer)

        require_minimal = extra_params.get("require_minimal", False) if isinstance(extra_params, dict) else False

        # Run correction pipeline
        result: Result = analyze_fsa_correction(student_fsa, expected_fsa, require_minimal)

        # Return LFResult
        return LFResult(
            is_correct=result.is_correct,
            feedback_items=[("result", result.feedback), ("errors", result.fsa_feedback.model_dump_json())]
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
