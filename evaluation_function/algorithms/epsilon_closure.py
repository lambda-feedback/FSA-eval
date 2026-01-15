"""
ε-Closure Computation

Implements ε-closure computation for ε-NFA support.
The ε-closure of a state is the set of states reachable from that state
using only ε-transitions (including the state itself).
"""

from typing import Set, Dict, List
from ..schemas import FSA, Transition


def epsilon_closure(state: str, epsilon_transitions: Dict[str, Set[str]]) -> Set[str]:
    """
    Compute the ε-closure of a single state.
    
    The ε-closure of a state q is the set of all states reachable from q
    using only ε-transitions, including q itself.
    
    Algorithm:
    1. Initialize closure with the state itself
    2. Use DFS/BFS to follow all ε-transitions
    3. Return the complete set of reachable states
    
    Args:
        state: The state to compute ε-closure for
        epsilon_transitions: Dict mapping state -> set of states reachable via ε
        
    Returns:
        Set of states in the ε-closure
        
    Example:
        >>> eps_trans = {"q0": {"q1", "q2"}, "q1": {"q3"}}
        >>> epsilon_closure("q0", eps_trans)
        {"q0", "q1", "q2", "q3"}
    """
    closure = {state}
    stack = [state]
    
    while stack:
        current = stack.pop()
        
        # Get all states reachable via ε from current
        if current in epsilon_transitions:
            for next_state in epsilon_transitions[current]:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
    
    return closure


def epsilon_closure_set(states: Set[str], epsilon_transitions: Dict[str, Set[str]]) -> Set[str]:
    """
    Compute the ε-closure of a set of states.
    
    This is the union of ε-closures of all states in the set.
    
    Args:
        states: Set of states to compute ε-closure for
        epsilon_transitions: Dict mapping state -> set of states reachable via ε
        
    Returns:
        Set of all states in the combined ε-closure
        
    Example:
        >>> eps_trans = {"q0": {"q1"}, "q2": {"q3"}}
        >>> epsilon_closure_set({"q0", "q2"}, eps_trans)
        {"q0", "q1", "q2", "q3"}
    """
    closure = set()
    
    for state in states:
        closure |= epsilon_closure(state, epsilon_transitions)
    
    return closure


def build_epsilon_transition_map(transitions: List[Transition]) -> Dict[str, Set[str]]:
    """
    Build a mapping of ε-transitions from a list of transitions.
    
    Args:
        transitions: List of all transitions in the FSA
        
    Returns:
        Dict mapping each state to the set of states reachable via ε-transitions
        
    Example:
        >>> transitions = [
        ...     Transition(from_state="q0", to_state="q1", symbol="ε"),
        ...     Transition(from_state="q0", to_state="q2", symbol="ε"),
        ...     Transition(from_state="q1", to_state="q3", symbol="a")
        ... ]
        >>> build_epsilon_transition_map(transitions)
        {"q0": {"q1", "q2"}}
    """
    epsilon_map: Dict[str, Set[str]] = {}
    
    for trans in transitions:
        # Check for ε-transitions (various representations)
        if trans.symbol in ("ε", "epsilon", ""):
            if trans.from_state not in epsilon_map:
                epsilon_map[trans.from_state] = set()
            epsilon_map[trans.from_state].add(trans.to_state)
    
    return epsilon_map


def compute_all_epsilon_closures(fsa: FSA) -> Dict[str, Set[str]]:
    """
    Compute ε-closures for all states in an FSA.
    
    This is useful for preprocessing before NFA to DFA conversion.
    
    Args:
        fsa: The finite state automaton
        
    Returns:
        Dict mapping each state to its ε-closure
        
    Example:
        >>> fsa = FSA(
        ...     states=["q0", "q1", "q2"],
        ...     alphabet=["a"],
        ...     transitions=[
        ...         Transition(from_state="q0", to_state="q1", symbol="ε"),
        ...         Transition(from_state="q1", to_state="q2", symbol="a")
        ...     ],
        ...     initial_state="q0",
        ...     accept_states=["q2"]
        ... )
        >>> compute_all_epsilon_closures(fsa)
        {"q0": {"q0", "q1"}, "q1": {"q1"}, "q2": {"q2"}}
    """
    epsilon_trans = build_epsilon_transition_map(fsa.transitions)
    closures = {}
    
    for state in fsa.states:
        closures[state] = epsilon_closure(state, epsilon_trans)
    
    return closures
