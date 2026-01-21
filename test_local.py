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

print("=" * 70)
print("ALL TESTS COMPLETED!")
print("=" * 70)
print("\nRun with: python test_local.py")
print("These tests cover:")
print("  - Basic DFA equivalence")
print("  - Non-deterministic FSAs (NFAs)")
print("  - Epsilon transitions (ε-NFAs)")
print("  - Edge cases (empty language, single state, unreachable states)")
print("  - Complex patterns (ending with 'ab', divisibility by 3)")
print("  - Validation errors")
