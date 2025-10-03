#!/usr/bin/env python3
"""
Diagnostic script to identify why Dashboard shows only 3 history entries
when the file contains 9 entries.
"""

import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.allocation_history_service import AllocationHistoryService
from loguru import logger

def check_file_directly():
    """Check the history file directly."""
    print("=" * 80)
    print("DIRECT FILE CHECK")
    print("=" * 80)
    
    history_file = Path("config/allocation_history.json")
    
    if not history_file.exists():
        print(f"❌ History file does not exist: {history_file}")
        return
    
    print(f"✅ History file exists: {history_file}")
    print(f"   File size: {history_file.stat().st_size} bytes")
    print(f"   Last modified: {history_file.stat().st_mtime}")
    
    with open(history_file, 'r') as f:
        history = json.load(f)
    
    print(f"📊 Total entries in file: {len(history)}")
    print()
    
    # Show first 3 entries
    for i, entry in enumerate(history[:3], 1):
        print(f"Entry {i}: {entry.get('request_id', 'NO_ID')}")
        print(f"  Timestamp: {entry.get('timestamp', 'NO_TIMESTAMP')}")
        print(f"  Engine: {entry.get('engine', 'NO_ENGINE')}")
        print(f"  Status: {entry.get('status', 'NO_STATUS')}")
        print()


def check_service_read():
    """Check what the service returns."""
    print("=" * 80)
    print("ALLOCATION HISTORY SERVICE CHECK")
    print("=" * 80)
    
    # Create service instance (like Dashboard does)
    service = AllocationHistoryService()
    service.initialize()
    
    print("✅ Service initialized")
    print(f"   History file path: {service.HISTORY_FILE}")
    print()
    
    # Call get_history with limit=10 (like Dashboard does)
    history = service.get_history(limit=10)
    
    print(f"📊 Service returned {len(history)} entries (limit=10)")
    print()
    
    # Show what was returned
    for i, entry in enumerate(history, 1):
        print(f"Entry {i}: {entry.get('allocation_id', 'NO_ID')}")
        print(f"  Timestamp: {entry.get('timestamp', 'NO_TIMESTAMP')}")
        print(f"  Engine: {entry.get('engine_name', 'NO_ENGINE')}")
        print(f"  Status: {entry.get('status', 'NO_STATUS')}")
        print()
    
    return len(history)


def check_service_internal():
    """Check what _read_history returns internally."""
    print("=" * 80)
    print("SERVICE INTERNAL _read_history() CHECK")
    print("=" * 80)
    
    service = AllocationHistoryService()
    service.initialize()
    
    # Call internal method directly
    raw_history = service._read_history()
    
    print(f"📊 _read_history() returned {len(raw_history)} entries")
    print()
    
    # Show first 3
    for i, entry in enumerate(raw_history[:3], 1):
        print(f"Entry {i}: {entry.get('request_id', 'NO_ID')}")
        print(f"  Timestamp: {entry.get('timestamp', 'NO_TIMESTAMP')}")
        print()
    
    return len(raw_history)


def check_filters():
    """Check if filters are being applied unexpectedly."""
    print("=" * 80)
    print("FILTER CHECK")
    print("=" * 80)
    
    service = AllocationHistoryService()
    service.initialize()
    
    # Get history without filters
    history_no_filter = service.get_history(limit=10, filters=None)
    print(f"Without filters: {len(history_no_filter)} entries")
    
    # Get history with empty filters dict
    history_empty_filter = service.get_history(limit=10, filters={})
    print(f"With empty filters: {len(history_empty_filter)} entries")
    
    # Get raw history
    raw_history = service._read_history()
    print(f"Raw from _read_history(): {len(raw_history)} entries")
    
    print()


def main():
    """Run all diagnostics."""
    print("\n")
    print("=" * 80)
    print("DASHBOARD HISTORY DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # Check file directly
    check_file_directly()
    
    # Check service internal method
    internal_count = check_service_internal()
    
    # Check service public method
    public_count = check_service_read()
    
    # Check filters
    check_filters()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"File should have: 9 entries")
    print(f"Service _read_history(): {internal_count} entries")
    print(f"Service get_history(limit=10): {public_count} entries")
    print()
    
    if public_count < 9:
        print("❌ PROBLEM CONFIRMED: Service returns fewer entries than file contains!")
        print()
        print("Possible causes:")
        print("  1. Filters being applied unexpectedly")
        print("  2. Data corruption in some entries")
        print("  3. Logic error in get_history() formatting")
        print("  4. Entries being skipped during formatting")
    else:
        print("✅ Service reads all entries correctly!")
        print("   Problem must be in Dashboard display logic.")


if __name__ == "__main__":
    main()
