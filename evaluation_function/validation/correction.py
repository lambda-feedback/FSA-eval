"""
FSA Correction Module

Generates diagnostic information for comparing student FSA against expected language:
- Generates strings that show differences between student FSA and expected language
- Identifies specific states/transitions causing errors
"""

from itertools import product
from typing import List, Optional, Tuple, Dict, Set
from collections import deque

from ..schemas import FSA, ValidationError, ErrorCode, ElementHighlight
from ..schemas.result import LanguageComparison, TestResult
from .validation import (
    is_valid_fsa,
    is_deterministic,
    accepts_string,
    find_unreachable_states,
    find_dead_states,
)


class DifferenceString:
    """Represents a string that demonstrates a difference between two FSAs."""
    
    def __init__(
        self,
        string: str,
        student_accepts: bool,
        expected_accepts: bool,
        student_trace: Optional[List[str]] = None,
        expected_trace: Optional[List[str]] = None
    ):
        self.string = string
        self.student_accepts = student_accepts
        self.expected_accepts = expected_accepts
        self.student_trace = student_trace or []
        self.expected_trace = expected_trace or []
    
    @property
    def difference_type(self) -> str:
        """Returns 'should_accept' or 'should_reject'."""
        return "should_accept" if self.expected_accepts else "should_reject"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "string": self.string,
            "student_accepts": self.student_accepts,
            "expected_accepts": self.expected_accepts,
            "difference_type": self.difference_type,
            "student_trace": self.student_trace,
            "expected_trace": self.expected_trace
        }


class TransitionError:
    """Represents an error in a specific transition."""
    
    def __init__(
        self,
        from_state: str,
        symbol: str,
        actual_to_state: Optional[str],
        expected_to_state: Optional[str],
        error_type: str,
        example_string: Optional[str] = None
    ):
        self.from_state = from_state
        self.symbol = symbol
        self.actual_to_state = actual_to_state
        self.expected_to_state = expected_to_state
        self.error_type = error_type  # "wrong_destination", "missing", "extra"
        self.example_string = example_string
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "from_state": self.from_state,
            "symbol": self.symbol,
            "actual_to_state": self.actual_to_state,
            "expected_to_state": self.expected_to_state,
            "error_type": self.error_type,
            "example_string": self.example_string
        }
    
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
            suggestion = f"Remove this transition or redirect it appropriately"
        
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


class StateError:
    """Represents an error related to a specific state."""
    
    def __init__(
        self,
        state_id: str,
        error_type: str,  # "should_be_accepting", "should_not_be_accepting", "unreachable", "dead"
        example_string: Optional[str] = None
    ):
        self.state_id = state_id
        self.error_type = error_type
        self.example_string = example_string
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "state_id": self.state_id,
            "error_type": self.error_type,
            "example_string": self.example_string
        }
    
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


class CorrectionResult:
    """Complete result of FSA correction analysis."""
    
    def __init__(self):
        self.difference_strings: List[DifferenceString] = []
        self.transition_errors: List[TransitionError] = []
        self.state_errors: List[StateError] = []
        self.validation_errors: List[ValidationError] = []
        self.is_equivalent: bool = True
        self.summary: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_equivalent": self.is_equivalent,
            "summary": self.summary,
            "difference_strings": [ds.to_dict() for ds in self.difference_strings],
            "transition_errors": [te.to_dict() for te in self.transition_errors],
            "state_errors": [se.to_dict() for se in self.state_errors],
            "validation_errors": [ve.model_dump() for ve in self.validation_errors]
        }
    
    def get_all_validation_errors(self) -> List[ValidationError]:
        """Get all errors as ValidationError objects for UI highlighting."""
        errors = list(self.validation_errors)
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
        results = []
        for diff in self.difference_strings:
            results.append(TestResult(
                input=diff.string,
                expected=diff.expected_accepts,
                actual=diff.student_accepts,
                passed=diff.student_accepts == diff.expected_accepts,
                trace=diff.student_trace
            ))
        return results


def trace_string(fsa: FSA, string: str) -> Tuple[bool, List[str]]:
    """
    Trace the execution of a string through an FSA.
    Returns (accepted, state_trace) where state_trace is the sequence of states visited.
    
    For NFAs, returns one possible trace if accepted.
    """
    # Check structural validity first
    if is_valid_fsa(fsa):
        return False, []
    
    # For deterministic FSAs
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
        # For deterministic FSA, there's only one next state
        trace.append(list(current_states)[0] if len(current_states) == 1 else f"{{{','.join(sorted(current_states))}}}")
    
    accepted = any(state in fsa.accept_states for state in current_states)
    return accepted, trace


def fsa_accepts(fsa: FSA, string: str) -> bool:
    """Check if an FSA accepts a string. Returns True if accepted, False otherwise."""
    errors = accepts_string(fsa, string)
    return len(errors) == 0


def generate_difference_strings(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10
) -> List[DifferenceString]:
    """
    Generate strings that demonstrate differences between student and expected FSAs.
    
    Args:
        student_fsa: The student's FSA
        expected_fsa: The expected/reference FSA
        max_length: Maximum length of strings to test
        max_differences: Maximum number of difference strings to return
    
    Returns:
        List of DifferenceString objects showing where the FSAs differ
    """
    differences: List[DifferenceString] = []
    
    # Validate both FSAs first
    student_errors = is_valid_fsa(student_fsa)
    expected_errors = is_valid_fsa(expected_fsa)
    
    if student_errors or expected_errors:
        return differences
    
    # Use the union of alphabets for comprehensive testing
    alphabet = list(set(student_fsa.alphabet) | set(expected_fsa.alphabet))
    
    # Test empty string first
    student_accepts_empty = fsa_accepts(student_fsa, "")
    expected_accepts_empty = fsa_accepts(expected_fsa, "")
    
    if student_accepts_empty != expected_accepts_empty:
        student_trace = trace_string(student_fsa, "")[1]
        expected_trace = trace_string(expected_fsa, "")[1]
        differences.append(DifferenceString(
            string="ε (empty string)",
            student_accepts=student_accepts_empty,
            expected_accepts=expected_accepts_empty,
            student_trace=student_trace,
            expected_trace=expected_trace
        ))
    
    # Test strings of increasing length
    for length in range(1, max_length + 1):
        if len(differences) >= max_differences:
            break
        
        for symbols in product(alphabet, repeat=length):
            if len(differences) >= max_differences:
                break
            
            string = ''.join(symbols)
            student_accepts = fsa_accepts(student_fsa, string)
            expected_accepts = fsa_accepts(expected_fsa, string)
            
            if student_accepts != expected_accepts:
                student_accepted, student_trace = trace_string(student_fsa, string)
                expected_accepted, expected_trace = trace_string(expected_fsa, string)
                
                differences.append(DifferenceString(
                    string=string,
                    student_accepts=student_accepts,
                    expected_accepts=expected_accepts,
                    student_trace=student_trace,
                    expected_trace=expected_trace
                ))
    
    return differences


def identify_state_errors(
    student_fsa: FSA,
    expected_fsa: FSA,
    difference_strings: List[DifferenceString]
) -> List[StateError]:
    """
    Identify state-level errors by analyzing difference strings.
    
    Looks for:
    - States that should/shouldn't be accepting
    - Unreachable states
    - Dead states
    """
    state_errors: List[StateError] = []
    seen_states: Set[str] = set()
    
    # Analyze acceptance state errors from difference strings
    for diff in difference_strings:
        if not diff.student_trace:
            continue
        
        # Get the final state(s) from the trace
        final_state = diff.student_trace[-1] if diff.student_trace else None
        
        if final_state and final_state not in seen_states:
            # Check if this is an acceptance issue
            if diff.expected_accepts and not diff.student_accepts:
                # Student rejects but should accept - final state might need to be accepting
                if final_state in student_fsa.states and final_state not in student_fsa.accept_states:
                    state_errors.append(StateError(
                        state_id=final_state,
                        error_type="should_be_accepting",
                        example_string=diff.string
                    ))
                    seen_states.add(final_state)
            elif not diff.expected_accepts and diff.student_accepts:
                # Student accepts but should reject - final state might need to be non-accepting
                if final_state in student_fsa.accept_states:
                    state_errors.append(StateError(
                        state_id=final_state,
                        error_type="should_not_be_accepting",
                        example_string=diff.string
                    ))
                    seen_states.add(final_state)
    
    # Check for unreachable states
    unreachable_errors = find_unreachable_states(student_fsa)
    for error in unreachable_errors:
        if error.highlight and error.highlight.state_id:
            state_errors.append(StateError(
                state_id=error.highlight.state_id,
                error_type="unreachable"
            ))
    
    # Check for dead states
    dead_errors = find_dead_states(student_fsa)
    for error in dead_errors:
        if error.highlight and error.highlight.state_id:
            # Only add if not already identified as another type of error
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
    """
    Identify specific transitions causing errors.
    
    Analyzes the traces to find where student FSA diverges from expected behavior.
    """
    transition_errors: List[TransitionError] = []
    seen_transitions: Set[Tuple[str, str]] = set()
    
    # Build transition maps for both FSAs
    student_transitions: Dict[Tuple[str, str], str] = {}
    expected_transitions: Dict[Tuple[str, str], str] = {}
    
    for t in student_fsa.transitions:
        student_transitions[(t.from_state, t.symbol)] = t.to_state
    
    for t in expected_fsa.transitions:
        expected_transitions[(t.from_state, t.symbol)] = t.to_state
    
    # Analyze traces to find divergence points
    for diff in difference_strings:
        if not diff.student_trace or not diff.expected_trace:
            continue
        
        string = diff.string if diff.string != "ε (empty string)" else ""
        
        # Walk through the traces to find where they diverge
        min_len = min(len(diff.student_trace), len(diff.expected_trace))
        
        for i in range(min_len):
            if diff.student_trace[i] != diff.expected_trace[i]:
                # Found divergence - the previous transition caused it
                if i > 0:
                    prev_state = diff.student_trace[i - 1]
                    symbol = string[i - 1] if i - 1 < len(string) else ""
                    key = (prev_state, symbol)
                    
                    if key not in seen_transitions and symbol:
                        student_dest = student_transitions.get(key)
                        expected_dest = expected_transitions.get(key)
                        
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
    
    # Check for missing transitions in student FSA that exist in expected
    alphabet = set(student_fsa.alphabet) | set(expected_fsa.alphabet)
    for state in student_fsa.states:
        for symbol in alphabet:
            key = (state, symbol)
            student_dest = student_transitions.get(key)
            expected_dest = expected_transitions.get((state, symbol))
            
            if expected_dest and not student_dest and key not in seen_transitions:
                # Find an example string that would use this transition
                example = _find_example_for_transition(student_fsa, state, symbol)
                transition_errors.append(TransitionError(
                    from_state=state,
                    symbol=symbol,
                    actual_to_state=None,
                    expected_to_state=expected_dest,
                    error_type="missing",
                    example_string=example
                ))
                seen_transitions.add(key)
    
    return transition_errors


def _find_example_for_transition(fsa: FSA, target_state: str, symbol: str) -> Optional[str]:
    """Find a string that reaches the target state and then needs the given symbol."""
    # BFS to find a path to the target state
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


def analyze_fsa_correction(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10
) -> CorrectionResult:
    """
    Main pipeline function: Analyze student FSA against expected FSA and identify corrections.
    
    This function:
    1. Validates both FSAs structurally
    2. Generates strings showing language differences
    3. Identifies specific states causing errors
    4. Identifies specific transitions causing errors
    
    Args:
        student_fsa: The student's FSA (assumed to be correctly formatted)
        expected_fsa: The expected/reference FSA
        max_length: Maximum length of test strings
        max_differences: Maximum number of difference strings to generate
    
    Returns:
        CorrectionResult with comprehensive analysis
    """
    result = CorrectionResult()
    
    # Step 1: Validate student FSA structure
    student_validation_errors = is_valid_fsa(student_fsa)
    if student_validation_errors:
        result.validation_errors = student_validation_errors
        result.is_equivalent = False
        result.summary = "Student FSA has structural errors that must be fixed first"
        return result
    
    # Step 2: Validate expected FSA structure
    expected_validation_errors = is_valid_fsa(expected_fsa)
    if expected_validation_errors:
        result.validation_errors = expected_validation_errors
        result.is_equivalent = False
        result.summary = "Expected FSA has structural errors (internal error)"
        return result
    
    # Step 3: Generate difference strings
    result.difference_strings = generate_difference_strings(
        student_fsa, expected_fsa, max_length, max_differences
    )
    
    if not result.difference_strings:
        result.is_equivalent = True
        result.summary = "The FSAs accept the same language (up to strings of length {})".format(max_length)
        return result
    
    result.is_equivalent = False
    
    # Step 4: Identify state errors
    result.state_errors = identify_state_errors(
        student_fsa, expected_fsa, result.difference_strings
    )
    
    # Step 5: Identify transition errors
    result.transition_errors = identify_transition_errors(
        student_fsa, expected_fsa, result.difference_strings
    )
    
    # Step 6: Generate summary
    num_diffs = len(result.difference_strings)
    should_accept = sum(1 for d in result.difference_strings if d.difference_type == "should_accept")
    should_reject = num_diffs - should_accept
    
    summary_parts = []
    if should_accept > 0:
        summary_parts.append(f"{should_accept} string(s) incorrectly rejected")
    if should_reject > 0:
        summary_parts.append(f"{should_reject} string(s) incorrectly accepted")
    
    if result.state_errors:
        summary_parts.append(f"{len(result.state_errors)} state issue(s) identified")
    if result.transition_errors:
        summary_parts.append(f"{len(result.transition_errors)} transition issue(s) identified")
    
    result.summary = "; ".join(summary_parts) if summary_parts else "Languages differ"
    
    return result


def get_correction_feedback(
    student_fsa: FSA,
    expected_fsa: FSA,
    max_length: int = 5,
    max_differences: int = 10
) -> dict:
    """
    Convenience function that returns correction analysis as a dictionary.
    
    This is the main entry point for the correction pipeline.
    
    Args:
        student_fsa: The student's FSA
        expected_fsa: The expected/reference FSA  
        max_length: Maximum length of test strings
        max_differences: Maximum number of difference strings to generate
    
    Returns:
        Dictionary containing:
        - is_equivalent: bool
        - summary: str
        - difference_strings: list of difference details
        - transition_errors: list of transition issues
        - state_errors: list of state issues
        - validation_errors: list of structural errors
    """
    result = analyze_fsa_correction(student_fsa, expected_fsa, max_length, max_differences)
    return result.to_dict()
