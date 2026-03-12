from enum import Enum

class ErrorCode(str, Enum):
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    NOT_FOUND = 'NOT_FOUND'
    CONFLICT = 'CONFLICT'
    AUTH_FAILED = 'AUTH_FAILED'
    HTTP_ERROR = 'HTTP_ERROR'
