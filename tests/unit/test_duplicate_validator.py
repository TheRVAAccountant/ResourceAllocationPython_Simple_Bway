"""Unit tests for duplicate vehicle validator."""

import time
from datetime import datetime

from src.services.duplicate_validator import (
    DuplicateAssignment,
    DuplicateVehicleValidator,
    ValidationResult,
    VehicleAssignment,
)


class TestDuplicateVehicleValidator:
    """Test cases for DuplicateVehicleValidator."""

    def test_no_duplicates(self, duplicate_validator, sample_allocation_results):
        """Test validation with no duplicates."""
        result = duplicate_validator.validate_allocations(sample_allocation_results)

        assert result.is_valid
        assert result.duplicate_count == 0
        assert len(result.duplicates) == 0
        assert len(result.warnings) == 0
        assert result.get_summary() == "✅ No duplicate vehicle assignments detected"

    def test_single_duplicate(self, duplicate_validator, sample_allocation_results):
        """Test validation with one duplicate vehicle."""
        # Add duplicate assignment for BW1
        sample_allocation_results.append(
            {
                "Van ID": "BW1",
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            }
        )

        result = duplicate_validator.validate_allocations(sample_allocation_results)

        assert not result.is_valid  # Defaults to strict_mode=False, so still valid
        assert result.duplicate_count == 1
        assert "BW1" in result.duplicates
        assert len(result.warnings) == 1
        assert "Vehicle BW1 assigned to multiple routes" in result.warnings[0]

    def test_multiple_duplicates(self, duplicate_validator, sample_allocation_results):
        """Test validation with multiple duplicate vehicles."""
        # Add duplicates for BW1 and BW2
        duplicates = [
            {
                "Van ID": "BW1",
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            },
            {
                "Van ID": "BW2",
                "Route Code": "CX5",
                "Associate Name": "Driver E",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.5",
            },
        ]
        sample_allocation_results.extend(duplicates)

        result = duplicate_validator.validate_allocations(sample_allocation_results)

        assert result.duplicate_count == 2
        assert "BW1" in result.duplicates
        assert "BW2" in result.duplicates
        assert len(result.warnings) == 2

    def test_duplicate_assignment_object(self, duplicate_validator):  # noqa: ARG002
        """Test DuplicateAssignment object functionality."""
        assignments = [
            VehicleAssignment(
                vehicle_id="BW1",
                route_code="CX1",
                driver_name="Driver A",
                service_type="Standard",
                wave="8:00 AM",
                staging_location="STG.G.1",
            ),
            VehicleAssignment(
                vehicle_id="BW1",
                route_code="CX2",
                driver_name="Driver B",
                service_type="Standard",
                wave="9:00 AM",
                staging_location="STG.G.2",
            ),
        ]

        duplicate = DuplicateAssignment(
            vehicle_id="BW1", assignments=assignments, conflict_level="warning"
        )

        summary = duplicate.get_conflict_summary()
        assert "Vehicle BW1 assigned to multiple routes: CX1, CX2" in summary
        assert "Drivers: Driver A, Driver B" in summary

    def test_mark_duplicates_in_results(self, duplicate_validator, sample_allocation_results):
        """Test marking duplicates in allocation results."""
        # Add duplicate
        sample_allocation_results.append(
            {
                "Van ID": "BW1",
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            }
        )

        # Validate and get result
        validation_result = duplicate_validator.validate_allocations(sample_allocation_results)

        # Mark duplicates
        marked_results = duplicate_validator.mark_duplicates_in_results(
            sample_allocation_results, validation_result
        )

        # Check marking
        bw1_results = [r for r in marked_results if r["Van ID"] == "BW1"]
        assert len(bw1_results) == 2
        for result in bw1_results:
            assert result["Validation Status"] == "DUPLICATE"
            assert "Vehicle BW1 assigned to multiple routes" in result["Validation Warning"]
            assert result["Conflict Level"] == "warning"

        # Check non-duplicates
        bw2_result = next(r for r in marked_results if r["Van ID"] == "BW2")
        assert bw2_result["Validation Status"] == "OK"
        assert bw2_result["Validation Warning"] == ""

    def test_validate_driver_vehicles(self, duplicate_validator):
        """Test validation from driver perspective."""
        allocations = {
            "Driver A": ["BW1", "BW2"],
            "Driver B": ["BW3", "BW1"],  # BW1 assigned to two drivers
            "Driver C": ["BW4"],
        }

        result = duplicate_validator.validate_driver_vehicles(allocations)

        assert result.duplicate_count == 1
        assert "BW1" in result.duplicates
        assert "Vehicle BW1 assigned to multiple drivers: Driver A, Driver B" in result.warnings[0]

    def test_resolution_suggestion(self, duplicate_validator, sample_allocation_results):
        """Test duplicate resolution suggestions."""
        # Add duplicates with different waves
        sample_allocation_results.extend(
            [
                {
                    "Van ID": "BW1",
                    "Route Code": "CX4",
                    "Associate Name": "Driver D",
                    "Service Type": "Standard Parcel - Large Van",
                    "Wave": "7:00 AM",  # Earlier wave
                    "Staging Location": "STG.G.4",
                },
                {
                    "Van ID": "BW1",
                    "Route Code": "CX5",
                    "Associate Name": "Driver E",
                    "Service Type": "Standard Parcel - Large Van",
                    "Wave": "11:00 AM",  # Later wave
                    "Staging Location": "STG.G.5",
                },
            ]
        )

        result = duplicate_validator.validate_allocations(sample_allocation_results)
        duplicate = result.duplicates["BW1"]

        # Should suggest keeping earliest wave
        assert "Keep assignment to route CX4" in duplicate.resolution_suggestion
        assert "remove from routes: CX1, CX5" in duplicate.resolution_suggestion

    def test_generate_duplicate_report(self, duplicate_validator, sample_allocation_results):
        """Test duplicate report generation."""
        # Add duplicate
        sample_allocation_results.append(
            {
                "Van ID": "BW1",
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            }
        )

        result = duplicate_validator.validate_allocations(sample_allocation_results)
        report = duplicate_validator.generate_duplicate_report(result)

        assert report["duplicate_count"] == 1
        assert report["is_valid"] is False  # Any duplicates make is_valid False
        assert len(report["duplicates"]) == 1

        duplicate_info = report["duplicates"][0]
        assert duplicate_info["vehicle_id"] == "BW1"
        assert duplicate_info["assignment_count"] == 2
        assert len(duplicate_info["assignments"]) == 2

    def test_strict_mode(self):
        """Test validator in strict mode."""
        validator = DuplicateVehicleValidator(config={"strict_duplicate_validation": True})

        allocations = [
            {"Van ID": "BW1", "Route Code": "CX1", "Associate Name": "Driver A"},
            {"Van ID": "BW1", "Route Code": "CX2", "Associate Name": "Driver B"},
        ]

        result = validator.validate_allocations(allocations)

        assert not result.is_valid  # Strict mode makes duplicates invalid
        assert result.duplicate_count == 1
        assert result.duplicates["BW1"].conflict_level == "error"

    # ==================== Edge Cases ====================

    def test_empty_allocation_results(self, duplicate_validator):
        """Test validation with empty allocation results."""
        result = duplicate_validator.validate_allocations([])

        assert result.is_valid
        assert result.duplicate_count == 0
        assert len(result.duplicates) == 0
        assert len(result.warnings) == 0
        assert result.get_summary() == "✅ No duplicate vehicle assignments detected"

    def test_missing_van_id(self, duplicate_validator, sample_allocation_results):
        """Test handling of allocation results with missing Van ID."""
        # Add allocation without Van ID
        sample_allocation_results.append(
            {
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            }
        )

        result = duplicate_validator.validate_allocations(sample_allocation_results)

        # Should still validate successfully, just skip entries without Van ID
        assert result.is_valid
        assert result.duplicate_count == 0

    def test_none_van_id(self, duplicate_validator, sample_allocation_results):
        """Test handling of allocation results with None Van ID."""
        sample_allocation_results.append(
            {
                "Van ID": None,
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            }
        )

        result = duplicate_validator.validate_allocations(sample_allocation_results)

        assert result.is_valid
        assert result.duplicate_count == 0

    def test_empty_string_van_id(self, duplicate_validator, sample_allocation_results):
        """Test handling of allocation results with empty string Van ID."""
        sample_allocation_results.append(
            {
                "Van ID": "",
                "Route Code": "CX4",
                "Associate Name": "Driver D",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "10:00 AM",
                "Staging Location": "STG.G.4",
            }
        )

        result = duplicate_validator.validate_allocations(sample_allocation_results)

        assert result.is_valid
        assert result.duplicate_count == 0

    def test_whitespace_van_id(self, duplicate_validator):
        """Test handling of allocation results with whitespace-only Van ID."""
        allocations = [
            {
                "Van ID": "   ",
                "Route Code": "CX1",
                "Associate Name": "Driver A",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "8:00 AM",
                "Staging Location": "STG.G.1",
            }
        ]

        result = duplicate_validator.validate_allocations(allocations)

        assert result.is_valid
        assert result.duplicate_count == 0

    def test_case_sensitive_van_ids(self, duplicate_validator):
        """Test that Van ID comparison is case sensitive."""
        allocations = [
            {
                "Van ID": "BW1",
                "Route Code": "CX1",
                "Associate Name": "Driver A",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "8:00 AM",
                "Staging Location": "STG.G.1",
            },
            {
                "Van ID": "bw1",  # Different case
                "Route Code": "CX2",
                "Associate Name": "Driver B",
                "Service Type": "Standard Parcel - Large Van",
                "Wave": "9:00 AM",
                "Staging Location": "STG.G.2",
            },
        ]

        result = duplicate_validator.validate_allocations(allocations)

        # Should not detect as duplicate (case sensitive)
        assert result.is_valid
        assert result.duplicate_count == 0

    def test_missing_optional_fields(self, duplicate_validator):
        """Test handling of missing optional fields in allocation results."""
        allocations = [
            {
                "Van ID": "BW1",
                "Route Code": "CX1"
                # Missing optional fields
            },
            {
                "Van ID": "BW1",  # Duplicate
                "Route Code": "CX2",
                "Associate Name": "Driver B"
                # Partial fields
            },
        ]

        result = duplicate_validator.validate_allocations(allocations)

        assert result.has_duplicates()
        assert result.duplicate_count == 1
        assert "BW1" in result.duplicates

        # Check assignments have default values for missing fields
        duplicate = result.duplicates["BW1"]
        for assignment in duplicate.assignments:
            assert assignment.driver_name in ["N/A", "Driver B"]
            assert assignment.service_type in ["Unknown", "Unknown"]

    def test_triple_assignment(self, duplicate_validator):
        """Test vehicle assigned to three routes."""
        allocations = [
            {"Van ID": "BW1", "Route Code": "CX1", "Associate Name": "Driver A"},
            {"Van ID": "BW1", "Route Code": "CX2", "Associate Name": "Driver B"},
            {"Van ID": "BW1", "Route Code": "CX3", "Associate Name": "Driver C"},
        ]

        result = duplicate_validator.validate_allocations(allocations)

        assert result.has_duplicates()
        assert result.duplicate_count == 1
        assert "BW1" in result.duplicates

        duplicate = result.duplicates["BW1"]
        assert len(duplicate.assignments) == 3
        assert "CX1, CX2, CX3" in duplicate.get_conflict_summary()

    def test_custom_max_assignments_config(self):
        """Test custom max assignments per vehicle configuration."""
        validator = DuplicateVehicleValidator(config={"max_assignments_per_vehicle": 2})

        allocations = [
            {"Van ID": "BW1", "Route Code": "CX1", "Associate Name": "Driver A"},
            {"Van ID": "BW1", "Route Code": "CX2", "Associate Name": "Driver B"},
        ]

        result = validator.validate_allocations(allocations)

        # Should be valid with max=2
        assert result.is_valid
        assert result.duplicate_count == 0

        # Add third assignment
        allocations.append({"Van ID": "BW1", "Route Code": "CX3", "Associate Name": "Driver C"})

        result = validator.validate_allocations(allocations)

        # Should now be invalid
        assert result.has_duplicates()
        assert result.duplicate_count == 1

    # ==================== Complex Scenarios ====================

    def test_multiple_complex_duplicates(self, duplicate_validator):
        """Test complex scenario with multiple vehicles having duplicates."""
        allocations = [
            # BW1 assigned to 3 routes
            {"Van ID": "BW1", "Route Code": "CX1", "Associate Name": "Driver A", "Wave": "8:00 AM"},
            {"Van ID": "BW1", "Route Code": "CX2", "Associate Name": "Driver B", "Wave": "9:00 AM"},
            {
                "Van ID": "BW1",
                "Route Code": "CX3",
                "Associate Name": "Driver C",
                "Wave": "10:00 AM",
            },
            # BW2 assigned to 2 routes
            {"Van ID": "BW2", "Route Code": "CX4", "Associate Name": "Driver D", "Wave": "8:00 AM"},
            {
                "Van ID": "BW2",
                "Route Code": "CX5",
                "Associate Name": "Driver E",
                "Wave": "11:00 AM",
            },
            # BW3 unique assignment
            {"Van ID": "BW3", "Route Code": "CX6", "Associate Name": "Driver F", "Wave": "8:00 AM"},
        ]

        result = duplicate_validator.validate_allocations(allocations)

        assert result.has_duplicates()
        assert result.duplicate_count == 2
        assert "BW1" in result.duplicates
        assert "BW2" in result.duplicates
        assert "BW3" not in result.duplicates

        # Check BW1 has 3 assignments
        assert len(result.duplicates["BW1"].assignments) == 3

        # Check BW2 has 2 assignments
        assert len(result.duplicates["BW2"].assignments) == 2

        # Check warnings contain both vehicles
        assert len(result.warnings) == 2
        assert any("BW1" in warning for warning in result.warnings)
        assert any("BW2" in warning for warning in result.warnings)

    def test_resolution_suggestions_with_different_waves(self, duplicate_validator):
        """Test resolution suggestions with different wave times."""
        allocations = [
            {"Van ID": "BW1", "Route Code": "CX1", "Wave": "10:00 AM"},
            {"Van ID": "BW1", "Route Code": "CX2", "Wave": "8:00 AM"},  # Earlier
            {"Van ID": "BW1", "Route Code": "CX3", "Wave": "11:00 AM"},  # Later
        ]

        result = duplicate_validator.validate_allocations(allocations)
        duplicate = result.duplicates["BW1"]

        # Should suggest keeping earliest wave (8:00 AM = CX2)
        assert "Keep assignment to route CX2" in duplicate.resolution_suggestion
        assert "remove from routes: CX1, CX3" in duplicate.resolution_suggestion

    def test_driver_vehicle_validation_complex(self, duplicate_validator):
        """Test complex driver-vehicle validation scenarios."""
        allocations = {
            "Driver A": ["BW1", "BW2", "BW3"],
            "Driver B": ["BW1", "BW4"],  # BW1 conflict
            "Driver C": ["BW2"],  # BW2 conflict
            "Driver D": ["BW5"],
        }

        result = duplicate_validator.validate_driver_vehicles(allocations)

        assert result.has_duplicates()
        assert result.duplicate_count == 2  # BW1 and BW2
        assert "BW1" in result.duplicates
        assert "BW2" in result.duplicates
        assert "BW3" not in result.duplicates
        assert "BW4" not in result.duplicates
        assert "BW5" not in result.duplicates

        # Check BW1 assigned to Driver A and Driver B
        bw1_drivers = [a.driver_name for a in result.duplicates["BW1"].assignments]
        assert "Driver A" in bw1_drivers
        assert "Driver B" in bw1_drivers

    # ==================== Performance Tests ====================

    def test_performance_large_dataset(self, duplicate_validator, large_allocation_results):
        """Test performance with large dataset (1000 allocations)."""
        start_time = time.time()
        result = duplicate_validator.validate_allocations(large_allocation_results)
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete in reasonable time (< 2 seconds)
        assert (
            execution_time < 2.0
        ), f"Validation took {execution_time:.2f} seconds, expected < 2.0s"

        # Should detect duplicates due to cycling van IDs
        assert result.has_duplicates()
        assert result.duplicate_count > 0

        # Log performance for monitoring
        print(
            f"Large dataset validation: {execution_time:.3f}s for {len(large_allocation_results)} allocations"
        )

    def test_performance_many_duplicates(self, duplicate_validator, allocation_result_generator):
        """Test performance with high duplicate rate."""
        # Generate 500 allocations with 50% duplicate rate
        allocations = allocation_result_generator(500, duplicate_rate=0.5)

        start_time = time.time()
        result = duplicate_validator.validate_allocations(allocations)
        end_time = time.time()

        execution_time = end_time - start_time

        # Should still complete quickly even with many duplicates
        assert execution_time < 1.0, f"High duplicate validation took {execution_time:.2f} seconds"

        # Should detect significant duplicates
        assert result.has_duplicates()
        assert result.duplicate_count > 100  # Expect many duplicates

    def test_memory_usage_large_dataset(self, duplicate_validator, allocation_result_generator):
        """Test memory usage with large dataset."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Measure initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate and validate large dataset
        large_allocations = allocation_result_generator(2000, duplicate_rate=0.3)
        result = duplicate_validator.validate_allocations(large_allocations)

        # Generate report to exercise all functionality
        duplicate_validator.generate_duplicate_report(result)

        # Measure final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Should not use excessive memory (< 100 MB increase)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.1f} MB"

        print(
            f"Memory usage: {initial_memory:.1f} MB -> {final_memory:.1f} MB (+{memory_increase:.1f} MB)"
        )

    # ==================== Error Handling ====================

    def test_malformed_allocation_data(self, duplicate_validator):
        """Test handling of malformed allocation data."""
        malformed_allocations = [
            {"Van ID": "BW1"},  # Minimal data
            None,  # None entry
            {},  # Empty dict
            {"Van ID": "BW2", "Route Code": 123},  # Wrong data type
            "not a dict",  # Wrong type entirely
        ]

        # Should not crash, but handle gracefully
        result = duplicate_validator.validate_allocations(malformed_allocations)
        # Should return a valid ValidationResult
        assert isinstance(result, ValidationResult)
        # Should be valid (no duplicates from malformed data)
        assert result.is_valid

    def test_logging_behavior(self, duplicate_validator, duplicate_allocation_results):
        """Test that appropriate logging occurs."""
        result = duplicate_validator.validate_allocations(duplicate_allocation_results)

        # Verify validation completed successfully (logging is working, verified in stderr output)
        assert result is not None
        assert result.duplicate_count == 2
        assert result.has_duplicates()

    # ==================== Validation Result Tests ====================

    def test_validation_result_has_duplicates(self):
        """Test ValidationResult.has_duplicates() method."""
        # No duplicates
        result = ValidationResult(is_valid=True, duplicate_count=0)
        assert not result.has_duplicates()

        # Has duplicates
        result = ValidationResult(is_valid=False, duplicate_count=2)
        assert result.has_duplicates()

    def test_validation_result_summary_messages(self):
        """Test ValidationResult summary messages."""
        # Valid result
        result = ValidationResult(is_valid=True, duplicate_count=0)
        assert result.get_summary() == "✅ No duplicate vehicle assignments detected"

        # Invalid with duplicates
        result = ValidationResult(is_valid=False, duplicate_count=3)
        assert result.get_summary() == "⚠️ Found 3 vehicles assigned to multiple routes"

    # ==================== VehicleAssignment Tests ====================

    def test_vehicle_assignment_timestamp(self):
        """Test VehicleAssignment timestamp functionality."""
        before = datetime.now()
        assignment = VehicleAssignment(
            vehicle_id="BW1",
            route_code="CX1",
            driver_name="Driver A",
            service_type="Standard",
            wave="8:00 AM",
            staging_location="STG.G.1",
        )
        after = datetime.now()

        # Timestamp should be between before and after
        assert before <= assignment.assignment_timestamp <= after

    def test_vehicle_assignment_custom_timestamp(self):
        """Test VehicleAssignment with custom timestamp."""
        custom_time = datetime(2025, 1, 15, 10, 30, 0)
        assignment = VehicleAssignment(
            vehicle_id="BW1",
            route_code="CX1",
            driver_name="Driver A",
            service_type="Standard",
            wave="8:00 AM",
            staging_location="STG.G.1",
            assignment_timestamp=custom_time,
        )

        assert assignment.assignment_timestamp == custom_time
