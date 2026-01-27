from typing import Any
from lf_toolkit.evaluation import Result as LFResult
from .schemas import FSA
from .schemas.result import Result
from .correction import analyze_fsa_correction

def validate_fsa(value: str | dict) -> FSA:
    if isinstance(value, str):
        return FSA.model_validate_json(value)
    return FSA.model_validate(value)

def evaluation_function(payload: Any) -> LFResult:
    """
    Evaluate a student's FSA response against the expected answer.
    
    Args:
        payload: dict with keys 'response', 'answer', 'params' (front-end may wrap everything)
    
    Returns:
        LFResult
    """
    try:
        # Extract response/answer from the payload
        raw_response = payload.get("response") or payload.get("params", {}).get("response")
        raw_answer = payload.get("answer") or payload.get("params", {}).get("answer")
        params = payload.get("params", {})

        if raw_response is None or raw_answer is None:
            raise ValueError("Missing response or answer in payload")

        # Parse FSAs
        student_fsa = validate_fsa(raw_response)
        expected_fsa = validate_fsa(raw_answer)

        require_minimal = params.get("require_minimal", False)

        # Run correction
        result: Result = analyze_fsa_correction(student_fsa, expected_fsa, require_minimal)

        # Convert to LFResult
        return LFResult(
            is_correct=result.is_correct,
            feedback_items=[("feedback", result.feedback)]
        )

    except Exception as e:
        return LFResult(
            is_correct=False,
            feedback_items=[(
                "error",
                f"Invalid FSA format: {str(e)}\n\npayload received:\n{payload}"
            )]
        )
