# FSA Correction Module

Compares student FSAs against expected FSAs, leveraging the validation module for detailed feedback.

## Exports

```python
from evaluation_function.correction import (
    analyze_fsa_correction,  # Main pipeline
    check_minimality,        # Check if FSA is minimal
    CorrectionResult,        # Result model
)
```

## Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   analyze_fsa_correction()                       │
│                 (student_fsa, expected_fsa)                      │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Structural Validation                                   │
│  └── is_valid_fsa() → List[ValidationError]                     │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Minimality Check (optional)                             │
│  └── check_minimality() → bool                                   │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: Structural Analysis                                     │
│  └── get_structured_info_of_fsa() → StructuralInfo              │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Language Equivalence                                    │
│  └── fsas_accept_same_language() → are_isomorphic()             │
│      Provides detailed feedback with ElementHighlight            │
├─────────────────────────────────────────────────────────────────┤
│  OUTPUT: CorrectionResult                                        │
│  ├── is_equivalent: bool                                         │
│  ├── is_isomorphic: bool                                         │
│  ├── is_minimal: Optional[bool]                                  │
│  ├── validation_errors: List[ValidationError]                   │
│  ├── equivalence_errors: List[ValidationError]                  │
│  └── structural_info: StructuralInfo                            │
│                                                                  │
│  Methods:                                                        │
│  ├── .model_dump() → dict                                       │
│  ├── .to_fsa_feedback() → FSAFeedback                           │
│  └── .get_language_comparison() → LanguageComparison            │
└─────────────────────────────────────────────────────────────────┘
```

## Usage

```python
from evaluation_function.correction import analyze_fsa_correction, check_minimality

# Compare two FSAs
result = analyze_fsa_correction(student_fsa, expected_fsa, check_minimality=True)

# Check result
result.is_equivalent      # bool
result.equivalence_errors # List[ValidationError] with ElementHighlight

# For UI
result.to_fsa_feedback()  # FSAFeedback schema

# As dict
result.model_dump()       # dict

# Check minimality only
check_minimality(fsa)     # bool
```
