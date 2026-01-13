from itertools import product
from typing import List, Set
from collections import deque

from evaluation_function.schemas.result import StructuralInfo

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
                message="The FSA has no states defined",
                code=ErrorCode.EMPTY_STATES,
                severity="error",
                suggestion="Add at least one state to the FSA"
            )
        )
        return errors  # Early return since other checks depend on states

    # Check if alphabet is empty
    if not alphabet:
        errors.append(
            ValidationError(
                message="The alphabet is empty",
                code=ErrorCode.EMPTY_ALPHABET,
                severity="error",
                suggestion="Add at least one symbol to the alphabet"
            )
        )

    # Initial state
    if fsa.initial_state not in states:
        errors.append(
            ValidationError(
                message=f"The initial state '{fsa.initial_state}' is not defined in the FSA",
                code=ErrorCode.INVALID_INITIAL,
                severity="error",
                highlight=ElementHighlight(
                    type="initial_state",
                    state_id=fsa.initial_state
                ),
                suggestion="Include the initial state in your FSA or change your initial state"
            )
        )

    # Accept states
    for acc in set(fsa.accept_states):
        if acc not in states:
            errors.append(
                ValidationError(
                    message=f"The accept state '{acc}' is not defined in the FSA",
                    code=ErrorCode.INVALID_ACCEPT,
                    severity="error",
                    highlight=ElementHighlight(
                        type="accept_state",
                        state_id=acc
                    ),
                    suggestion="Include the accept state in your FSA or change your accept state"
                )
            )

    # Transitions
    for t in fsa.transitions:
        if t.from_state not in states:
            errors.append(
                ValidationError(
                    message=f"The source state '{t.from_state}' in transition '{t.symbol}' is not defined",
                    code=ErrorCode.INVALID_TRANSITION_SOURCE,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Add state '{t.from_state}' to the FSA or change the transition source"
                )
            )
        if t.to_state not in states:
            errors.append(
                ValidationError(
                    message=f"The destination state '{t.to_state}' in transition '{t.symbol}' is not defined",
                    code=ErrorCode.INVALID_TRANSITION_DEST,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Add state '{t.to_state}' to the FSA or change the transition destination"
                )
            )
        if t.symbol not in alphabet:
            errors.append(
                ValidationError(
                    message=f"The transition symbol '{t.symbol}' is not in the alphabet",
                    code=ErrorCode.INVALID_SYMBOL,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion=f"Add symbol '{t.symbol}' to the alphabet or change the transition symbol"
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
    
    for t in fsa.transitions:
        key = (t.from_state, t.symbol)
        if key in seen:
            errors.append(
                ValidationError(
                    message=f"Non-deterministic: multiple transitions from '{t.from_state}' on symbol '{t.symbol}'",
                    code=ErrorCode.DUPLICATE_TRANSITION,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    ),
                    suggestion="Remove duplicate transitions or convert to NFA if nondeterminism is intended"
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
                message="Cannot check completeness for non-deterministic FSA",
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
                        message=f"Missing transition from state '{state}' on symbol '{symbol}' to make the FSA complete",
                        code=ErrorCode.MISSING_TRANSITION,
                        severity="error",
                        highlight=ElementHighlight(
                            type="state",
                            state_id=state,
                            symbol=symbol
                        ),
                        suggestion=f"Add a transition from state '{state}' on symbol '{symbol}'"
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
                    message=f"State '{state}' is unreachable from the initial state",
                    code=ErrorCode.UNREACHABLE_STATE,
                    severity="warning",  # Changed to warning as it's not always an error
                    highlight=ElementHighlight(
                        type="state",
                        state_id=state
                    ),
                    suggestion=f"Add a transition to state '{state}' from a reachable state, or remove it if unnecessary"
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
                        message=f"State '{state}' cannot reach any accepting state (no accept states defined)",
                        code=ErrorCode.DEAD_STATE,
                        severity="warning",
                        highlight=ElementHighlight(
                            type="state",
                            state_id=state
                        ),
                        suggestion="Add at least one accept state to the FSA"
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
                    message=f"State '{state}' is dead (cannot reach any accepting state)",
                    code=ErrorCode.DEAD_STATE,
                    severity="warning",  # Changed to warning as it's not always an error
                    highlight=ElementHighlight(
                        type="state",
                        state_id=state
                    ),
                    suggestion=f"Add a transition from state '{state}' to a state that can reach an accept state, or make state '{state}' accepting"
                )
            )
    return errors


def accepts_string(fsa: FSA, string: str) -> List[ValidationError]:
    """
    Simulate the FSA on a string.
    Returns [] if accepted, else a ValidationError.
    """
    # First check if FSA is structurally valid
    structural_errors = is_valid_fsa(fsa)
    if structural_errors:
        return structural_errors
    
    current_states: Set[str] = {fsa.initial_state}

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
        current_states = next_states
        if not current_states:
            return [
                ValidationError(
                    message=f"String '{string}' rejected: no transition from state(s) {current_states} on symbol '{symbol}'",
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


def fsas_accept_same_language(fsa1: FSA, fsa2: FSA, max_length: int = 5) -> List[ValidationError]:
    """
    Approximate check for language equivalence by testing all strings up to max_length.
    Returns [] if equivalent, else a ValidationError.
    """
    errors = []

    if set(fsa1.alphabet) != set(fsa2.alphabet):
        errors.append(
            ValidationError(
                message=f"Alphabets of FSAs differ: FSA1 alphabet = {set(fsa1.alphabet)}, FSA2 alphabet = {set(fsa2.alphabet)}",
                code=ErrorCode.LANGUAGE_MISMATCH,
                severity="error"
            )
        )
        return errors

    alphabet = fsa1.alphabet
    
    # Check empty string
    empty_string_error = fsas_accept_same_string(fsa1, fsa2, "")
    if empty_string_error:
        return empty_string_error
    
    for length in range(1, max_length + 1):
        for s in product(alphabet, repeat=length):
            string = ''.join(s)
            err = fsas_accept_same_string(fsa1, fsa2, string)
            if err:
                errors.append(
                    ValidationError(
                        message=f"FSAs differ on string '{string}' of length {length}",
                        code=ErrorCode.LANGUAGE_MISMATCH,
                        severity="error"
                    )
                )
                return errors  # stop at first counterexample
    return errors


def get_structured_info_of_fsa(fsa: FSA) -> StructuralInfo:
    """
    Get structured information about the FSA including properties and analysis.
    """
    # Get validation errors first
    validation_errors = is_valid_fsa(fsa)
    
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