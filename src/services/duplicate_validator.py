"""Duplicate vehicle assignment validator service."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

from src.core.base_service import BaseService


@dataclass
class VehicleAssignment:
    """Represents a single vehicle assignment."""

    vehicle_id: str
    route_code: str
    driver_name: str
    service_type: str
    wave: str
    staging_location: str
    assignment_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DuplicateAssignment:
    """Represents a duplicate vehicle assignment conflict."""

    vehicle_id: str
    assignments: list[VehicleAssignment]
    conflict_level: str = "warning"  # "warning" or "error"
    resolution_suggestion: str = ""

    def get_conflict_summary(self) -> str:
        """Get a human-readable summary of the conflict."""
        routes = [a.route_code for a in self.assignments]
        drivers = [a.driver_name for a in self.assignments]
        return (
            f"Vehicle {self.vehicle_id} assigned to multiple routes: "
            f"{', '.join(routes)} (Drivers: {', '.join(drivers)})"
        )


@dataclass
class ValidationResult:
    """Result of duplicate validation check."""

    is_valid: bool
    duplicate_count: int = 0
    duplicates: dict[str, DuplicateAssignment] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def has_duplicates(self) -> bool:
        """Check if any duplicates were found."""
        return self.duplicate_count > 0

    def get_summary(self) -> str:
        """Get validation summary message."""
        if self.duplicate_count == 0:
            return "✅ No duplicate vehicle assignments detected"
        else:
            # Duplicates found - check conflict level for appropriate icon
            has_errors = any(dup.conflict_level == "error" for dup in self.duplicates.values())
            icon = "❌" if has_errors else "⚠️"
            return f"{icon} Found {self.duplicate_count} vehicles assigned to multiple routes"


class DuplicateVehicleValidator(BaseService):
    """Service for validating duplicate vehicle assignments."""

    def __init__(self, config: dict | None = None):
        """Initialize the validator.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self.strict_mode = self.get_config("strict_duplicate_validation", False)
        self.max_assignments_per_vehicle = self.get_config("max_assignments_per_vehicle", 1)

    def initialize(self) -> None:
        """Initialize the duplicate vehicle validator service.

        This method is called to set up the validator for use.
        """
        logger.info("Initializing DuplicateVehicleValidator")

        # Verify configuration values
        if self.max_assignments_per_vehicle < 1:
            logger.warning(
                f"Invalid max_assignments_per_vehicle: {self.max_assignments_per_vehicle}. "
                "Setting to default value of 1."
            )
            self.max_assignments_per_vehicle = 1

        # Mark as initialized
        self._initialized = True
        logger.info(
            f"DuplicateVehicleValidator initialized with strict_mode={self.strict_mode}, "
            f"max_assignments_per_vehicle={self.max_assignments_per_vehicle}"
        )

    def validate(self) -> bool:
        """Validate the service configuration and state.

        Returns:
            True if the service is valid and ready to use.
        """
        try:
            # Check if we have valid configuration
            if not isinstance(self.strict_mode, bool):
                logger.error(f"Invalid strict_mode value: {self.strict_mode}")
                return False

            if (
                not isinstance(self.max_assignments_per_vehicle, int)
                or self.max_assignments_per_vehicle < 1
            ):
                logger.error(
                    f"Invalid max_assignments_per_vehicle value: {self.max_assignments_per_vehicle}"
                )
                return False

            # Service is valid
            logger.debug("DuplicateVehicleValidator validation successful")
            return True

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False

    def validate_allocations(self, allocation_results: list[dict]) -> ValidationResult:
        """
        Validate allocation results for duplicate vehicle assignments.

        Args:
            allocation_results: List of allocation result dictionaries.

        Returns:
            ValidationResult with duplicate information.
        """
        logger.info(f"Validating {len(allocation_results)} allocations for duplicates")

        # Track vehicle assignments
        vehicle_assignments: dict[str, list[VehicleAssignment]] = defaultdict(list)

        # Build assignment map
        for result in allocation_results:
            # Skip invalid entries (None, non-dict, etc.)
            if not isinstance(result, dict):
                logger.warning(f"Skipping invalid allocation entry: {type(result).__name__}")
                continue

            van_id = result.get("Van ID")
            if not van_id or not isinstance(van_id, str):
                continue

            assignment = VehicleAssignment(
                vehicle_id=van_id,
                route_code=str(result.get("Route Code", "Unknown")),
                driver_name=str(result.get("Associate Name", "N/A")),
                service_type=str(result.get("Service Type", "Unknown")),
                wave=str(result.get("Wave", "Unknown")),
                staging_location=str(result.get("Staging Location", "Unknown")),
            )

            vehicle_assignments[van_id].append(assignment)

        # Find duplicates
        duplicates = {}
        warnings = []

        for vehicle_id, assignments in vehicle_assignments.items():
            if len(assignments) > self.max_assignments_per_vehicle:
                # Create duplicate assignment record
                duplicate = DuplicateAssignment(
                    vehicle_id=vehicle_id,
                    assignments=assignments,
                    conflict_level="error" if self.strict_mode else "warning",
                )

                # Add resolution suggestion
                duplicate.resolution_suggestion = self._suggest_resolution(assignments)

                duplicates[vehicle_id] = duplicate
                warnings.append(duplicate.get_conflict_summary())

                logger.warning(f"Duplicate assignment detected: {duplicate.get_conflict_summary()}")

        # Create validation result
        result = ValidationResult(
            is_valid=len(duplicates) == 0,  # Invalid if any duplicates found
            duplicate_count=len(duplicates),
            duplicates=duplicates,
            warnings=warnings,
        )

        logger.info(f"Validation complete: {result.get_summary()}")
        return result

    def _parse_wave_time(self, wave_str: str) -> tuple[int, int]:
        """
        Parse wave time string to sortable tuple (hour_24, minute).

        Args:
            wave_str: Wave time string like "8:00 AM" or "11:30 PM"

        Returns:
            Tuple of (hour_24, minute) for sorting
        """
        try:
            import re

            # Extract time components
            match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", str(wave_str).upper())
            if not match:
                return (99, 99)  # Sort unknown times last

            hour = int(match.group(1))
            minute = int(match.group(2))
            period = match.group(3)

            # Convert to 24-hour format
            if period == "PM" and hour != 12:
                hour += 12
            elif period == "AM" and hour == 12:
                hour = 0

            return (hour, minute)
        except Exception:
            return (99, 99)  # Sort errors last

    def _suggest_resolution(self, assignments: list[VehicleAssignment]) -> str:
        """
        Suggest resolution for duplicate assignments.

        Args:
            assignments: List of conflicting assignments.

        Returns:
            Resolution suggestion string.
        """
        # Sort by wave time to suggest keeping earliest
        sorted_assignments = sorted(assignments, key=lambda a: self._parse_wave_time(a.wave))

        if len(sorted_assignments) > 1:
            keep_route = sorted_assignments[0].route_code
            remove_routes = [a.route_code for a in sorted_assignments[1:]]
            return (
                f"Suggestion: Keep assignment to route {keep_route}, "
                f"remove from routes: {', '.join(remove_routes)}"
            )

        return "Review assignments and remove duplicates"

    def validate_driver_vehicles(self, allocations: dict[str, list[str]]) -> ValidationResult:
        """
        Validate allocations from driver perspective (AllocationResult format).

        Args:
            allocations: Dict mapping driver_id to list of vehicle_ids.

        Returns:
            ValidationResult with any issues found.
        """
        logger.info("Validating driver-vehicle allocations")

        # Invert the mapping to check for duplicate vehicles
        vehicle_to_drivers: dict[str, list[str]] = defaultdict(list)

        for driver_id, vehicle_ids in allocations.items():
            for vehicle_id in vehicle_ids:
                vehicle_to_drivers[vehicle_id].append(driver_id)

        # Find vehicles assigned to multiple drivers
        duplicates = {}
        warnings = []

        for vehicle_id, driver_ids in vehicle_to_drivers.items():
            if len(driver_ids) > 1:
                # Create assignments from driver data
                assignments = [
                    VehicleAssignment(
                        vehicle_id=vehicle_id,
                        route_code="N/A",
                        driver_name=driver_id,
                        service_type="N/A",
                        wave="N/A",
                        staging_location="N/A",
                    )
                    for driver_id in driver_ids
                ]

                duplicate = DuplicateAssignment(
                    vehicle_id=vehicle_id,
                    assignments=assignments,
                    conflict_level="error" if self.strict_mode else "warning",
                )

                duplicates[vehicle_id] = duplicate
                warning_msg = (
                    f"Vehicle {vehicle_id} assigned to multiple drivers: "
                    f"{', '.join(driver_ids)}"
                )
                warnings.append(warning_msg)
                logger.warning(warning_msg)

        result = ValidationResult(
            is_valid=len(duplicates) == 0 or not self.strict_mode,
            duplicate_count=len(duplicates),
            duplicates=duplicates,
            warnings=warnings,
        )

        return result

    def mark_duplicates_in_results(
        self, allocation_results: list[dict], validation_result: ValidationResult
    ) -> list[dict]:
        """
        Mark duplicate assignments in allocation results.

        Args:
            allocation_results: Original allocation results.
            validation_result: Validation result with duplicate info.

        Returns:
            Updated allocation results with duplicate markers.
        """
        if not validation_result.has_duplicates():
            return allocation_results

        # Create a copy to avoid modifying original
        marked_results = []

        for result in allocation_results:
            result_copy = result.copy()
            van_id = result_copy.get("Van ID")

            if van_id and van_id in validation_result.duplicates:
                duplicate = validation_result.duplicates[van_id]
                result_copy["Validation Status"] = "DUPLICATE"
                result_copy["Validation Warning"] = duplicate.get_conflict_summary()
                result_copy["Conflict Level"] = duplicate.conflict_level
            else:
                result_copy["Validation Status"] = "OK"
                result_copy["Validation Warning"] = ""
                result_copy["Conflict Level"] = ""

            marked_results.append(result_copy)

        return marked_results

    def generate_duplicate_report(self, validation_result: ValidationResult) -> dict[str, any]:
        """
        Generate a detailed duplicate report.

        Args:
            validation_result: Validation result to report on.

        Returns:
            Report dictionary with detailed duplicate information.
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": validation_result.get_summary(),
            "duplicate_count": validation_result.duplicate_count,
            "is_valid": validation_result.is_valid,
            "duplicates": [],
        }

        for vehicle_id, duplicate in validation_result.duplicates.items():
            duplicate_info = {
                "vehicle_id": vehicle_id,
                "conflict_level": duplicate.conflict_level,
                "assignment_count": len(duplicate.assignments),
                "resolution_suggestion": duplicate.resolution_suggestion,
                "assignments": [
                    {
                        "route_code": a.route_code,
                        "driver_name": a.driver_name,
                        "service_type": a.service_type,
                        "wave": a.wave,
                        "staging_location": a.staging_location,
                        "timestamp": a.assignment_timestamp.isoformat(),
                    }
                    for a in duplicate.assignments
                ],
            }
            report["duplicates"].append(duplicate_info)

        return report
