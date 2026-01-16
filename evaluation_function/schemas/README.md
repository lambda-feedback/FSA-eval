# FSA Evaluation Schemas

This directory contains Pydantic schemas for the FSA evaluation microservice.

## Schema Files

| File | Purpose |
|------|---------|
| `fsa.py` | FSA representation (student response) |
| `answer.py` | Answer specification (expected language) |
| `params.py` | Evaluation parameters (configuration) |
| `result.py` | Evaluation result with UI highlighting |

## FSA Schema (`fsa.py`)

Represents a Finite State Automaton as a 5-tuple (Q, Σ, δ, q0, F).

```json
{
    "states": ["q0", "q1", "q2"],
    "alphabet": ["a", "b"],
    "transitions": [
        {"from_state": "q0", "to_state": "q1", "symbol": "a"},
        {"from_state": "q1", "to_state": "q2", "symbol": "b"}
    ],
    "initial_state": "q0",
    "accept_states": ["q2"]
}
```

## Params Schema (`params.py`)

Configuration for evaluation behavior:

```json
{
    "evaluation_mode": "lenient",
    "expected_type": "DFA",
    "feedback_verbosity": "standard",
    "check_minimality": false,
    "check_completeness": false,
    "highlight_errors": true,
    "show_counterexample": true,
    "max_test_length": 10
}
```

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `evaluation_mode` | `strict`, `lenient`, `partial` | `lenient` | Exact match vs language equivalence |
| `expected_type` | `DFA`, `NFA`, `any` | `any` | Required automaton type |
| `feedback_verbosity` | `minimal`, `standard`, `detailed` | `standard` | Feedback detail level |
| `highlight_errors` | `boolean` | `true` | Include element refs for UI |
| `show_counterexample` | `boolean` | `true` | Show distinguishing string |

## Result Schema (`result.py`)

Evaluation result with structured feedback for UI highlighting.

### Complete Example

```json
{
    "is_correct": false,
    "feedback": "Your FSA rejects 'ab' but it should accept it.",
    "score": 0.75,
    "fsa_feedback": {
        "summary": "Language mismatch - incorrect behavior on some inputs",
        "errors": [
            {
                "message": "Missing transition from state 'q1' on symbol 'b'",
                "code": "MISSING_TRANSITION",
                "severity": "error",
                "highlight": {
                    "type": "state",
                    "state_id": "q1"
                },
                "suggestion": "Add a transition from 'q1' on input 'b'"
            },
            {
                "message": "Transition points to non-existent state 'q5'",
                "code": "INVALID_TRANSITION_DEST",
                "severity": "error",
                "highlight": {
                    "type": "transition",
                    "from_state": "q0",
                    "to_state": "q5",
                    "symbol": "a"
                },
                "suggestion": "Change destination to an existing state"
            }
        ],
        "structural": {
            "is_deterministic": true,
            "is_complete": false,
            "num_states": 3,
            "num_transitions": 5,
            "unreachable_states": [],
            "dead_states": ["q2"]
        },
        "language": {
            "are_equivalent": false,
            "counterexample": "ab",
            "counterexample_type": "should_accept"
        },
        "test_results": [
            {
                "input": "ab",
                "expected": true,
                "actual": false,
                "passed": false,
                "trace": ["q0", "-(a)->q1", "-(b)->∅"]
            }
        ],
        "hints": [
            "State 'q2' cannot reach any accepting state",
            "Try tracing through your FSA with the string 'ab'"
        ]
    }
}
```

## UI Highlighting Guide

The `highlight` field in `ValidationError` tells the frontend which FSA element has an error.

### Highlighting States

```json
{
    "highlight": {
        "type": "state",
        "state_id": "q1"
    }
}
```
**Frontend action:** Highlight state circle with id "q1" in red/error color.

### Highlighting Transitions

```json
{
    "highlight": {
        "type": "transition",
        "from_state": "q0",
        "to_state": "q1",
        "symbol": "a"
    }
}
```
**Frontend action:** Highlight the specific transition arrow from q0 to q1 labeled "a".

### Highlighting Initial State

```json
{
    "highlight": {
        "type": "initial_state",
        "state_id": "q0"
    }
}
```
**Frontend action:** Highlight the initial state marker/arrow for q0.

### Highlighting Accept State

```json
{
    "highlight": {
        "type": "accept_state",
        "state_id": "q2"
    }
}
```
**Frontend action:** Highlight the double-circle or accept indicator for q2.

### Highlighting Alphabet Symbol

```json
{
    "highlight": {
        "type": "alphabet_symbol",
        "symbol": "a"
    }
}
```
**Frontend action:** Highlight alphabet symbol "a" in the alphabet list/panel.

## Error Codes (`ErrorCode` Enum)

Error codes are defined as a **type-safe enum** in `result.py`:

```python
from evaluation_function.schemas import ErrorCode

# Use enum values for type safety
error_code = ErrorCode.INVALID_STATE  # ✅ Type-safe
error_code = "INVALID_STATE"          # ❌ No type checking
```

### Available Error Codes

| Code | Element Type | Description |
|------|--------------|-------------|
| `INVALID_STATE` | state | State ID not in states list |
| `INVALID_INITIAL` | initial_state | Initial state not in states list |
| `INVALID_ACCEPT` | accept_state | Accept state not in states list |
| `INVALID_SYMBOL` | alphabet_symbol | Symbol not in alphabet |
| `INVALID_TRANSITION_SOURCE` | transition | Transition source state invalid |
| `INVALID_TRANSITION_DEST` | transition | Transition destination state invalid |
| `INVALID_TRANSITION_SYMBOL` | transition | Transition symbol not in alphabet |
| `MISSING_TRANSITION` | state | DFA missing required transition |
| `DUPLICATE_TRANSITION` | transition | Multiple transitions for (state, symbol) |
| `UNREACHABLE_STATE` | state | State not reachable from initial |
| `DEAD_STATE` | state | State cannot reach accept state |
| `WRONG_AUTOMATON_TYPE` | general | Wrong automaton type (e.g., NFA when DFA expected) |
| `NOT_DETERMINISTIC` | general | FSA has non-deterministic transitions |
| `NOT_COMPLETE` | general | DFA missing some transitions |
| `LANGUAGE_MISMATCH` | general | FSA accepts wrong language |
| `TEST_CASE_FAILED` | general | Failed specific test case |
| `EMPTY_STATES` | general | No states defined |
| `EMPTY_ALPHABET` | general | No alphabet symbols defined |
| `EVALUATION_ERROR` | general | Internal evaluation error |

## Usage in Evaluation Function

```python
from evaluation_function.schemas import (
    FSA, 
    Answer, 
    Params, 
    Result, 
    ElementHighlight, 
    ValidationError,
    ErrorCode  # Import the enum
)

# Parse student response
fsa = FSA(**response_data)

# Validate and create error with highlighting
if invalid_state:
    error = ValidationError(
        message=f"State '{state}' does not exist",
        code=ErrorCode.INVALID_STATE,  # Use enum value
        severity="error",
        highlight=ElementHighlight(
            type="state",
            state_id=state
        ),
        suggestion=f"Add '{state}' to the states list"
    )

# Return result
result = Result(
    is_correct=False,
    feedback="Your FSA has structural errors",
    fsa_feedback=FSAFeedback(
        errors=[error],
        ...
    )
)
```
