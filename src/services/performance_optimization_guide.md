# Performance Optimization Integration Guide

## Overview

This guide shows how to integrate the performance optimizations into the existing Resource Allocation system with minimal disruption.

## Integration Steps

### 1. Replace Duplicate Validator

In `gas_compatible_allocator.py`, update the import and initialization:

```python
# Replace:
from src.services.duplicate_validator import DuplicateVehicleValidator

# With:
from src.services.optimized_duplicate_validator import OptimizedDuplicateValidator as DuplicateVehicleValidator
```

### 2. Update Excel Writing Operations

In `daily_details_writer.py`, integrate bulk writing:

```python
from src.services.optimized_excel_writer import OptimizedExcelWriter

class DailyDetailsWriter(BaseService):
    def __init__(self, excel_service=None):
        super().__init__()
        self.excel_service = excel_service
        # Add optimized writer
        self.optimized_writer = OptimizedExcelWriter()

    def append_to_existing_file(self, file_path, allocation_result, allocation_date, vehicle_log_dict=None):
        # Use optimized writer for bulk operations
        with self.optimized_writer.bulk_write_context(worksheet) as bulk:
            # Convert allocation results to DataFrame
            df = pd.DataFrame(allocation_result.allocations)

            # Write using optimized method
            rows_written = self.optimized_writer.write_dataframe_optimized(
                worksheet, df, start_row=next_row,
                progress_callback=self.progress_callback
            )
```

### 3. Update Thick Border Service

In `daily_details_thick_borders.py`, replace with optimized version:

```python
from src.services.optimized_thick_borders import OptimizedThickBorderService

# In the writer service:
self.thick_border_service = OptimizedThickBorderService()

# When applying borders:
self.thick_border_service.apply_thick_borders_optimized(
    worksheet, start_row=2, progress_callback=callback
)
```

### 4. Add Performance Monitoring

In `allocation_tab.py`, add monitoring:

```python
from src.utils.performance_monitor import get_monitor, track_performance

class AllocationTab:
    def __init__(self):
        self.monitor = get_monitor()

    @track_performance("allocation_workflow")
    def run_allocation(self):
        # Existing allocation code
        with self.monitor.measure_operation("excel_loading", {"files": 3}):
            # Load Excel files

        with self.monitor.measure_operation("vehicle_allocation", {"routes": len(routes)}):
            # Run allocation

        # Generate report after completion
        report = self.monitor.generate_report()
        logger.info(f"Performance report:\n{report}")
```

### 5. Update GUI for Responsiveness

In `allocation_tab.py`, use threading for long operations:

```python
import threading
from queue import Queue

class AllocationTab:
    def run_allocation_async(self):
        """Run allocation in background thread."""
        self.progress_queue = Queue()

        def allocation_worker():
            try:
                # Run allocation with progress updates
                self.allocator.allocate_vehicles_to_routes(
                    progress_callback=lambda p: self.progress_queue.put(p)
                )
                self.progress_queue.put(("complete", None))
            except Exception as e:
                self.progress_queue.put(("error", str(e)))

        # Start worker thread
        thread = threading.Thread(target=allocation_worker)
        thread.daemon = True
        thread.start()

        # Update GUI with progress
        self.after(100, self.check_progress)

    def check_progress(self):
        """Check progress from worker thread."""
        try:
            while not self.progress_queue.empty():
                item = self.progress_queue.get_nowait()

                if isinstance(item, (int, float)):
                    # Update progress bar
                    self.progress_var.set(item)
                elif item[0] == "complete":
                    self.on_allocation_complete()
                    return
                elif item[0] == "error":
                    self.on_allocation_error(item[1])
                    return
        except:
            pass

        # Check again in 100ms
        self.after(100, self.check_progress)
```

## Configuration Options

Add to `.env` file:

```env
# Performance optimization settings
CHUNK_SIZE=1000
BUFFER_SIZE=5000
ENABLE_ASYNC_WRITES=true
ENABLE_MEMORY_TRACKING=true
MAX_PARALLEL_WORKERS=4

# Performance thresholds
ALLOCATION_TIME_THRESHOLD=30.0
EXCEL_LOAD_TIME_THRESHOLD=10.0
MEMORY_PEAK_THRESHOLD=2048
GUI_RESPONSE_THRESHOLD=0.1
```

## Testing the Optimizations

### 1. Unit Tests

```python
import pytest
from src.services.optimized_duplicate_validator import OptimizedDuplicateValidator

def test_duplicate_validator_performance():
    validator = OptimizedDuplicateValidator()

    # Create test data
    test_allocations = [
        {"Van ID": f"BW{i}", "Route Code": f"CX{i}"}
        for i in range(1000)
    ]

    # Measure performance
    import time
    start = time.time()
    result = validator.validate_allocations(test_allocations)
    duration = time.time() - start

    assert duration < 0.5  # Should complete in under 500ms
    assert result.is_valid
```

### 2. Integration Tests

```python
def test_excel_bulk_write_performance():
    writer = OptimizedExcelWriter()

    # Create large dataset
    df = pd.DataFrame({
        'A': range(10000),
        'B': [f'Value {i}' for i in range(10000)]
    })

    # Test bulk write
    with tempfile.NamedTemporaryFile(suffix='.xlsx') as tmp:
        wb = Workbook()
        ws = wb.active

        start = time.time()
        writer.write_dataframe_optimized(ws, df)
        duration = time.time() - start

        assert duration < 5.0  # Should complete in under 5 seconds
```

## Rollback Plan

If issues arise, revert by:

1. Restoring original imports in affected files
2. Removing performance monitoring code
3. Reverting to synchronous operations

Keep both versions available during transition:

```python
if config.get("USE_OPTIMIZED_SERVICES", False):
    from src.services.optimized_duplicate_validator import OptimizedDuplicateValidator
else:
    from src.services.duplicate_validator import DuplicateVehicleValidator
```

## Monitoring Production Performance

After deployment:

1. Check performance reports daily
2. Monitor memory usage trends
3. Track user-reported issues
4. Analyze slow operation logs

```python
# Add to daily operations
monitor = get_monitor()
daily_report = monitor.generate_report(
    f"reports/performance_{date.today()}.md"
)

# Alert on threshold violations
if monitor.get_summary()["max_time"] > 60:
    send_alert("Performance degradation detected")
```

## Expected Results

With these optimizations:

- **Excel I/O**: 5-10x faster
- **Memory Usage**: 50% reduction
- **GUI Responsiveness**: Never blocks >100ms
- **Overall Processing**: 3-5x faster

## Next Steps

1. Implement Phase 1 optimizations (1-2 days)
2. Test with production-size datasets
3. Monitor performance metrics
4. Iterate based on results
5. Consider Phase 2/3 optimizations if needed
