class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code


class FreshError(Exception):
    """Raised when an error occurs in the Presh module."""

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code
