from typing import Any
from lf_toolkit.evaluation import Result as LFResult, Params

from .schemas import FSA, FSAFrontend
from .schemas.result import Result
from .correction import analyze_fsa_correction

# def evaluation_function(
#     payload: Any
# ) -> LFResult:
#   return LFResult(
#     is_correct=False,
#         feedback_items=[("error", f"{payload}")]
#     )

def evaluation_function(
    response: Any,
    answer: Any,
    params: Params,
) -> LFResult:
    """
    Evaluate a student's FSA response against the expected answer.
    
    Args:
        response: Student's FSA (dict with states, alphabet, transitions, etc.), since frontend constriants, this is FSAFrontend
        answer: Expected FSA still, FSAFrontend for the same reason
        params: Extra parameters (e.g., require_minimal)
    
    Returns:
        LFResult with is_correct and feedback
    """
    try:
        # Parse FSAs from input
        student_fsa_ = FSAFrontend.model_validate(response)
        expected_fsa_ = FSAFrontend.model_validate(answer)

        student_fsa = student_fsa_.from_flattened()
        expected_fsa = expected_fsa_.from_flattened()

        
        # Get require_minimal from params if present
        require_minimal = params.get("require_minimal", False) if hasattr(params, "get") else False
        
        # Run correction pipeline
        result: Result = analyze_fsa_correction(student_fsa, expected_fsa, require_minimal)
        
        # Convert to lf_toolkit Result
        return LFResult(
            is_correct=result.is_correct,
            feedback_items=[("feedback", result.feedback)]
        )
        
    except Exception as e:
        return LFResult(
            is_correct=False,
            feedback_items=[("error", f"Invalid FSA format: {str(e)}, received: \n\nresponse: {response}\n\n answer: {answer}, \n\nparams: {params}")]
        )
