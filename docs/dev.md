# FSA Evaluation Function

Evaluation function for validating Finite State Automata (FSA) against language specifications.

## Schemas

The evaluation function uses four main schemas defined in `evaluation_function/schemas/`:

### 1. FSA Schema (`fsa.py`)

The student response - an FSA representation:

```json
{
    "states": ["q0", "q1", "q2"],
    "alphabet": ["a", "b"],
    "transitions": [
        {"from": "q0", "to": "q1", "symbol": "a"},
        {"from": "q1", "to": "q2", "symbol": "b"}
    ],
    "initial_state": "q0",
    "accept_states": ["q2"],
    "positions": {
        "q0": {"x": 100, "y": 200}
    }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `states` | `string[]` | Yes | List of state identifiers |
| `alphabet` | `string[]` | Yes | Input alphabet symbols |
| `transitions` | `Transition[]` | Yes | List of transitions |
| `initial_state` | `string` | Yes | Starting state |
| `accept_states` | `string[]` | Yes | Accepting/final states |
| `positions` | `object` | No | State positions for UI |

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

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_STATE` | State not in states list |
| `INVALID_SYMBOL` | Symbol not in alphabet |
| `MISSING_INITIAL` | No initial state defined |
| `INVALID_INITIAL` | Initial state not in states |
| `INVALID_ACCEPT` | Accept state not in states |
| `MISSING_TRANSITION` | DFA missing required transition |
| `DUPLICATE_TRANSITION` | DFA has non-deterministic transition |
| `UNREACHABLE_STATE` | State cannot be reached from initial |
| `DEAD_STATE` | State cannot reach any accept state |

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
