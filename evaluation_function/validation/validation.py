from typing import Dict, List, Optional, Set
from collections import deque

from evaluation_function.schemas.result import StructuralInfo
from ..algorithms.minimization import hopcroft_minimization
from ..schemas import FSA, ValidationError, ErrorCode, ElementHighlight, ValidationResult


# =============================================================================
# Structural validation
# =============================================================================

def is_valid_fsa(fsa: FSA) -> ValidationResult[bool]:
    errors: List[ValidationError] = []
    states = set(fsa.states)
    alphabet = set(fsa.alphabet)

    if not states:
        errors.append(
            ValidationError(
                message="Your FSA needs at least one state to work.",
                code=ErrorCode.EMPTY_STATES,
                severity="error",
                suggestion="Start by adding a state."
            )
        )
        return ValidationResult.failure(False, errors)

    if not alphabet:
        errors.append(
            ValidationError(
                message="Your FSA needs an alphabet.",
                code=ErrorCode.EMPTY_ALPHABET,
                severity="error",
                suggestion="Define at least one input symbol."
            )
        )

    if fsa.initial_state not in states:
        errors.append(
            ValidationError(
                message=f"Initial state '{fsa.initial_state}' does not exist.",
                code=ErrorCode.INVALID_INITIAL,
                severity="error",
                highlight=ElementHighlight(
                    type="initial_state",
                    state_id=fsa.initial_state
                )
            )
        )

    for acc in set(fsa.accept_states):
        if acc not in states:
            errors.append(
                ValidationError(
                    message=f"Accepting state '{acc}' does not exist.",
                    code=ErrorCode.INVALID_ACCEPT,
                    severity="error",
                    highlight=ElementHighlight(
                        type="accept_state",
                        state_id=acc
                    )
                )
            )

    for t in fsa.transitions:
        if t.from_state not in states:
            errors.append(
                ValidationError(
                    message=f"Transition source '{t.from_state}' does not exist.",
                    code=ErrorCode.INVALID_TRANSITION_SOURCE,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    )
                )
            )
        if t.to_state not in states:
            errors.append(
                ValidationError(
                    message=f"Transition destination '{t.to_state}' does not exist.",
                    code=ErrorCode.INVALID_TRANSITION_DEST,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    )
                )
            )
        if t.symbol not in alphabet:
            errors.append(
                ValidationError(
                    message=f"Symbol '{t.symbol}' not in alphabet.",
                    code=ErrorCode.INVALID_SYMBOL,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    )
                )
            )

    return (
        ValidationResult.success(True)
        if not errors
        else ValidationResult.failure(False, errors)
    )


# =============================================================================
# Determinism & completeness
# =============================================================================

def is_deterministic(fsa: FSA) -> ValidationResult[bool]:
    structural = is_valid_fsa(fsa)
    if not structural.ok:
        return structural

    errors: List[ValidationError] = []
    seen = set()

    for t in fsa.transitions:
        key = (t.from_state, t.symbol)
        if key in seen:
            errors.append(
                ValidationError(
                    message=f"Multiple transitions from '{t.from_state}' on '{t.symbol}'.",
                    code=ErrorCode.DUPLICATE_TRANSITION,
                    severity="error",
                    highlight=ElementHighlight(
                        type="transition",
                        from_state=t.from_state,
                        to_state=t.to_state,
                        symbol=t.symbol
                    )
                )
            )
        seen.add(key)

    return (
        ValidationResult.success(True)
        if not errors
        else ValidationResult.failure(False, errors)
    )


def is_complete(fsa: FSA) -> ValidationResult[bool]:
    det = is_deterministic(fsa)
    if not det.ok:
        return ValidationResult.failure(
            False,
            det.errors + [
                ValidationError(
                    message="Completeness requires determinism.",
                    code=ErrorCode.NOT_DETERMINISTIC,
                    severity="error"
                )
            ],
        )

    errors: List[ValidationError] = []
    states = set(fsa.states)
    alphabet = set(fsa.alphabet)
    transition_keys = {(t.from_state, t.symbol) for t in fsa.transitions}

    for state in states:
        for symbol in alphabet:
            if (state, symbol) not in transition_keys:
                errors.append(
                    ValidationError(
                        message=f"Missing transition from '{state}' on '{symbol}'.",
                        code=ErrorCode.MISSING_TRANSITION,
                        severity="error",
                        highlight=ElementHighlight(
                            type="state",
                            state_id=state,
                            symbol=symbol
                        )
                    )
                )

    return (
        ValidationResult.success(True)
        if not errors
        else ValidationResult.failure(False, errors)
    )


# =============================================================================
# Reachability & dead states
# =============================================================================

def find_unreachable_states(fsa: FSA) -> ValidationResult[List[str]]:
    if fsa.initial_state not in set(fsa.states):
        return ValidationResult.success([])

    visited = set()
    queue = deque([fsa.initial_state])

    while queue:
        state = queue.popleft()
        if state in visited:
            continue
        visited.add(state)
        for t in fsa.transitions:
            if t.from_state == state:
                queue.append(t.to_state)

    unreachable = [s for s in fsa.states if s not in visited]

    errors = [
        ValidationError(
            message=f"State '{s}' is unreachable.",
            code=ErrorCode.UNREACHABLE_STATE,
            severity="warning",
            highlight=ElementHighlight(type="state", state_id=s)
        )
        for s in unreachable
    ]

    return (
        ValidationResult.success(unreachable)
        if not errors
        else ValidationResult.failure(unreachable, errors)
    )


def find_dead_states(fsa: FSA) -> ValidationResult[List[str]]:
    if not fsa.accept_states:
        dead = list(fsa.states)
        errors = [
            ValidationError(
                message="No accepting states; language is empty.",
                code=ErrorCode.DEAD_STATE,
                severity="warning",
                highlight=ElementHighlight(type="state", state_id=s)
            )
            for s in dead
        ]
        return ValidationResult.failure(dead, errors)

    reachable_to_accept = set(fsa.accept_states)
    queue = deque(fsa.accept_states)

    predecessors = {s: [] for s in fsa.states}
    for t in fsa.transitions:
        predecessors[t.to_state].append(t.from_state)

    while queue:
        state = queue.popleft()
        for pred in predecessors[state]:
            if pred not in reachable_to_accept:
                reachable_to_accept.add(pred)
                queue.append(pred)

    dead = [s for s in fsa.states if s not in reachable_to_accept]
    errors = [
        ValidationError(
            message=f"State '{s}' is a dead state.",
            code=ErrorCode.DEAD_STATE,
            severity="warning",
            highlight=ElementHighlight(type="state", state_id=s)
        )
        for s in dead
    ]

    return (
        ValidationResult.success(dead)
        if not errors
        else ValidationResult.failure(dead, errors)
    )


# =============================================================================
# Simulation
# =============================================================================

def accepts_string(fsa: FSA, string: str) -> ValidationResult[bool]:
    valid = is_valid_fsa(fsa)
    if not valid.ok:
        return valid

    current_states: Set[str] = {fsa.initial_state}

    for symbol in string:
        if symbol not in fsa.alphabet:
            return ValidationResult.failure(False, [
                ValidationError(
                    message=f"Symbol '{symbol}' not in alphabet.",
                    code=ErrorCode.INVALID_SYMBOL,
                    severity="error"
                )
            ])

        next_states = {
            t.to_state
            for s in current_states
            for t in fsa.transitions
            if t.from_state == s and t.symbol == symbol
        }

        if not next_states:
            return ValidationResult.failure(False, [
                ValidationError(
                    message=f"String '{string}' rejected.",
                    code=ErrorCode.TEST_CASE_FAILED,
                    severity="error"
                )
            ])

        current_states = next_states

    accepted = any(s in fsa.accept_states for s in current_states)
    return (
        ValidationResult.success(True)
        if accepted
        else ValidationResult.failure(False, [
            ValidationError(
                message=f"String '{string}' rejected.",
                code=ErrorCode.TEST_CASE_FAILED,
                severity="error"
            )
        ])
    )


# =============================================================================
# Language equivalence & minimality
# =============================================================================

def fsas_accept_same_string(fsa1: FSA, fsa2: FSA, string: str) -> ValidationResult[bool]:
    r1 = accepts_string(fsa1, string)
    r2 = accepts_string(fsa2, string)

    if r1.ok != r2.ok:
        return ValidationResult.failure(False, [
            ValidationError(
                message=f"FSAs differ on string '{string}'.",
                code=ErrorCode.LANGUAGE_MISMATCH,
                severity="error"
            )
        ])

    return ValidationResult.success(True)


def fsas_accept_same_language(fsa1: FSA, fsa2: FSA) -> ValidationResult[bool]:
    return are_isomorphic(
        hopcroft_minimization(fsa1),
        hopcroft_minimization(fsa2),
    )


def are_isomorphic(fsa1: FSA, fsa2: FSA) -> ValidationResult[bool]:
    """
    Checks if two DFAs are isomorphic. 
    Returns a list of ValidationErrors if they differ, otherwise an empty list.
    Assumes DFAs are minimized and complete.
    """
    errors = []
    # 1. Alphabet Check (Mandatory)
    if set(fsa1.alphabet) != set(fsa2.alphabet):
        errors.append(
            ValidationError(
                message="The alphabet of your FSA does not match the required alphabet.",
                code=ErrorCode.LANGUAGE_MISMATCH,
                severity="error",
                suggestion=f"Your alphabet: {set(fsa1.alphabet)}. Expected: {set(fsa2.alphabet)}."
            )
        )

    # 2. Basic Structural Check (State Count)
    if len(fsa1.states) != len(fsa2.states):
        errors.append(
            ValidationError(
                message=f"FSA structure mismatch: expected {len(fsa2.states)} states, but found {len(fsa1.states)}.",
                code=ErrorCode.LANGUAGE_MISMATCH,
                severity="error",
                suggestion="Verify if you have unnecessary states or if you have minimized your FSA."
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
            expected_type = "accepting" if s2 in accept2 else "non-accepting"
            errors.append(
                ValidationError(
                    message=f"State '{s1}' is incorrectly marked. It should be an {expected_type} state.",
                    code=ErrorCode.LANGUAGE_MISMATCH,
                    severity="error",
                    highlight=ElementHighlight(type="state", state_id=s1),
                    suggestion=f"Toggle the 'accept' status of state '{s1}'."
                )
            )

        # 5. Check Transitions for every symbol in the shared alphabet
        for symbol in fsa1.alphabet:
            dest1 = trans1.get((s1, symbol))
            dest2 = trans2.get((s2, symbol))

            # Missing Transition Check
            if (dest1 is None) != (dest2 is None):
                errors.append(
                    ValidationError(
                        message=f"Missing or extra transition from state '{s1}' on symbol '{symbol}'.",
                        code=ErrorCode.LANGUAGE_MISMATCH,
                        severity="error",
                        highlight=ElementHighlight(type="state", state_id=s1, symbol=symbol),
                        suggestion="Ensure your DFA is complete and follows the transition logic."
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
                                message=f"Transition from '{s1}' on '{symbol}' leads to the wrong state.",
                                code=ErrorCode.LANGUAGE_MISMATCH,
                                severity="error",
                                highlight=ElementHighlight(
                                    type="transition", 
                                    from_state=s1, 
                                    to_state=dest1, 
                                    symbol=symbol
                                ),
                                suggestion="Check if this transition should point to a different state."
                            )
                        )
    return (
        ValidationResult.success(True)
        if not errors
        else ValidationResult.failure(False, errors)
    )


def is_minimal(fsa: FSA) -> ValidationResult[bool]:
    minimized = hopcroft_minimization(fsa)
    if len(minimized.states) < len(fsa.states):
        return ValidationResult.failure(False, [
            ValidationError(
                message="FSA is not minimal.",
                code=ErrorCode.NOT_MINIMAL,
                severity="error"
            )
        ])
    return ValidationResult.success(True)


# =============================================================================
# Structured info
# =============================================================================

def get_structured_info_of_fsa(fsa: FSA) -> StructuralInfo:
    det = is_deterministic(fsa)
    comp = is_complete(fsa)
    dead = find_dead_states(fsa)
    unreachable = find_unreachable_states(fsa)

    return StructuralInfo(
        is_deterministic=det.ok,
        is_complete=comp.ok,
        num_states=len(fsa.states),
        num_transitions=len(fsa.transitions),
        dead_states=dead.value or [],
        unreachable_states=unreachable.value or [],
    )
