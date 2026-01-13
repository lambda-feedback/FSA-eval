"""
FSA Representation Schema

Defines the structure for Finite State Automata passed as student response.
"""

from typing import List
from pydantic import BaseModel, Field


class Transition(BaseModel):
    """
    A single transition in the automaton.
    
    Represents: δ(from_state, symbol) = to_state
    """
    from_state: str = Field(..., description="Source state identifier")
    to_state: str = Field(..., description="Destination state identifier")
    symbol: str = Field(..., description="Input symbol (use 'ε' for epsilon transitions)")


class FSA(BaseModel):
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
    
    transitions: List[Transition] = Field(
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
        json_schema_extra = {
            "example": {
                "states": ["q0", "q1", "q2"],
                "alphabet": ["a", "b"],
                "transitions": [
                    {"from_state": "q0", "to_state": "q1", "symbol": "a"},
                    {"from_state": "q1", "to_state": "q2", "symbol": "b"}
                ],
                "initial_state": "q0",
                "accept_states": ["q2"]
            }
        }
