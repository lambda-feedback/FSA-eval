from typing import List
from pydantic import BaseModel, Field
from .fsa import FSA, Transition

# frontend zod restricts typing, this is the current workaround

class FSAFrontend(BaseModel):
    """
    Finite State Automaton representation.

    Represents a 5-tuple (Q, Σ, δ, q0, F) where:
    - Q = states
    - Σ = alphabet  
    - δ = transitions (transition function)
    - q0 = initial_state
    - F = accept_states

    Example:
    {
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q2", "symbol": "b"}
        ],
        "initial_state": "q0",
        "accept_states": ["q2"]
    }
    """
    states: List[str] = Field(
        ..., 
        min_length=1, 
        description="Q: Set of all state identifiers"
    )
    
    alphabet: List[str] = Field(
        ..., 
        min_length=1, 
        description="Σ: Input alphabet symbols (excluding epsilon)"
    )
    
    transitions: List[str] = Field(
        default_factory=list, 
        description="δ: Transition function as a list of (from_state, symbol, to_state) tuples"
    )
    
    initial_state: str = Field(
        ..., 
        description="q0: The starting state"
    )
    
    accept_states: List[str] = Field(
        default_factory=list, 
        description="F: Set of accepting/final states"
    )

    class Config:
        schema_extra = {
            "example": {
                "states": ["q0", "q1", "q2"],
                "alphabet": ["a", "b"],
                "transitions": [
                    "q0|a|q1|",
                    "q1|b|q2",
                ],
                "initial_state": "q0",
                "accept_states": ["q2"]
            }
        }

    @classmethod
    def from_flattened(cls, data: dict) -> FSA:
        """
        Convert frontend FSA payload (with transitions as "from|symbol|to") 
        into the FSABackend model with proper Transition objects.
        """
        states = data.get("states", [])
        alphabet = data.get("alphabet", [])
        initial_state = data.get("initial_state", "q0")
        accept_states = data.get("accept_states", [])

        flat_transitions = data.get("transitions", [])
        transitions: List[Transition] = []
        for t in flat_transitions:
            try:
                from_state, symbol, to_state = t.split("|")
                transitions.append(
                    Transition(from_state=from_state, symbol=symbol, to_state=to_state)
                )
            except ValueError:
                raise ValueError(f"Invalid transition format: '{t}'")

        return FSA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state=initial_state,
            accept_states=accept_states,
        )
