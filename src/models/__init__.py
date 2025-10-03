"""Data models for the resource allocation system."""

from src.models.allocation import (
    Vehicle,
    Driver,
    AllocationRequest,
    AllocationResult,
    AllocationStatus
)
from src.models.excel import ExcelRange, ExcelStyle, BorderStyle
from src.models.email import EmailMessage, EmailRecipient, EmailTemplate

__all__ = [
    "Vehicle",
    "Driver",
    "AllocationRequest",
    "AllocationResult",
    "AllocationStatus",
    "ExcelRange",
    "ExcelStyle",
    "BorderStyle",
    "EmailMessage",
    "EmailRecipient",
    "EmailTemplate",
]