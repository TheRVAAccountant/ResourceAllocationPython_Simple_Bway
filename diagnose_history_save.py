"""Diagnostic script to understand why allocation history is not being saved."""

import json
from pathlib import Path
from datetime import datetime
from src.services.allocation_history_service import AllocationHistoryService
from src.models.allocation import AllocationResult, AllocationStatus

def check_history_file():
    """Check current state of allocation_history.json."""
    history_file = Path("config/allocation_history.json")
    
    print("=" * 80)
    print("ALLOCATION HISTORY FILE DIAGNOSTIC")
    print("=" * 80)
    
    if not history_file.exists():
        print("❌ History file does not exist!")
        return
    
    print(f"✅ History file exists: {history_file}")
    print(f"   File size: {history_file.stat().st_size} bytes")
    print(f"   Last modified: {datetime.fromtimestamp(history_file.stat().st_mtime)}")
    print()
    
    # Read and parse
    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    print(f"📊 Total entries in history: {len(history)}")
    print()
    
    if history:
        print("LAST 3 ENTRIES:")
        print("-" * 80)
        for i, entry in enumerate(history[:3], 1):
            print(f"\nEntry {i}:")
            print(f"  Timestamp: {entry.get('timestamp')}")
            print(f"  Engine: {entry.get('engine')}")
            print(f"  Request ID: {entry.get('request_id')}")
            print(f"  Status: {entry.get('status')}")
            print(f"  Total Routes: {entry.get('total_routes')}")
            print(f"  Allocated: {entry.get('allocated_count')}")
            print(f"  Unallocated: {entry.get('unallocated_count')}")
            print(f"  Allocation Rate: {entry.get('allocation_rate')}%")
            print(f"  Duplicate Conflicts: {entry.get('duplicate_conflicts')}")
            print(f"  Error: {entry.get('error')}")
            files = entry.get('files', {})
            print(f"  Files:")
            for key, val in files.items():
                print(f"    - {key}: {val}")

def test_save_allocation():
    """Test saving a new allocation to verify the service works."""
    print("\n" + "=" * 80)
    print("TESTING ALLOCATION HISTORY SERVICE")
    print("=" * 80)
    
    # Create test allocation result
    test_result = AllocationResult(
        request_id="TEST_DIAGNOSTIC_" + datetime.now().strftime('%Y%m%d_%H%M%S'),
        allocations={"Test Driver": ["TEST-VAN-001", "TEST-VAN-002"]},
        unallocated_vehicles=["TEST-VAN-003"],
        status=AllocationStatus.COMPLETED,
        timestamp=datetime.now(),
        warnings=[],
        errors=[],
        metadata={
            "source": "Diagnostic Test",
            "total_routes": 2,
            "total_assigned": 2,
            "total_unassigned": 1,
            "duplicate_count": 0
        }
    )
    
    print("\n✅ Created test AllocationResult:")
    print(f"   Request ID: {test_result.request_id}")
    print(f"   Status: {test_result.status}")
    print(f"   Timestamp: {test_result.timestamp}")
    print()
    
    # Initialize history service
    history_service = AllocationHistoryService()
    history_service.initialize()
    
    print("✅ Initialized AllocationHistoryService")
    print()
    
    # Try to save
    print("📝 Attempting to save test allocation...")
    try:
        history_service.save_allocation(
            result=test_result,
            engine_name="DiagnosticTest",
            files={
                "test_file_1": "path/to/test1.xlsx",
                "test_file_2": "path/to/test2.xlsx"
            },
            duplicate_conflicts=0,
            error=None
        )
        print("✅ Successfully saved test allocation!")
    except Exception as e:
        print(f"❌ Failed to save: {e}")
        import traceback
        print(traceback.format_exc())
    
    print()
    print("🔍 Retrieving history to verify save...")
    history = history_service.get_history(limit=5)
    print(f"   Retrieved {len(history)} entries")
    
    if history:
        print(f"\n   Latest entry structure:")
        print(f"     Keys: {list(history[0].keys())}")
        print(f"     Allocation ID: {history[0].get('allocation_id')}")
        print(f"     Engine: {history[0].get('engine_name')}")
        print(f"     Timestamp: {history[0].get('timestamp')}")
        
        if history[0].get('allocation_id') == test_result.request_id:
            print("\n✅ Test allocation was successfully saved and retrieved!")
        else:
            print("\n⚠️ Test allocation may not have been saved")
            print(f"   Expected: {test_result.request_id}")
            print(f"   Found: {history[0].get('allocation_id')}")
    else:
        print("❌ No history entries found")

def check_allocation_result_structure():
    """Check if AllocationResult model is causing issues."""
    print("\n" + "=" * 80)
    print("CHECKING ALLOCATIONRESULT MODEL")
    print("=" * 80)
    
    # Create a sample result similar to what GAS allocator creates
    from collections import defaultdict
    
    driver_vehicles = {
        "John Doe": ["VAN-001", "VAN-002"],
        "Jane Smith": ["VAN-003"]
    }
    
    unallocated_ids = ["VAN-004", "VAN-005"]
    
    warnings = ["Found 1 duplicate vehicle assignments"]
    errors = []
    duplicate_count = 1
    
    allocation_result = AllocationResult(
        request_id=f"GAS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        allocations=driver_vehicles,
        unallocated_vehicles=unallocated_ids,
        status=AllocationStatus.COMPLETED,
        timestamp=datetime.now(),
        warnings=warnings,
        errors=errors,
        metadata={
            "source": "GAS_Compatible",
            "total_routes": 3,
            "total_assigned": 3,
            "total_unassigned": 2,
            "duplicate_count": duplicate_count,
            "detailed_results": []  # Empty for test
        }
    )
    
    print("✅ Created GAS-style AllocationResult")
    print(f"   Request ID: {allocation_result.request_id}")
    print(f"   Status: {allocation_result.status}")
    print(f"   Status Type: {type(allocation_result.status)}")
    print(f"   Has .value attribute: {hasattr(allocation_result.status, 'value')}")
    if hasattr(allocation_result.status, 'value'):
        print(f"   Status.value: {allocation_result.status.value}")
    print(f"   Metadata: {allocation_result.metadata}")
    print()
    
    # Try to extract duplicate_count like record_history() does
    duplicate_conflicts = 0
    metadata = getattr(allocation_result, 'metadata', {}) or {}
    if metadata:
        duplicate_conflicts = metadata.get('duplicate_count', 0)
    if isinstance(duplicate_conflicts, (list, tuple, set)):
        duplicate_conflicts = len([item for item in duplicate_conflicts if item is not None])
    
    print(f"✅ Extracted duplicate_conflicts: {duplicate_conflicts}")
    print()
    
    # Test saving this result
    print("📝 Testing save with GAS-style result...")
    history_service = AllocationHistoryService()
    history_service.initialize()
    
    try:
        history_service.save_allocation(
            result=allocation_result,
            engine_name="GASCompatibleAllocator",
            files={
                "day_of_ops": "inputs/test_day_of_ops.xlsx",
                "daily_routes": "inputs/test_daily_routes.xlsx",
                "vehicle_status": "Daily Summary Log 2025.xlsx"
            },
            duplicate_conflicts=duplicate_conflicts,
            error=None
        )
        print("✅ Successfully saved GAS-style allocation!")
    except Exception as e:
        print(f"❌ Failed to save: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    check_history_file()
    test_save_allocation()
    check_allocation_result_structure()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
