"""
FSA Correction Module

Compares student FSAs against expected FSAs using the validation module.

Pipeline (4 Steps):
1. Structural Validation - is_valid_fsa
2. Minimality Check - check_minimality (if required)
3. Structural Analysis - get_structured_info_of_fsa
4. Language Equivalence - fsas_accept_same_language (-> are_isomorphic)

The validation module's are_isomorphic() provides all "why" feedback:
- State acceptance errors with ElementHighlight
- Transition errors (missing/extra/wrong) with ElementHighlight
- Alphabet and state count mismatches

Main Functions:
- analyze_fsa_correction: Full pipeline (FSA vs FSA -> CorrectionResult)
- get_fsa_feedback: Returns FSAFeedback schema (for UI)
- check_fsa_properties: Structural properties of single FSA
- check_minimality: Verify FSA is minimal
"""

from .correction import (
    # Main pipeline
    analyze_fsa_correction,
    get_correction_feedback,
    get_fsa_feedback,
    check_fsa_properties,
    check_minimality,
    quick_equivalence_check,
    
    # Result class
    CorrectionResult,
)

__all__ = [
    "analyze_fsa_correction",
    "get_correction_feedback",
    "get_fsa_feedback",
    "check_fsa_properties",
    "check_minimality",
    "quick_equivalence_check",
    "CorrectionResult",
]
