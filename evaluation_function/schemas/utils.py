from .fsa import FSA, Transition



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

# if __name__ == "__main__":
#     fsa = make_fsa(
#             states=["q0", "q1"],
#             alphabet=["a"],
#             transitions=[
#                 {"from_state": "q0", "to_state": "q0", "symbol": "a"},
#                 {"from_state": "q0", "to_state": "q1", "symbol": "a"},  # Non-deterministic
#             ],
#             initial="q0",
#             accept=["q1"],
#         )
#     draw_fsa(fsa, False, True, "./valid.png")
#     fsa = make_fsa(
#             states=["q0"],
#             alphabet=["a"],
#             transitions=[],
#             initial="q0",
#             accept=["q1"],  # q1 is not in states
#         )
#     draw_fsa(fsa, False, True, "./invalid.png")
    