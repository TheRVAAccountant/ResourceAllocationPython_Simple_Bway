"""Data model representing an associate/employee record."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass(slots=True)
class AssociateRecord:
    """Structured representation of a single associate entry."""

    name: str
    transporter_id: str
    position: str
    qualifications: List[str]
    id_expiration: Optional[date]
    personal_phone: str
    work_phone: str
    email: str
    status: str
    days_until_expiration: Optional[int]
    is_active: bool
    is_expired: bool
    is_expiring_soon: bool

    def formatted_qualifications(self) -> str:
        """Return qualifications joined in a user-friendly format."""
        return ", ".join(self.qualifications)
