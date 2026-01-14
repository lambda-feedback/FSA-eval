"""
Comprehensive tests for epsilon closure computation.

Tests the ε-closure algorithms used in ε-NFA processing.
"""

import pytest
from evaluation_function.algorithms.epsilon_closure import (
    epsilon_closure,
    epsilon_closure_set,
    build_epsilon_transition_map,
    compute_all_epsilon_closures
)
from evaluation_function.schemas import FSA, Transition


class TestEpsilonClosure:
    """Test epsilon_closure function."""
    
    def test_single_state_no_epsilon_transitions(self):
        """Test ε-closure of a state with no epsilon transitions."""
        epsilon_trans = {}
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0"}
    
    def test_single_epsilon_transition(self):
        """Test ε-closure with one epsilon transition."""
        epsilon_trans = {"q0": {"q1"}}
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0", "q1"}
    
    def test_chain_of_epsilon_transitions(self):
        """Test ε-closure with chained epsilon transitions."""
        epsilon_trans = {
            "q0": {"q1"},
            "q1": {"q2"},
            "q2": {"q3"}
        }
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0", "q1", "q2", "q3"}
    
    def test_multiple_epsilon_transitions_from_state(self):
        """Test ε-closure with multiple epsilon transitions from one state."""
        epsilon_trans = {
            "q0": {"q1", "q2"},
            "q1": {"q3"}
        }
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0", "q1", "q2", "q3"}
    
    def test_epsilon_cycle(self):
        """Test ε-closure with cyclic epsilon transitions."""
        epsilon_trans = {
            "q0": {"q1"},
            "q1": {"q2"},
            "q2": {"q0"}  # Cycle back
        }
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0", "q1", "q2"}
    
    def test_complex_epsilon_graph(self):
        """Test ε-closure with complex epsilon transition graph."""
        epsilon_trans = {
            "q0": {"q1", "q2"},
            "q1": {"q3", "q4"},
            "q2": {"q5"},
            "q4": {"q6"}
        }
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0", "q1", "q2", "q3", "q4", "q5", "q6"}
    
    def test_state_with_no_outgoing_epsilon(self):
        """Test ε-closure of state with no outgoing epsilon transitions."""
        epsilon_trans = {"q0": {"q1"}}
        result = epsilon_closure("q1", epsilon_trans)
        assert result == {"q1"}


class TestEpsilonClosureSet:
    """Test epsilon_closure_set function."""
    
    def test_empty_set(self):
        """Test ε-closure of empty state set."""
        epsilon_trans = {}
        result = epsilon_closure_set(set(), epsilon_trans)
        assert result == set()
    
    def test_single_state(self):
        """Test ε-closure of single state set."""
        epsilon_trans = {"q0": {"q1"}}
        result = epsilon_closure_set({"q0"}, epsilon_trans)
        assert result == {"q0", "q1"}
    
    def test_multiple_states(self):
        """Test ε-closure of multiple states."""
        epsilon_trans = {
            "q0": {"q1"},
            "q2": {"q3"}
        }
        result = epsilon_closure_set({"q0", "q2"}, epsilon_trans)
        assert result == {"q0", "q1", "q2", "q3"}
    
    def test_overlapping_closures(self):
        """Test ε-closure where closures overlap."""
        epsilon_trans = {
            "q0": {"q1", "q2"},
            "q3": {"q2"}
        }
        result = epsilon_closure_set({"q0", "q3"}, epsilon_trans)
        assert result == {"q0", "q1", "q2", "q3"}
    
    def test_set_with_no_epsilon_transitions(self):
        """Test ε-closure of states with no epsilon transitions."""
        epsilon_trans = {}
        result = epsilon_closure_set({"q0", "q1", "q2"}, epsilon_trans)
        assert result == {"q0", "q1", "q2"}


class TestBuildEpsilonTransitionMap:
    """Test build_epsilon_transition_map function."""
    
    def test_no_transitions(self):
        """Test with no transitions."""
        transitions = []
        result = build_epsilon_transition_map(transitions)
        assert result == {}
    
    def test_no_epsilon_transitions(self):
        """Test with only regular transitions."""
        transitions = [
            Transition(from_state="q0", to_state="q1", symbol="a"),
            Transition(from_state="q1", to_state="q2", symbol="b")
        ]
        result = build_epsilon_transition_map(transitions)
        assert result == {}
    
    def test_epsilon_symbol_variants(self):
        """Test different epsilon symbol representations."""
        transitions = [
            Transition(from_state="q0", to_state="q1", symbol="ε"),
            Transition(from_state="q1", to_state="q2", symbol="epsilon"),
            Transition(from_state="q2", to_state="q3", symbol="")
        ]
        result = build_epsilon_transition_map(transitions)
        assert result == {
            "q0": {"q1"},
            "q1": {"q2"},
            "q2": {"q3"}
        }
    
    def test_multiple_epsilon_from_same_state(self):
        """Test multiple epsilon transitions from same state."""
        transitions = [
            Transition(from_state="q0", to_state="q1", symbol="ε"),
            Transition(from_state="q0", to_state="q2", symbol="ε"),
            Transition(from_state="q0", to_state="q3", symbol="ε")
        ]
        result = build_epsilon_transition_map(transitions)
        assert result == {"q0": {"q1", "q2", "q3"}}
    
    def test_mixed_transitions(self):
        """Test mix of epsilon and regular transitions."""
        transitions = [
            Transition(from_state="q0", to_state="q1", symbol="a"),
            Transition(from_state="q0", to_state="q2", symbol="ε"),
            Transition(from_state="q2", to_state="q3", symbol="b"),
            Transition(from_state="q2", to_state="q4", symbol="ε")
        ]
        result = build_epsilon_transition_map(transitions)
        assert result == {
            "q0": {"q2"},
            "q2": {"q4"}
        }


class TestComputeAllEpsilonClosures:
    """Test compute_all_epsilon_closures function."""
    
    def test_simple_fsa_no_epsilon(self):
        """Test FSA with no epsilon transitions."""
        fsa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q2", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        result = compute_all_epsilon_closures(fsa)
        assert result == {
            "q0": {"q0"},
            "q1": {"q1"},
            "q2": {"q2"}
        }
    
    def test_fsa_with_epsilon_transitions(self):
        """Test FSA with epsilon transitions."""
        fsa = FSA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q1", to_state="q2", symbol="a"),
                Transition(from_state="q2", to_state="q3", symbol="ε")
            ],
            initial_state="q0",
            accept_states=["q3"]
        )
        result = compute_all_epsilon_closures(fsa)
        assert result == {
            "q0": {"q0", "q1"},
            "q1": {"q1"},
            "q2": {"q2", "q3"},
            "q3": {"q3"}
        }
    
    def test_fsa_with_epsilon_cycle(self):
        """Test FSA with epsilon cycle."""
        fsa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q1", to_state="q2", symbol="ε"),
                Transition(from_state="q2", to_state="q0", symbol="ε")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        result = compute_all_epsilon_closures(fsa)
        # All states can reach each other via epsilon
        expected_closure = {"q0", "q1", "q2"}
        assert result == {
            "q0": expected_closure,
            "q1": expected_closure,
            "q2": expected_closure
        }
    
    def test_disconnected_epsilon_components(self):
        """Test FSA with disconnected epsilon components."""
        fsa = FSA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q2", to_state="q3", symbol="ε")
            ],
            initial_state="q0",
            accept_states=["q1", "q3"]
        )
        result = compute_all_epsilon_closures(fsa)
        assert result == {
            "q0": {"q0", "q1"},
            "q1": {"q1"},
            "q2": {"q2", "q3"},
            "q3": {"q3"}
        }


class TestEpsilonClosureEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_self_loop_epsilon(self):
        """Test epsilon self-loop."""
        epsilon_trans = {"q0": {"q0"}}
        result = epsilon_closure("q0", epsilon_trans)
        assert result == {"q0"}
    
    def test_large_epsilon_graph(self):
        """Test with larger epsilon transition graph."""
        # Create a graph with 10 states, each connecting to next
        epsilon_trans = {f"q{i}": {f"q{i+1}"} for i in range(9)}
        result = epsilon_closure("q0", epsilon_trans)
        expected = {f"q{i}" for i in range(10)}
        assert result == expected
    
    def test_star_shaped_epsilon_graph(self):
        """Test star-shaped epsilon transition graph."""
        epsilon_trans = {
            "q0": {f"q{i}" for i in range(1, 6)}
        }
        result = epsilon_closure("q0", epsilon_trans)
        expected = {f"q{i}" for i in range(6)}
        assert result == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
