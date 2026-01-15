"""
FSA Correction Module

Provides diagnostic information for comparing student FSAs against expected languages:
- Generate strings that show differences between student FSA and expected language
- Identify specific states/transitions causing errors

Main Functions:
- analyze_fsa_correction: Full pipeline for FSA comparison and error identification
- get_correction_feedback: Convenience function returning dict results
- get_fsa_feedback: Returns FSAFeedback schema (recommended for UI integration)
- check_fsa_properties: Get structural properties of a single FSA
- quick_equivalence_check: Fast check if two FSAs are equivalent
"""

from .correction import (
    # Main pipeline functions
    analyze_fsa_correction,
    get_correction_feedback,
    get_fsa_feedback,
    check_fsa_properties,
    quick_equivalence_check,
    
    # Helper functions
    trace_string,
    fsa_accepts,
    generate_difference_strings,
    identify_state_errors,
    identify_transition_errors,
    
    # Result classes
    CorrectionResult,
    DifferenceString,
    TransitionError,
    StateError,
)

__all__ = [
    # Main pipeline
    "analyze_fsa_correction",
    "get_correction_feedback",
    "get_fsa_feedback",
    "check_fsa_properties",
    "quick_equivalence_check",
    
    # Helpers
    "trace_string",
    "fsa_accepts",
    "generate_difference_strings",
    "identify_state_errors",
    "identify_transition_errors",
    
    # Classes
    "CorrectionResult",
    "DifferenceString",
    "TransitionError",
    "StateError",
]
