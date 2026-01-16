"""FSA Correction Module

Compares student FSAs against expected FSAs.

Exports:
- analyze_fsa_correction: Main pipeline (FSA vs FSA -> CorrectionResult)
- check_minimality: Check if FSA is minimal
- CorrectionResult: Result model with .to_fsa_feedback(), .model_dump()
"""

from .correction import (
    analyze_fsa_correction,
    check_minimality,
    CorrectionResult,
)

__all__ = [
    "analyze_fsa_correction",
    "check_minimality",
    "CorrectionResult",
]
