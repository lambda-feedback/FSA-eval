# FSA Correction Module

Compares student FSAs against expected FSAs, returns `Result` with `FSAFeedback`.

## Exports

```python
from evaluation_function.correction import (
    analyze_fsa_correction,  # Main pipeline -> Result
    check_minimality,        # Check if FSA is minimal
)
```

## Pipeline

```
analyze_fsa_correction(student_fsa, expected_fsa, require_minimal=False) -> Result
├── 1. Validate student FSA (is_valid_fsa)
├── 2. Check minimality (if required)
├── 3. Structural analysis (get_structured_info_of_fsa)
└── 4. Language equivalence (fsas_accept_same_language -> are_isomorphic)
         └── All "why" feedback comes from here
```

## Result

```python
Result(
    is_correct: bool,         # True if FSAs accept same language
    feedback: str,            # Human-readable summary
    fsa_feedback: FSAFeedback # Structured feedback for UI
)
```

## Usage

```python
from evaluation_function.correction import analyze_fsa_correction

result = analyze_fsa_correction(student_fsa, expected_fsa)
result.is_correct           # bool
result.feedback             # "Correct!" or "Languages differ: ..."
result.fsa_feedback.errors  # List[ValidationError] with ElementHighlight
```
