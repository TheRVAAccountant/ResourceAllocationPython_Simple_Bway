"""Validation service for data integrity checks."""

from typing import Optional, Any, Union
from datetime import date, datetime, timedelta
from decimal import Decimal
from loguru import logger
import pandas as pd
import re

from src.core.base_service import BaseService, error_handler
from src.models.allocation import (
    Vehicle, Driver, AllocationRequest, AllocationResult,
    VehicleType, Priority
)


class ValidationRule:
    """Represents a validation rule."""
    
    def __init__(self, name: str, validator: callable, error_message: str, severity: str = "error"):
        """Initialize validation rule.
        
        Args:
            name: Rule name.
            validator: Validation function.
            error_message: Error message template.
            severity: Severity level (error, warning, info).
        """
        self.name = name
        self.validator = validator
        self.error_message = error_message
        self.severity = severity
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """Run validation.
        
        Args:
            value: Value to validate.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            is_valid = self.validator(value)
            if not is_valid:
                return False, self.error_message
            return True, None
        except Exception as e:
            return False, f"{self.error_message}: {str(e)}"


class ValidationResult:
    """Result of validation."""
    
    def __init__(self):
        """Initialize validation result."""
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.passed_rules: list[str] = []
        self.failed_rules: list[str] = []
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed.
        
        Returns:
            True if no errors.
        """
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings.
        
        Returns:
            True if warnings exist.
        """
        return len(self.warnings) > 0
    
    def add_error(self, message: str, rule_name: Optional[str] = None):
        """Add error message.
        
        Args:
            message: Error message.
            rule_name: Name of failed rule.
        """
        self.errors.append(message)
        if rule_name:
            self.failed_rules.append(rule_name)
    
    def add_warning(self, message: str):
        """Add warning message.
        
        Args:
            message: Warning message.
        """
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add info message.
        
        Args:
            message: Info message.
        """
        self.info.append(message)
    
    def add_passed_rule(self, rule_name: str):
        """Add passed rule.
        
        Args:
            rule_name: Name of passed rule.
        """
        self.passed_rules.append(rule_name)
    
    def get_summary(self) -> dict[str, Any]:
        """Get validation summary.
        
        Returns:
            Summary dictionary.
        """
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "passed_rules": len(self.passed_rules),
            "failed_rules": len(self.failed_rules),
            "errors": self.errors,
            "warnings": self.warnings
        }


class ValidationService(BaseService):
    """Service for data validation.
    
    Provides comprehensive validation for vehicles, drivers,
    allocation requests, and results.
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the validation service.
        
        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        
        # Validation rules
        self.vehicle_rules: list[ValidationRule] = []
        self.driver_rules: list[ValidationRule] = []
        self.allocation_rules: list[ValidationRule] = []
        
        # Configuration
        self.strict_mode = self.get_config("strict_validation", True)
        self.allow_duplicates = self.get_config("allow_duplicates", False)
        self.check_references = self.get_config("check_references", True)
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def initialize(self) -> None:
        """Initialize the validation service."""
        logger.info("Initializing Validation Service")
        self._initialized = True
    
    def validate(self) -> bool:
        """Validate the service configuration.
        
        Returns:
            True if configuration is valid.
        """
        return True
    
    def _initialize_default_rules(self):
        """Initialize default validation rules."""
        # Vehicle rules
        self.vehicle_rules.extend([
            ValidationRule(
                "vehicle_number_format",
                lambda v: bool(re.match(r'^[A-Z0-9]{3,}$', v.vehicle_number)),
                "Vehicle number must be at least 3 alphanumeric characters"
            ),
            ValidationRule(
                "vehicle_priority_range",
                lambda v: 0 <= v.priority <= 100,
                "Vehicle priority must be between 0 and 100"
            ),
            ValidationRule(
                "vehicle_capacity_positive",
                lambda v: v.capacity is None or v.capacity > 0,
                "Vehicle capacity must be positive",
                severity="warning"
            ),
            ValidationRule(
                "vehicle_fuel_level_range",
                lambda v: v.fuel_level is None or (0 <= v.fuel_level <= 100),
                "Fuel level must be between 0 and 100",
                severity="warning"
            )
        ])
        
        # Driver rules
        self.driver_rules.extend([
            ValidationRule(
                "driver_employee_id_format",
                lambda d: bool(re.match(r'^[A-Z0-9]{3,}$', d.employee_id)),
                "Employee ID must be at least 3 alphanumeric characters"
            ),
            ValidationRule(
                "driver_name_valid",
                lambda d: len(d.name.strip()) >= 2,
                "Driver name must be at least 2 characters"
            ),
            ValidationRule(
                "driver_experience_valid",
                lambda d: 0 <= d.experience_years <= 50,
                "Experience years must be between 0 and 50"
            ),
            ValidationRule(
                "driver_max_vehicles_valid",
                lambda d: 0 < d.max_vehicles <= 10,
                "Max vehicles must be between 1 and 10"
            )
        ])
        
        # Allocation rules
        self.allocation_rules.extend([
            ValidationRule(
                "allocation_has_vehicles",
                lambda a: len(a.vehicles) > 0,
                "Allocation request must have at least one vehicle"
            ),
            ValidationRule(
                "allocation_has_drivers",
                lambda a: len(a.drivers) > 0,
                "Allocation request must have at least one driver"
            ),
            ValidationRule(
                "allocation_date_valid",
                lambda a: a.allocation_date >= date.today() - timedelta(days=30),
                "Allocation date cannot be more than 30 days in the past",
                severity="warning"
            )
        ])
    
    @error_handler
    def validate_vehicle(self, vehicle: Vehicle) -> ValidationResult:
        """Validate a vehicle.
        
        Args:
            vehicle: Vehicle to validate.
        
        Returns:
            Validation result.
        """
        result = ValidationResult()
        
        # Run validation rules
        for rule in self.vehicle_rules:
            is_valid, error_msg = rule.validate(vehicle)
            if is_valid:
                result.add_passed_rule(rule.name)
            else:
                if rule.severity == "error":
                    result.add_error(error_msg, rule.name)
                elif rule.severity == "warning":
                    result.add_warning(error_msg)
                else:
                    result.add_info(error_msg)
        
        # Additional checks
        if vehicle.last_service_date and vehicle.last_service_date > date.today():
            result.add_warning("Last service date is in the future")
        
        logger.debug(f"Vehicle {vehicle.vehicle_number} validation: {result.is_valid}")
        return result
    
    @error_handler
    def validate_driver(self, driver: Driver) -> ValidationResult:
        """Validate a driver.
        
        Args:
            driver: Driver to validate.
        
        Returns:
            Validation result.
        """
        result = ValidationResult()
        
        # Run validation rules
        for rule in self.driver_rules:
            is_valid, error_msg = rule.validate(driver)
            if is_valid:
                result.add_passed_rule(rule.name)
            else:
                if rule.severity == "error":
                    result.add_error(error_msg, rule.name)
                elif rule.severity == "warning":
                    result.add_warning(error_msg)
                else:
                    result.add_info(error_msg)
        
        # Additional checks
        if driver.shift_start and driver.shift_end:
            if driver.shift_start >= driver.shift_end:
                result.add_error("Shift start time must be before end time")
        
        if driver.assigned_vehicles and len(driver.assigned_vehicles) > driver.max_vehicles:
            result.add_warning(f"Driver already has {len(driver.assigned_vehicles)} vehicles assigned")
        
        logger.debug(f"Driver {driver.employee_id} validation: {result.is_valid}")
        return result
    
    @error_handler
    def validate_allocation_request(self, request: AllocationRequest) -> ValidationResult:
        """Validate an allocation request.
        
        Args:
            request: Allocation request to validate.
        
        Returns:
            Validation result.
        """
        result = ValidationResult()
        
        # Run allocation rules
        for rule in self.allocation_rules:
            is_valid, error_msg = rule.validate(request)
            if is_valid:
                result.add_passed_rule(rule.name)
            else:
                if rule.severity == "error":
                    result.add_error(error_msg, rule.name)
                elif rule.severity == "warning":
                    result.add_warning(error_msg)
                else:
                    result.add_info(error_msg)
        
        # Validate individual vehicles
        invalid_vehicles = []
        for vehicle in request.vehicles:
            vehicle_result = self.validate_vehicle(vehicle)
            if not vehicle_result.is_valid:
                invalid_vehicles.append(vehicle.vehicle_number)
                for error in vehicle_result.errors:
                    result.add_error(f"Vehicle {vehicle.vehicle_number}: {error}")
        
        # Validate individual drivers
        invalid_drivers = []
        for driver in request.drivers:
            driver_result = self.validate_driver(driver)
            if not driver_result.is_valid:
                invalid_drivers.append(driver.employee_id)
                for error in driver_result.errors:
                    result.add_error(f"Driver {driver.employee_id}: {error}")
        
        # Check for duplicates
        if not self.allow_duplicates:
            vehicle_ids = [v.vehicle_id for v in request.vehicles]
            if len(vehicle_ids) != len(set(vehicle_ids)):
                result.add_error("Duplicate vehicles in request")
            
            driver_ids = [d.driver_id for d in request.drivers]
            if len(driver_ids) != len(set(driver_ids)):
                result.add_error("Duplicate drivers in request")
        
        # Check capacity
        total_capacity = sum(d.max_vehicles for d in request.drivers)
        if total_capacity < len(request.vehicles):
            result.add_warning(f"Total driver capacity ({total_capacity}) less than vehicles ({len(request.vehicles)})")
        
        logger.info(f"Allocation request validation: {result.is_valid}")
        return result
    
    @error_handler
    def validate_allocation_result(self, result: AllocationResult) -> ValidationResult:
        """Validate an allocation result.
        
        Args:
            result: Allocation result to validate.
        
        Returns:
            Validation result.
        """
        validation = ValidationResult()
        
        # Check for duplicate vehicle assignments
        all_allocated = []
        for driver_id, vehicles in result.allocations.items():
            all_allocated.extend(vehicles)
        
        if len(all_allocated) != len(set(all_allocated)):
            validation.add_error("Duplicate vehicle assignments detected")
        
        # Check for vehicles in both allocated and unallocated
        allocated_set = set(all_allocated)
        unallocated_set = set(result.unallocated_vehicles)
        
        if allocated_set & unallocated_set:
            validation.add_error("Vehicles found in both allocated and unallocated lists")
        
        # Validate allocation counts
        for driver_id, vehicles in result.allocations.items():
            if len(vehicles) == 0:
                validation.add_warning(f"Driver {driver_id} has no vehicles assigned")
            elif len(vehicles) > 10:
                validation.add_warning(f"Driver {driver_id} has {len(vehicles)} vehicles (unusually high)")
        
        # Check result status
        if result.status == "failed" and not result.errors:
            validation.add_warning("Result marked as failed but no errors provided")
        
        logger.info(f"Allocation result validation: {validation.is_valid}")
        return validation
    
    def validate_excel_data(self, df: pd.DataFrame, data_type: str) -> ValidationResult:
        """Validate Excel data.
        
        Args:
            df: DataFrame to validate.
            data_type: Type of data (vehicles or drivers).
        
        Returns:
            Validation result.
        """
        result = ValidationResult()
        
        # Check required columns
        if data_type == "vehicles":
            required = ["Vehicle Number", "Type", "Location", "Status"]
            missing = [col for col in required if col not in df.columns]
            if missing:
                result.add_error(f"Missing required columns: {missing}")
        
        elif data_type == "drivers":
            required = ["Employee ID", "Name", "Location", "Status"]
            missing = [col for col in required if col not in df.columns]
            if missing:
                result.add_error(f"Missing required columns: {missing}")
        
        # Check for empty values
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                result.add_warning(f"Column '{col}' has {null_count} empty values")
        
        # Check for duplicates
        if data_type == "vehicles" and "Vehicle Number" in df.columns:
            duplicates = df["Vehicle Number"].duplicated().sum()
            if duplicates > 0:
                result.add_error(f"Found {duplicates} duplicate vehicle numbers")
        
        elif data_type == "drivers" and "Employee ID" in df.columns:
            duplicates = df["Employee ID"].duplicated().sum()
            if duplicates > 0:
                result.add_error(f"Found {duplicates} duplicate employee IDs")
        
        logger.info(f"Excel {data_type} validation: {result.is_valid}")
        return result
    
    def add_custom_rule(self, rule: ValidationRule, target: str):
        """Add custom validation rule.
        
        Args:
            rule: Validation rule to add.
            target: Target type (vehicle, driver, allocation).
        """
        if target == "vehicle":
            self.vehicle_rules.append(rule)
        elif target == "driver":
            self.driver_rules.append(rule)
        elif target == "allocation":
            self.allocation_rules.append(rule)
        else:
            logger.error(f"Unknown validation target: {target}")
    
    def remove_rule(self, rule_name: str, target: str) -> bool:
        """Remove validation rule.
        
        Args:
            rule_name: Name of rule to remove.
            target: Target type.
        
        Returns:
            True if removed.
        """
        rules_list = None
        if target == "vehicle":
            rules_list = self.vehicle_rules
        elif target == "driver":
            rules_list = self.driver_rules
        elif target == "allocation":
            rules_list = self.allocation_rules
        
        if rules_list:
            for i, rule in enumerate(rules_list):
                if rule.name == rule_name:
                    rules_list.pop(i)
                    logger.info(f"Removed validation rule: {rule_name}")
                    return True
        
        return False