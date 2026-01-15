# FSA Correction Module

Compares student FSAs against expected FSAs, leveraging the validation module for detailed feedback.

## Architecture

The correction module is a thin wrapper around the validation module. All detailed "why" feedback comes from `are_isomorphic()` in `validation.py`.

## Pipeline (4 Steps)

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
│  └── fsas_accept_same_language()                                │
│      └── are_isomorphic() provides detailed feedback:            │
│          • State acceptance errors with ElementHighlight         │
│          • Transition errors with ElementHighlight               │
│          • Alphabet mismatches                                   │
│          • State count differences                               │
├─────────────────────────────────────────────────────────────────┤
│  OUTPUT: CorrectionResult                                        │
│  ├── is_equivalent: bool                                         │
│  ├── is_isomorphic: bool                                         │
│  ├── is_minimal: Optional[bool]                                  │
│  ├── validation_errors: List[ValidationError]                   │
│  ├── equivalence_errors: List[ValidationError] (from isomorphism)│
│  └── structural_info: StructuralInfo                            │
└─────────────────────────────────────────────────────────────────┘
```

## Why No Separate Feedback Functions?

The validation module's `are_isomorphic()` already provides detailed feedback:

| What `are_isomorphic()` returns | Example |
|--------------------------------|---------|
| **Alphabet mismatch** | "Your alphabet: {a}. Expected: {a, b}" |
| **State count mismatch** | "expected 3 states, but found 4" |
| **Wrong acceptance** | "State 'q1' should be accepting" with `ElementHighlight` |
| **Missing transition** | "Missing transition from 'q1' on 'a'" with `ElementHighlight` |
| **Wrong destination** | "Transition from 'q1' on 'a' leads to wrong state" with `ElementHighlight` |

Each error includes an `ElementHighlight` for UI rendering.

## Usage

```python
from evaluation_function.correction import analyze_fsa_correction, get_fsa_feedback

# Full analysis
result = analyze_fsa_correction(student_fsa, expected_fsa, check_minimality=True)
print(result.is_equivalent)
print(result.equivalence_errors)  # Detailed errors from are_isomorphic()

# For UI
feedback = get_fsa_feedback(student_fsa, expected_fsa)
print(feedback.summary)
print(feedback.errors)  # List[ValidationError] with ElementHighlight
```

## Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `analyze_fsa_correction` | `CorrectionResult` | Full comparison pipeline |
| `get_fsa_feedback` | `FSAFeedback` | Structured feedback for UI |
| `get_correction_feedback` | `dict` | Same as above, as dict |
| `check_fsa_properties` | `dict` | Properties of single FSA |
| `check_minimality` | `bool` | Is FSA minimal? |
| `quick_equivalence_check` | `tuple` | Fast equivalence check |
