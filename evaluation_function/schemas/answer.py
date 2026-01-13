"""
Answer Parameter Schema

Defines how the correct answer can be specified:
- regex: Regular expression
- test_cases: List of input/expected pairs
- reference_fsa: A reference FSA to compare against
- grammar: Formal grammar definition
"""

from typing import List, Literal, Union, Optional
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """A single test case with input and expected result."""
    input: str = Field(..., description="Input string to test")
    expected: bool = Field(..., description="True if should accept, False if reject")
    description: Optional[str] = Field(default=None, description="Optional description")


class RegexAnswer(BaseModel):
    """Answer as a regular expression."""
    type: Literal["regex"] = "regex"
    value: str = Field(..., description="Regular expression pattern")


class TestCasesAnswer(BaseModel):
    """Answer as a set of test cases."""
    type: Literal["test_cases"] = "test_cases"
    value: List[TestCase] = Field(..., min_length=1)


class ReferenceFSAAnswer(BaseModel):
    """Answer as a reference FSA (uses same structure as response)."""
    type: Literal["reference_fsa"] = "reference_fsa"
    value: dict = Field(..., description="Reference FSA to compare against")


class GrammarAnswer(BaseModel):
    """Answer as a formal grammar."""
    type: Literal["grammar"] = "grammar"
    value: dict = Field(..., description="Grammar definition with productions")


# Union of all answer types
Answer = Union[RegexAnswer, TestCasesAnswer, ReferenceFSAAnswer, GrammarAnswer]
