"""
Pytest configuration and shared fixtures for FSA algorithm tests.
"""

import pytest
from evaluation_function.schemas import FSA, Transition


@pytest.fixture
def simple_dfa():
    """Simple DFA accepting strings with at least one 'a'."""
    return FSA(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", to_state="q1", symbol="a"),
            Transition(from_state="q0", to_state="q0", symbol="b"),
            Transition(from_state="q1", to_state="q1", symbol="a"),
            Transition(from_state="q1", to_state="q1", symbol="b")
        ],
        initial_state="q0",
        accept_states=["q1"]
    )


@pytest.fixture
def simple_nfa():
    """Simple NFA with non-determinism."""
    return FSA(
        states=["q0", "q1"],
        alphabet=["a"],
        transitions=[
            Transition(from_state="q0", to_state="q0", symbol="a"),
            Transition(from_state="q0", to_state="q1", symbol="a")
        ],
        initial_state="q0",
        accept_states=["q1"]
    )


@pytest.fixture
def epsilon_nfa():
    """ε-NFA with epsilon transitions."""
    return FSA(
        states=["q0", "q1", "q2"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", to_state="q1", symbol="ε"),
            Transition(from_state="q1", to_state="q2", symbol="a"),
            Transition(from_state="q2", to_state="q2", symbol="b")
        ],
        initial_state="q0",
        accept_states=["q2"]
    )


@pytest.fixture
def minimizable_dfa():
    """DFA with equivalent states that can be minimized."""
    return FSA(
        states=["q0", "q1", "q2", "q3"],
        alphabet=["a"],
        transitions=[
            Transition(from_state="q0", to_state="q1", symbol="a"),
            Transition(from_state="q1", to_state="q2", symbol="a"),
            Transition(from_state="q2", to_state="q3", symbol="a"),
            Transition(from_state="q3", to_state="q3", symbol="a")
        ],
        initial_state="q0",
        accept_states=["q3"]
    )


@pytest.fixture
def strings_ending_ab_nfa():
    """NFA accepting strings ending in 'ab'."""
    return FSA(
        states=["q0", "q1", "q2"],
        alphabet=["a", "b"],
        transitions=[
            Transition(from_state="q0", to_state="q0", symbol="a"),
            Transition(from_state="q0", to_state="q0", symbol="b"),
            Transition(from_state="q0", to_state="q1", symbol="a"),
            Transition(from_state="q1", to_state="q2", symbol="b")
        ],
        initial_state="q0",
        accept_states=["q2"]
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
