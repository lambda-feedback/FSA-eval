from collections import defaultdict
from .fsa import FSA

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


# is_nfa()
# make_complete()
# add_sink_state()

