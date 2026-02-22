from typing import Any, Tuple
from lf_toolkit.evaluation import Result as LFResult

from evaluation_function.schemas.params import Params
from .schemas import FSA, FSAFrontend
from .schemas.result import FSAFeedback, Result
from .correction import analyze_fsa_correction
import json

def validate_fsa(value: str | dict) -> Tuple[FSA, Params]:
    """Parse a FSA from JSON string or dict."""
    if isinstance(value, str):
        return FSAFrontend.model_validate_json(value).toFSA()
    return FSAFrontend.model_validate(value).toFSA(), Params.model_validate_json(FSAFrontend.model_validate(value).config)

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
        if not response or not answer:
            response = params.get("response") if isinstance(params, dict) else None
            answer = params.get("answer") if isinstance(params, dict) else None
            params = params.get("params") if isinstance(params, dict) else None
            # raise ValueError(
            #     f"Missing FSA data: response or answer is None\n"
            #     f"response: {response}\nanswer: {answer}"
            # )
        # Parse FSAs
        student_fsa, _ = validate_fsa(response)
        expected_fsa, expected_config = validate_fsa(answer)

        # Run correction pipeline
        result: Result = analyze_fsa_correction(student_fsa, expected_fsa, expected_config)

        # Return LFResult
        return LFResult(
            is_correct=result.is_correct,
            feedback_items=[("result", result.feedback), ("errors", result.fsa_feedback.model_dump_json())]
        )

    except Exception as e:
        result: Result = Result(
            is_correct=False,
            feedback=f"Error during evaluation: {str(e)}",
            fsa_feedback=FSAFeedback(
                summary=f"Error during evaluation: {str(e)}",
                errors=[]
            )
        )
        return LFResult(
            is_correct=False,
            feedback_items=[(
                "error",
                result.fsa_feedback.model_dump_json()
            )]
        )
