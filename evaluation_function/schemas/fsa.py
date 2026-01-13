"""
FSA Representation Schema

Defines the structure for Finite State Automata passed as student response.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class StatePosition(BaseModel):
    """Visual position of a state (for drag-and-drop UI)."""
    x: float
    y: float


class Transition(BaseModel):
    """A single transition in the automaton."""
    from_state: str = Field(..., alias="from")
    to_state: str = Field(..., alias="to")
    symbol: str

    class Config:
        populate_by_name = True


class FSA(BaseModel):
    """
    Finite State Automaton representation.
    
    Example:
    {
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from": "q0", "to": "q1", "symbol": "a"},
            {"from": "q1", "to": "q2", "symbol": "b"}
        ],
        "initial_state": "q0",
        "accept_states": ["q2"]
    }
    """
    states: List[str] = Field(..., min_length=1, description="Set of state identifiers")
    alphabet: List[str] = Field(..., min_length=1, description="Input alphabet symbols")
    transitions: List[Transition] = Field(default_factory=list, description="Transition function")
    initial_state: str = Field(..., description="Initial state")
    accept_states: List[str] = Field(default_factory=list, description="Accepting/final states")
    
    # Optional UI metadata
    positions: Optional[Dict[str, StatePosition]] = Field(default=None, description="State positions for UI")

    class Config:
        json_schema_extra = {
            "example": {
                "states": ["q0", "q1", "q2"],
                "alphabet": ["a", "b"],
                "transitions": [
                    {"from": "q0", "to": "q1", "symbol": "a"},
                    {"from": "q1", "to": "q2", "symbol": "b"}
                ],
                "initial_state": "q0",
                "accept_states": ["q2"]
            }
        }
