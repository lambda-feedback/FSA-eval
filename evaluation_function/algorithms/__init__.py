"""
FSA Algorithms

Implementation of core finite state automata algorithms:
- ε-closure computation for ε-NFA support
- Subset construction for NFA→DFA conversion
- Hopcroft's algorithm for DFA minimization
"""

from .epsilon_closure import epsilon_closure, epsilon_closure_set
from .nfa_to_dfa import nfa_to_dfa, subset_construction
from .minimization import minimize_dfa, hopcroft_minimization

__all__ = [
    # ε-closure
    "epsilon_closure",
    "epsilon_closure_set",
    # NFA to DFA conversion
    "nfa_to_dfa",
    "subset_construction",
    # DFA minimization
    "minimize_dfa",
    "hopcroft_minimization",
]
