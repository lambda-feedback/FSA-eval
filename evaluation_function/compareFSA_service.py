# dummy file for shimmy tests

import sys
import json
from typing import Any
from .evaluation import evaluation_function
from lf_toolkit.evaluation import Params

def main():
    for line in sys.stdin:
        try:
            # Parse request from Shimmy
            req = json.loads(line)
            response: Any = req["input"]["response"]
            answer: Any = req["input"]["answer"]
            params_dict: dict = req["input"].get("params", {})
            params = Params(params_dict)

            # Call your evaluation function
            result = evaluation_function(response, answer, params)

            # Convert LFResult to JSON
            resp = {
                "output": {
                    "is_correct": result.is_correct,
                    "feedback_items": result.feedback_items
                }
            }
            print(json.dumps(resp), flush=True)

        except Exception as e:
            # Always return JSON even on error
            resp = {"output": {"is_correct": False, "feedback_items": [("error", str(e))]}}
            print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    main()
