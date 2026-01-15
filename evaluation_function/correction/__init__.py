"""
FSA Correction Module

Provides diagnostic information for comparing student FSAs against expected languages:
- Generate strings that show differences between student FSA and expected language
- Identify specific states/transitions causing errors

Main Entry Point:
- evaluate_fsa: Full pipeline (Answer + Params -> Result)

Pipeline Functions:
- analyze_fsa_correction: FSA vs FSA comparison
- get_correction_feedback: Returns dict result
- get_fsa_feedback: Returns FSAFeedback schema (for UI)
- check_fsa_properties: Structural properties of single FSA
- quick_equivalence_check: Fast equivalence check

Supports All Answer Types:
- TestCasesAnswer: Test FSA on specific strings
- ReferenceFSAAnswer: Compare languages via minimization + isomorphism
- RegexAnswer: Convert regex to FSA (TODO)
- GrammarAnswer: Convert grammar to FSA (TODO)
"""

from .correction import (
    # Main evaluation pipeline (Answer + Params -> Result)
    evaluate_fsa,
    evaluate_against_test_cases,
    
    # FSA vs FSA comparison
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
    # Main pipeline (Answer + Params -> Result)
    "evaluate_fsa",
    "evaluate_against_test_cases",
    
    # FSA vs FSA comparison
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
