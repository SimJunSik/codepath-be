"""
Code execution service using subprocess (MVP version)
Production: Replace with Docker-based sandboxing
"""
import subprocess
import json
import time
from typing import Dict, Any, List
from app.core.config import settings
from app.core.exceptions import CodeExecutionError


class CodeExecutionService:
    """Service for executing Python code safely"""

    def __init__(self):
        self.timeout = settings.CODE_EXECUTION_TIMEOUT
        self.max_output = settings.CODE_EXECUTION_MAX_OUTPUT

    def execute_code(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Python code against test cases

        Args:
            code: Python code to execute
            test_cases: List of test cases with input and expected output

        Returns:
            Execution results including passed tests and errors
        """
        results = []
        passed_count = 0
        total_execution_time = 0

        for idx, test_case in enumerate(test_cases):
            test_input = test_case.get("input", {})
            expected_output = test_case.get("expected_output")
            is_hidden = test_case.get("is_hidden", False)

            try:
                # Execute code with test input
                result = self._run_code(code, test_input)

                # Check if output matches expected
                passed = self._compare_output(result["output"], expected_output)

                if passed:
                    passed_count += 1

                total_execution_time += result["execution_time"]

                # Create test result
                test_result = {
                    "test_id": idx,
                    "passed": passed,
                    "input": test_input if not is_hidden else None,
                    "expected": expected_output if not is_hidden else None,
                    "actual": result["output"] if not is_hidden else None,
                    "error": result.get("error"),
                    "execution_time": result["execution_time"]
                }

                results.append(test_result)

            except Exception as e:
                # Test execution failed
                test_result = {
                    "test_id": idx,
                    "passed": False,
                    "input": test_input if not is_hidden else None,
                    "expected": expected_output if not is_hidden else None,
                    "actual": None,
                    "error": str(e),
                    "execution_time": 0
                }
                results.append(test_result)

        return {
            "passed_tests": passed_count,
            "total_tests": len(test_cases),
            "test_results": results,
            "execution_time": total_execution_time
        }

    def _run_code(self, code: str, test_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Python code with given input

        Args:
            code: Python code to execute
            test_input: Input parameters for the code

        Returns:
            Execution result with output and timing

        Raises:
            CodeExecutionError: If execution fails
        """
        # Prepare execution script
        wrapper_code = self._create_wrapper(code, test_input)

        start_time = time.time()

        try:
            # Execute code in subprocess with timeout
            result = subprocess.run(
                ["python", "-c", wrapper_code],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            execution_time = int((time.time() - start_time) * 1000)  # milliseconds

            # Check for errors
            if result.returncode != 0:
                return {
                    "output": None,
                    "error": result.stderr[:self.max_output],
                    "execution_time": execution_time
                }

            # Parse output
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
            raise CodeExecutionError(f"Code execution timed out after {self.timeout} seconds")
        except Exception as e:
            raise CodeExecutionError(f"Code execution failed: {str(e)}")

    def _create_wrapper(self, user_code: str, test_input: Dict[str, Any]) -> str:
        """
        Create wrapper code that executes user code with test input

        Args:
            user_code: User's code
            test_input: Test input parameters

        Returns:
            Wrapper code as string
        """
        wrapper = f"""
import json
import sys

# User code
{user_code}

# Test input
test_input = {json.dumps(test_input)}

try:
    # Call solution function with test inputs
    if hasattr(sys.modules[__name__], 'solution'):
        result = solution(**test_input)
    else:
        result = None

    # Output result as JSON
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"error": str(e)}}), file=sys.stderr)
    sys.exit(1)
"""
        return wrapper

    def _compare_output(self, actual: Any, expected: Any) -> bool:
        """
        Compare actual output with expected output

        Args:
            actual: Actual output from code execution
            expected: Expected output

        Returns:
            True if outputs match, False otherwise
        """
        # Handle None cases
        if actual is None and expected is None:
            return True
        if actual is None or expected is None:
            return False

        # Handle different types
        if type(actual) != type(expected):
            # Try to convert and compare
            try:
                return str(actual) == str(expected)
            except:
                return False

        # Handle lists (order matters)
        if isinstance(actual, list) and isinstance(expected, list):
            if len(actual) != len(expected):
                return False
            return all(self._compare_output(a, e) for a, e in zip(actual, expected))

        # Handle dictionaries (allow actual to have extra keys)
        if isinstance(actual, dict) and isinstance(expected, dict):
            if not set(expected.keys()).issubset(set(actual.keys())):
                return False
            return all(self._compare_output(actual[k], expected[k]) for k in expected.keys())

        # Handle floats with tolerance
        if isinstance(actual, float) and isinstance(expected, float):
            return abs(actual - expected) < 1e-9

        # Direct comparison
        return actual == expected
