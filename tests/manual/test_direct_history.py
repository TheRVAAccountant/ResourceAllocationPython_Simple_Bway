#!/usr/bin/env python3
"""Direct test of history save/load."""

import json
from datetime import datetime
from pathlib import Path
from src.services.allocation_history_service import AllocationHistoryService
from src.models.allocation import AllocationResult, AllocationStatus

# Initialize service
print("1. Initializing service...")
service = AllocationHistoryService()
service.initialize()
print(f"   - History file: {service.HISTORY_FILE}")
print(f"   - Max entries: {service.max_entries}")
print(f"   - Retention days: {service.retention_days}")
print(f"   - Auto cleanup: {service.auto_cleanup}")

# Create test result
print("\n2. Creating test result...")
result = AllocationResult(
    request_id="test_direct",
    allocations={"Driver1": ["V1", "V2"]},
    unallocated_vehicles=["V3"],
    status=AllocationStatus.COMPLETED,
    timestamp=datetime.now()
)
print(f"   - Result ID: {result.request_id}")
print(f"   - Status: {result.status}")

# Save directly
print("\n3. Saving to history...")
try:
    service.save_allocation(
        result=result,
        engine_name="TestEngine",
        files={"test": "file.xlsx"},
        duplicate_conflicts=[],
        error=None
    )
    print("   ✓ Save completed")
except Exception as e:
    print(f"   ✗ Save failed: {e}")
    import traceback
    traceback.print_exc()

# Check file immediately
print("\n4. Checking file...")
if service.HISTORY_FILE.exists():
    with open(service.HISTORY_FILE) as f:
        data = json.load(f)
    print(f"   - File exists with {len(data)} entries")
    if data:
        print(f"   - First entry keys: {list(data[0].keys())}")
        print(f"   - First entry: {json.dumps(data[0], indent=4)}")
else:
    print("   ✗ File does not exist")

# Try to read back
print("\n5. Reading history...")
history = service.get_history(limit=10)
print(f"   - Got {len(history)} entries")
if history:
    print(f"   - First entry keys: {list(history[0].keys())}")
