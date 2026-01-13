from itertools import product
from typing import Set
from ..schemas.fsa import FSA

def is_valid_fsa(fsa: FSA) -> bool:
    states = set(fsa.states)
    alphabet = set(fsa.alphabet)

    if fsa.initial_state not in states:
        return False

    if not set(fsa.accept_states).issubset(states):
        return False

    for t in fsa.transitions:
        if t.from_state not in states:
            return False
        if t.to_state not in states:
            return False
        if t.symbol not in alphabet:
            return False

    return True

def is_deterministic(fsa: FSA) -> bool:
    if not is_valid_fsa(fsa):
        return False

    seen = set()

    for t in fsa.transitions:
        key = (t.from_state, t.symbol)
        if key in seen:
            return False
        seen.add(key)

    return True

def is_complete(fsa: FSA) -> bool:
    if not is_deterministic(fsa):
        return False

    states = set(fsa.states)
    alphabet = set(fsa.alphabet)

    seen = {(t.from_state, t.symbol) for t in fsa.transitions}

    for state in states:
        for symbol in alphabet:
            if (state, symbol) not in seen:
                return False

    return True

def classify_fsa(fsa: FSA) -> dict:
    return {
        "valid": is_valid_fsa(fsa),
        "deterministic": is_deterministic(fsa),
        "complete": is_complete(fsa),
    }

# simple bfs
def accepts_string(fsa: FSA, string: str) -> bool:
    """
    Simulate the FSA on a given string.
    Returns True if the string is accepted, False otherwise.
    """
    current_states: Set[str] = {fsa.initial_state}

    for symbol in string:
        next_states = set()
        for state in current_states:
            for t in fsa.transitions:
                if t.from_state == state and t.symbol == symbol:
                    next_states.add(t.to_state)
        current_states = next_states
        if not current_states:
            return False

    return any(state in fsa.accept_states for state in current_states)


def fsas_accept_same_string(fsa1: FSA, fsa2: FSA, string: str) -> bool:
    """
    Check if two FSAs accept the same given string.
    """
    return accepts_string(fsa1, string) and accepts_string(fsa2, string)

def fsas_accept_same_language(fsa1: FSA, fsa2: FSA, max_length: int = 5) -> bool:
    """
    Approximate check if two FSAs accept the same language.
    Checks all strings over the alphabet up to length `max_length`.
    Warning: exponential in alphabet size * max_length.
    """
    alphabet = fsa1.alphabet
    if set(fsa1.alphabet) != set(fsa2.alphabet):
        return False

    for length in range(max_length + 1):
        for s in product(alphabet, repeat=length):
            string = ''.join(s)
            if accepts_string(fsa1, string) != accepts_string(fsa2, string):
                return False
    return True
# Note: This is practical for small alphabets and short strings.
# For full correctness on infinite languages, you need minimized DFA equivalence.

# is_nfa()
# make_complete()
# add_sink_state()

