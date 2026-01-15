"""
FSA Correction Module

Generates diagnostic information for comparing student FSA against expected language:
- Generates strings that show differences between student FSA and expected language
- Identifies specific states/transitions causing errors

Leverages validation functions from the validation module for structural analysis.
Uses Pydantic models from schemas module for consistent data structures.
"""

from itertools import product
from typing import List, Optional, Tuple, Dict, Set, Literal
from collections import deque
from pydantic import BaseModel, Field, computed_field

# Schema imports - using Pydantic models for data structures
from ..schemas import FSA, ValidationError, ErrorCode, ElementHighlight
from ..schemas.result import LanguageComparison, TestResult, StructuralInfo, FSAFeedback

# Validation imports - leveraging all available validation functions
from ..validation.validation import (
    is_valid_fsa,
    is_deterministic,
    is_complete,
    accepts_string,
    find_unreachable_states,
    find_dead_states,
    fsas_accept_same_string,
    fsas_accept_same_language,
    are_isomorphic,
    get_structured_info_of_fsa,
)


# =============================================================================
# Pydantic Models for Correction Results
# =============================================================================

class DifferenceString(BaseModel):
    """Represents a string that demonstrates a difference between two FSAs."""
    string: str = Field(..., description="The test string")
    student_accepts: bool = Field(..., description="Whether student FSA accepts this string")
    expected_accepts: bool = Field(..., description="Whether expected FSA accepts this string")
    student_trace: List[str] = Field(default_factory=list, description="State trace in student FSA")
    expected_trace: List[str] = Field(default_factory=list, description="State trace in expected FSA")
    
    @computed_field
    @property
    def difference_type(self) -> Literal["should_accept", "should_reject"]:
        """Returns 'should_accept' or 'should_reject'."""
        return "should_accept" if self.expected_accepts else "should_reject"


class TransitionError(BaseModel):
    """Represents an error in a specific transition."""
    from_state: str
    symbol: str
    actual_to_state: Optional[str] = None
    expected_to_state: Optional[str] = None
    error_type: Literal["wrong_destination", "missing", "extra"]
    example_string: Optional[str] = None
    
    def to_validation_error(self) -> ValidationError:
        """Convert to ValidationError for UI highlighting."""
        if self.error_type == "wrong_destination":
            message = (
                f"Transition from '{self.from_state}' on '{self.symbol}' goes to "
                f"'{self.actual_to_state}' but should go to '{self.expected_to_state}'"
            )
            suggestion = f"Change the destination of this transition to '{self.expected_to_state}'"
        elif self.error_type == "missing":
            message = (
                f"Missing transition from '{self.from_state}' on '{self.symbol}' "
                f"(expected to go to '{self.expected_to_state}')"
            )
            suggestion = f"Add a transition from '{self.from_state}' on '{self.symbol}' to '{self.expected_to_state}'"
        else:  # extra
            message = (
                f"Extra transition from '{self.from_state}' on '{self.symbol}' to "
                f"'{self.actual_to_state}' (this transition should not exist)"
            )
            suggestion = "Remove this transition or redirect it appropriately"
        
        if self.example_string:
            message += f". Example: string '{self.example_string}' {'is incorrectly handled' if self.error_type != 'extra' else 'causes incorrect behavior'}"
        
        return ValidationError(
            message=message,
            code=ErrorCode.LANGUAGE_MISMATCH,
            severity="error",
            highlight=ElementHighlight(
                type="transition",
                from_state=self.from_state,
                to_state=self.actual_to_state or self.expected_to_state,
                symbol=self.symbol
            ),
            suggestion=suggestion
        )


class StateError(BaseModel):
    """Represents an error related to a specific state."""
    state_id: str
    error_type: Literal["should_be_accepting", "should_not_be_accepting", "unreachable", "dead"]
    example_string: Optional[str] = None
    
    def to_validation_error(self) -> ValidationError:
        """Convert to ValidationError for UI highlighting."""
        if self.error_type == "should_be_accepting":
            message = f"State '{self.state_id}' should be an accepting state"
            suggestion = f"Add '{self.state_id}' to the accept states"
            code = ErrorCode.LANGUAGE_MISMATCH
        elif self.error_type == "should_not_be_accepting":
            message = f"State '{self.state_id}' should not be an accepting state"
            suggestion = f"Remove '{self.state_id}' from the accept states"
            code = ErrorCode.LANGUAGE_MISMATCH
        elif self.error_type == "unreachable":
            message = f"State '{self.state_id}' is unreachable from the initial state"
            suggestion = f"Add a transition to reach '{self.state_id}' or remove it if unnecessary"
            code = ErrorCode.UNREACHABLE_STATE
        else:  # dead
            message = f"State '{self.state_id}' is dead (cannot reach any accepting state)"
            suggestion = f"Add a path from '{self.state_id}' to an accepting state"
            code = ErrorCode.DEAD_STATE
        
        if self.example_string:
            message += f". Example: string '{self.example_string}' ends in this state"
        
        return ValidationError(
            message=message,
            code=code,
            severity="error" if self.error_type in ["should_be_accepting", "should_not_be_accepting"] else "warning",
            highlight=ElementHighlight(
                type="state" if self.error_type not in ["should_be_accepting", "should_not_be_accepting"] else "accept_state",
                state_id=self.state_id
            ),
            suggestion=suggestion
        )


class CorrectionResult(BaseModel):
    """Complete result of FSA correction analysis."""
    is_equivalent: bool = True
    summary: str = ""
    difference_strings: List[DifferenceString] = Field(default_factory=list)
    transition_errors: List[TransitionError] = Field(default_factory=list)
    state_errors: List[StateError] = Field(default_factory=list)
    validation_errors: List[ValidationError] = Field(default_factory=list)
    isomorphism_errors: List[ValidationError] = Field(default_factory=list)
    structural_info: Optional[StructuralInfo] = None
    
    def get_all_validation_errors(self) -> List[ValidationError]:
        """Get all errors as ValidationError objects for UI highlighting."""
        errors = list(self.validation_errors)
        errors.extend(self.isomorphism_errors)
        errors.extend([te.to_validation_error() for te in self.transition_errors])
        errors.extend([se.to_validation_error() for se in self.state_errors])
        return errors
    
    def get_language_comparison(self) -> LanguageComparison:
        """Convert to LanguageComparison schema."""
        counterexample = None
        counterexample_type = None
        
        if self.difference_strings:
            first_diff = self.difference_strings[0]
            counterexample = first_diff.string
            counterexample_type = first_diff.difference_type
        
        return LanguageComparison(
            are_equivalent=self.is_equivalent,
            counterexample=counterexample,
            counterexample_type=counterexample_type
        )
    
    def get_test_results(self) -> List[TestResult]:
        """Convert difference strings to TestResult objects."""
        return [
            TestResult(
                input=diff.string,
                expected=diff.expected_accepts,
                actual=diff.student_accepts,
                passed=diff.student_accepts == diff.expected_accepts,
                trace=diff.student_trace
            )
            for diff in self.difference_strings
        ]

    def to_fsa_feedback(self) -> FSAFeedback:
        """Convert to FSAFeedback schema for structured output."""
        all_errors = self.get_all_validation_errors()
        errors = [e for e in all_errors if e.severity == "error"]
        warnings = [e for e in all_errors if e.severity in ("warning", "info")]
        
        hints = []
        if any("accepting" in e.error_type for e in self.state_errors):
            hints.append("Check which states should be accepting based on the language definition")
        if any(e.error_type == "missing" for e in self.transition_errors):
            hints.append("Ensure all necessary transitions are defined for your FSA")
        if self.structural_info:
            if self.structural_info.unreachable_states:
                hints.append("Consider removing unreachable states or adding transitions to reach them")
            if self.structural_info.dead_states:
                hints.append("Dead states can never lead to acceptance - add paths to accepting states")
        
        return FSAFeedback(
            summary=self.summary,
            errors=errors,
            warnings=warnings,
            structural=self.structural_info,
            language=self.get_language_comparison(),
            test_results=self.get_test_results(),
            hints=hints
        )


# =============================================================================
# Helper Functions (leveraging validation module)
# =============================================================================

def trace_string(fsa: FSA, string: str) -> Tuple[bool, List[str]]:
    """
    Trace execution of a string through an FSA.
    Returns (accepted, state_trace).
    """
    if is_valid_fsa(fsa):  # Returns errors if invalid
        return False, []
    
    current_states: Set[str] = {fsa.initial_state}
    trace = [fsa.initial_state]
    
    for symbol in string:
        if symbol not in set(fsa.alphabet):
            return False, trace
        
        next_states = set()
        for state in current_states:
            for t in fsa.transitions:
                if t.from_state == state and t.symbol == symbol:
                    next_states.add(t.to_state)
        
        if not next_states:
            return False, trace
        
        current_states = next_states
        trace.append(list(current_states)[0] if len(current_states) == 1 
                     else f"{{{','.join(sorted(current_states))}}}")
    
    accepted = any(state in fsa.accept_states for state in current_states)
    return accepted, trace


def fsa_accepts(fsa: FSA, string: str) -> bool:
    """Check if FSA accepts string. Leverages accepts_string from validation."""
    return len(accepts_string(fsa, string)) == 0


def _fsas_differ_on_string(fsa1: FSA, fsa2: FSA, string: str) -> bool:
    """Check if FSAs differ on string. Leverages fsas_accept_same_string from validation."""
    return len(fsas_accept_same_string(fsa1, fsa2, string)) > 0


# =============================================================================
# Core Analysis Functions
# =============================================================================

def generate_difference_strings(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10
) -> List[DifferenceString]:
    """Generate strings demonstrating differences between FSAs."""
    differences: List[DifferenceString] = []
    
    # Validate using is_valid_fsa
    if is_valid_fsa(student_fsa) or is_valid_fsa(expected_fsa):
        return differences
    
    alphabet = list(set(student_fsa.alphabet) | set(expected_fsa.alphabet))
    
    # Test empty string using fsas_accept_same_string
    if _fsas_differ_on_string(student_fsa, expected_fsa, ""):
        differences.append(DifferenceString(
            string="ε (empty string)",
            student_accepts=fsa_accepts(student_fsa, ""),
            expected_accepts=fsa_accepts(expected_fsa, ""),
            student_trace=trace_string(student_fsa, "")[1],
            expected_trace=trace_string(expected_fsa, "")[1]
        ))
    
    # Test strings using fsas_accept_same_string
    for length in range(1, max_length + 1):
        if len(differences) >= max_differences:
            break
        for symbols in product(alphabet, repeat=length):
            if len(differences) >= max_differences:
                break
            string = ''.join(symbols)
            if _fsas_differ_on_string(student_fsa, expected_fsa, string):
                differences.append(DifferenceString(
                    string=string,
                    student_accepts=fsa_accepts(student_fsa, string),
                    expected_accepts=fsa_accepts(expected_fsa, string),
                    student_trace=trace_string(student_fsa, string)[1],
                    expected_trace=trace_string(expected_fsa, string)[1]
                ))
    
    return differences


def identify_state_errors(
    student_fsa: FSA,
    expected_fsa: FSA,
    difference_strings: List[DifferenceString]
) -> List[StateError]:
    """Identify state-level errors using find_unreachable_states and find_dead_states."""
    state_errors: List[StateError] = []
    seen_states: Set[str] = set()
    
    # Analyze acceptance errors from difference strings
    for diff in difference_strings:
        if not diff.student_trace:
            continue
        final_state = diff.student_trace[-1]
        if final_state and final_state not in seen_states:
            if diff.expected_accepts and not diff.student_accepts:
                if final_state in student_fsa.states and final_state not in student_fsa.accept_states:
                    state_errors.append(StateError(
                        state_id=final_state,
                        error_type="should_be_accepting",
                        example_string=diff.string
                    ))
                    seen_states.add(final_state)
            elif not diff.expected_accepts and diff.student_accepts:
                if final_state in student_fsa.accept_states:
                    state_errors.append(StateError(
                        state_id=final_state,
                        error_type="should_not_be_accepting",
                        example_string=diff.string
                    ))
                    seen_states.add(final_state)
    
    # Use find_unreachable_states from validation
    for error in find_unreachable_states(student_fsa):
        if error.highlight and error.highlight.state_id:
            state_errors.append(StateError(
                state_id=error.highlight.state_id,
                error_type="unreachable"
            ))
    
    # Use find_dead_states from validation
    for error in find_dead_states(student_fsa):
        if error.highlight and error.highlight.state_id:
            if error.highlight.state_id not in seen_states:
                state_errors.append(StateError(
                    state_id=error.highlight.state_id,
                    error_type="dead"
                ))
    
    return state_errors


def identify_transition_errors(
    student_fsa: FSA,
    expected_fsa: FSA,
    difference_strings: List[DifferenceString]
) -> List[TransitionError]:
    """Identify transition-level errors by analyzing traces."""
    transition_errors: List[TransitionError] = []
    seen_transitions: Set[Tuple[str, str]] = set()
    
    # Build transition maps
    student_trans = {(t.from_state, t.symbol): t.to_state for t in student_fsa.transitions}
    expected_trans = {(t.from_state, t.symbol): t.to_state for t in expected_fsa.transitions}
    
    # Analyze traces for divergence
    for diff in difference_strings:
        if not diff.student_trace or not diff.expected_trace:
            continue
        string = diff.string if diff.string != "ε (empty string)" else ""
        min_len = min(len(diff.student_trace), len(diff.expected_trace))
        
        for i in range(min_len):
            if diff.student_trace[i] != diff.expected_trace[i] and i > 0:
                prev_state = diff.student_trace[i - 1]
                symbol = string[i - 1] if i - 1 < len(string) else ""
                key = (prev_state, symbol)
                if key not in seen_transitions and symbol:
                    student_dest = student_trans.get(key)
                    expected_dest = expected_trans.get(key)
                    if student_dest and expected_dest and student_dest != expected_dest:
                        transition_errors.append(TransitionError(
                            from_state=prev_state,
                            symbol=symbol,
                            actual_to_state=student_dest,
                            expected_to_state=expected_dest,
                            error_type="wrong_destination",
                            example_string=diff.string
                        ))
                        seen_transitions.add(key)
                break
    
    # Check missing transitions
    alphabet = set(student_fsa.alphabet) | set(expected_fsa.alphabet)
    for state in student_fsa.states:
        for symbol in alphabet:
            key = (state, symbol)
            if expected_trans.get(key) and not student_trans.get(key) and key not in seen_transitions:
                transition_errors.append(TransitionError(
                    from_state=state,
                    symbol=symbol,
                    actual_to_state=None,
                    expected_to_state=expected_trans[key],
                    error_type="missing",
                    example_string=_find_example_for_transition(student_fsa, state, symbol)
                ))
                seen_transitions.add(key)
    
    return transition_errors


def _find_example_for_transition(fsa: FSA, target_state: str, symbol: str) -> Optional[str]:
    """Find example string reaching target_state then needing symbol."""
    if target_state == fsa.initial_state:
        return symbol
    
    visited = {fsa.initial_state: ""}
    queue = deque([fsa.initial_state])
    
    while queue:
        state = queue.popleft()
        for t in fsa.transitions:
            if t.from_state == state and t.to_state not in visited:
                visited[t.to_state] = visited[state] + t.symbol
                queue.append(t.to_state)
                if t.to_state == target_state:
                    return visited[target_state] + symbol
    return None


# =============================================================================
# Main Pipeline Functions
# =============================================================================

def analyze_fsa_correction(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10,
    check_isomorphism: bool = True
) -> CorrectionResult:
    """
    Main pipeline: Analyze student FSA against expected FSA.
    
    Leverages validation functions:
    - is_valid_fsa, is_deterministic, is_complete
    - find_unreachable_states, find_dead_states
    - accepts_string, fsas_accept_same_string, fsas_accept_same_language
    - are_isomorphic, get_structured_info_of_fsa
    """
    result = CorrectionResult()
    
    # Validate using is_valid_fsa
    student_errors = is_valid_fsa(student_fsa)
    if student_errors:
        result.validation_errors = student_errors
        result.is_equivalent = False
        result.summary = "Student FSA has structural errors that must be fixed first"
        return result
    
    expected_errors = is_valid_fsa(expected_fsa)
    if expected_errors:
        result.validation_errors = expected_errors
        result.is_equivalent = False
        result.summary = "Expected FSA has structural errors (internal error)"
        return result
    
    # Get structural info using get_structured_info_of_fsa
    result.structural_info = get_structured_info_of_fsa(student_fsa)
    
    # Check equivalence using fsas_accept_same_language (minimization + isomorphism)
    if check_isomorphism:
        try:
            equiv_errors = fsas_accept_same_language(student_fsa, expected_fsa)
            if not equiv_errors:
                result.is_equivalent = True
                result.summary = "FSAs accept the same language (verified via minimization and isomorphism)"
                return result
            result.isomorphism_errors = equiv_errors
        except Exception:
            pass
    
    # Generate difference strings
    result.difference_strings = generate_difference_strings(
        student_fsa, expected_fsa, max_length, max_differences
    )
    
    if not result.difference_strings and not result.isomorphism_errors:
        result.is_equivalent = True
        result.summary = f"FSAs accept the same language (up to strings of length {max_length})"
        return result
    
    result.is_equivalent = False
    
    # Identify errors using validation functions
    result.state_errors = identify_state_errors(student_fsa, expected_fsa, result.difference_strings)
    result.transition_errors = identify_transition_errors(student_fsa, expected_fsa, result.difference_strings)
    
    # Generate summary
    num_diffs = len(result.difference_strings)
    should_accept = sum(1 for d in result.difference_strings if d.difference_type == "should_accept")
    should_reject = num_diffs - should_accept
    
    parts = []
    if should_accept:
        parts.append(f"{should_accept} string(s) incorrectly rejected")
    if should_reject:
        parts.append(f"{should_reject} string(s) incorrectly accepted")
    if result.state_errors:
        parts.append(f"{len(result.state_errors)} state issue(s)")
    if result.transition_errors:
        parts.append(f"{len(result.transition_errors)} transition issue(s)")
    if result.isomorphism_errors:
        parts.append(f"{len(result.isomorphism_errors)} structural difference(s)")
    if result.structural_info:
        if result.structural_info.unreachable_states:
            parts.append(f"{len(result.structural_info.unreachable_states)} unreachable state(s)")
        if result.structural_info.dead_states:
            parts.append(f"{len(result.structural_info.dead_states)} dead state(s)")
    
    result.summary = "; ".join(parts) if parts else "Languages differ"
    return result


def get_correction_feedback(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10,
    check_isomorphism: bool = True
) -> dict:
    """Returns correction analysis as dict (uses model_dump)."""
    result = analyze_fsa_correction(student_fsa, expected_fsa, max_length, max_differences, check_isomorphism)
    return result.model_dump()


def get_fsa_feedback(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10,
    check_isomorphism: bool = True
) -> FSAFeedback:
    """Returns structured FSAFeedback schema (recommended for UI)."""
    result = analyze_fsa_correction(student_fsa, expected_fsa, max_length, max_differences, check_isomorphism)
    return result.to_fsa_feedback()


def check_fsa_properties(fsa: FSA) -> dict:
    """
    Get FSA properties using validation functions.
    Uses is_valid_fsa, is_deterministic, is_complete, find_unreachable_states,
    find_dead_states, get_structured_info_of_fsa.
    """
    result = {
        "is_valid": True,
        "is_deterministic": True,
        "is_complete": True,
        "validation_errors": [],
        "determinism_errors": [],
        "completeness_errors": [],
        "unreachable_states": [],
        "dead_states": [],
        "structural_info": None
    }
    
    validation_errors = is_valid_fsa(fsa)
    if validation_errors:
        result["is_valid"] = False
        result["validation_errors"] = [e.model_dump() for e in validation_errors]
        return result
    
    det_errors = is_deterministic(fsa)
    result["is_deterministic"] = len(det_errors) == 0
    result["determinism_errors"] = [e.model_dump() for e in det_errors]
    
    if result["is_deterministic"]:
        comp_errors = is_complete(fsa)
        result["is_complete"] = len(comp_errors) == 0
        result["completeness_errors"] = [e.model_dump() for e in comp_errors]
    else:
        result["is_complete"] = False
    
    result["unreachable_states"] = [
        e.highlight.state_id for e in find_unreachable_states(fsa)
        if e.highlight and e.highlight.state_id
    ]
    result["dead_states"] = [
        e.highlight.state_id for e in find_dead_states(fsa)
        if e.highlight and e.highlight.state_id
    ]
    result["structural_info"] = get_structured_info_of_fsa(fsa).model_dump()
    
    return result


def quick_equivalence_check(
    student_fsa: FSA,
    expected_fsa: FSA
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Quick equivalence check using fsas_accept_same_language."""
    if is_valid_fsa(student_fsa) or is_valid_fsa(expected_fsa):
        return False, None, None
    
    if not fsas_accept_same_language(student_fsa, expected_fsa):
        return True, None, None
    
    differences = generate_difference_strings(student_fsa, expected_fsa, max_length=5, max_differences=1)
    if differences:
        return False, differences[0].string, differences[0].difference_type
    
    return False, None, None
