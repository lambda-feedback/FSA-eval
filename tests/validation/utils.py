from evaluation_function.schemas.fsa import FSA, Transition


def make_fsa(states, alphabet, transitions, initial, accept):
    return FSA(
        states=states,
        alphabet=alphabet,
        transitions=[
            Transition(**t) for t in transitions
        ],
        initial_state=initial,
        accept_states=accept,
    )
