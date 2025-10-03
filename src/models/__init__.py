"""Data models for the resource allocation system."""

from src.models.allocation import (
    AllocationRequest,
    AllocationResult,
    AllocationStatus,
    Driver,
    Vehicle,
)
from src.models.email import EmailMessage, EmailRecipient, EmailTemplate
from src.models.excel import BorderStyle, ExcelRange, ExcelStyle

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
