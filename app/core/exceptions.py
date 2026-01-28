"""
Custom exception classes
"""


class CodePathException(Exception):
    """Base exception for CodePath application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(CodePathException):
    """Authentication failed exception"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(CodePathException):
    """Authorization failed exception"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class NotFoundError(CodePathException):
    """Resource not found exception"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(CodePathException):
    """Validation error exception"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class ConflictError(CodePathException):
    """Resource conflict exception"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=409)


class CodeExecutionError(CodePathException):
    """Code execution error exception"""
    def __init__(self, message: str = "Code execution failed"):
        super().__init__(message, status_code=400)
