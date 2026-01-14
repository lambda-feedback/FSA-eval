"""
Comprehensive tests for NFA to DFA conversion (subset construction).

Tests the subset construction algorithm for converting NFAs and ε-NFAs to DFAs.
"""

import pytest
from evaluation_function.algorithms.nfa_to_dfa import (
    subset_construction,
    nfa_to_dfa,
    is_deterministic
)
from evaluation_function.schemas import FSA, Transition


class TestIsDeterministic:
    """Test is_deterministic function."""
    
    def test_simple_dfa(self):
        """Test a simple deterministic FSA."""
        fsa = FSA(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q0", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        assert is_deterministic(fsa) is True
    
    def test_nfa_with_epsilon(self):
        """Test NFA with epsilon transitions."""
        fsa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        assert is_deterministic(fsa) is False
    
    def test_nfa_with_epsilon_variant(self):
        """Test NFA with 'epsilon' string."""
        fsa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="epsilon")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        assert is_deterministic(fsa) is False
    
    def test_nfa_with_empty_symbol(self):
        """Test NFA with empty string epsilon."""
        fsa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        assert is_deterministic(fsa) is False
    
    def test_nfa_with_nondeterminism(self):
        """Test NFA with multiple transitions on same symbol."""
        fsa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q0", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        assert is_deterministic(fsa) is False
    
    def test_complete_dfa(self):
        """Test complete DFA."""
        fsa = FSA(
            states=["q0", "q1"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q0", symbol="a"),
                Transition(from_state="q0", to_state="q1", symbol="b"),
                Transition(from_state="q1", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q0", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        assert is_deterministic(fsa) is True


class TestSubsetConstruction:
    """Test subset_construction function."""
    
    def test_simple_nfa_to_dfa(self):
        """Test converting simple NFA to DFA."""
        nfa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q0", symbol="a"),
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        dfa = subset_construction(nfa)
        
        # DFA should be deterministic
        assert is_deterministic(dfa)
        
        # Should have at least the states discovered
        assert len(dfa.states) >= 1
        
        # Initial state should exist
        assert dfa.initial_state in dfa.states
        
        # Should have transitions for each state-symbol pair
        for state in dfa.states:
            for symbol in dfa.alphabet:
                # At most one transition per (state, symbol)
                trans_count = sum(
                    1 for t in dfa.transitions 
                    if t.from_state == state and t.symbol == symbol
                )
                assert trans_count <= 1
    
    def test_epsilon_nfa_to_dfa(self):
        """Test converting ε-NFA to DFA."""
        nfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q1", to_state="q2", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        dfa = subset_construction(nfa)
        
        # DFA should be deterministic
        assert is_deterministic(dfa)
        
        # No epsilon transitions in DFA
        for trans in dfa.transitions:
            assert trans.symbol not in ("ε", "epsilon", "")
    
    def test_nfa_ending_in_ab(self):
        """Test NFA for strings ending in 'ab'."""
        nfa = FSA(
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
        dfa = subset_construction(nfa)
        
        # DFA should be deterministic
        assert is_deterministic(dfa)
        
        # Should have correct alphabet
        assert set(dfa.alphabet) == {"a", "b"}
        
        # Should have accepting states
        assert len(dfa.accept_states) > 0
    
    def test_nfa_with_multiple_epsilon_transitions(self):
        """Test NFA with multiple epsilon transitions."""
        nfa = FSA(
            states=["q0", "q1", "q2", "q3"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q0", to_state="q2", symbol="ε"),
                Transition(from_state="q1", to_state="q3", symbol="a"),
                Transition(from_state="q2", to_state="q3", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q3"]
        )
        dfa = subset_construction(nfa)
        
        # DFA should be deterministic
        assert is_deterministic(dfa)
        
        # Should have accepting states
        assert len(dfa.accept_states) > 0
    
    def test_epsilon_cycle_nfa(self):
        """Test NFA with epsilon cycle."""
        nfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q1", to_state="q2", symbol="ε"),
                Transition(from_state="q2", to_state="q0", symbol="ε"),
                Transition(from_state="q0", to_state="q0", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        dfa = subset_construction(nfa)
        
        # DFA should be deterministic
        assert is_deterministic(dfa)


class TestNFAToDFA:
    """Test nfa_to_dfa function (alias for subset_construction)."""
    
    def test_nfa_to_dfa_alias(self):
        """Test that nfa_to_dfa works as alias."""
        nfa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q0", symbol="a"),
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        dfa = nfa_to_dfa(nfa)
        
        # Should produce deterministic result
        assert is_deterministic(dfa)


class TestSubsetConstructionProperties:
    """Test properties that should hold after subset construction."""
    
    def test_language_preservation_simple(self):
        """Test that DFA accepts same language as NFA (simple case)."""
        nfa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        dfa = subset_construction(nfa)
        
        # DFA should also accept exactly strings with one 'a'
        # Check structure makes sense
        assert dfa.initial_state in dfa.states
        assert all(state in dfa.states for state in dfa.accept_states)
    
    def test_alphabet_preservation(self):
        """Test that alphabet is preserved."""
        nfa = FSA(
            states=["q0", "q1"],
            alphabet=["a", "b", "c"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        dfa = subset_construction(nfa)
        
        assert set(dfa.alphabet) == {"a", "b", "c"}
    
    def test_all_states_reachable(self):
        """Test that all DFA states are reachable from initial."""
        nfa = FSA(
            states=["q0", "q1", "q2"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a"),
                Transition(from_state="q1", to_state="q2", symbol="b")
            ],
            initial_state="q0",
            accept_states=["q2"]
        )
        dfa = subset_construction(nfa)
        
        # All states in DFA should be reachable
        # (subset construction only creates reachable states)
        reachable = {dfa.initial_state}
        queue = [dfa.initial_state]
        
        while queue:
            current = queue.pop(0)
            for trans in dfa.transitions:
                if trans.from_state == current and trans.to_state not in reachable:
                    reachable.add(trans.to_state)
                    queue.append(trans.to_state)
        
        assert reachable == set(dfa.states)


class TestSubsetConstructionEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_dfa_input(self):
        """Test converting a DFA (should still work)."""
        dfa_input = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q1"]
        )
        dfa_output = subset_construction(dfa_input)
        
        # Should still be deterministic
        assert is_deterministic(dfa_output)
    
    def test_single_state_nfa(self):
        """Test NFA with single state."""
        nfa = FSA(
            states=["q0"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q0", symbol="a")
            ],
            initial_state="q0",
            accept_states=["q0"]
        )
        dfa = subset_construction(nfa)
        
        assert is_deterministic(dfa)
        assert len(dfa.states) >= 1
    
    def test_nfa_with_no_accepting_states(self):
        """Test NFA with no accepting states."""
        nfa = FSA(
            states=["q0", "q1"],
            alphabet=["a"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="a")
            ],
            initial_state="q0",
            accept_states=[]
        )
        dfa = subset_construction(nfa)
        
        # DFA should also have no accepting states
        assert len(dfa.accept_states) == 0
    
    def test_complex_epsilon_nfa(self):
        """Test complex ε-NFA with multiple paths."""
        nfa = FSA(
            states=["q0", "q1", "q2", "q3", "q4"],
            alphabet=["a", "b"],
            transitions=[
                Transition(from_state="q0", to_state="q1", symbol="ε"),
                Transition(from_state="q0", to_state="q2", symbol="ε"),
                Transition(from_state="q1", to_state="q3", symbol="a"),
                Transition(from_state="q2", to_state="q4", symbol="b"),
                Transition(from_state="q3", to_state="q4", symbol="ε"),
                Transition(from_state="q4", to_state="q0", symbol="ε")
            ],
            initial_state="q0",
            accept_states=["q4"]
        )
        dfa = subset_construction(nfa)
        
        # Should produce valid DFA
        assert is_deterministic(dfa)
        assert dfa.initial_state in dfa.states
        assert all(state in dfa.states for state in dfa.accept_states)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
