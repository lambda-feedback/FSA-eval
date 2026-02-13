from typing import Dict, List, Set
from collections import deque

from evaluation_function.schemas.result import StructuralInfo
from ..algorithms.minimization import hopcroft_minimization
from ..algorithms.nfa_to_dfa import nfa_to_dfa, is_deterministic as is_dfa_check
from ..algorithms.epsilon_closure import epsilon_closure_set, build_epsilon_transition_map

from ..schemas import FSA, ValidationError, ErrorCode, ElementHighlight


def is_valid_fsa(fsa: FSA) -> List[ValidationError]:
    """
    Structural validation: initial state, accept states, transitions, and symbols.
    Does NOT check determinism or completeness.
    """
    errors = []
    states = set(fsa.states)
    alphabet = set(fsa.alphabet)

    # Check if states set is empty
    if not states:
        errors.append(
            ValidationError(
                message="Your FSA needs at least one state to work. Every automaton must have states to process input!",
                code=ErrorCode.EMPTY_STATES,
                severity="error",
                suggestion="Start by adding a state - this will be your starting point for the automaton"
            )
        )
        return errors  # Early return since other checks depend on states

    # Check if alphabet is empty
    if not alphabet:
        errors.append(
            ValidationError(
                message="Your FSA needs an alphabet - the set of symbols it can read. Without an alphabet, there's nothing to process!",
                code=ErrorCode.EMPTY_ALPHABET,
                severity="error",
                suggestion="Define the input symbols your FSA should recognize (e.g., 'a', 'b', '0', '1')"
            )
        )

    # Initial state
    if fsa.initial_state not in states:
        errors.append(
            ValidationError(
                message=f"Oops! Your initial state '{fsa.initial_state}' doesn't exist in your FSA. The initial state must be one of your defined states.",
                code=ErrorCode.INVALID_INITIAL,
                severity="error",
                highlight=ElementHighlight(
                    type="initial_state",
                    state_id=fsa.initial_state
                ),
                suggestion=f"Either add '{fsa.initial_state}' to your states, or choose an existing state as the initial state"
            )
        )

    # Accept states
    for acc in set(fsa.accept_states):
        if acc not in states:
            errors.append(
                ValidationError(
                    message=f"The accepting state '{acc}' isn't in your FSA. Accepting states must be part of your state set.",
                    code=ErrorCode.INVALID_ACCEPT,
                    severity="error",
                    highlight=ElementHighlight(
                        type="accept_state",
                        state_id=acc
                    ),
                    suggestion=f"Either add '{acc}' to your states, or remove it from accepting states"
                )
            )

    # Transitions
    for t in fsa.transitions:
        if t.from_state not in states:
            errors.append(
                ValidationError(
                    message=f"This transition starts from '{t.from_state}', but that state doesn't exist in your FSA.",
                    code=ErrorCode.INVALID_TRANSITION_SOURCE,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Add '{t.from_state}' to your states, or update this transition to start from an existing state"
                )
            )
        if t.to_state not in states:
            errors.append(
                ValidationError(
                    message=f"This transition goes to '{t.to_state}', but that state doesn't exist in your FSA.",
                    code=ErrorCode.INVALID_TRANSITION_DEST,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Add '{t.to_state}' to your states, or update this transition to go to an existing state"
                )
            )
        if t.symbol not in alphabet and t.symbol not in ("ε", "epsilon", ""):
            errors.append(
                ValidationError(
                    message=f"The symbol '{t.symbol}' in this transition isn't in your alphabet. Transitions can only use symbols from the alphabet.",
                    code=ErrorCode.INVALID_SYMBOL,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Either add '{t.symbol}' to your alphabet, or change this transition to use an existing symbol"
                )
            )

    return errors


def is_deterministic(fsa: FSA) -> List[ValidationError]:
    """
    Checks for multiple transitions from the same state on the same symbol.
    Returns a list of ValidationErrors if nondeterministic.
    """
    errors = []
    seen = set()
    
    # First check if FSA is structurally valid
    structural_errors = is_valid_fsa(fsa)
    if structural_errors:
        return structural_errors
    
    # Check for epsilon transitions (makes FSA non-deterministic)
    for t in fsa.transitions:
        if t.symbol in ("ε", "epsilon", ""):
            errors.append(
                ValidationError(
                    message=f"Your FSA has an epsilon (ε) transition from '{t.from_state}' to '{t.to_state}'. A DFA cannot have epsilon transitions.",
                    code=ErrorCode.NOT_DETERMINISTIC,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion="Remove epsilon transitions to make this a DFA, or note that your FSA is an NFA/ε-NFA, which is also valid!"
                )
            )
    if errors:
        return errors

    for t in fsa.transitions:
        key = (t.from_state, t.symbol)
        if key in seen:
            errors.append(
                ValidationError(
                    message=f"Your FSA has multiple transitions from state '{t.from_state}' when reading '{t.symbol}'. In a DFA, each state can only have one transition per symbol.",
                    code=ErrorCode.DUPLICATE_TRANSITION,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Keep only one transition from '{t.from_state}' on '{t.symbol}', or if you meant to create an NFA, that's also valid!"
                )
            )
        seen.add(key)

    return errors


def is_complete(fsa: FSA) -> List[ValidationError]:
    """
    Checks if every state has a transition for every symbol (requires deterministic FSA).
    """
    errors = []
    
    # First check if FSA is deterministic
    det_errors = is_deterministic(fsa)
    if det_errors:
        errors.extend(det_errors)
        errors.append(
            ValidationError(
                message="We can only check completeness for deterministic FSAs. Please fix the determinism issues first.",
                code=ErrorCode.NOT_DETERMINISTIC,
                severity="error"
            )
        )
        return errors
    
    states = set(fsa.states)
    alphabet = set(fsa.alphabet)
    transition_keys = {(t.from_state, t.symbol) for t in fsa.transitions}

    for state in states:
        for symbol in alphabet:
            if (state, symbol) not in transition_keys:
                errors.append(
                    ValidationError(
                        message=f"State '{state}' is missing a transition for symbol '{symbol}'. A complete DFA needs transitions for every symbol from every state.",
                        code=ErrorCode.MISSING_TRANSITION,
                        severity="error",
                        highlight=ElementHighlight(
                            type="state",
                            state_id=state,
                            symbol=symbol
                        ),
                        suggestion=f"Add a transition from '{state}' when reading '{symbol}' - it can go to any state, including a 'trap' state"
                    )
                )
    return errors


def find_unreachable_states(fsa: FSA) -> List[ValidationError]:
    """
    Returns ValidationErrors for all unreachable states.
    """
    errors = []
    
    # Check if initial state is valid
    if fsa.initial_state not in set(fsa.states):
        # This error should already be caught by is_valid_fsa
        return []
    
    visited = set()
    queue = deque([fsa.initial_state])
    transitions = fsa.transitions

    while queue:
        state = queue.popleft()
        if state in visited:
            continue
        visited.add(state)
        for t in transitions:
            if t.from_state == state and t.to_state not in visited:
                queue.append(t.to_state)

    for state in fsa.states:
        if state not in visited:
            errors.append(
                ValidationError(
                    message=f"State '{state}' can never be reached! There's no path from your initial state to this state.",
                    code=ErrorCode.UNREACHABLE_STATE,
                    severity="warning",
                    highlight=ElementHighlight(
                        type="state",
                        state_id=state
                    ),
                    suggestion=f"Connect '{state}' to your FSA by adding a transition to it, or remove it if it's not needed"
                )
            )
    return errors


def find_dead_states(fsa: FSA) -> List[ValidationError]:
    """
    Returns ValidationErrors for all dead states (cannot reach an accepting state).
    """
    errors = []
    
    # Check if there are any accept states
    if not fsa.accept_states:
        # All non-accepting states are dead if there are no accept states
        for state in fsa.states:
            if state != fsa.initial_state or state not in fsa.accept_states:
                errors.append(
                    ValidationError(
                        message=f"Your FSA has no accepting states, so no input string can ever be accepted! This means the language is empty.",
                        code=ErrorCode.DEAD_STATE,
                        severity="warning",
                        highlight=ElementHighlight(
                            type="state",
                            state_id=state
                        ),
                        suggestion="If you want your FSA to accept some strings, mark at least one state as accepting"
                    )
                )
        return errors
    
    transitions = fsa.transitions
    reachable_to_accept = set(fsa.accept_states)
    queue = deque(fsa.accept_states)

    predecessors = {s: [] for s in fsa.states}
    for t in transitions:
        if t.from_state in fsa.states and t.to_state in fsa.states:
            predecessors[t.to_state].append(t.from_state)

    while queue:
        state = queue.popleft()
        for pred in predecessors[state]:
            if pred not in reachable_to_accept:
                reachable_to_accept.add(pred)
                queue.append(pred)

    for state in fsa.states:
        if state not in reachable_to_accept:
            errors.append(
                ValidationError(
                    message=f"State '{state}' is a dead end - once you enter it, you can never reach an accepting state. This is often called a 'trap state'.",
                    code=ErrorCode.DEAD_STATE,
                    severity="warning",
                    highlight=ElementHighlight(
                        type="state",
                        state_id=state
                    ),
                    suggestion=f"This might be intentional (to reject certain inputs), or you could add a path from '{state}' to an accepting state"
                )
            )
    return errors


def accepts_string(fsa: FSA, string: str) -> List[ValidationError]:
    """
    Simulate the FSA on a string, with full ε-transition support.
    Returns [] if accepted, else a ValidationError.
    """
    # First check if FSA is structurally valid
    structural_errors = is_valid_fsa(fsa)
    if structural_errors:
        return structural_errors

    # Build epsilon transition map for ε-closure computation
    epsilon_trans = build_epsilon_transition_map(fsa.transitions)

    # Start with ε-closure of the initial state
    current_states: Set[str] = epsilon_closure_set({fsa.initial_state}, epsilon_trans)

    for symbol in string:
        # Check if symbol is in alphabet
        if symbol not in set(fsa.alphabet):
            return [
                ValidationError(
                    message=f"String '{string}' contains symbol '{symbol}' not in alphabet",
                    code=ErrorCode.INVALID_SYMBOL,
                    severity="error"
                )
            ]

        next_states = set()
        for state in current_states:
            for t in fsa.transitions:
                if t.from_state == state and t.symbol == symbol:
                    next_states.add(t.to_state)

        # Compute ε-closure of the states reached after reading the symbol
        current_states = epsilon_closure_set(next_states, epsilon_trans)

        if not current_states:
            return [
                ValidationError(
                    message=f"String '{string}' rejected: no transition on symbol '{symbol}'",
                    code=ErrorCode.TEST_CASE_FAILED,
                    severity="error"
                )
            ]

    if any(state in fsa.accept_states for state in current_states):
        return []
    else:
        return [
            ValidationError(
                message=f"String '{string}' rejected: reached non-accepting state(s) {current_states}",
                code=ErrorCode.TEST_CASE_FAILED,
                severity="error"
            )
        ]


def fsas_accept_same_string(fsa1: FSA, fsa2: FSA, string: str) -> List[ValidationError]:
    """
    Returns empty list if both FSAs agree on string acceptance, else a ValidationError.
    """
    errs1 = accepts_string(fsa1, string)
    errs2 = accepts_string(fsa2, string)

    # Both strings were accepted (no errors means accepted)
    accepted1 = len(errs1) == 0
    accepted2 = len(errs2) == 0
    
    if accepted1 != accepted2:
        return [
            ValidationError(
                message=f"FSAs differ on string '{string}': FSA1 {'accepts' if accepted1 else 'rejects'}, FSA2 {'accepts' if accepted2 else 'rejects'}",
                code=ErrorCode.LANGUAGE_MISMATCH,
                severity="error"
            )
        ]
    return []


def fsas_accept_same_language(fsa1: FSA, fsa2: FSA) -> List[ValidationError]:
    # Convert NFA/ε-NFA to DFA before minimization (Hopcroft requires DFA input)
    if not is_dfa_check(fsa1):
        fsa1 = nfa_to_dfa(fsa1)
    if not is_dfa_check(fsa2):
        fsa2 = nfa_to_dfa(fsa2)

    fsa1_min = hopcroft_minimization(fsa1)
    fsa2_min = hopcroft_minimization(fsa2)
    return are_isomorphic(fsa1_min, fsa2_min)
    # """
    # Approximate check for language equivalence by testing all strings up to max_length.
    # Returns [] if equivalent, else a ValidationError.
    # """
    # errors = []

    # if set(fsa1.alphabet) != set(fsa2.alphabet):
    #     errors.append(
    #         ValidationError(
    #             message=f"Alphabets of FSAs differ: FSA1 alphabet = {set(fsa1.alphabet)}, FSA2 alphabet = {set(fsa2.alphabet)}",
    #             code=ErrorCode.LANGUAGE_MISMATCH,
    #             severity="error"
    #         )
    #     )
    #     return errors

    # alphabet = fsa1.alphabet
    
    # # Check empty string
    # empty_string_error = fsas_accept_same_string(fsa1, fsa2, "")
    # if empty_string_error:
    #     return empty_string_error
    
    # for length in range(1, max_length + 1):
    #     for s in product(alphabet, repeat=length):
    #         string = ''.join(s)
    #         err = fsas_accept_same_string(fsa1, fsa2, string)
    #         if err:
    #             errors.append(
    #                 ValidationError(
    #                     message=f"FSAs differ on string '{string}' of length {length}",
    #                     code=ErrorCode.LANGUAGE_MISMATCH,
    #                     severity="error"
    #                 )
    #             )
    #             return errors  # stop at first counterexample
    # return errors


def get_structured_info_of_fsa(fsa: FSA) -> StructuralInfo:
    """
    Get structured information about the FSA including properties and analysis.
    """
    # Check determinism - returns boolean
    det_errors = is_deterministic(fsa)
    is_deterministic_bool = len(det_errors) == 0
    
    # Check completeness - returns boolean
    comp_errors = is_complete(fsa)
    is_complete_bool = len(comp_errors) == 0
    
    # Get dead states - extract state IDs from errors
    dead_state_errors = find_dead_states(fsa)
    dead_states_list = []
    for error in dead_state_errors:
        if error.highlight and error.highlight.state_id:
            dead_states_list.append(error.highlight.state_id)
    
    # Get unreachable states - extract state IDs from errors
    unreachable_state_errors = find_unreachable_states(fsa)
    unreachable_states_list = []
    for error in unreachable_state_errors:
        if error.highlight and error.highlight.state_id:
            unreachable_states_list.append(error.highlight.state_id)
    
    return StructuralInfo(
        is_deterministic=is_deterministic_bool,
        is_complete=is_complete_bool,
        num_states=len(fsa.states),
        num_transitions=len(fsa.transitions),
        dead_states=dead_states_list,
        unreachable_states=unreachable_states_list
    )
    
def are_isomorphic(fsa1: FSA, fsa2: FSA) -> List[ValidationError]:
    """
    Checks if two DFAs are isomorphic. 
    Returns a list of ValidationErrors if they differ, otherwise an empty list.
    Assumes DFAs are minimized and complete.
    """
    errors = []
    # 1. Alphabet Check (Mandatory)
    if set(fsa1.alphabet) != set(fsa2.alphabet):
        student_only = set(fsa1.alphabet) - set(fsa2.alphabet)
        expected_only = set(fsa2.alphabet) - set(fsa1.alphabet)
        
        msg_parts = ["Your alphabet doesn't match what's expected."]
        if student_only:
            msg_parts.append(f"You have extra symbols: {student_only}")
        if expected_only:
            msg_parts.append(f"You're missing symbols: {expected_only}")
        
        errors.append(
            ValidationError(
                message=" ".join(msg_parts),
                code=ErrorCode.LANGUAGE_MISMATCH,
                severity="error",
                suggestion="Make sure your alphabet contains exactly the symbols needed for this language"
            )
        )

    # 2. Basic Structural Check (State Count)
    if len(fsa1.states) != len(fsa2.states):
        if len(fsa1.states) > len(fsa2.states):
            errors.append(
                ValidationError(
                    message=f"Your FSA has {len(fsa1.states)} states, but the minimal solution only needs {len(fsa2.states)}. You might have redundant states.",
                    code=ErrorCode.LANGUAGE_MISMATCH,
                    severity="error",
                    suggestion="Look for states that behave identically and could be merged, or check for unreachable states"
                )
            )
        else:
            errors.append(
                ValidationError(
                    message=f"Your FSA has {len(fsa1.states)} states, but at least {len(fsa2.states)} are needed. You might be missing some states.",
                    code=ErrorCode.LANGUAGE_MISMATCH,
                    severity="error",
                    suggestion="Think about what different 'situations' your FSA needs to remember - each usually needs its own state"
                )
            )

    # 3. State Mapping Initialization
    mapping: Dict[str, str] = {fsa1.initial_state: fsa2.initial_state}
    queue = deque([fsa1.initial_state])
    visited = {fsa1.initial_state}

    # Optimization: Pre-map transitions
    trans1 = {(t.from_state, t.symbol): t.to_state for t in fsa1.transitions}
    trans2 = {(t.from_state, t.symbol): t.to_state for t in fsa2.transitions}
    accept1 = set(fsa1.accept_states)
    accept2 = set(fsa2.accept_states)

    while queue:
        s1 = queue.popleft()
        s2 = mapping[s1]

        # 4. Check Acceptance Parity
        if (s1 in accept1) != (s2 in accept2):
            if s2 in accept2:
                errors.append(
                    ValidationError(
                        message=f"State '{s1}' should be an accepting state, but it's not marked as one. Strings that end here should be accepted!",
                        code=ErrorCode.LANGUAGE_MISMATCH,
                        severity="error",
                        highlight=ElementHighlight(type="state", state_id=s1),
                        suggestion=f"Mark state '{s1}' as an accepting state (add it to your accept states)"
                    )
                )
            else:
                errors.append(
                    ValidationError(
                        message=f"State '{s1}' is marked as accepting, but it shouldn't be. Strings that end here should be rejected!",
                        code=ErrorCode.LANGUAGE_MISMATCH,
                        severity="error",
                        highlight=ElementHighlight(type="state", state_id=s1),
                        suggestion=f"Remove state '{s1}' from your accepting states"
                    )
                )

        # 5. Check Transitions for every symbol in the shared alphabet
        for symbol in fsa1.alphabet:
            dest1 = trans1.get((s1, symbol))
            dest2 = trans2.get((s2, symbol))

            # Missing Transition Check
            if (dest1 is None) != (dest2 is None):
                if dest1 is None:
                    errors.append(
                        ValidationError(
                            message=f"State '{s1}' is missing a transition for symbol '{symbol}'. What should happen when you read '{symbol}' here?",
                            code=ErrorCode.LANGUAGE_MISMATCH,
                            severity="error",
                            highlight=ElementHighlight(type="state", state_id=s1, symbol=symbol),
                            suggestion=f"Add a transition from '{s1}' on '{symbol}' to handle this input"
                        )
                    )
                else:
                    errors.append(
                        ValidationError(
                            message=f"State '{s1}' has an unexpected transition on '{symbol}'. This transition might not be needed.",
                            code=ErrorCode.LANGUAGE_MISMATCH,
                            severity="error",
                            highlight=ElementHighlight(type="state", state_id=s1, symbol=symbol),
                            suggestion=f"Review if the transition from '{s1}' on '{symbol}' is correct"
                        )
                    )
            
            if dest1 is not None:
                if dest1 not in mapping:
                    # New state discovered: check if we've exceeded state count in mapping
                    mapping[dest1] = dest2
                    visited.add(dest1)
                    queue.append(dest1)
                else:
                    # Consistency check: does fsa1 transition to the same logical state as fsa2?
                    if mapping[dest1] != dest2:
                        errors.append(
                            ValidationError(
                                message=f"When in state '{s1}' and reading '{symbol}', you go to '{dest1}', but that leads to incorrect behavior. Check where this transition should go!",
                                code=ErrorCode.LANGUAGE_MISMATCH,
                                severity="error",
                                highlight=ElementHighlight(
                                    type="transition", 
                                    from_state=s1, 
                                    to_state=dest1, 
                                    symbol=symbol
                                ),
                                suggestion=f"Think about what state the FSA should be in after reading '{symbol}' from '{s1}' - try tracing through some example strings"
                            )
                        )

    return errors