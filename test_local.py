"""
Local test script for FSA evaluation function.
Bypasses Lambda/API Gateway to test the evaluation function directly.
"""

from evaluation_function.evaluation import evaluation_function
from lf_toolkit.evaluation import Params

# Test Case 1: Equivalent DFAs (should pass)
print("=" * 60)
print("Test 1: Equivalent DFAs")
print("=" * 60)

response_data = {
    "states": ["q0", "q1"],
    "alphabet": ["a", "b"],
    "transitions": ["q0|a|q1", "q1|a|q1", "q1|b|q1"],
    "initial_state": "q0",
    "accept_states": ["q1"]
}

answer_data = {
    "states": ["s0", "s1"],
    "alphabet": ["a", "b"],
    "transitions": ["s0|a|s1", "s1|a|s1", "s1|b|s1"],
    "initial_state": "s0",
    "accept_states": ["s1"]
}

try:
    result = evaluation_function(response_data, answer_data, Params())
    print(f"Result: {result.to_dict()}")
    print()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test Case 2: Different Languages (should fail)
print("=" * 60)
print("Test 2: Different Languages")
print("=" * 60)

response_data_2 = {
    "states": ["q0", "q1"],
    "alphabet": ["a", "b"],
    "transitions": ["q0|a|q1", "q1|b|q1"],  # Missing some transitions
    "initial_state": "q0",
    "accept_states": ["q1"]
}

try:
    result = evaluation_function(response_data_2, answer_data, Params())
    print(f"Result: {result.to_dict()}")
    print()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test Case 3: Simple accepting FSA
print("=" * 60)
print("Test 3: Simple FSA - accepts 'a'")
print("=" * 60)

simple_response = {
    "states": ["q0", "q1", "q2"],
    "alphabet": ["a", "b"],
    "transitions": [
        "q0|a|q1",
        "q0|b|q2",
        "q1|a|q2",
        "q1|b|q2",
        "q2|a|q2",
        "q2|b|q2"
    ],
    "initial_state": "q0",
    "accept_states": ["q1"]
}

simple_answer = {
    "states": ["s0", "s1", "s2"],
    "alphabet": ["a", "b"],
    "transitions": [
        "s0|a|s1",
        "s0|b|s2",
        "s1|a|s2",
        "s1|b|s2",
        "s2|a|s2",
        "s2|b|s2"
    ],
    "initial_state": "s0",
    "accept_states": ["s1"]
}

try:
    result = evaluation_function(simple_response, simple_answer, Params())
    print(f"Result: {result.to_dict()}")
    print()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print()

print("=" * 60)
print("Tests completed!")
print("=" * 60)
