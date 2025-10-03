"""
Verification script for Bug #2 fix - list comparison in _apply_filters()

This script tests that the filter logic now works correctly after fixing
the list comparison bug on line 403.
"""

from src.services.allocation_history_service import AllocationHistoryService

print("=" * 60)
print("FILTER BUG FIX VERIFICATION")
print("=" * 60)

# Initialize service
service = AllocationHistoryService()
service.initialize()

# Get history without filters (should always work)
print("\n✓ Test 1: get_history() without filters")
history = service.get_history(limit=10)
print(f"   Retrieved {len(history)} entries")

# Test with has_duplicates filter (this was causing the error)
print("\n✓ Test 2: get_history() with has_duplicates filter")
try:
    filtered_history = service.get_history(limit=10, filters={'has_duplicates': True})
    print(f"   SUCCESS! Retrieved {len(filtered_history)} entries with duplicates")
except TypeError as e:
    print(f"   FAILED: {e}")
    exit(1)

# Test with has_errors filter
print("\n✓ Test 3: get_history() with has_errors filter")
try:
    filtered_history = service.get_history(limit=10, filters={'has_errors': True})
    print(f"   SUCCESS! Retrieved {len(filtered_history)} entries with errors")
except TypeError as e:
    print(f"   FAILED: {e}")
    exit(1)

# Test with both filters
print("\n✓ Test 4: get_history() with multiple filters")
try:
    filtered_history = service.get_history(
        limit=10, 
        filters={'has_duplicates': True, 'has_errors': True}
    )
    print(f"   SUCCESS! Retrieved {len(filtered_history)} entries with duplicates AND errors")
except TypeError as e:
    print(f"   FAILED: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL FILTER TESTS PASSED!")
print("=" * 60)
print("\n📝 Bug #2 Fix Summary:")
print("   Before: e['duplicate_conflicts'] > 0  # Compared list to int ❌")
print("   After:  len(e.get('duplicate_conflicts', [])) > 0  # Checks list length ✅")
print("\n👉 The GUI app needs to be restarted to see the fix!")
print("   Please close the running GUI and launch it again with:")
print("   ./run_app.sh")
