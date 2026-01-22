from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from pydantic import BaseModel

from .correction.correction import analyze_fsa_correction

from .schemas.fsa import FSA

from .schemas.result import Result
from lf_toolkit.evaluation import Result as LFResult, Params
from .evaluation import evaluation_function

app = FastAPI(title="FSA Evaluation API")

# -----------------------------
# CORS Setup: allow all origins
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# -----------------------------
# Request Schema
# -----------------------------

class EvaluationRequest(BaseModel):
    """
    Payload sent from frontend.

    response / answer:
      - can be a dict (already-parsed JSON)
      - or a JSON string
    """
    response: Any
    answer: Any
    params: Params


# -----------------------------
# Helper: parse FSA safely
# -----------------------------

def validate_fsa(value: str | dict) -> FSA:
    """
    Parse an FSA from string or dict into the FSA model.
    """
    if isinstance(value, str):
        return FSA.model_validate_json(value)
    return FSA.model_validate(value)


# -----------------------------
# API Endpoint
# -----------------------------

@app.post("/evaluate/fsa", response_model=Result)
def evaluate_fsa(payload: EvaluationRequest):
    """
    Evaluate a student's FSA against the expected answer using analyze_fsa_correction.
    Returns detailed structured Result suitable for UI highlighting.
    """
    try:
        # Parse FSAs
        student_fsa = validate_fsa(payload.response)
        expected_fsa = validate_fsa(payload.answer)

        # Extract require_minimal if present in params
        require_minimal = getattr(payload.params, "require_minimal", False)

        # Run the correction pipeline
        correction_result = analyze_fsa_correction(student_fsa, expected_fsa, require_minimal)

        # Construct the final Result object
        return Result(
            is_correct=correction_result.is_correct,
            feedback=correction_result.feedback,
            fsa_feedback=getattr(correction_result, "fsa_feedback", None),
            score=getattr(correction_result, "score", None),
            input_data=student_fsa  # dev/debug info
        )

    except Exception as e:
        # Return structured HTTP error with all input
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Evaluation failed",
                "message": str(e),
                "received": {
                    "response": payload.response,
                    "answer": payload.answer,
                    "params": payload.params,
                },
            },
        )
