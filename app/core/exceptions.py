class AppError(Exception):
    """Base for all domain errors."""
    def __init__(self, detail: str = "An unexpected error occurred"):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""
    def __init__(self, resource: str = "Resource", detail: str | None = None):
        super().__init__(detail or f"{resource} not found")


class AlreadyExistsError(AppError):
    """Raised when attempting to create a duplicate resource."""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail)


class AuthenticationError(AppError):
    """Raised for invalid credentials or tokens."""
    def __init__(self, detail: str = "Invalid or expired credentials"):
        super().__init__(detail)


class AuthorizationError(AppError):
    """Raised when a user lacks permission."""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail)


class ValidationError(AppError):
    """Raised for invalid input that isn't caught by Pydantic."""
    def __init__(self, detail: str = "Invalid input"):
        super().__init__(detail)


class ExternalServiceError(AppError):
    """Raised when an external service (LLM, etc.) fails."""
    def __init__(self, detail: str = "External service unavailable"):
        super().__init__(detail)
