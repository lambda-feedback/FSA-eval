# FSA Correction Module

This module provides diagnostic information for comparing a student's FSA against an expected language, generating difference strings and identifying specific states/transitions causing errors.

## Overview

The correction module builds on top of the **validation** and **schemas** modules to create a comprehensive FSA comparison pipeline.

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        analyze_fsa_correction()                          │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Structural Validation                                                │
│     └── is_valid_fsa() → List[ValidationError]                          │
│                                                                          │
│  2. Structural Analysis                                                  │
│     └── get_structured_info_of_fsa() → StructuralInfo                   │
│         ├── is_deterministic() → bool                                    │
│         ├── is_complete() → bool                                         │
│         ├── find_unreachable_states() → List[state_id]                  │
│         └── find_dead_states() → List[state_id]                         │
│                                                                          │
│  3. Language Equivalence Check                                           │
│     └── fsas_accept_same_language()                                      │
│         ├── hopcroft_minimization() → minimized FSA                      │
│         └── are_isomorphic() → List[ValidationError]                    │
│                                                                          │
│  4. Difference String Generation (if not equivalent)                     │
│     └── generate_difference_strings()                                    │
│         └── fsas_accept_same_string() for each test string              │
│             └── accepts_string() for each FSA                            │
│                                                                          │
│  5. Error Identification                                                 │
│     ├── identify_state_errors()                                          │
│     │   ├── Trace analysis for acceptance errors                        │
│     │   ├── find_unreachable_states()                                   │
│     │   └── find_dead_states()                                          │
│     └── identify_transition_errors()                                     │
│         └── Trace comparison between FSAs                                │
│                                                                          │
│  6. Result Construction                                                  │
│     └── CorrectionResult → FSAFeedback (for UI)                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Integration with Modules

| Module | Function | Purpose in Correction |
|--------|----------|----------------------|
| **validation** | `is_valid_fsa` | Validates FSA structure before comparison |
| **validation** | `is_deterministic` | Checks for NFA behavior |
| **validation** | `is_complete` | Checks DFA completeness |
| **validation** | `accepts_string` | Tests individual string acceptance |
| **validation** | `find_unreachable_states` | Identifies unreachable states |
| **validation** | `find_dead_states` | Identifies dead states |
| **validation** | `fsas_accept_same_string` | Compares FSAs on single string |
| **validation** | `fsas_accept_same_language` | Language equivalence (minimization + isomorphism) |
| **validation** | `get_structured_info_of_fsa` | Combined structural analysis |
| **schemas** | `FSA`, `Transition` | FSA data representation |
| **schemas** | `ValidationError`, `ErrorCode` | Error representation with UI highlighting |
| **schemas** | `ElementHighlight` | Specifies which element to highlight |
| **schemas** | `FSAFeedback`, `StructuralInfo` | Structured feedback output |
| **schemas** | `LanguageComparison`, `TestResult` | Language comparison results |

## Functions

### Main Pipeline Functions

#### `analyze_fsa_correction(student_fsa, expected_fsa, max_length=5, max_differences=10, check_isomorphism=True) -> CorrectionResult`

Main pipeline function that performs comprehensive FSA comparison.

**Pipeline Steps:**
1. Validate both FSAs using `is_valid_fsa`
2. Get structural info using `get_structured_info_of_fsa`
3. Check language equivalence using `fsas_accept_same_language`
4. Generate difference strings showing where languages differ
5. Identify state errors using `find_unreachable_states` and `find_dead_states`
6. Identify transition errors from trace analysis

**Parameters:**
- `student_fsa`: The student's FSA (FSA schema)
- `expected_fsa`: The expected/reference FSA (FSA schema)
- `max_length`: Maximum length of test strings (default: 5)
- `max_differences`: Maximum number of difference strings (default: 10)
- `check_isomorphism`: Whether to use minimization + isomorphism check (default: True)

**Returns:** `CorrectionResult` object with comprehensive analysis

#### `get_correction_feedback(student_fsa, expected_fsa, ...) -> dict`

Convenience wrapper that returns correction analysis as a dictionary.

```python
from evaluation_function.correction.correction import get_correction_feedback

feedback = get_correction_feedback(student_fsa, expected_fsa)
# Returns dict with: is_equivalent, summary, difference_strings, 
# transition_errors, state_errors, validation_errors, etc.
```

#### `get_fsa_feedback(student_fsa, expected_fsa, ...) -> FSAFeedback`

**Recommended entry point** - Returns structured feedback using the `FSAFeedback` schema from `schemas.result`. This is the best choice for UI integration.

```python
from evaluation_function.correction.correction import get_fsa_feedback

feedback = get_fsa_feedback(student_fsa, expected_fsa)
# Returns FSAFeedback with:
# - summary: str
# - errors: List[ValidationError] (severity="error")
# - warnings: List[ValidationError] (severity="warning"/"info")
# - structural: StructuralInfo
# - language: LanguageComparison
# - test_results: List[TestResult]
# - hints: List[str]

# Easy serialization
json_data = feedback.model_dump()
```

### Utility Functions

#### `generate_difference_strings(student_fsa, expected_fsa, max_length=5, max_differences=10) -> List[DifferenceString]`

Generates strings that demonstrate differences between two FSAs.

Internally uses `fsas_accept_same_string` from validation module to efficiently check if FSAs differ on each string.

#### `identify_state_errors(student_fsa, expected_fsa, difference_strings) -> List[StateError]`

Analyzes difference strings to identify state-level errors:
- States that should be accepting but aren't
- States that shouldn't be accepting but are
- Unreachable states (via `find_unreachable_states`)
- Dead states (via `find_dead_states`)

#### `identify_transition_errors(student_fsa, expected_fsa, difference_strings) -> List[TransitionError]`

Analyzes traces to identify transition-level errors:
- Wrong destination transitions
- Missing transitions
- Extra transitions

#### `check_fsa_properties(fsa) -> dict`

Gets detailed property analysis of a single FSA, leveraging:
- `is_valid_fsa`: structural validation
- `is_deterministic`: determinism check
- `is_complete`: completeness check
- `find_unreachable_states`: reachability analysis
- `find_dead_states`: dead state analysis
- `get_structured_info_of_fsa`: combined structural info

#### `quick_equivalence_check(student_fsa, expected_fsa) -> Tuple[bool, Optional[str], Optional[str]]`

Quick check if two FSAs accept the same language using `fsas_accept_same_language` from validation. Returns `(are_equivalent, counterexample, counterexample_type)`.

#### `trace_string(fsa, string) -> Tuple[bool, List[str]]`

Traces execution of a string through an FSA, returning `(accepted, state_trace)`.

#### `fsa_accepts(fsa, string) -> bool`

Checks if an FSA accepts a string. Leverages `accepts_string` from validation module.

## Data Classes

### `DifferenceString`

Represents a string demonstrating a difference between two FSAs.

```python
class DifferenceString:
    string: str                    # The test string
    student_accepts: bool          # Whether student FSA accepts
    expected_accepts: bool         # Whether expected FSA accepts
    student_trace: List[str]       # State trace in student FSA
    expected_trace: List[str]      # State trace in expected FSA
    
    @property
    def difference_type(self) -> str:  # "should_accept" or "should_reject"
```

### `TransitionError`

Represents an error in a specific transition.

```python
class TransitionError:
    from_state: str
    symbol: str
    actual_to_state: Optional[str]
    expected_to_state: Optional[str]
    error_type: str  # "wrong_destination", "missing", "extra"
    example_string: Optional[str]
    
    def to_validation_error(self) -> ValidationError
```

### `StateError`

Represents an error related to a specific state.

```python
class StateError:
    state_id: str
    error_type: str  # "should_be_accepting", "should_not_be_accepting", "unreachable", "dead"
    example_string: Optional[str]
    
    def to_validation_error(self) -> ValidationError
```

### `CorrectionResult`

Complete result of FSA correction analysis.

```python
class CorrectionResult:
    difference_strings: List[DifferenceString]
    transition_errors: List[TransitionError]
    state_errors: List[StateError]
    validation_errors: List[ValidationError]
    is_equivalent: bool
    summary: str
    structural_info: Optional[StructuralInfo]
    isomorphism_errors: List[ValidationError]
    
    def to_dict(self) -> dict
    def get_all_validation_errors(self) -> List[ValidationError]
    def get_language_comparison(self) -> LanguageComparison
    def get_test_results(self) -> List[TestResult]
```

## Leveraged Validation Functions

The correction module leverages these functions from `validation.validation`:

| Function | Purpose in Correction |
|----------|----------------------|
| `is_valid_fsa` | Validates FSA structure before comparison |
| `is_deterministic` | Checks determinism in property analysis |
| `is_complete` | Checks completeness in property analysis |
| `accepts_string` | Tests string acceptance |
| `find_unreachable_states` | Identifies unreachable states |
| `find_dead_states` | Identifies dead states |
| `fsas_accept_same_language` | Checks language equivalence via minimization |
| `are_isomorphic` | Used internally by `fsas_accept_same_language` |
| `get_structured_info_of_fsa` | Gets structural info for feedback |

## Example Usage

```python
from evaluation_function.schemas import FSA, Transition
from evaluation_function.correction.correction import (
    analyze_fsa_correction,
    get_correction_feedback,
    check_fsa_properties,
    quick_equivalence_check
)

# Define FSAs
student_fsa = FSA(
    states=["q0", "q1"],
    alphabet=["a", "b"],
    transitions=[
        Transition(from_state="q0", symbol="a", to_state="q1"),
        Transition(from_state="q1", symbol="b", to_state="q0"),
    ],
    initial_state="q0",
    accept_states=["q1"]
)

expected_fsa = FSA(
    states=["s0", "s1", "s2"],
    alphabet=["a", "b"],
    transitions=[
        Transition(from_state="s0", symbol="a", to_state="s1"),
        Transition(from_state="s1", symbol="b", to_state="s2"),
        Transition(from_state="s2", symbol="a", to_state="s1"),
    ],
    initial_state="s0",
    accept_states=["s1", "s2"]
)

# Full analysis
result = analyze_fsa_correction(student_fsa, expected_fsa)
print(f"Equivalent: {result.is_equivalent}")
print(f"Summary: {result.summary}")

for diff in result.difference_strings:
    print(f"String '{diff.string}': student={diff.student_accepts}, expected={diff.expected_accepts}")

# Get as dictionary
feedback = get_correction_feedback(student_fsa, expected_fsa)

# Check properties of single FSA
props = check_fsa_properties(student_fsa)
print(f"Deterministic: {props['is_deterministic']}")
print(f"Complete: {props['is_complete']}")

# Quick equivalence check
is_eq, counterexample, ce_type = quick_equivalence_check(student_fsa, expected_fsa)
if not is_eq and counterexample:
    print(f"Counterexample: '{counterexample}' ({ce_type})")
```

## Integration with Schemas

The correction module integrates with the result schemas:

```python
result = analyze_fsa_correction(student_fsa, expected_fsa)

# Get LanguageComparison for evaluation response
lang_comparison = result.get_language_comparison()

# Get TestResult list for detailed test feedback
test_results = result.get_test_results()

# Get all errors as ValidationError for UI highlighting
all_errors = result.get_all_validation_errors()
```
