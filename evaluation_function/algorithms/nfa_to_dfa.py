"""
NFA to DFA Conversion (Subset Construction)

Implements the subset construction algorithm to convert an NFA (or ε-NFA)
to an equivalent DFA.
"""

from typing import Set, Dict, FrozenSet, List, Tuple
from ..schemas import FSA, Transition
from .epsilon_closure import (
    epsilon_closure_set,
    build_epsilon_transition_map
)


def subset_construction(nfa: FSA) -> FSA:
    """
    Convert an NFA (or ε-NFA) to an equivalent DFA using subset construction.
    
    Algorithm (Subset Construction / Powerset Construction):
    1. Start with ε-closure of initial state as first DFA state
    2. For each DFA state (which is a set of NFA states):
       - For each symbol in alphabet:
         - Find all NFA states reachable on that symbol
         - Compute ε-closure of those states
         - This becomes a new DFA state
    3. Continue until no new states are discovered
    4. A DFA state is accepting if it contains any NFA accepting state
    
    Args:
        nfa: The NFA or ε-NFA to convert
        
    Returns:
        An equivalent DFA
        
    Example:
        >>> nfa = FSA(
        ...     states=["q0", "q1"],
        ...     alphabet=["a"],
        ...     transitions=[
        ...         Transition(from_state="q0", to_state="q0", symbol="a"),
        ...         Transition(from_state="q0", to_state="q1", symbol="a")
        ...     ],
        ...     initial_state="q0",
        ...     accept_states=["q1"]
        ... )
        >>> dfa = subset_construction(nfa)
        >>> # DFA will have deterministic transitions
    """
    # Build ε-transition map
    epsilon_trans = build_epsilon_transition_map(nfa.transitions)
    
    # Build transition function for non-ε symbols
    nfa_transitions: Dict[Tuple[str, str], Set[str]] = {}
    for trans in nfa.transitions:
        # Skip ε-transitions
        if trans.symbol not in ("ε", "epsilon", ""):
            key = (trans.from_state, trans.symbol)
            if key not in nfa_transitions:
                nfa_transitions[key] = set()
            nfa_transitions[key].add(trans.to_state)
    
    # Initialize DFA construction
    initial_closure = epsilon_closure_set({nfa.initial_state}, epsilon_trans)
    initial_state_key = frozenset(initial_closure)
    
    # Map from frozenset of NFA states to DFA state name
    state_mapping: Dict[FrozenSet[str], str] = {}
    state_counter = 0
    
    def get_dfa_state_name(nfa_state_set: FrozenSet[str]) -> str:
        """Get or create a DFA state name for a set of NFA states."""
        nonlocal state_counter
        if nfa_state_set not in state_mapping:
            state_mapping[nfa_state_set] = f"q{state_counter}"
            state_counter += 1
        return state_mapping[nfa_state_set]
    
    # Track which DFA states we've processed
    unprocessed_states = [initial_state_key]
    processed_states: Set[FrozenSet[str]] = set()
    dfa_transitions: List[Transition] = []
    
    # Get initial DFA state name
    initial_dfa_state = get_dfa_state_name(initial_state_key)
    
    # Process each DFA state
    while unprocessed_states:
        current_nfa_set = unprocessed_states.pop()
        
        if current_nfa_set in processed_states:
            continue
        
        processed_states.add(current_nfa_set)
        current_dfa_state = get_dfa_state_name(current_nfa_set)
        
        # For each symbol in the alphabet
        for symbol in nfa.alphabet:
            # Find all NFA states reachable from current set on this symbol
            reachable_states: Set[str] = set()
            
            for nfa_state in current_nfa_set:
                key = (nfa_state, symbol)
                if key in nfa_transitions:
                    reachable_states |= nfa_transitions[key]
            
            # Compute ε-closure of reachable states
            if reachable_states:
                closure = epsilon_closure_set(reachable_states, epsilon_trans)
                next_state_key = frozenset(closure)
                next_dfa_state = get_dfa_state_name(next_state_key)
                
                # Add DFA transition
                dfa_transitions.append(Transition(
                    from_state=current_dfa_state,
                    to_state=next_dfa_state,
                    symbol=symbol
                ))
                
                # Add to unprocessed if not seen before
                if next_state_key not in processed_states:
                    unprocessed_states.append(next_state_key)
    
    # Determine accepting states
    # A DFA state is accepting if it contains any NFA accepting state
    nfa_accept_states = set(nfa.accept_states)
    dfa_accept_states = []
    
    for nfa_state_set, dfa_state_name in state_mapping.items():
        if nfa_state_set & nfa_accept_states:  # Intersection check
            dfa_accept_states.append(dfa_state_name)
    
    # Build the DFA
    dfa = FSA(
        states=list(state_mapping.values()),
        alphabet=nfa.alphabet,
        transitions=dfa_transitions,
        initial_state=initial_dfa_state,
        accept_states=dfa_accept_states
    )
    
    return dfa


def nfa_to_dfa(nfa: FSA) -> FSA:
    """
    Convert NFA to DFA (alias for subset_construction).
    
    This is the main entry point for NFA to DFA conversion.
    
    Args:
        nfa: The NFA or ε-NFA to convert
        
    Returns:
        An equivalent DFA
    """
    return subset_construction(nfa)


def is_deterministic(fsa: FSA) -> bool:
    """
    Check if an FSA is deterministic (a DFA).
    
    An FSA is deterministic if:
    1. No ε-transitions exist
    2. For each (state, symbol) pair, there is at most one transition
    
    Args:
        fsa: The FSA to check
        
    Returns:
        True if the FSA is a DFA, False if it's an NFA
    """
    # Check for ε-transitions
    for trans in fsa.transitions:
        if trans.symbol in ("ε", "epsilon", ""):
            return False
    
    # Check for multiple transitions on same (state, symbol) pair
    seen_pairs: Set[Tuple[str, str]] = set()
    
    for trans in fsa.transitions:
        pair = (trans.from_state, trans.symbol)
        if pair in seen_pairs:
            return False  # Non-deterministic
        seen_pairs.add(pair)
    
    return True
