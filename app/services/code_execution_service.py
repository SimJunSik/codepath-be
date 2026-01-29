"""
Code execution service using AWS Lambda for secure, isolated execution.
Falls back to local subprocess in development environment.
"""
import json
import time
import subprocess
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.exceptions import CodeExecutionError
import logging

logger = logging.getLogger(__name__)

# Dangerous patterns to block before execution
BLOCKED_PATTERNS = [
    '__import__', 'importlib', 'eval(', 'exec(',
    'compile(', 'open(', 'file(', '__builtins__',
    'os.system', 'subprocess', 'Popen',
    'socket', 'connect(', 'bind(',
    'pty.', 'spawn',
]


class CodeExecutionService:
    """Service for executing Python code safely via AWS Lambda"""

    def __init__(self):
        self.timeout = settings.CODE_EXECUTION_TIMEOUT
        self.max_output = settings.CODE_EXECUTION_MAX_OUTPUT
        self.lambda_function = settings.CODE_EXECUTOR_LAMBDA_NAME
        self.aws_region = settings.AWS_REGION
        self.use_lambda = settings.USE_LAMBDA_EXECUTOR

    def execute_code(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Python code against test cases.

        Args:
            code: Python code to execute
            test_cases: List of test cases with input and expected output

        Returns:
            Execution results including passed tests and errors
        """
        # Pre-execution security check
        security_error = self._check_code_security(code)
        if security_error:
            return {
                "passed_tests": 0,
                "total_tests": len(test_cases),
                "test_results": [{
                    "test_id": idx,
                    "passed": False,
                    "error": security_error,
                    "execution_time": 0
                } for idx in range(len(test_cases))],
                "execution_time": 0,
                "security_blocked": True
            }

        start_time = time.time()

        try:
            if self.use_lambda:
                result = self._execute_via_lambda(code, test_cases)
            else:
                result = self._execute_locally(code, test_cases)

            result["execution_time"] = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {
                "passed_tests": 0,
                "total_tests": len(test_cases),
                "test_results": [{
                    "test_id": idx,
                    "passed": False,
                    "error": str(e),
                    "execution_time": 0
                } for idx in range(len(test_cases))],
                "execution_time": int((time.time() - start_time) * 1000)
            }

    def _check_code_security(self, code: str) -> Optional[str]:
        """Pre-execution security check for obvious malicious patterns."""
        code_lower = code.lower()

        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in code_lower:
                return f"Security violation: '{pattern}' is not allowed"

        return None

    def _execute_via_lambda(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute code via AWS Lambda function.

        Args:
            code: Python code to execute
            test_cases: Test cases to run

        Returns:
            Execution results
        """
        try:
            import boto3

            # Create Lambda client
            lambda_client = boto3.client('lambda', region_name=self.aws_region)

            # Prepare payload
            payload = {
                'code': code,
                'test_cases': test_cases
            }

            # Invoke Lambda
            response = lambda_client.invoke(
                FunctionName=self.lambda_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            # Parse response
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))

            if response['StatusCode'] != 200:
                raise CodeExecutionError(f"Lambda invocation failed: {response_payload}")

            # Parse body
            body = json.loads(response_payload.get('body', '{}'))

            if not body.get('success', False) and 'error' in body:
                # Return error in expected format
                return {
                    "passed_tests": 0,
                    "total_tests": len(test_cases),
                    "test_results": [{
                        "test_id": idx,
                        "passed": False,
                        "error": body['error'],
                        "execution_time": 0
                    } for idx in range(len(test_cases))],
                }

            return {
                "passed_tests": body.get('passed_tests', 0),
                "total_tests": body.get('total_tests', len(test_cases)),
                "test_results": body.get('test_results', [])
            }

        except ImportError:
            logger.warning("boto3 not available, falling back to local execution")
            return self._execute_locally(code, test_cases)
        except Exception as e:
            logger.error(f"Lambda execution failed: {e}")
            raise CodeExecutionError(f"Lambda execution failed: {str(e)}")

    def _execute_locally(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute code locally (development only).

        Args:
            code: Python code to execute
            test_cases: Test cases to run

        Returns:
            Execution results
        """
        if settings.ENVIRONMENT == "production":
            raise CodeExecutionError(
                "Local execution is disabled in production. Lambda executor required."
            )

        logger.warning("Using local execution - Lambda not available")

        results = []
        passed_count = 0

        for idx, test_case in enumerate(test_cases):
            test_input = test_case.get("input", {})
            expected_output = test_case.get("expected_output")
            is_hidden = test_case.get("is_hidden", False)

            try:
                result = self._run_code_subprocess(code, test_input)
                passed = self._compare_output(result["output"], expected_output)

                if passed:
                    passed_count += 1

                results.append({
                    "test_id": idx,
                    "passed": passed,
                    "input": test_input if not is_hidden else None,
                    "expected": expected_output if not is_hidden else None,
                    "actual": result["output"] if not is_hidden else None,
                    "error": result.get("error"),
                    "execution_time": result["execution_time"]
                })

            except Exception as e:
                results.append({
                    "test_id": idx,
                    "passed": False,
                    "input": test_input if not is_hidden else None,
                    "expected": expected_output if not is_hidden else None,
                    "actual": None,
                    "error": str(e),
                    "execution_time": 0
                })

        return {
            "passed_tests": passed_count,
            "total_tests": len(test_cases),
            "test_results": results
        }

    def _run_code_subprocess(
        self,
        code: str,
        test_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run code via subprocess with security restrictions."""
        wrapper_code = self._create_secure_wrapper(code, test_input)

        start_time = time.time()

        try:
            result = subprocess.run(
                ["python", "-c", wrapper_code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONNOUSERSITE": "1",
                }
            )

            execution_time = int((time.time() - start_time) * 1000)

            if result.returncode != 0:
                return {
                    "output": None,
                    "error": result.stderr[:self.max_output],
                    "execution_time": execution_time
                }

            try:
                output = json.loads(result.stdout)
                return {
                    "output": output,
                    "error": None,
                    "execution_time": execution_time
                }
            except json.JSONDecodeError:
                return {
                    "output": result.stdout[:self.max_output],
                    "error": None,
                    "execution_time": execution_time
                }

        except subprocess.TimeoutExpired:
            raise CodeExecutionError(f"Execution timed out after {self.timeout}s")
        except Exception as e:
            raise CodeExecutionError(f"Execution failed: {str(e)}")

    def _create_secure_wrapper(
        self,
        user_code: str,
        test_input: Dict[str, Any]
    ) -> str:
        """Create wrapper code with import restrictions."""
        return f'''
import json
import sys

BLOCKED_MODULES = frozenset([
    'os', 'subprocess', 'shutil', 'pathlib',
    'socket', 'http', 'urllib', 'requests', 'httpx', 'aiohttp',
    'ftplib', 'smtplib', 'telnetlib', 'ssl', 'asyncio',
    'multiprocessing', 'threading', 'concurrent', '_thread',
    'ctypes', 'cffi', 'importlib', 'pkgutil', 'inspect',
    'gc', 'resource', 'signal', 'pty', 'tty', 'termios',
    'code', 'codeop', 'dis', 'pickle', 'shelve',
    'marshal', 'dbm', 'sqlite3', 'psycopg2', 'pymysql',
    'io', '_io',
])

ALLOWED_MODULES = frozenset([
    'json', 'math', 'random', 'string', 'collections',
    'itertools', 'functools', 'operator', 'copy',
    'decimal', 'fractions', 'statistics', 'datetime',
    'typing', 're', 'heapq', 'bisect', 'array',
    'dataclasses', 'enum', 'numbers', 'cmath',
])

_original_import = __builtins__.__import__

def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    top_module = name.split('.')[0]
    if top_module in BLOCKED_MODULES:
        raise ImportError(f"Import of '{{name}}' is not allowed")
    if top_module not in ALLOWED_MODULES and top_module != 'sys':
        raise ImportError(f"Import of '{{name}}' is not permitted")
    return _original_import(name, globals, locals, fromlist, level)

__builtins__.__import__ = restricted_import

# User code
{user_code}

# Test input
test_input = {json.dumps(test_input)}

try:
    if 'solution' in dir():
        result = solution(**test_input)
    else:
        result = None
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"error": str(e)}}), file=sys.stderr)
    sys.exit(1)
'''

    def _compare_output(self, actual: Any, expected: Any) -> bool:
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
            return all(self._compare_output(a, e) for a, e in zip(actual, expected))

        if isinstance(actual, dict) and isinstance(expected, dict):
            if not set(expected.keys()).issubset(set(actual.keys())):
                return False
            return all(self._compare_output(actual[k], expected[k]) for k in expected.keys())

        if isinstance(actual, float) and isinstance(expected, float):
            return abs(actual - expected) < 1e-9

        return actual == expected
