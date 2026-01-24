"""
Main entry point for the FSA evaluation function.

Supports two communication modes with shimmy:
1. File-based (recommended for large payloads): shimmy passes input/output file paths as args
2. RPC/IPC (default): Uses lf_toolkit's server for stdio/IPC communication
"""

import sys
import json
from typing import Any, Dict

from lf_toolkit import create_server, run
from lf_toolkit.evaluation import Params, Result as LFResult

from .evaluation import evaluation_function
from .preview import preview_function


def handle_file_based_communication(input_path: str, output_path: str) -> None:
    """
    Handle file-based communication with shimmy.
    
    Reads input JSON from input_path, processes it, and writes result to output_path.
    This is used when shimmy is configured with --interface file.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path to write the output JSON file
    """
    # Read input from file
    with open(input_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    # Extract command and request data
    command = input_data.get('command', 'eval')
    request_id = input_data.get('$id')
    
    # Build response structure
    response_data: Dict[str, Any] = {}
    if request_id is not None:
        response_data['$id'] = request_id
    response_data['command'] = command
    
    try:
        if command == 'eval':
            # Extract evaluation inputs
            response = input_data.get('response')
            answer = input_data.get('answer')
            params_dict = input_data.get('params', {})
            
            # Create params object
            params = Params(**params_dict) if params_dict else Params()
            
            # Call evaluation function
            result = evaluation_function(response, answer, params)
            
            # Convert result to dict
            if hasattr(result, 'to_dict'):
                response_data['result'] = result.to_dict()
            elif isinstance(result, dict):
                response_data['result'] = result
            else:
                response_data['result'] = {'is_correct': False, 'feedback': str(result)}
                
        elif command == 'preview':
            # Extract preview inputs
            response = input_data.get('response')
            params_dict = input_data.get('params', {})
            
            params = Params(**params_dict) if params_dict else Params()
            
            # Call preview function
            result = preview_function(response, params)
            
            if hasattr(result, 'to_dict'):
                response_data['result'] = result.to_dict()
            elif isinstance(result, dict):
                response_data['result'] = result
            else:
                response_data['result'] = {'preview': str(result)}
                
        else:
            response_data['result'] = {
                'is_correct': False,
                'feedback': f'Unknown command: {command}'
            }
            
    except Exception as e:
        response_data['result'] = {
            'is_correct': False,
            'feedback': f'Error processing request: {str(e)}'
        }
    
    # Write output to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, ensure_ascii=False)


def main():
    """
    Run the evaluation function.
    
    Detects communication mode based on command-line arguments:
    - If 2+ args provided: File-based communication (last 2 args are input/output paths)
    - Otherwise: RPC/IPC server mode using lf_toolkit
    """
    # Check for file-based communication
    # shimmy passes input and output file paths as the last two arguments
    if len(sys.argv) >= 3:
        input_path = sys.argv[-2]
        output_path = sys.argv[-1]
        
        # Verify they look like file paths (basic check)
        if not input_path.startswith('-') and not output_path.startswith('-'):
            handle_file_based_communication(input_path, output_path)
            return
    
    # Fall back to RPC/IPC server mode
    server = create_server()
    server.eval(evaluation_function)
    server.preview(preview_function)
    run(server)


if __name__ == "__main__":
    main()