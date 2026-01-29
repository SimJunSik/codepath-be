"""
AWS Lambda handler for secure Python code execution.
Runs user code in an isolated Lambda environment with restricted imports.
"""
import json
import sys
import builtins
from typing import Any, Dict

# Blocked dangerous modules
BLOCKED_MODULES = frozenset([
    'os', 'subprocess', 'shutil', 'pathlib',
    'socket', 'http', 'urllib', 'requests', 'httpx', 'aiohttp',
    'ftplib', 'smtplib', 'telnetlib', 'ssl', 'asyncio',
    'multiprocessing', 'threading', 'concurrent', '_thread',
    'ctypes', 'cffi', 'importlib', 'pkgutil', 'inspect',
    'gc', 'resource', 'signal', 'pty', 'tty', 'termios',
    'code', 'codeop', 'dis', 'pickle', 'shelve',
    'marshal', 'dbm', 'sqlite3', 'psycopg2', 'pymysql',
    'boto3', 'botocore',  # Block AWS SDK access
])

# Allowed safe modules for coding problems
ALLOWED_MODULES = frozenset([
    'json', 'math', 'random', 'string', 'collections',
    'itertools', 'functools', 'operator', 'copy',
    'decimal', 'fractions', 'statistics', 'datetime',
    'typing', 're', 'heapq', 'bisect', 'array',
    'dataclasses', 'enum', 'numbers', 'cmath',
])

# Dangerous code patterns to block
BLOCKED_PATTERNS = [
    '__import__', 'importlib', 'eval(', 'exec(',
    'compile(', 'open(', 'file(', '__builtins__',
    'os.system', 'subprocess', 'Popen',
    'socket', 'connect(', 'bind(',
    'pty.', 'spawn', 'boto3', 'botocore',
]

# Store original import
_original_import = builtins.__import__


def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Restricted import that blocks dangerous modules."""
    top_module = name.split('.')[0]

    if top_module in BLOCKED_MODULES:
        raise ImportError(f"Import of '{name}' is not allowed for security reasons")

    if top_module not in ALLOWED_MODULES:
        raise ImportError(f"Import of '{name}' is not permitted. Only safe modules allowed.")

    return _original_import(name, globals, locals, fromlist, level)


def check_code_security(code: str) -> str | None:
    """Pre-execution security check for dangerous patterns."""
    code_lower = code.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in code_lower:
            return f"Security violation: '{pattern}' is not allowed"

    return None


def execute_user_code(user_code: str, test_input: Dict[str, Any]) -> Dict[str, Any]:
    """Execute user code in restricted environment."""
    # Install restricted import
    builtins.__import__ = restricted_import

    try:
        # Create restricted namespace
        restricted_globals = {
            '__builtins__': {
                # Safe builtins only
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'reversed': reversed,
                'list': list,
                'dict': dict,
                'set': set,
                'frozenset': frozenset,
                'tuple': tuple,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'bytes': bytes,
                'bytearray': bytearray,
                'complex': complex,
                'abs': abs,
                'all': all,
                'any': any,
                'min': min,
                'max': max,
                'sum': sum,
                'pow': pow,
                'round': round,
                'divmod': divmod,
                'hash': hash,
                'id': id,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'callable': callable,
                'repr': repr,
                'ascii': ascii,
                'bin': bin,
                'oct': oct,
                'hex': hex,
                'ord': ord,
                'chr': chr,
                'format': format,
                'slice': slice,
                'iter': iter,
                'next': next,
                'True': True,
                'False': False,
                'None': None,
                '__import__': restricted_import,
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'KeyError': KeyError,
                'IndexError': IndexError,
                'StopIteration': StopIteration,
                'ZeroDivisionError': ZeroDivisionError,
            },
            '__name__': '__main__',
        }

        # Execute user code
        exec(user_code, restricted_globals)

        # Find and call solution function
        if 'solution' in restricted_globals:
            result = restricted_globals['solution'](**test_input)
            return {'success': True, 'output': result}
        else:
            return {'success': False, 'error': "No 'solution' function found"}

    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        # Restore original import
        builtins.__import__ = _original_import


def lambda_handler(event, context):
    """
    Lambda entry point.

    Expected event format:
    {
        "code": "def solution(x): return x * 2",
        "test_cases": [
            {"input": {"x": 5}, "expected_output": 10}
        ]
    }
    """
    try:
        code = event.get('code', '')
        test_cases = event.get('test_cases', [])

        # Security check
        security_error = check_code_security(code)
        if security_error:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': security_error,
                    'passed_tests': 0,
                    'total_tests': len(test_cases),
                    'test_results': []
                })
            }

        results = []
        passed_count = 0

        for idx, test_case in enumerate(test_cases):
            test_input = test_case.get('input', {})
            expected_output = test_case.get('expected_output')
            is_hidden = test_case.get('is_hidden', False)

            # Execute code
            exec_result = execute_user_code(code, test_input)

            if exec_result['success']:
                actual_output = exec_result['output']
                passed = compare_output(actual_output, expected_output)

                if passed:
                    passed_count += 1

                results.append({
                    'test_id': idx,
                    'passed': passed,
                    'input': test_input if not is_hidden else None,
                    'expected': expected_output if not is_hidden else None,
                    'actual': actual_output if not is_hidden else None,
                    'error': None
                })
            else:
                results.append({
                    'test_id': idx,
                    'passed': False,
                    'input': test_input if not is_hidden else None,
                    'expected': expected_output if not is_hidden else None,
                    'actual': None,
                    'error': exec_result['error']
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'passed_tests': passed_count,
                'total_tests': len(test_cases),
                'test_results': results
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Lambda execution error: {str(e)}'
            })
        }


def compare_output(actual: Any, expected: Any) -> bool:
    """Compare actual output with expected output."""
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False

    if type(actual) != type(expected):
        try:
            return str(actual) == str(expected)
        except:
            return False

    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return False
        return all(compare_output(a, e) for a, e in zip(actual, expected))

    if isinstance(actual, dict) and isinstance(expected, dict):
        if not set(expected.keys()).issubset(set(actual.keys())):
            return False
        return all(compare_output(actual[k], expected[k]) for k in expected.keys())

    if isinstance(actual, float) and isinstance(expected, float):
        return abs(actual - expected) < 1e-9

    return actual == expected
