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
    config: str | None = Field(default=None)

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "states": ["q0", "q1", "q2"],
    #             "alphabet": ["a", "b"],
    #             "transitions": [
    #                 "q0|a|q1|",
    #                 "q1|b|q2",
    #             ],
    #             "initial_state": "q0",
    #             "accept_states": ["q2"]
    #         }
    #     }

    def toFSA(self) -> FSA:
        transitions: List[Transition] = []

        for t in self.transitions:
            parts = t.split("|")

            # allow trailing delimiter but enforce structure
            if len(parts) == 4 and parts[-1] == "":
                parts = parts[:-1]

            if len(parts) != 3:
                raise ValueError(
                    f"Invalid transition format '{t}'. "
                    "Expected 'from|symbol|to'"
                )

            from_state, symbol, to_state = parts

            if from_state not in self.states:
                raise ValueError(f"Unknown from_state '{from_state}'")

            if to_state not in self.states:
                raise ValueError(f"Unknown to_state '{to_state}'")

            if symbol not in self.alphabet:
                raise ValueError(f"Symbol '{symbol}' not in alphabet")

            transitions.append(
                Transition(
                    from_state=from_state,
                    symbol=symbol,
                    to_state=to_state,
                )
            )

        if self.initial_state not in self.states:
            raise ValueError("initial_state must be in states")

        for s in self.accept_states:
            if s not in self.states:
                raise ValueError(f"Accept state '{s}' not in states")

        return FSA(
            states=self.states,
            alphabet=self.alphabet,
            transitions=transitions,
            initial_state=self.initial_state,
            accept_states=self.accept_states,
        )