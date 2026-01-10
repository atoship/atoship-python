"""
Exception classes for atoship SDK
"""

from typing import Optional, Dict, Any


class atoshipError(Exception):
    """Base exception for all atoship SDK errors"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ValidationError(atoshipError):
    """Raised when request validation fails"""
    pass


class AuthenticationError(atoshipError):
    """Raised when authentication fails"""
    pass


class AuthorizationError(atoshipError):
    """Raised when authorization fails (403)"""
    pass


class NotFoundError(atoshipError):
    """Raised when resource is not found (404)"""
    pass


class RateLimitError(atoshipError):
    """Raised when rate limit is exceeded (429)"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)
        self.retry_after = details.get('retryAfter') if details else None


class ServerError(atoshipError):
    """Raised when server error occurs (5xx)"""
    pass


class NetworkError(atoshipError):
    """Raised when network error occurs"""
    pass


class TimeoutError(atoshipError):
    """Raised when request times out"""
    pass


class ConfigurationError(atoshipError):
    """Raised when SDK configuration is invalid"""
    pass


def create_error_from_response(status_code: int, response_data: Dict[str, Any]) -> atoshipError:
    """Create appropriate error from HTTP response"""
    
    message = response_data.get('error', 'Unknown error')
    code = response_data.get('code')
    details = response_data.get('details', {})
    
    if status_code == 400:
        return ValidationError(message, code, details)
    elif status_code == 401:
        return AuthenticationError(message, code, details)
    elif status_code == 403:
        return AuthorizationError(message, code, details)
    elif status_code == 404:
        return NotFoundError(message, code, details)
    elif status_code == 429:
        return RateLimitError(message, code, details)
    elif 500 <= status_code < 600:
        return ServerError(message, code, details)
    else:
        return atoshipError(message, code, details)


def is_retriable_error(error: Exception) -> bool:
    """Check if error is retriable"""
    
    if isinstance(error, (NetworkError, TimeoutError)):
        return True
    
    if isinstance(error, ServerError):
        return True
    
    if isinstance(error, RateLimitError):
        return False  # Handle rate limits differently
    
    return False