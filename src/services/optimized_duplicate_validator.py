"""Optimized duplicate vehicle assignment validator service."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
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
    assignments: List[VehicleAssignment]
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
    duplicates: Dict[str, DuplicateAssignment] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def has_duplicates(self) -> bool:
        """Check if any duplicates were found."""
        return self.duplicate_count > 0
    
    def get_summary(self) -> str:
        """Get validation summary message."""
        if self.is_valid:
            return "✅ No duplicate vehicle assignments detected"
        return f"⚠️ Found {self.duplicate_count} vehicles assigned to multiple routes"


class OptimizedDuplicateValidator(BaseService):
    """Optimized service for validating duplicate vehicle assignments.
    
    Performance improvements:
    1. Uses sets for O(1) duplicate detection
    2. Lazy object creation - only creates VehicleAssignment for duplicates
    3. In-place marking instead of copying all results
    4. Pre-compiled string templates for faster formatting
    """
    
    # Pre-compiled templates for better performance
    CONFLICT_TEMPLATE = "Vehicle {} assigned to multiple routes: {} (Drivers: {})"
    SUGGESTION_TEMPLATE = "Suggestion: Keep assignment to route {}, remove from routes: {}"
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the validator.
        
        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self.strict_mode = self.get_config("strict_duplicate_validation", False)
        self.max_assignments_per_vehicle = self.get_config("max_assignments_per_vehicle", 1)
        
        # Pre-allocate data structures for better performance
        self._vehicle_assignments_cache = defaultdict(list)
        self._processed_vehicles = set()
    
    def validate_allocations(
        self,
        allocation_results: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> ValidationResult:
        """
        Validate allocation results for duplicate vehicle assignments.
        
        Args:
            allocation_results: List of allocation result dictionaries.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            ValidationResult with duplicate information.
        """
        logger.info(f"Validating {len(allocation_results)} allocations for duplicates")
        
        # Clear caches from previous runs
        self._vehicle_assignments_cache.clear()
        self._processed_vehicles.clear()
        
        # First pass: Build lightweight index
        vehicle_indices = defaultdict(list)
        for idx, result in enumerate(allocation_results):
            van_id = result.get("Van ID")
            if van_id:
                vehicle_indices[van_id].append(idx)
            
            # Report progress if callback provided
            if progress_callback and idx % 100 == 0:
                progress_callback(idx / len(allocation_results) * 50)  # First 50%
        
        # Second pass: Process only duplicates
        duplicates = {}
        warnings = []
        duplicate_count = 0
        
        for van_id, indices in vehicle_indices.items():
            if len(indices) <= self.max_assignments_per_vehicle:
                continue
            
            duplicate_count += 1
            
            # Only create VehicleAssignment objects for duplicates
            assignments = []
            for idx in indices:
                result = allocation_results[idx]
                assignment = VehicleAssignment(
                    vehicle_id=van_id,
                    route_code=result.get("Route Code", "Unknown"),
                    driver_name=result.get("Associate Name", "N/A"),
                    service_type=result.get("Service Type", "Unknown"),
                    wave=result.get("Wave", "Unknown"),
                    staging_location=result.get("Staging Location", "Unknown")
                )
                assignments.append(assignment)
            
            # Create duplicate record
            duplicate = DuplicateAssignment(
                vehicle_id=van_id,
                assignments=assignments,
                conflict_level="error" if self.strict_mode else "warning"
            )
            
            # Generate resolution suggestion
            duplicate.resolution_suggestion = self._suggest_resolution_fast(assignments)
            
            duplicates[van_id] = duplicate
            
            # Use pre-compiled template for warning
            routes = [a.route_code for a in assignments]
            drivers = [a.driver_name for a in assignments]
            warning = self.CONFLICT_TEMPLATE.format(van_id, ', '.join(routes), ', '.join(drivers))
            warnings.append(warning)
            
            logger.warning(f"Duplicate assignment detected: {warning}")
        
        # Report final progress
        if progress_callback:
            progress_callback(100)
        
        # Create validation result
        result = ValidationResult(
            is_valid=duplicate_count == 0 or not self.strict_mode,
            duplicate_count=duplicate_count,
            duplicates=duplicates,
            warnings=warnings
        )
        
        logger.info(f"Validation complete: {result.get_summary()}")
        return result
    
    def _suggest_resolution_fast(self, assignments: List[VehicleAssignment]) -> str:
        """
        Suggest resolution for duplicate assignments with better performance.
        
        Args:
            assignments: List of conflicting assignments.
            
        Returns:
            Resolution suggestion string.
        """
        if len(assignments) <= 1:
            return "Review assignments and remove duplicates"
        
        # Sort by wave (keep earliest)
        sorted_assignments = sorted(assignments, key=lambda a: a.wave)
        
        keep_route = sorted_assignments[0].route_code
        remove_routes = [a.route_code for a in sorted_assignments[1:]]
        
        return self.SUGGESTION_TEMPLATE.format(keep_route, ', '.join(remove_routes))
    
    def mark_duplicates_in_results_inplace(
        self,
        allocation_results: List[Dict],
        validation_result: ValidationResult
    ) -> None:
        """
        Mark duplicate assignments in allocation results IN-PLACE.
        
        This is much more memory efficient than creating copies.
        
        Args:
            allocation_results: Original allocation results (modified in-place).
            validation_result: Validation result with duplicate info.
        """
        if not validation_result.has_duplicates():
            # Add default validation status to all results
            for result in allocation_results:
                result["Validation Status"] = "OK"
                result["Validation Warning"] = ""
                result["Conflict Level"] = ""
            return
        
        # First, set all to OK (bulk operation)
        for result in allocation_results:
            result["Validation Status"] = "OK"
            result["Validation Warning"] = ""
            result["Conflict Level"] = ""
        
        # Then mark only duplicates
        for result in allocation_results:
            van_id = result.get("Van ID")
            if van_id and van_id in validation_result.duplicates:
                duplicate = validation_result.duplicates[van_id]
                result["Validation Status"] = "DUPLICATE"
                result["Validation Warning"] = duplicate.get_conflict_summary()
                result["Conflict Level"] = duplicate.conflict_level
    
    def validate_with_early_exit(
        self,
        allocation_results: List[Dict],
        stop_on_first: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Fast validation with early exit option.
        
        Args:
            allocation_results: List of allocation results.
            stop_on_first: If True, stops on first duplicate found.
            
        Returns:
            Tuple of (is_valid, first_duplicate_message).
        """
        seen_vehicles: Set[str] = set()
        
        for result in allocation_results:
            van_id = result.get("Van ID")
            if not van_id:
                continue
            
            if van_id in seen_vehicles:
                if stop_on_first:
                    message = f"Duplicate found: Vehicle {van_id}"
                    return False, message
            
            seen_vehicles.add(van_id)
        
        return True, None
    
    def get_duplicate_statistics(
        self,
        validation_result: ValidationResult
    ) -> Dict[str, any]:
        """
        Get detailed statistics about duplicates for reporting.
        
        Args:
            validation_result: Validation result to analyze.
            
        Returns:
            Dictionary with duplicate statistics.
        """
        if not validation_result.has_duplicates():
            return {
                "total_duplicates": 0,
                "vehicles_affected": 0,
                "routes_affected": 0,
                "max_assignments_per_vehicle": 0,
                "average_assignments_per_duplicate": 0
            }
        
        routes_affected = set()
        max_assignments = 0
        total_assignments = 0
        
        for duplicate in validation_result.duplicates.values():
            assignment_count = len(duplicate.assignments)
            max_assignments = max(max_assignments, assignment_count)
            total_assignments += assignment_count
            
            for assignment in duplicate.assignments:
                routes_affected.add(assignment.route_code)
        
        return {
            "total_duplicates": validation_result.duplicate_count,
            "vehicles_affected": len(validation_result.duplicates),
            "routes_affected": len(routes_affected),
            "max_assignments_per_vehicle": max_assignments,
            "average_assignments_per_duplicate": (
                total_assignments / validation_result.duplicate_count 
                if validation_result.duplicate_count > 0 else 0
            )
        }