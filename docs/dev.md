# FSA Evaluation Function

Evaluation function for validating Finite State Automata (FSA) against language specifications.

## Overview

This evaluation function:
1. Validates FSA structure (states, transitions, initial/accept states)
2. Checks language correctness against answer specification
3. Provides detailed feedback with **UI element highlighting** for errors
4. Supports multiple answer formats (test cases, reference FSA, regex, grammar)

## Schemas

The evaluation function uses four main Pydantic schemas in `evaluation_function/schemas/`:

### 1. FSA Schema (`fsa.py`)

The student's FSA submission - represents a 5-tuple (Q, Σ, δ, q0, F):

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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `states` | `string[]` | Yes | Q: Set of state identifiers |
| `alphabet` | `string[]` | Yes | Σ: Input alphabet symbols |
| `transitions` | `Transition[]` | Yes | δ: Transition function |
| `initial_state` | `string` | Yes | q0: Starting state |
| `accept_states` | `string[]` | Yes | F: Accepting/final states |

### 2. Answer Schema (`answer.py`)

How the correct answer is specified. Supports four types:

#### Regex
```json
{
    "type": "regex",
    "value": "(a|b)*ab"
}
```

#### Test Cases
```json
{
    "type": "test_cases",
    "value": [
        {"input": "ab", "expected": true},
        {"input": "ba", "expected": false}
    ]
}
```

#### Reference FSA
```json
{
    "type": "reference_fsa",
    "value": { /* FSA object */ }
}
```

#### Grammar
```json
{
    "type": "grammar",
    "value": {
        "start": "S",
        "productions": {"S": ["aS", "bS", "ab"]}
    }
}
```

### 3. Params Schema (`params.py`)

Evaluation configuration:

```json
{
    "evaluation_mode": "lenient",
    "expected_type": "DFA",
    "feedback_verbosity": "standard",
    "highlight_errors": true,
    "show_counterexample": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `evaluation_mode` | `strict\|lenient\|partial` | `lenient` | Evaluation strictness |
| `expected_type` | `DFA\|NFA\|any` | `any` | Required automaton type |
| `feedback_verbosity` | `minimal\|standard\|detailed` | `standard` | Feedback detail level |
| `check_minimality` | `boolean` | `false` | Check if FSA is minimal |
| `check_completeness` | `boolean` | `false` | Check if DFA is complete |
| `highlight_errors` | `boolean` | `true` | Include element IDs for UI |
| `show_counterexample` | `boolean` | `true` | Show distinguishing string |
| `max_test_length` | `integer` | `10` | Max generated test length |

### 4. Result Schema (`result.py`)

Evaluation result with structured feedback:

```json
{
    "is_correct": false,
    "feedback": "Your FSA rejects 'ab' but it should accept.",
    "score": 0.8,
    "fsa_feedback": {
        "summary": "Language mismatch",
        "errors": [
            {
                "message": "Missing transition",
                "code": "MISSING_TRANSITION",
                "severity": "error",
                "element_type": "transition",
                "from_state": "q0",
                "symbol": "b",
                "suggestion": "Add transition from q0 on 'b'"
            }
        ],
        "language": {
            "are_equivalent": false,
            "counterexample": "ab",
            "counterexample_type": "should_accept"
        },
        "structural": {
            "is_deterministic": true,
            "num_states": 3,
            "unreachable_states": []
        }
    }
}
```

## UI Highlighting

Errors include a `highlight` field that tells the frontend exactly which FSA element to highlight:

### Example: Highlight Invalid Transition
```json
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
    "suggestion": "Change destination to an existing state or add state 'q5'"
}
```

**Frontend should:** Highlight the transition arrow from q0 to q5 on symbol 'a' in red.

### Example: Highlight Missing State
```json
{
    "message": "State 'q1' is unreachable from the initial state",
    "code": "UNREACHABLE_STATE",
    "severity": "warning",
    "highlight": {
        "type": "state",
        "state_id": "q1"
    },
    "suggestion": "Add a path from the initial state to 'q1' or remove this state"
}
```

**Frontend should:** Highlight state circle q1 in orange/warning color.

### Highlight Types

| Type | Fields | Use Case |
|------|--------|----------|
| `state` | `state_id` | Highlight a specific state |
| `transition` | `from_state`, `to_state`, `symbol` | Highlight a specific transition arrow |
| `initial_state` | `state_id` | Highlight the initial state marker |
| `accept_state` | `state_id` | Highlight the accept state indicator |
| `alphabet_symbol` | `symbol` | Highlight a symbol in the alphabet |

## Error Codes

| Code | Highlight Type | Description |
|------|----------------|-------------|
| `INVALID_STATE` | state | State ID not in states list |
| `INVALID_INITIAL` | initial_state | Initial state not in states list |
| `INVALID_ACCEPT` | accept_state | Accept state not in states list |
| `INVALID_SYMBOL` | alphabet_symbol | Symbol not in alphabet |
| `INVALID_TRANSITION_SOURCE` | transition | Source state doesn't exist |
| `INVALID_TRANSITION_DEST` | transition | Destination state doesn't exist |
| `INVALID_TRANSITION_SYMBOL` | transition | Symbol not in alphabet |
| `MISSING_TRANSITION` | state | DFA missing transition from this state |
| `DUPLICATE_TRANSITION` | transition | Non-deterministic transition |
| `UNREACHABLE_STATE` | state | State not reachable from initial |
| `DEAD_STATE` | state | State cannot reach accept state |

## Examples

### Simple Evaluation

**Input:**
```python
response = {
    "states": ["q0", "q1"],
    "alphabet": ["a"],
    "transitions": [{"from": "q0", "to": "q1", "symbol": "a"}],
    "initial_state": "q0",
    "accept_states": ["q1"]
}

answer = {
    "type": "test_cases",
    "value": [
        {"input": "a", "expected": True},
        {"input": "", "expected": False}
    ]
}

params = {"feedback_verbosity": "detailed"}
```

**Output:**
```python
{
    "is_correct": True,
    "feedback": "Correct! Your FSA accepts the expected language."
}
```
