"""Data model representing an associate/employee record."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class AssociateRecord:
    """Structured representation of a single associate entry.

    Represents driver and helper associates with their qualifications,
    contact information, and certification status.

    Attributes:
        name: Full name of the associate
        transporter_id: Amazon Transporter ID (unique identifier)
        position: Role(s) - typically "Helper, Driver"
        qualifications: List of certifications and vehicle types
        id_expiration: License/certification expiration date
        personal_phone: Personal contact phone number
        work_phone: Work contact phone number
        email: Email address
        status: Employment status (ACTIVE or INACTIVE)
        days_until_expiration: Days until certification expires (negative if expired)
        is_active: Whether associate is currently active
        is_expired: Whether certification has expired
        is_expiring_soon: Whether certification expires within 30 days
    """

    name: str
    transporter_id: str
    position: str
    qualifications: list[str]
    id_expiration: date | None
    personal_phone: str
    work_phone: str
    email: str
    status: str
    days_until_expiration: int | None
    is_active: bool
    is_expired: bool
    is_expiring_soon: bool

    # Derived qualification flags (computed from qualifications list)
    is_step_van_qualified: bool = field(default=False, init=False)
    is_edv_qualified: bool = field(default=False, init=False)
    is_cdv_qualified: bool = field(default=False, init=False)
    is_dot_qualified: bool = field(default=False, init=False)
    is_helper_only: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Parse qualifications after initialization."""
        self._parse_qualifications()

    def _parse_qualifications(self) -> None:
        """Parse qualifications list into boolean flags.

        Analyzes the qualifications list and sets appropriate boolean flags
        for vehicle types and certifications.
        """
        # Join qualifications for easier searching
        qual_str = " ".join(q.lower() for q in self.qualifications)
        position_lower = self.position.lower()

        # Vehicle type qualifications
        self.is_step_van_qualified = "step van" in qual_str
        self.is_edv_qualified = "edv" in qual_str
        self.is_cdv_qualified = "cdv" in qual_str

        # Certification qualifications
        self.is_dot_qualified = "dot" in qual_str

        # Role determination
        self.is_helper_only = "helper" in position_lower and "driver" not in position_lower

    def formatted_qualifications(self) -> str:
        """Return qualifications joined in a user-friendly format."""
        return ", ".join(self.qualifications)

    def get_eligible_vehicle_types(self) -> list[str]:
        """Get list of vehicle types this associate can operate.

        Returns:
            List of vehicle type strings
        """
        vehicle_types = []

        if self.is_step_van_qualified:
            vehicle_types.append("Step Van")

        if self.is_edv_qualified:
            vehicle_types.append("EDV")

        if self.is_cdv_qualified:
            vehicle_types.append("CDV")

        # Standard Parcel if has CDV but no specific van type
        if self.is_cdv_qualified and not (self.is_step_van_qualified or self.is_edv_qualified):
            vehicle_types.append("Standard Parcel")

        return vehicle_types

    def get_eligible_service_types(self) -> list[str]:
        """Get list of service types this associate can handle.

        Maps qualifications to business service type strings used in allocation.

        Returns:
            List of service type strings matching allocation service types
        """
        service_types = []

        if self.is_step_van_qualified:
            service_types.append("Standard Parcel Step Van - US")

        if self.is_edv_qualified:
            service_types.extend(
                [
                    "Standard Parcel - Extra Large Van - US",
                    "Nursery Route Level X",
                ]
            )

        if self.is_cdv_qualified:
            service_types.extend(
                [
                    "Standard Parcel - Large Van",
                    "Standard Parcel",
                ]
            )

        return list(set(service_types))  # Remove duplicates

    def __str__(self) -> str:
        """String representation of associate."""
        return f"{self.name} ({self.transporter_id}) - {self.status}"
