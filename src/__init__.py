"""Resource Allocation Python System.

A comprehensive Python-based resource allocation system with Excel integration,
designed to manage fleet allocation, scheduling, and reporting.
"""

__version__ = "1.0.0"
__author__ = "Resource Allocation Team"

# Lazy imports to avoid circular dependencies
__all__ = [
    "AllocationEngine",
    "ExcelService",
    "EmailService",
    "ValidationService",
]


def __getattr__(name):
    """Lazy import of main components."""
    if name == "AllocationEngine":
        from src.core.allocation_engine import AllocationEngine

        return AllocationEngine
    elif name == "ExcelService":
        from src.services.excel_service import ExcelService

        return ExcelService
    elif name == "EmailService":
        from src.services.email_service import EmailService

        return EmailService
    elif name == "ValidationService":
        from src.services.validation_service import ValidationService

        return ValidationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
