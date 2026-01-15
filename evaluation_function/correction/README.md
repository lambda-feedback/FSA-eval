# FSA Correction Module

This module provides diagnostic information for comparing a student's FSA against an expected language, generating difference strings and identifying specific states/transitions causing errors.

## Overview

The correction module builds on top of the **validation** and **schemas** modules to create a comprehensive FSA evaluation pipeline that supports all schema types.

## Main Entry Point: `evaluate_fsa`

The `evaluate_fsa` function is the **recommended entry point** for full evaluation. It handles all Answer types and respects Params configuration.

```python
from evaluation_function.correction import evaluate_fsa
from evaluation_function.schemas import FSA, Params, TestCase
from evaluation_function.schemas.answer import TestCasesAnswer, ReferenceFSAAnswer

# Example with test cases
answer = TestCasesAnswer(
    type="test_cases",
    value=[
        TestCase(input="a", expected=True),
        TestCase(input="b", expected=False),
    ]
)
params = Params(expected_type="DFA", feedback_verbosity="detailed")
result = evaluate_fsa(student_fsa, answer, params)

# Result is a schemas.result.Result object
print(result.is_correct)       # bool
print(result.feedback)         # Human-readable message
print(result.score)            # Optional partial credit
print(result.fsa_feedback)     # FSAFeedback for UI
```

## Full Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              evaluate_fsa()                                  │
│                     (Answer + Params → Result)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  INPUT SCHEMAS:                                                              │
│  ├── FSA (student response)                                                 │
│  ├── Answer (test_cases | reference_fsa | regex | grammar)                  │
│  └── Params (evaluation_mode, expected_type, feedback_verbosity, etc.)      │
├─────────────────────────────────────────────────────────────────────────────┤
│  PIPELINE STEPS:                                                             │
│                                                                              │
│  1. Structural Validation                                                    │
│     └── is_valid_fsa() → List[ValidationError]                              │
│                                                                              │
│  2. Structural Analysis                                                      │
│     └── get_structured_info_of_fsa() → StructuralInfo                       │
│         ├── is_deterministic() → bool                                        │
│         ├── is_complete() → bool                                             │
│         ├── find_unreachable_states() → List[state_id]                      │
│         └── find_dead_states() → List[state_id]                             │
│                                                                              │
│  3. Type Constraint Check (from Params.expected_type)                        │
│     └── is_deterministic() if expected_type="DFA"                           │
│                                                                              │
│  4. Completeness Check (if Params.check_completeness)                        │
│     └── is_complete()                                                        │
│                                                                              │
│  5. Language Evaluation (based on Answer type):                              │
│     ├── TestCasesAnswer:                                                     │
│     │   └── accepts_string() for each test case                             │
│     ├── ReferenceFSAAnswer:                                                  │
│     │   └── analyze_fsa_correction() → full comparison                      │
│     │       ├── fsas_accept_same_language() (minimization + isomorphism)    │
│     │       ├── generate_difference_strings()                               │
│     │       ├── identify_state_errors()                                     │
│     │       └── identify_transition_errors()                                │
│     ├── RegexAnswer: (TODO)                                                  │
│     └── GrammarAnswer: (TODO)                                                │
│                                                                              │
│  6. Score Calculation (if Params.evaluation_mode="partial")                  │
│                                                                              │
│  7. Feedback Generation (based on Params.feedback_verbosity)                 │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  OUTPUT SCHEMA:                                                              │
│  └── Result                                                                  │
│      ├── is_correct: bool                                                    │
│      ├── feedback: str                                                       │
│      ├── score: Optional[float] (0.0-1.0)                                   │
│      └── fsa_feedback: FSAFeedback                                          │
│          ├── summary: str                                                    │
│          ├── errors: List[ValidationError]                                  │
│          ├── warnings: List[ValidationError]                                │
│          ├── structural: StructuralInfo                                     │
│          ├── language: LanguageComparison                                   │
│          ├── test_results: List[TestResult]                                 │
│          └── hints: List[str]                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Schema Integration

| Schema | Type | Purpose |
|--------|------|---------|
| **FSA** | Input | Student's finite state automaton |
| **Answer** | Input | Expected language (4 types) |
| **Params** | Input | Evaluation configuration |
| **Result** | Output | Complete evaluation result |
| **FSAFeedback** | Output | Detailed feedback for UI |
| **ValidationError** | Internal | Errors with ElementHighlight |
| **StructuralInfo** | Internal | FSA properties |
| **LanguageComparison** | Internal | Language equivalence result |
| **TestResult** | Internal | Individual test case results |

### Answer Types

| Type | Schema | Evaluation Method |
|------|--------|-------------------|
| `test_cases` | `TestCasesAnswer` | `accepts_string()` for each case |
| `reference_fsa` | `ReferenceFSAAnswer` | `fsas_accept_same_language()` |
| `regex` | `RegexAnswer` | TODO: regex_to_fsa conversion |
| `grammar` | `GrammarAnswer` | TODO: grammar_to_fsa conversion |

### Params Configuration

| Parameter | Effect |
|-----------|--------|
| `expected_type="DFA"` | Fails if FSA is non-deterministic |
| `check_completeness=True` | Checks all (state, symbol) have transitions |
| `evaluation_mode="partial"` | Returns `score` with partial credit |
| `feedback_verbosity` | Controls feedback detail level |
| `highlight_errors=False` | Removes ElementHighlight from errors |
| `show_counterexample=False` | Hides counterexample string |

## Functions 
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
