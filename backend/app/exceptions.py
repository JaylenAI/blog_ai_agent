class DomainError(Exception):
    """Base domain error."""
    status_code: int = 400


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class InvalidStateError(DomainError):
    status_code = 400
