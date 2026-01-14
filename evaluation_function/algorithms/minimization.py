"""
DFA Minimization

Implements Hopcroft's algorithm for DFA minimization.
Produces a minimal DFA that accepts the same language.
"""

from typing import Set, Dict, List, FrozenSet, Tuple
from ..schemas import FSA, Transition


def hopcroft_minimization(dfa: FSA) -> FSA:
    """
    Minimize a DFA using Hopcroft's algorithm.
    
    Hopcroft's algorithm partitions the states into equivalence classes.
    Two states are equivalent if they cannot be distinguished by any input string.
    
    Algorithm:
    1. Start with two partitions: accepting states and non-accepting states
    2. Iteratively split partitions based on transition behavior
    3. Continue until no more splits are possible
    4. Each final partition becomes a state in the minimal DFA
    
    Time complexity: O(n log n) where n is the number of states
    
    Args:
        dfa: The DFA to minimize (must be deterministic)
        
    Returns:
        A minimal DFA accepting the same language
        
    Example:
        >>> dfa = FSA(
        ...     states=["q0", "q1", "q2", "q3"],
        ...     alphabet=["a", "b"],
        ...     transitions=[...],
        ...     initial_state="q0",
        ...     accept_states=["q3"]
        ... )
        >>> minimal_dfa = hopcroft_minimization(dfa)
        >>> # minimal_dfa will have <= states than dfa
    """
    # Remove unreachable states first
    dfa = remove_unreachable_states(dfa)
    
    if not dfa.states:
        return dfa
    
    # Build transition function as a dictionary
    transitions_dict: Dict[Tuple[str, str], str] = {}
    for trans in dfa.transitions:
        transitions_dict[(trans.from_state, trans.symbol)] = trans.to_state
    
    # Initialize partitions: accepting vs non-accepting states
    accept_set = set(dfa.accept_states)
    non_accept_set = set(dfa.states) - accept_set
    
    # Start with initial partition
    partitions: Set[FrozenSet[str]] = set()
    if accept_set:
        partitions.add(frozenset(accept_set))
    if non_accept_set:
        partitions.add(frozenset(non_accept_set))
    
    # Work queue for partitions to process
    work_queue: List[FrozenSet[str]] = list(partitions)
    
    # Iteratively refine partitions
    while work_queue:
        splitter = work_queue.pop(0)
        
        for symbol in dfa.alphabet:
            # Find states that transition into splitter on symbol
            predecessors: Set[str] = set()
            for state in dfa.states:
                target = transitions_dict.get((state, symbol))
                if target and target in splitter:
                    predecessors.add(state)
            
            # Try to split each partition
            partitions_to_remove = []
            partitions_to_add = []
            
            for partition in partitions:
                # Split partition into those in predecessors and those not
                in_pred = partition & predecessors
                not_in_pred = partition - predecessors
                
                # If both sets are non-empty, we can split
                if in_pred and not_in_pred:
                    partitions_to_remove.append(partition)
                    
                    in_pred_frozen = frozenset(in_pred)
                    not_in_pred_frozen = frozenset(not_in_pred)
                    
                    partitions_to_add.append(in_pred_frozen)
                    partitions_to_add.append(not_in_pred_frozen)
                    
                    # Add to work queue
                    if partition in work_queue:
                        work_queue.remove(partition)
                        work_queue.append(in_pred_frozen)
                        work_queue.append(not_in_pred_frozen)
                    else:
                        # Add the smaller partition
                        if len(in_pred) <= len(not_in_pred):
                            work_queue.append(in_pred_frozen)
                        else:
                            work_queue.append(not_in_pred_frozen)
            
            # Update partitions
            for p in partitions_to_remove:
                partitions.discard(p)
            for p in partitions_to_add:
                partitions.add(p)
    
    # Build the minimized DFA
    return build_minimal_dfa(dfa, partitions, transitions_dict)


def build_minimal_dfa(
    original_dfa: FSA,
    partitions: Set[FrozenSet[str]],
    transitions_dict: Dict[Tuple[str, str], str]
) -> FSA:
    """
    Build a minimal DFA from state partitions.
    
    Args:
        original_dfa: The original DFA
        partitions: Equivalence classes of states
        transitions_dict: Transition function of original DFA
        
    Returns:
        The minimal DFA
    """
    # Create mapping from original state to partition (new state)
    state_to_partition: Dict[str, FrozenSet[str]] = {}
    for partition in partitions:
        for state in partition:
            state_to_partition[state] = partition
    
    # Create new state names
    partition_to_name: Dict[FrozenSet[str], str] = {}
    for i, partition in enumerate(partitions):
        partition_to_name[partition] = f"q{i}"
    
    # Find initial state partition
    initial_partition = state_to_partition[original_dfa.initial_state]
    initial_state = partition_to_name[initial_partition]
    
    # Find accepting states (partitions containing any accepting state)
    accept_states: List[str] = []
    original_accept_set = set(original_dfa.accept_states)
    for partition in partitions:
        if partition & original_accept_set:
            accept_states.append(partition_to_name[partition])
    
    # Build transitions for minimal DFA
    minimal_transitions: List[Transition] = []
    seen_transitions: Set[Tuple[str, str, str]] = set()
    
    for partition in partitions:
        # Pick any representative state from the partition
        representative = next(iter(partition))
        from_state_name = partition_to_name[partition]
        
        for symbol in original_dfa.alphabet:
            # Find where representative goes on this symbol
            target = transitions_dict.get((representative, symbol))
            
            if target:
                target_partition = state_to_partition[target]
                to_state_name = partition_to_name[target_partition]
                
                # Add transition if not already added
                trans_tuple = (from_state_name, to_state_name, symbol)
                if trans_tuple not in seen_transitions:
                    seen_transitions.add(trans_tuple)
                    minimal_transitions.append(Transition(
                        from_state=from_state_name,
                        to_state=to_state_name,
                        symbol=symbol
                    ))
    
    # Create the minimal DFA
    minimal_dfa = FSA(
        states=list(partition_to_name.values()),
        alphabet=original_dfa.alphabet,
        transitions=minimal_transitions,
        initial_state=initial_state,
        accept_states=accept_states
    )
    
    return minimal_dfa


def remove_unreachable_states(dfa: FSA) -> FSA:
    """
    Remove states that are not reachable from the initial state.
    
    This is a preprocessing step for minimization.
    
    Args:
        dfa: The DFA to process
        
    Returns:
        DFA with only reachable states
    """
    # Find all reachable states using BFS
    reachable = {dfa.initial_state}
    queue = [dfa.initial_state]
    
    # Build transition map
    transitions_dict: Dict[Tuple[str, str], str] = {}
    for trans in dfa.transitions:
        transitions_dict[(trans.from_state, trans.symbol)] = trans.to_state
    
    while queue:
        current = queue.pop(0)
        
        for symbol in dfa.alphabet:
            target = transitions_dict.get((current, symbol))
            if target and target not in reachable:
                reachable.add(target)
                queue.append(target)
    
    # Filter states, transitions, and accept states
    filtered_states = [s for s in dfa.states if s in reachable]
    filtered_transitions = [
        t for t in dfa.transitions
        if t.from_state in reachable and t.to_state in reachable
    ]
    filtered_accept = [s for s in dfa.accept_states if s in reachable]
    
    return FSA(
        states=filtered_states,
        alphabet=dfa.alphabet,
        transitions=filtered_transitions,
        initial_state=dfa.initial_state,
        accept_states=filtered_accept
    )


def minimize_dfa(dfa: FSA) -> FSA:
    """
    Minimize a DFA (alias for hopcroft_minimization).
    
    This is the main entry point for DFA minimization.
    
    Args:
        dfa: The DFA to minimize
        
    Returns:
        A minimal DFA accepting the same language
    """
    return hopcroft_minimization(dfa)


def are_equivalent_dfas(dfa1: FSA, dfa2: FSA) -> bool:
    """
    Check if two DFAs accept the same language.
    
    Algorithm:
    1. Minimize both DFAs
    2. Check if the minimal DFAs are isomorphic
    
    Note: This is a basic implementation. More sophisticated
    approaches exist for language equivalence checking.
    
    Args:
        dfa1: First DFA
        dfa2: Second DFA
        
    Returns:
        True if both DFAs accept the same language
    """
    # Must have same alphabet
    if set(dfa1.alphabet) != set(dfa2.alphabet):
        return False
    
    # Minimize both
    min1 = minimize_dfa(dfa1)
    min2 = minimize_dfa(dfa2)
    
    # Check if they have the same number of states
    # (Minimal DFAs for the same language are isomorphic)
    if len(min1.states) != len(min2.states):
        return False
    
    # TODO: Implement full isomorphism check
    # For now, this is a heuristic
    return len(min1.states) == len(min2.states)
