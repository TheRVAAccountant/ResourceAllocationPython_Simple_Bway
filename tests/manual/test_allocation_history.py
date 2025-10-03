#!/usr/bin/env python3
"""
Quick test script to verify allocation history functionality.
Tests that history is saved and retrieved correctly.
"""

from datetime import datetime
from pathlib import Path

from loguru import logger

from src.models.allocation import AllocationResult, AllocationStatus
from src.services.allocation_history_service import AllocationHistoryService


def test_history_service():
    """Test the allocation history service."""
    print("\n" + "=" * 80)
    print("ALLOCATION HISTORY SERVICE TEST")
    print("=" * 80 + "\n")

    # Initialize service
    print("1. Initializing AllocationHistoryService...")
    service = AllocationHistoryService()
    service.initialize()
    print("   ✓ Service initialized\n")

    # Create mock allocation result
    print("2. Creating mock allocation result...")
    result = AllocationResult(
        request_id="test_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        allocations={"Test Driver": ["TEST123", "TEST456"]},  # driver_id -> list of vehicle_ids
        unallocated_vehicles=["TEST789"],
        status=AllocationStatus.COMPLETED,
        timestamp=datetime.now(),
    )
    print(f"   ✓ Created result with ID: {result.request_id}\n")

    # Save to history
    print("3. Saving allocation to history...")
    try:
        service.save_allocation(
            result=result,
            engine_name="TestEngine",
            files={"test_input": "test_file.xlsx"},
            duplicate_conflicts=[],
            error=None,
        )
        print("   ✓ Allocation saved successfully\n")
    except Exception as e:
        print(f"   ✗ Error saving allocation: {e}\n")
        return False

    # Retrieve history
    print("4. Retrieving history...")
    try:
        history = service.get_history(limit=5)
        print(f"   ✓ Retrieved {len(history)} history entries\n")

        if history:
            print("5. Latest allocation:")
            latest = history[0]
            print(f"   - ID: {latest['allocation_id']}")
            print(f"   - Timestamp: {latest['timestamp']}")
            print(f"   - Engine: {latest['engine_name']}")
            print(f"   - Status: {latest['status']}")
            print(f"   - Total Routes: {latest['metrics']['total_routes']}")
            print(f"   - Allocated: {latest['metrics']['allocated_vehicles']}")
            print(f"   - Success Rate: {latest['metrics']['success_rate']:.1%}")
            print()
        else:
            print("   ! No history entries found\n")
    except Exception as e:
        print(f"   ✗ Error retrieving history: {e}\n")
        return False

    # Get statistics
    print("6. Getting statistics...")
    try:
        stats = service.get_statistics(days=30)
        print(f"   - Total Allocations: {stats['total_allocations']}")
        print(f"   - Success Rate: {stats['success_rate']:.1%}")
        print(f"   - Total Routes Allocated: {stats['total_routes_allocated']}")
        print(f"   - Total Vehicles Allocated: {stats['total_vehicles_allocated']}")
        print(f"   - Allocations with Duplicates: {stats['allocations_with_duplicates']}")
        print(f"   - Allocations with Errors: {stats['allocations_with_errors']}")
        print()
    except Exception as e:
        print(f"   ✗ Error getting statistics: {e}\n")
        return False

    # Check history file
    print("7. Verifying history file...")
    history_file = Path("config/allocation_history.json")
    if history_file.exists():
        size_kb = history_file.stat().st_size / 1024
        print(f"   ✓ History file exists: {history_file}")
        print(f"   ✓ Size: {size_kb:.2f} KB\n")
    else:
        print(f"   ✗ History file not found at {history_file}\n")
        return False

    print("=" * 80)
    print("✓ ALL TESTS PASSED")
    print("=" * 80 + "\n")
    return True


if __name__ == "__main__":
    logger.remove()  # Remove default handler
    logger.add(lambda msg: None)  # Suppress logs for cleaner output

    success = test_history_service()
    exit(0 if success else 1)
