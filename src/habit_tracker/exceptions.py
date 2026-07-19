class DomainError(Exception):
    """Base class for errors raised by the service layer."""


class NotFoundError(DomainError):
    pass


class ValidationError(DomainError):
    pass
