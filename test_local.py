"""
Local test script for FSA evaluation function.
Bypasses Lambda/API Gateway to test the evaluation function directly.
Tests cover: basic equivalence, NFAs, epsilon transitions, edge cases, and validation errors.
"""

from evaluation_function.evaluation import evaluation_function
from lf_toolkit.evaluation import Params


def run_test(test_num, test_name, response_data, answer_data, params=None):
    """Helper function to run a test case"""
    print("=" * 70)
    print(f"Test {test_num}: {test_name}")
    print("=" * 70)
    
    if params is None:
        params = Params()
    
    try:
        result = evaluation_function(response_data, answer_data, params)
        result_dict = result.to_dict()
        status = "[PASS]" if result_dict['is_correct'] else "[FAIL]"
        print(f"{status} Result: {result_dict['is_correct']}")
        print(f"  Feedback: {result_dict['feedback']}")
        if 'command' in result_dict:
            print(f"  Command: {result_dict['command']}")
        print()
        return result_dict
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        print()
        return None


# =============================================================================
# BASIC TESTS
# =============================================================================

# Test 1: Equivalent DFAs with different state names (should pass)
run_test(
    1, "Equivalent DFAs - accepts a(a|b)*",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": ["q0|a|q1", "q1|a|q1", "q1|b|q1"],
        "initial_state": "q0",
        "accept_states": ["q1"]
    },
    answer_data={
        "states": ["s0", "s1"],
        "alphabet": ["a", "b"],
        "transitions": ["s0|a|s1", "s1|a|s1", "s1|b|s1"],
        "initial_state": "s0",
        "accept_states": ["s1"]
    }
)

# Test 2: Different Languages (should fail)
run_test(
    2, "Different Languages - incomplete transitions",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": ["q0|a|q1", "q1|b|q1"],  # Missing transitions
        "initial_state": "q0",
        "accept_states": ["q1"]
    },
    answer_data={
        "states": ["s0", "s1"],
        "alphabet": ["a", "b"],
        "transitions": ["s0|a|s1", "s1|a|s1", "s1|b|s1"],
        "initial_state": "s0",
        "accept_states": ["s1"]
    }
)

# Test 3: Simple FSA - accepts exactly 'a'
run_test(
    3, "Simple DFA - accepts exactly 'a'",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1", "q0|b|q2",
            "q1|a|q2", "q1|b|q2",
            "q2|a|q2", "q2|b|q2"
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    },
    answer_data={
        "states": ["s0", "s1", "s2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s1", "s0|b|s2",
            "s1|a|s2", "s1|b|s2",
            "s2|a|s2", "s2|b|s2"
        ],
        "initial_state": "s0",
        "accept_states": ["s1"]
    }
)

# =============================================================================
# EPSILON TRANSITION TESTS (ε-NFA)
# =============================================================================

# Test 4: ε-NFA that accepts strings with 'ab'
run_test(
    4, "ε-NFA - accepts strings containing 'ab'",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q0", "q0|b|q0",  # Stay in q0
            "q0|a|q1",              # Go to q1 on 'a'
            "q1|b|q2",              # Go to q2 on 'b'
            "q2|a|q2", "q2|b|q2"   # Stay in q2 (accept)
        ],
        "initial_state": "q0",
        "accept_states": ["q2"]
    },
    answer_data={
        "states": ["s0", "s1", "s2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s0", "s0|b|s0",
            "s0|a|s1",
            "s1|b|s2",
            "s2|a|s2", "s2|b|s2"
        ],
        "initial_state": "s0",
        "accept_states": ["s2"]
    }
)

# Test 5: ε-NFA with epsilon transitions
run_test(
    5, "ε-NFA with epsilon transitions - (a|b)*",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|ε|q1",     # Epsilon to q1
            "q1|a|q2",     # a to q2
            "q1|b|q2",     # b to q2
            "q2|ε|q1",     # Epsilon back to q1
        ],
        "initial_state": "q0",
        "accept_states": ["q0", "q2"]
    },
    answer_data={
        "states": ["s0"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s0",
            "s0|b|s0"
        ],
        "initial_state": "s0",
        "accept_states": ["s0"]
    }
)

# =============================================================================
# NFA TESTS (Non-deterministic)
# =============================================================================

# Test 6: NFA with multiple transitions on same symbol
run_test(
    6, "NFA - multiple transitions on 'a'",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1",     # Non-deterministic on 'a'
            "q0|a|q2",     # Two transitions on 'a'
            "q1|b|q1",
            "q2|b|q2"
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    },
    answer_data={
        "states": ["s0", "s1"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s1",
            "s1|b|s1"
        ],
        "initial_state": "s0",
        "accept_states": ["s1"]
    }
)

# =============================================================================
# EDGE CASES
# =============================================================================

# Test 7: Empty language (no accept states)
run_test(
    7, "Empty Language - no accept states",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1",
            "q1|a|q1",
            "q1|b|q1"
        ],
        "initial_state": "q0",
        "accept_states": []  # No accept states
    },
    answer_data={
        "states": ["s0", "s1"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s1",
            "s1|a|s1",
            "s1|b|s1"
        ],
        "initial_state": "s0",
        "accept_states": []
    }
)

# Test 8: Accepts empty string (initial state is accept state)
run_test(
    8, "Accepts empty string - ε ∈ L",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a"],
        "transitions": [
            "q0|a|q1",
            "q1|a|q1"
        ],
        "initial_state": "q0",
        "accept_states": ["q0", "q1"]  # Initial state is accepting
    },
    answer_data={
        "states": ["s0", "s1"],
        "alphabet": ["a"],
        "transitions": [
            "s0|a|s1",
            "s1|a|s1"
        ],
        "initial_state": "s0",
        "accept_states": ["s0", "s1"]
    }
)

# Test 9: Single state FSA (accepts everything)
run_test(
    9, "Single State DFA - accepts all strings",
    response_data={
        "states": ["q0"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q0",
            "q0|b|q0"
        ],
        "initial_state": "q0",
        "accept_states": ["q0"]
    },
    answer_data={
        "states": ["s0"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s0",
            "s0|b|s0"
        ],
        "initial_state": "s0",
        "accept_states": ["s0"]
    }
)

# Test 10: Complex DFA - even number of 'a's
run_test(
    10, "Complex DFA - even number of 'a's",
    response_data={
        "states": ["even", "odd"],
        "alphabet": ["a", "b"],
        "transitions": [
            "even|a|odd",
            "odd|a|even",
            "even|b|even",
            "odd|b|odd"
        ],
        "initial_state": "even",
        "accept_states": ["even"]
    },
    answer_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1",
            "q1|a|q0",
            "q0|b|q0",
            "q1|b|q1"
        ],
        "initial_state": "q0",
        "accept_states": ["q0"]
    }
)

# Test 11: Non-minimal DFA (has redundant states)
run_test(
    11, "Non-minimal DFA - redundant states",
    response_data={
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1",
            "q0|b|q2",
            "q1|a|q1", "q1|b|q1",
            "q2|a|q3", "q2|b|q3",
            "q3|a|q3", "q3|b|q3"
        ],
        "initial_state": "q0",
        "accept_states": ["q1", "q2"]  # q2 and q3 behave similarly
    },
    answer_data={
        "states": ["s0", "s1", "s2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s1",
            "s0|b|s1",
            "s1|a|s1", "s1|b|s1",
            "s2|a|s2", "s2|b|s2"
        ],
        "initial_state": "s0",
        "accept_states": ["s1"]
    }
)

# Test 12: Unreachable states
run_test(
    12, "DFA with unreachable states",
    response_data={
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1",
            "q0|b|q1",
            "q1|a|q1", "q1|b|q1",
            "q2|a|q3",  # q2 and q3 are unreachable
            "q3|a|q3", "q3|b|q3"
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    },
    answer_data={
        "states": ["s0", "s1"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s1",
            "s0|b|s1",
            "s1|a|s1", "s1|b|s1"
        ],
        "initial_state": "s0",
        "accept_states": ["s1"]
    }
)

# =============================================================================
# COMPLEX PATTERN TESTS
# =============================================================================

# Test 13: Strings ending with 'ab'
run_test(
    13, "Strings ending with 'ab'",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "q0|a|q1", "q0|b|q0",
            "q1|a|q1", "q1|b|q2",
            "q2|a|q1", "q2|b|q0"
        ],
        "initial_state": "q0",
        "accept_states": ["q2"]
    },
    answer_data={
        "states": ["s0", "s1", "s2"],
        "alphabet": ["a", "b"],
        "transitions": [
            "s0|a|s1", "s0|b|s0",
            "s1|a|s1", "s1|b|s2",
            "s2|a|s1", "s2|b|s0"
        ],
        "initial_state": "s0",
        "accept_states": ["s2"]
    }
)

# Test 14: Binary numbers divisible by 3
run_test(
    14, "Binary numbers divisible by 3",
    response_data={
        "states": ["r0", "r1", "r2"],
        "alphabet": ["0", "1"],
        "transitions": [
            "r0|0|r0", "r0|1|r1",
            "r1|0|r2", "r1|1|r0",
            "r2|0|r1", "r2|1|r2"
        ],
        "initial_state": "r0",
        "accept_states": ["r0"]
    },
    answer_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["0", "1"],
        "transitions": [
            "q0|0|q0", "q0|1|q1",
            "q1|0|q2", "q1|1|q0",
            "q2|0|q1", "q2|1|q2"
        ],
        "initial_state": "q0",
        "accept_states": ["q0"]
    }
)

# Test 15: Wrong answer for divisibility by 3 (should fail)
run_test(
    15, "Wrong divisibility by 3 (should fail)",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "transitions": [
            "q0|0|q0", "q0|1|q1",
            "q1|0|q1", "q1|1|q0"
        ],
        "initial_state": "q0",
        "accept_states": ["q0"]  # This is wrong for div by 3
    },
    answer_data={
        "states": ["r0", "r1", "r2"],
        "alphabet": ["0", "1"],
        "transitions": [
            "r0|0|r0", "r0|1|r1",
            "r1|0|r2", "r1|1|r0",
            "r2|0|r1", "r2|1|r2"
        ],
        "initial_state": "r0",
        "accept_states": ["r0"]
    }
)

# =============================================================================
# PREVIEW FUNCTION TESTS
# =============================================================================

print("\n")
print("#" * 70)
print("# PREVIEW FUNCTION TESTS (Pre-submission Validation)")
print("#" * 70)
print()

from evaluation_function.preview import preview_function
from lf_toolkit.preview import Params as PreviewParams


def run_preview_test(test_num, test_name, response_data, params=None):
    """Helper function to run a preview test case"""
    print("=" * 70)
    print(f"Preview Test {test_num}: {test_name}")
    print("=" * 70)
    
    if params is None:
        params = PreviewParams()
    
    try:
        result = preview_function(response_data, params)
        
        # Handle both Result object and dict
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {'preview': result}
        
        # Extract preview data
        preview_data = result_dict.get('preview', {})
        if hasattr(preview_data, 'model_dump'):
            preview_data = preview_data.model_dump()
        
        sympy_data = preview_data.get('sympy', {})
        is_valid = sympy_data.get('valid', False) if sympy_data else False
        
        status = "[VALID]" if is_valid else "[INVALID]"
        print(f"{status} FSA is valid: {is_valid}")
        
        feedback = preview_data.get('feedback', '')
        if feedback:
            print(f"  Feedback:\n    {str(feedback).replace(chr(10), chr(10) + '    ')}")
        
        if sympy_data and sympy_data.get('errors'):
            print(f"  Errors: {len(sympy_data['errors'])}")
        if sympy_data and sympy_data.get('warnings'):
            print(f"  Warnings: {len(sympy_data['warnings'])}")
        
        print()
        return result_dict
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        print()
        return None


# Preview Test P1: Valid DFA
run_preview_test(
    "P1", "Valid DFA - should pass",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "b"}
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    }
)

# Preview Test P2: Invalid initial state
run_preview_test(
    "P2", "Invalid initial state - should fail",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"}
        ],
        "initial_state": "q99",  # Does not exist
        "accept_states": ["q1"]
    }
)

# Preview Test P3: Invalid accept state
run_preview_test(
    "P3", "Invalid accept state - should fail",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"}
        ],
        "initial_state": "q0",
        "accept_states": ["q99"]  # Does not exist
    }
)

# Preview Test P4: Transition references non-existent state
run_preview_test(
    "P4", "Transition to non-existent state - should fail",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q99", "symbol": "a"}  # q99 doesn't exist
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    }
)

# Preview Test P5: Transition with invalid symbol
run_preview_test(
    "P5", "Transition with symbol not in alphabet - should fail",
    response_data={
        "states": ["q0", "q1"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "c"}  # 'c' not in alphabet
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    }
)

# Preview Test P6: FSA with unreachable states (warning)
run_preview_test(
    "P6", "FSA with unreachable states - valid with warning",
    response_data={
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            {"from_state": "q2", "to_state": "q3", "symbol": "a"}  # q2, q3 unreachable
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    }
)

# Preview Test P7: FSA with dead states (warning)
run_preview_test(
    "P7", "FSA with dead states - valid with warning",
    response_data={
        "states": ["q0", "q1", "dead"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q0", "to_state": "dead", "symbol": "b"},
            {"from_state": "q1", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            {"from_state": "dead", "to_state": "dead", "symbol": "a"},
            {"from_state": "dead", "to_state": "dead", "symbol": "b"}
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]  # "dead" can never reach accept
    }
)

# Preview Test P8: Not a valid FSA structure (parse error)
run_preview_test(
    "P8", "Invalid structure - missing required fields",
    response_data={
        "states": ["q0"],
        # Missing alphabet, transitions, initial_state, accept_states
    }
)

# Preview Test P9: Empty states list
run_preview_test(
    "P9", "Empty states list - should fail",
    response_data={
        "states": [],
        "alphabet": ["a"],
        "transitions": [],
        "initial_state": "q0",
        "accept_states": []
    }
)

# Preview Test P10: NFA (valid, non-deterministic)
run_preview_test(
    "P10", "Valid NFA - non-deterministic allowed",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q0", "to_state": "q2", "symbol": "a"},  # Non-deterministic
            {"from_state": "q1", "to_state": "q1", "symbol": "b"},
            {"from_state": "q2", "to_state": "q2", "symbol": "b"}
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    }
)

# Preview Test P11: Epsilon transitions
run_preview_test(
    "P11", "Epsilon NFA - epsilon transitions",
    response_data={
        "states": ["q0", "q1", "q2"],
        "alphabet": ["a", "b"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q2", "symbol": "b"}
        ],
        "initial_state": "q0",
        "accept_states": ["q2"]
    }
)

# Preview Test P12: Null/None response
run_preview_test(
    "P12", "Null response - should fail gracefully",
    response_data=None
)

# Preview Test P13: String response (JSON)
import json
run_preview_test(
    "P13", "JSON string response - should parse",
    response_data=json.dumps({
        "states": ["q0", "q1"],
        "alphabet": ["a"],
        "transitions": [
            {"from_state": "q0", "to_state": "q1", "symbol": "a"},
            {"from_state": "q1", "to_state": "q1", "symbol": "a"}
        ],
        "initial_state": "q0",
        "accept_states": ["q1"]
    })
)

print("=" * 70)
print("ALL EVALUATION + PREVIEW TESTS COMPLETED!")
print("=" * 70)
print("\nRun with: python test_local.py")
print("\nEvaluation tests cover:")
print("  - Basic DFA equivalence")
print("  - Non-deterministic FSAs (NFAs)")
print("  - Epsilon transitions")
print("  - Edge cases (empty language, single state, unreachable states)")
print("  - Complex patterns (ending with 'ab', divisibility by 3)")
print("\nPreview tests cover:")
print("  - Valid FSA validation")
print("  - Invalid initial/accept states")
print("  - Invalid transitions (state/symbol)")
print("  - Unreachable and dead states (warnings)")
print("  - Parse errors (invalid structure, null input)")
print("  - NFA and epsilon transition support")
print("  - JSON string input parsing")
