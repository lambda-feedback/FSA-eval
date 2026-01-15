# FSA Algorithm Tests

Comprehensive pytest test suite for the FSA evaluation algorithms.

## Test Structure

```
test/
├── __init__.py                    # Test package init
├── conftest.py                    # Shared fixtures and configuration
├── test_epsilon_closure.py        # ε-closure computation tests
├── test_nfa_to_dfa.py             # NFA→DFA conversion tests
├── test_minimization.py           # DFA minimization tests
└── test_validation.py             # validation tests
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run specific test file

```bash
pytest evaluation_function/test/test_epsilon_closure.py
pytest evaluation_function/test/test_nfa_to_dfa.py
pytest evaluation_function/test/test_minimization.py
pytest evaluation_function/test/test_validation.py
```

### Run specific test class or function

```bash
# Run specific class
pytest evaluation_function/test/test_epsilon_closure.py::TestEpsilonClosure

# Run specific test
pytest evaluation_function/test/test_epsilon_closure.py::TestEpsilonClosure::test_single_epsilon_transition
```

### Run with coverage

```bash
pytest --cov=evaluation_function/algorithms --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run with verbose output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Run and show print statements

```bash
pytest -s
```

### Run specific markers

```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

## Test Categories

### Epsilon Closure Tests (`test_epsilon_closure.py`)

- **TestEpsilonClosure**: Single state ε-closure
  - No epsilon transitions
  - Single/chain epsilon transitions
  - Multiple branches
  - Cycles
  - Complex graphs

- **TestEpsilonClosureSet**: Multiple state ε-closure
  - Empty sets
  - Single/multiple states
  - Overlapping closures

- **TestBuildEpsilonTransitionMap**: Epsilon map construction
  - Different epsilon representations (ε, epsilon, "")
  - Mixed transitions

- **TestComputeAllEpsilonClosures**: Bulk ε-closure computation
  - Simple/complex FSAs
  - Epsilon cycles
  - Disconnected components

### NFA to DFA Tests (`test_nfa_to_dfa.py`)

- **TestIsDeterministic**: Determinism checking
  - Simple DFAs
  - NFAs with epsilon/non-determinism
  - Complete DFAs

- **TestSubsetConstruction**: NFA→DFA conversion
  - Simple NFAs
  - ε-NFAs
  - Complex patterns (strings ending in 'ab')
  - Epsilon cycles

- **TestSubsetConstructionProperties**: Invariant properties
  - Language preservation
  - Alphabet preservation
  - State reachability

- **TestSubsetConstructionEdgeCases**: Edge cases
  - DFA input
  - Single state
  - No accepting states
  - Complex ε-NFAs

### Minimization Tests (`test_minimization.py`)

- **TestRemoveUnreachableStates**: Unreachable state removal
  - All reachable
  - Single/multiple unreachable
  - Unreachable accept states

- **TestHopcroftMinimization**: Hopcroft's algorithm
  - Already minimal DFAs
  - Minimizable DFAs
  - Complete DFAs
  - With unreachable states

- **TestMinimizationProperties**: Invariant properties
  - Determinism preservation
  - Alphabet preservation
  - Idempotence
  - No unreachable states in result

- **TestMinimizationEdgeCases**: Edge cases
  - Empty accept states
  - All states accepting

## Fixtures

Defined in `conftest.py`:

- `simple_dfa`: DFA accepting strings with at least one 'a'
- `simple_nfa`: Simple NFA with non-determinism
- `epsilon_nfa`: ε-NFA with epsilon transitions
- `minimizable_dfa`: DFA with equivalent states
- `strings_ending_ab_nfa`: NFA for strings ending in 'ab'

### Using fixtures

```python
def test_my_function(simple_dfa):
    result = my_function(simple_dfa)
    assert result is not None
```

## Test Coverage Goals

Target: **> 90% coverage** for all algorithm modules

Current modules:
- `epsilon_closure.py`: ε-closure algorithms
- `nfa_to_dfa.py`: Subset construction
- `minimization.py`: Hopcroft's minimization

## Writing New Tests

### Test naming convention

```python
class TestFunctionName:
    def test_normal_case(self):
        """Test normal behavior."""
        pass
    
    def test_edge_case(self):
        """Test edge case."""
        pass
    
    def test_error_case(self):
        """Test error handling."""
        pass
```

### Example test structure

```python
def test_epsilon_closure_example():
    # Arrange
    epsilon_trans = {"q0": {"q1"}}
    
    # Act
    result = epsilon_closure("q0", epsilon_trans)
    
    # Assert
    assert result == {"q0", "q1"}
```

## Continuous Integration

Tests run automatically on:
- Every push
- Every pull request
- Before deployment

## Troubleshooting

### Import errors

Make sure you're in the project root:
```bash
cd FSA-eval
pytest
```

### Module not found

Install in development mode:
```bash
pip install -e .
# or
poetry install
```

### Slow tests

Skip slow tests during development:
```bash
pytest -m "not slow"
```

## Resources

- [Pytest documentation](https://docs.pytest.org/)
- [Pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest markers](https://docs.pytest.org/en/stable/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)
