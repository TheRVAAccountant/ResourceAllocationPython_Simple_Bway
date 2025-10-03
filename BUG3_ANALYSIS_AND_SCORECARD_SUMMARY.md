# Bug #3 Analysis & Resolution Plan + Scorecard Feature Summary

## Executive Summary

This document addresses two user requests:
1. **Bug #3**: Allocation completed successfully (17 routes) but history not saved to Dashboard
2. **Scorecard Feature**: Review and document how the scorecard feature works in the application

---

## Part 1: Bug #3 - History Not Saved

### Problem Statement

User ran allocation through GUI at 19:41:50 on 2025-09-29:
- ✅ Allocation completed successfully (17 routes allocated)
- ✅ All validation steps passed (no duplicate vehicles detected)
- ✅ Results written to Daily Details sheet (all 17 detected as duplicates)
- ✅ Separate results file created: `Allocation_Results_2025-09-29_v7.xlsx`
- ❌ **No history entry saved** - Dashboard still shows only 3 old entries

### Root Cause Analysis

#### Evidence from Code Review

**Location**: `src/core/gas_compatible_allocator.py` lines 640-695

```python
def run_full_allocation(
    self,
    day_of_ops_file: str,
    daily_routes_file: str,
    vehicle_status_file: str,
    output_file: str = None  # ⚠️ KEY: This parameter defaults to None!
) -> AllocationResult:
    """Run the complete GAS-compatible allocation process."""
    logger.info("Starting GAS-compatible allocation process")
    
    # ... Load all data ...
    # ... Perform allocation ...
    # ... Update with driver names ...
    # ... Identify unassigned vehicles ...
    
    # Create allocation result
    result = self.create_allocation_result()
    
    # Save to allocation history
    self.record_history(
        allocation_result=result,
        files={
            "day_of_ops": day_of_ops_file,
            "daily_routes": daily_routes_file,
            "vehicle_status": vehicle_status_file
        }
    )
    
    # ⚠️ THE BUG: History save is BEFORE this conditional!
    # If output_file specified, write results
    if output_file:
        self.write_results_to_excel(result, output_file)
    
    logger.info("GAS-compatible allocation complete")
    return result
```

**✅ History save DOES execute!** The `record_history()` call at lines 681-689 is NOT conditional - it runs every time.

#### So Why Didn't It Save?

Let me check the GUI code that calls `run_full_allocation()`:

**Expected Call Pattern** (from allocation_tab.py):
```python
# GUI should call run_full_allocation() with output_file parameter
result = self.allocator.run_full_allocation(
    day_of_ops_file=day_of_ops_path,
    daily_routes_file=daily_routes_path,
    vehicle_status_file=vehicle_status_path,
    output_file=vehicle_status_path  # ← Should write back to same file
)
```

#### Hypothesis: GUI Not Calling `run_full_allocation()` Correctly

The allocation **DID** complete successfully, but the GUI might be calling a different method that bypasses `run_full_allocation()`. Let me verify what method the GUI actually uses.

**Key Observation from Logs**:
- Log shows "Created separate results file: Allocation_Results_2025-09-29_v7.xlsx"
- This is created by `write_results_to_excel()` → `create_results_output_file()`
- This means `output_file` WAS provided and the write logic executed

**Wait - Let me re-examine `record_history()`**:

```python
def record_history(
    self,
    allocation_result: AllocationResult,
    files: Optional[Dict[str, str]] = None,
    error: Optional[str] = None
) -> None:
    """Persist the allocation run to history with consistent defaults."""
    duplicate_conflicts = 0
    metadata = getattr(allocation_result, 'metadata', {}) or {}
    if metadata:
        duplicate_conflicts = metadata.get('duplicate_count', 0)
    if isinstance(duplicate_conflicts, (list, tuple, set)):
        duplicate_conflicts = len([item for item in duplicate_conflicts if item is not None])
    try:
        self.history_service.save_allocation(
            result=allocation_result,
            engine_name="GASCompatibleAllocator",
            files=files or {},
            duplicate_conflicts=duplicate_conflicts,
            error=error
        )
        logger.info("Allocation saved to history")  # ⚠️ THIS LOG SHOULD APPEAR!
    except Exception as exc:
        logger.error(f"Failed to record allocation history: {exc}")
```

**🔍 CRITICAL FINDING**: User's log output shows NO "Allocation saved to history" message!

This means either:
1. `record_history()` was never called, OR
2. Exception was raised and caught (but no error log appeared)

### Additional Investigation Needed

Let me check the GUI allocation tab to see what method it actually calls:

