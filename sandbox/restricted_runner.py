"""
Restricted code runner for sandbox environment.
This script is copied into the container and executes user code safely.
"""
import sys
import json
import builtins
from typing import Any, Dict

# Dangerous modules that should be blocked
BLOCKED_MODULES = frozenset([
    'os', 'subprocess', 'sys', 'shutil', 'pathlib',
    'socket', 'http', 'urllib', 'requests', 'httpx', 'aiohttp',
    'ftplib', 'smtplib', 'telnetlib', 'ssl', 'asyncio',
    'multiprocessing', 'threading', 'concurrent', '_thread',
    'ctypes', 'cffi', 'importlib', 'pkgutil', 'inspect',
    'gc', 'resource', 'signal', 'pty', 'tty', 'termios',
    'code', 'codeop', 'compile', 'dis', 'pickle', 'shelve',
    'marshal', 'dbm', 'sqlite3', 'psycopg2', 'pymysql',
    'builtins', '__builtins__', 'io', '_io',
])

# Allowed safe modules
ALLOWED_MODULES = frozenset([
    'json', 'math', 'random', 'string', 'collections',
    'itertools', 'functools', 'operator', 'copy',
    'decimal', 'fractions', 'statistics', 'datetime',
    'typing', 're', 'heapq', 'bisect', 'array',
    'dataclasses', 'enum', 'numbers', 'cmath',
])

# Store original import
_original_import = builtins.__import__


def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Restricted import that blocks dangerous modules.
    """
    # Get the top-level module name
    top_module = name.split('.')[0]

    # Block dangerous modules
    if top_module in BLOCKED_MODULES:
        raise ImportError(f"Import of '{name}' is not allowed for security reasons")

    # Allow only whitelisted modules
    if top_module not in ALLOWED_MODULES:
        raise ImportError(f"Import of '{name}' is not allowed. Only safe modules are permitted.")

    return _original_import(name, globals, locals, fromlist, level)


def create_safe_builtins() -> Dict[str, Any]:
    """
    Create a restricted builtins dictionary.
    """
    dangerous_builtins = [
        'eval', 'exec', 'compile', '__import__', 'open',
        'input', 'breakpoint', 'memoryview', 'globals', 'locals',
        'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
        'type', 'object', '__build_class__',
    ]

    safe_builtins = {}
    for name in dir(builtins):
        if not name.startswith('_') and name not in dangerous_builtins:
            safe_builtins[name] = getattr(builtins, name)

    # Add safe versions of some builtins
    safe_builtins['print'] = print  # Allow print for debugging
    safe_builtins['len'] = len
    safe_builtins['range'] = range
    safe_builtins['enumerate'] = enumerate
    safe_builtins['zip'] = zip
    safe_builtins['map'] = map
    safe_builtins['filter'] = filter
    safe_builtins['sorted'] = sorted
    safe_builtins['reversed'] = reversed
    safe_builtins['list'] = list
    safe_builtins['dict'] = dict
    safe_builtins['set'] = set
    safe_builtins['frozenset'] = frozenset
    safe_builtins['tuple'] = tuple
    safe_builtins['str'] = str
    safe_builtins['int'] = int
    safe_builtins['float'] = float
    safe_builtins['bool'] = bool
    safe_builtins['bytes'] = bytes
    safe_builtins['bytearray'] = bytearray
    safe_builtins['complex'] = complex
    safe_builtins['abs'] = abs
    safe_builtins['all'] = all
    safe_builtins['any'] = any
    safe_builtins['min'] = min
    safe_builtins['max'] = max
    safe_builtins['sum'] = sum
    safe_builtins['pow'] = pow
    safe_builtins['round'] = round
    safe_builtins['divmod'] = divmod
    safe_builtins['hash'] = hash
    safe_builtins['id'] = id
    safe_builtins['isinstance'] = isinstance
    safe_builtins['issubclass'] = issubclass
    safe_builtins['callable'] = callable
    safe_builtins['repr'] = repr
    safe_builtins['ascii'] = ascii
    safe_builtins['bin'] = bin
    safe_builtins['oct'] = oct
    safe_builtins['hex'] = hex
    safe_builtins['ord'] = ord
    safe_builtins['chr'] = chr
    safe_builtins['format'] = format
    safe_builtins['slice'] = slice
    safe_builtins['iter'] = iter
    safe_builtins['next'] = next
    safe_builtins['__import__'] = restricted_import

    return safe_builtins


def execute_user_code(user_code: str, test_input: Dict[str, Any]) -> Any:
    """
    Execute user code in a restricted environment.
    """
    # Install restricted import
    builtins.__import__ = restricted_import

    # Create restricted global namespace
    restricted_globals = {
        '__builtins__': create_safe_builtins(),
        '__name__': '__main__',
    }

    # Execute user code to define functions
    exec(user_code, restricted_globals)

    # Find and call the solution function
    if 'solution' in restricted_globals:
        result = restricted_globals['solution'](**test_input)
        return result
    else:
        raise ValueError("No 'solution' function found in code")


def main():
    """
    Main entry point for the restricted runner.
    Reads code and input from stdin, outputs result as JSON to stdout.
    """
    try:
        # Read input from stdin (JSON format: {"code": "...", "input": {...}})
        input_data = json.loads(sys.stdin.read())
        user_code = input_data['code']
        test_input = input_data.get('input', {})

        # Execute user code
        result = execute_user_code(user_code, test_input)

        # Output result
        print(json.dumps({'success': True, 'result': result}))

    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
