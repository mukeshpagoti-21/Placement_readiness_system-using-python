"""Custom exceptions for the Placement Readiness Management System."""


class PlacementError(Exception):
    """Base exception for all system errors."""


class ValidationError(PlacementError):
    """Raised when input values fail validation rules."""


class NotFoundError(PlacementError):
    """Raised when a requested student or batch does not exist."""


class DuplicateError(PlacementError):
    """Raised when trying to add a duplicate student or batch ID."""


class FileStorageError(PlacementError):
    """Raised when reading or writing TXT files fails."""
