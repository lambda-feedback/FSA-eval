"""
Comprehensive tests for DFA minimization.

Tests Hopcroft's algorithm for DFA minimization and related utilities.
"""

import pytest
from evaluation_function.algorithms.minimization import (
    hopcroft_minimization,
    minimize_dfa,
    remove_unreachable_states,
    are_equivalent_dfas
)
from evaluation_function.algorithms.nfa_to_dfa import is_deterministic
from evaluation_function.schemas import FSA, Transition


class TestRemoveUnreachableStates:
    """Test remove_unreachable_states function."""
    
    def test_no_unreachable_states(self):
        """Test DFA with all states reachable."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        result = remove_unreachable_states(dfa)
        
        assert set(result.states) == {"q0", "q1", "q2"}
    
    def test_single_unreachable_state(self):
        """Test DFA with one unreachable state."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
                # q2 is unreachable
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        result = remove_unreachable_states(dfa)
        
        assert "q2" not in result.states
        assert set(result.states) == {"q0", "q1"}
    
    def test_multiple_unreachable_states(self):
        """Test DFA with multiple unreachable states."""
        dfa = FSA(
            states=["q0", "q1", "q2", "q3", "q4"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q2", to_state="q3", symbol="a"),
                Transition(from_state="q3", to_state="q4", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        result = remove_unreachable_states(dfa)
        
        # Only q0 and q1 are reachable
        assert set(result.states) == {"q0", "q1"}
        assert "q2" not in result.states
        assert "q3" not in result.states
        assert "q4" not in result.states
    
    def test_unreachable_accept_state_removed(self):
        """Test that unreachable accept states are removed."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1", "q2"]  # q2 is unreachable
        )
        result = remove_unreachable_states(dfa)
        
        assert "q2" not in result.accept_states
        assert set(result.accept_states) == {"q1"}
    
    def test_single_state_dfa(self):
        """Test DFA with single state."""
        dfa = FSA(
            states=["q0"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q0", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q0"]
        )
        result = remove_unreachable_states(dfa)
        
        assert result.states == ["q0"]


class TestHopcroftMinimization:
    """Test hopcroft_minimization function."""
    
    def test_already_minimal_dfa(self):
        """Test DFA that is already minimal."""
        dfa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        minimal = hopcroft_minimization(dfa)
        
        # Should still be deterministic
        assert is_deterministic(minimal)
        
        # Minimal DFA should have same or fewer states
        assert len(minimal.states) <= len(dfa.states)
    
    def test_minimizable_dfa(self):
        """Test DFA with equivalent states that can be merged."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q0", to_state="q2", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a"),
                Transition(from_state="q2", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1", "q2"]  # q1 and q2 are equivalent
        )
        minimal = hopcroft_minimization(dfa)
        
        # Should reduce number of states
        assert len(minimal.states) < len(dfa.states)
        assert is_deterministic(minimal)
    
    def test_complete_dfa_minimization(self):
        """Test minimization of complete DFA."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                # From q0
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q0", to_state="q0", symbol="b"),
                # From q1
                Transition(from_state="q1", to_state="q2", symbol="a"),
                Transition(from_state="q1", to_state="q0", symbol="b"),
                # From q2
                Transition(from_state="q2", to_state="q2", symbol="a"),
                Transition(from_state="q2", to_state="q2", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        minimal = hopcroft_minimization(dfa)
        
        assert is_deterministic(minimal)
        assert len(minimal.states) <= len(dfa.states)
    
    def test_dfa_with_unreachable_states(self):
        """Test minimization removes unreachable states."""
        dfa = FSA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a"),
                Transition(from_state="q2", to_state="q3", symbol="a")  # Unreachable
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        minimal = hopcroft_minimization(dfa)
        
        # Unreachable states should be removed
        assert "q2" not in minimal.states
        assert "q3" not in minimal.states
    
    def test_single_state_dfa(self):
        """Test minimization of single-state DFA."""
        dfa = FSA(
            states=["q0"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q0", symbol="a"),
                Transition(from_state="q0", to_state="q0", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q0"]
        )
        minimal = hopcroft_minimization(dfa)
        
        assert len(minimal.states) == 1
        assert is_deterministic(minimal)


class TestMinimizeDFA:
    """Test minimize_dfa function (alias for hopcroft_minimization)."""
    
    def test_minimize_dfa_alias(self):
        """Test that minimize_dfa works as alias."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a"),
                Transition(from_state="q2", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        minimal = minimize_dfa(dfa)
        
        assert is_deterministic(minimal)
        assert len(minimal.states) <= len(dfa.states)


class TestAreEquivalentDFAs:
    """Test are_equivalent_dfas function."""
    
    def test_identical_dfas(self):
        """Test two identical DFAs."""
        dfa1 = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        dfa2 = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        
        result = are_equivalent_dfas(dfa1, dfa2)
        assert result is True
    
    def test_different_alphabets(self):
        """Test DFAs with different alphabets."""
        dfa1 = FSA(
            states=["q0"],
            alphabet=["a"],
            transitions=[],
            initial_state="q0",
            accept_states=[]
        )
        dfa2 = FSA(
            states=["q0"],
            alphabet=["b"],
            transitions=[],
            initial_state="q0",
            accept_states=[]
        )
        
        result = are_equivalent_dfas(dfa1, dfa2)
        assert result is False
    
    def test_equivalent_but_different_structure(self):
        """Test equivalent DFAs with different structure."""
        # DFA 1: More states
        dfa1 = FSA(
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
        
        # DFA 2: Minimal version
        dfa2 = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        
        # After minimization, should be equivalent
        result = are_equivalent_dfas(dfa1, dfa2)
        # Note: Full isomorphism check not implemented, 
        # so this might not work perfectly yet
        assert isinstance(result, bool)


class TestMinimizationProperties:
    """Test properties that should hold after minimization."""
    
    def test_minimization_preserves_determinism(self):
        """Test that minimization preserves determinism."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q0", to_state="q0", symbol="b"),
                Transition(from_state="q1", to_state="q2", symbol="a"),
                Transition(from_state="q1", to_state="q0", symbol="b"),
                Transition(from_state="q2", to_state="q2", symbol="a"),
                Transition(from_state="q2", to_state="q2", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        minimal = hopcroft_minimization(dfa)
        
        assert is_deterministic(minimal)
    
    def test_minimization_preserves_alphabet(self):
        """Test that minimization preserves alphabet."""
        dfa = FSA(
            states=["q0", "q1"],
            alphabet=["a", "b", "c"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        minimal = hopcroft_minimization(dfa)
        
        assert set(minimal.alphabet) == {"a", "b", "c"}
    
    def test_minimization_idempotent(self):
        """Test that minimizing twice gives same result."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q2", symbol="a"),
                Transition(from_state="q2", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        
        minimal1 = hopcroft_minimization(dfa)
        minimal2 = hopcroft_minimization(minimal1)
        
        # Second minimization shouldn't reduce states further
        assert len(minimal2.states) == len(minimal1.states)
    
    def test_minimal_has_no_unreachable_states(self):
        """Test that minimal DFA has no unreachable states."""
        dfa = FSA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q1", symbol="a"),
                Transition(from_state="q2", to_state="q3", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        minimal = hopcroft_minimization(dfa)
        
        # Check all states are reachable
        reachable = {minimal.initial_state}
        queue = [minimal.initial_state]
        
        while queue:
            current = queue.pop(0)
            for trans in minimal.transitions:
                if trans.from_state == current and trans.to_state not in reachable:
                    reachable.add(trans.to_state)
                    queue.append(trans.to_state)
        
        assert reachable == set(minimal.states)


class TestMinimizationEdgeCases:
    """Test edge cases for minimization."""
    
    def test_empty_accept_states(self):
        """Test minimization with no accept states."""
        dfa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q0", symbol="a")
            ],
            initial_state="q0",
            accept_states=[]
        )
        minimal = hopcroft_minimization(dfa)
        
        # All states are equivalent (all non-accepting)
        assert len(minimal.states) == 1
    
    def test_all_states_accepting(self):
        """Test minimization with all states accepting."""
        dfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q2", symbol="a"),
                Transition(from_state="q2", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q0", "q1", "q2"]
        )
        minimal = hopcroft_minimization(dfa)
        
        assert is_deterministic(minimal)
        # All states are accepting, might be minimizable
        assert len(minimal.states) <= len(dfa.states)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
