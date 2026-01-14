# FSA Validator & Analyzer

A Python-based utility module for the structural validation, property analysis, and string simulation of **Finite State Automata (FSA)**. This module is designed to work with Pydantic-based FSA schemas to ensure mathematical correctness and provide detailed feedback on structural flaws.

## 🚀 Key Features

* **Structural Validation**: Verifies that initial states, accept states, and transitions reference defined states and alphabet symbols.
* **Property Analysis**:
* **Determinism**: Checks for multiple transitions from the same state on the same symbol.
* **Completeness**: Ensures every state has a transition for every symbol in the alphabet.


* **State Reachability**:
* **Unreachable States**: Identifies states that cannot be reached from the initial state using BFS.
* **Dead States**: Identifies states from which an accepting state can never be reached.


* **String Simulation**: Simulates the FSA (NFA or DFA) on a given input string to determine acceptance.
* **Language Equivalence**: Approximates whether two FSAs are equivalent by testing all possible strings up to a specified maximum length.

---

## 🛠 Function Reference

### 1. Validation & Properties

| Function | Description |
| --- | --- |
| `is_valid_fsa(fsa)` | Returns a list of structural errors (missing states, invalid symbols). |
| `is_deterministic(fsa)` | Validates if the FSA behaves as a DFA. |
| `is_complete(fsa)` | Validates if the transition function is total (requires a DFA). |

### 2. Graph Analysis

| Function | Description |
| --- | --- |
| `find_unreachable_states(fsa)` | Finds states inaccessible from the start. |
| `find_dead_states(fsa)` | Finds states that are "trapped" and cannot reach an accept state. |

### 3. Language & Testing

| Function | Description |
| --- | --- |
| `accepts_string(fsa, string)` | Tests if the FSA accepts a specific string. Supports non-determinism. |
| `fsas_accept_same_language(fsa1, fsa2)` | Compares two FSAs for equivalence up to a specific string length. |

### 4. Isomorphism
| Function | Description |
| --- | --- |
| `are_isomorphism(fsa1, fsa2)`| Check if two FSA are isomorphic |

---

## 📋 Data Structure Support

The module expects an `FSA` object (typically a Pydantic model) with the following attributes:

* `states`: `List[str]`
* `alphabet`: `List[str]`
* `initial_state`: `str`
* `accept_states`: `List[str]`
* `transitions`: `List[Transition]` (where transitions have `from_state`, `to_state`, and `symbol`)

---

## 💡 Usage Example

```python
from your_module import is_valid_fsa, find_dead_states

# Example: Checking for dead states
errors = find_dead_states(my_fsa)

for error in errors:
    print(f"Error Code: {error.code}")
    print(f"Message: {error.message}")
    print(f"Suggestion: {error.suggestion}")

```

## ⚠️ Error Handling

All functions return a `List[ValidationError]`. An empty list `[]` indicates that the check passed successfully. Each `ValidationError` object contains:

* `message`: Human-readable explanation.
* `code`: A unique `ErrorCode` for programmatic handling.
* `severity`: "error" or "warning".
* `highlight`: Metadata identifying the specific state or transition causing the issue.