"""Safe authentication errors."""


class AuthenticationError(ValueError):
    pass


class AuthenticationConfigurationError(RuntimeError):
    pass


class TokenRevokedError(AuthenticationError):
    pass
