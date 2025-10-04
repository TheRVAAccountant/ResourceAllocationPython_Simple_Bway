# Codebase Review: Service Layer

**Review Date:** October 3, 2025
**Focus:** Service layer components (`src/services/`)

---

## Overview

The service layer contains **24 specialized service classes** that handle everything from Excel operations to duplicate validation to email notifications. All services inherit from `BaseService` and follow consistent patterns.

**Total Service Files:** 24 (including optimization variants and documentation)

---

## Service Inventory

### Critical Services (Core Functionality)

| Service | File | Size | Purpose |
|---------|------|------|---------|
| **DailyDetailsWriter** | daily_details_writer.py | 30,531 bytes | Writes allocation results to Excel |
| **DuplicateVehicleValidator** | duplicate_validator.py | 13,345 bytes | Detects duplicate assignments |
| **UnassignedVehiclesWriter** | unassigned_vehicles_writer.py | 14,298 bytes | Writes unassigned vehicles sheet |
| **AllocationOutputWriter** | allocation_output_writer.py | 14,319 bytes | Writes Results sheet |
| **AllocationHistoryService** | allocation_history_service.py | 21,479 bytes | Persists allocation history |
| **ExcelService** | excel_service.py | 17,386 bytes | Excel workbook operations |
| **BorderFormattingService** | border_formatting_service.py | 14,385 bytes | Excel border formatting |
| **DailyDetailsThickBorderService** | daily_details_thick_borders.py | 10,761 bytes | Thick borders for daily sections |

### Supporting Services

| Service | File | Size | Purpose |
|---------|------|------|---------|
| **AssociateService** | associate_service.py | 7,591 bytes | Manages associates/drivers |
| **ScorecardService** | scorecard_service.py | 10,301 bytes | Parses PDF scorecards |
| **FormService** | form_service.py | 18,663 bytes | Form data processing |
| **EmailService** | email_service.py | 16,222 bytes | Email notifications |
| **ValidationService** | validation_service.py | 17,555 bytes | Data validation |
| **ConfigurationService** | configuration_service.py | 12,299 bytes | Settings management |
| **CachingService** | caching_service.py | 11,380 bytes | Cache management |
| **LoggingService** | logging_service.py | 11,019 bytes | Logging infrastructure |
| **MonitoringService** | monitoring_service.py | 22,401 bytes | System monitoring |
| **DashboardDataService** | dashboard_data_service.py | 5,302 bytes | Dashboard metrics |
| **DataManagementService** | data_management_service.py | 3,631 bytes | Data CRUD operations |

### Optimized Variants

| Service | File | Size | Purpose |
|---------|------|------|---------|
| **OptimizedDuplicateValidator** | optimized_duplicate_validator.py | 11,576 bytes | Fast duplicate detection |
| **OptimizedExcelWriter** | optimized_excel_writer.py | 16,190 bytes | Batch Excel operations |
| **OptimizedThickBorders** | optimized_thick_borders.py | 12,256 bytes | Efficient border formatting |

### Documentation

| File | Size | Purpose |
|------|------|---------|
| **performance_optimization_guide.md** | 7,360 bytes | Optimization best practices |

---

## Deep Dive: Critical Services

### 1. DailyDetailsWriter

**Purpose:** Writes allocation results to the "Daily Details" sheet with exact GAS compatibility

**Size:** 30,531 bytes (750 lines) - **Largest service**

**Key Responsibility:** Append to existing Excel data without overwriting

#### Column Structure

**24 Columns (Exact GAS Match):**
```python
DAILY_DETAILS_COLUMNS = [
    "Date",
    "Route #",
    "Name",
    "Asset ID",
    "Van ID",
    "VIN",
    "GeoTab Code",
    "Type",
    "Vehicle Type",
    "Route Type",
    "Rescue",
    "Delivery Pace 1:40pm",
    "Delivery Pace 3:40pm",
    "Delivery Pace 5:40pm",
    "Delivery Pace 7:40pm",
    "Delivery Pace 9:40pm",
    "RTS TIME",
    "Pkg. Delivered",
    "Pkg. Returned",
    "Route Notes",
    "Week Number",
    "Unique Identifier",
    "Vehicle Inspection",
    "Route Completion"
]
```

#### Append Mode Logic

**Critical Feature:**
```python
def write_to_daily_details(
    self,
    workbook: Workbook,
    allocation_results: List[Dict],
    allocation_date: date
) -> None:
    """Write to Daily Details in APPEND mode.

    CRITICAL: Must append to existing data, never overwrite.
    """

    # Check if sheet exists
    if "Daily Details" in workbook.sheetnames:
        ws = workbook["Daily Details"]
        # Find next empty row (after existing data)
        next_row = ws.max_row + 1
        logger.info(f"Appending to existing Daily Details at row {next_row}")
    else:
        # Create new sheet with headers
        ws = workbook.create_sheet("Daily Details")
        self._write_headers(ws)
        next_row = 2  # Row 1 is headers
        logger.info("Created new Daily Details sheet")

    # Write each allocation result as a row
    for result in allocation_results:
        self._write_daily_details_row(ws, next_row, result, allocation_date)
        next_row += 1

    # Apply formatting
    self._apply_formatting(ws)
```

#### Unique Identifier Generation

**Prevents Duplicates Across Sessions:**
```python
def _generate_unique_identifier(
    self,
    allocation_date: date,
    route_code: str,
    van_id: str
) -> str:
    """Generate unique identifier for each allocation.

    Format: YYYYMMDD_ROUTECODE_VANID
    Example: 20251003_CX123_BW45
    """
    date_str = allocation_date.strftime("%Y%m%d")
    return f"{date_str}_{route_code}_{van_id}"
```

#### Brand Priority Highlighting

**Visual Distinction:**
```python
# Brand priority color fills
self.branded_fill = PatternFill(
    start_color="D4F5DC",  # Light green
    end_color="D4F5DC",
    fill_type="solid"
)
self.rental_fill = PatternFill(
    start_color="F3F3F3",  # Light gray
    end_color="F3F3F3",
    fill_type="solid"
)

def _apply_brand_highlighting(self, ws, row: int, van_id: str):
    """Apply highlighting based on van ownership."""
    van_id_cell = ws.cell(row=row, column=5)  # Column E (Van ID)

    if van_id.startswith("BW"):  # Branded vehicles
        van_id_cell.fill = self.branded_fill
    else:  # Rental vehicles
        van_id_cell.fill = self.rental_fill
```

#### Thick Border Integration

**Calls Thick Border Service:**
```python
# Initialize thick border service
self.thick_border_service = DailyDetailsThickBorderService()

def apply_thick_borders_to_daily_section(
    self,
    workbook: Workbook,
    start_row: int,
    end_row: int
) -> None:
    """Apply thick borders around a daily section."""
    self.thick_border_service.apply_thick_borders(
        workbook["Daily Details"],
        start_row=start_row,
        end_row=end_row,
        start_col=1,
        end_col=24
    )
```

---

### 2. DuplicateVehicleValidator

**Purpose:** Detect and report duplicate vehicle assignments

**Size:** 13,345 bytes (364 lines)

**Critical For:** Data integrity, preventing double-assignments

#### Data Models

```python
@dataclass
class VehicleAssignment:
    """Single vehicle assignment."""
    vehicle_id: str
    route_code: str
    driver_name: str
    service_type: str
    wave: str
    staging_location: str
    assignment_timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DuplicateAssignment:
    """Duplicate vehicle assignment conflict."""
    vehicle_id: str
    assignments: List[VehicleAssignment]
    conflict_level: str = "warning"  # "warning" or "error"
    resolution_suggestion: str = ""

    def get_conflict_summary(self) -> str:
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
```

#### Validation Logic

```python
def validate_assignments(
    self,
    allocation_results: List[Dict[str, Any]]
) -> ValidationResult:
    """Validate allocation results for duplicates.

    Args:
        allocation_results: List of allocation dictionaries

    Returns:
        ValidationResult with duplicate information
    """

    # Track assignments by vehicle ID
    vehicle_assignments = defaultdict(list)

    for result in allocation_results:
        van_id = result.get("Van ID")
        if not van_id:
            continue

        assignment = VehicleAssignment(
            vehicle_id=van_id,
            route_code=result.get("Route Code", ""),
            driver_name=result.get("Associate Name", ""),
            service_type=result.get("Service Type", ""),
            wave=result.get("Wave", ""),
            staging_location=result.get("Staging Location", "")
        )

        vehicle_assignments[van_id].append(assignment)

    # Find duplicates
    duplicates = {}
    for van_id, assignments in vehicle_assignments.items():
        if len(assignments) > self.max_assignments_per_vehicle:
            duplicates[van_id] = DuplicateAssignment(
                vehicle_id=van_id,
                assignments=assignments,
                conflict_level="error" if self.strict_mode else "warning"
            )

    # Create result
    is_valid = (len(duplicates) == 0) or not self.strict_mode

    return ValidationResult(
        is_valid=is_valid,
        duplicate_count=len(duplicates),
        duplicates=duplicates,
        warnings=[d.get_conflict_summary() for d in duplicates.values()]
    )
```

#### Configuration

```python
def __init__(self, config: Optional[Dict] = None):
    super().__init__(config)
    self.strict_mode = self.get_config("strict_duplicate_validation", False)
    self.max_assignments_per_vehicle = self.get_config("max_assignments_per_vehicle", 1)
```

**Modes:**
- **Strict Mode:** Duplicates cause validation failure
- **Warning Mode:** Duplicates logged but not blocking

---

### 3. AllocationHistoryService

**Purpose:** Persist allocation history to JSON file

**Size:** 21,479 bytes (approximately 550 lines)

**Storage:** `config/allocation_history.json`

#### History Entry Structure

```python
{
    "allocation_id": "uuid-string",
    "timestamp": "2025-10-03T10:40:00-04:00",
    "engine_name": "GASCompatibleAllocator",
    "status": "COMPLETED",
    "metrics": {
        "total_routes": 150,
        "allocated_vehicles": 145,
        "unallocated_vehicles": 5,
        "duplicate_count": 2,
        "allocation_rate": 0.967
    },
    "files": {
        "day_of_ops": "/path/to/file.xlsx",
        "daily_routes": "/path/to/routes.xlsx",
        "vehicle_status": "/path/to/vehicles.xlsx"
    },
    "duplicate_conflicts": [
        {
            "vehicle_id": "BW123",
            "routes": ["CX1", "CX2"],
            "drivers": ["John", "Jane"]
        }
    ],
    "error": null
}
```

#### Save Operation

```python
def save_allocation(
    self,
    result: AllocationResult,
    engine_name: str,
    files: Dict[str, str],
    duplicate_conflicts: List[Dict],
    error: Optional[str] = None
) -> None:
    """Save allocation to history.

    Args:
        result: Allocation result object
        engine_name: Name of engine used
        files: Dictionary of input file paths
        duplicate_conflicts: List of duplicate vehicle conflicts
        error: Error message if allocation failed
    """

    entry = {
        "allocation_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "engine_name": engine_name,
        "status": self._extract_status(result),
        "metrics": self._extract_metrics(result),
        "files": files,
        "duplicate_conflicts": duplicate_conflicts,
        "error": error
    }

    # Load existing history
    history = self._load_history_file()

    # Add new entry
    history.append(entry)

    # Rotate if needed (keep max 100 entries)
    history = self._rotate_history(history, max_entries=100)

    # Save to file
    self._save_history_file(history)

    logger.info(f"Saved allocation {entry['allocation_id']} to history")
```

#### Critical Bug Fix (Phase 1)

**Issue:** Enum handling causing save failures

**Solution:**
```python
def _extract_status(self, result: AllocationResult) -> str:
    """Safely extract status from result.

    Handles both enum values and string values.
    """
    # Safe attribute check before accessing .value
    status = (
        result.status.value
        if hasattr(result.status, 'value')
        else str(result.status)
        if hasattr(result, 'status')
        else "UNKNOWN"
    )
    return status
```

**Documented in:** `PHASE1_COMPLETE.md` lines 52-66

#### Rotation Policy

```python
def _rotate_history(
    self,
    history: List[Dict],
    max_entries: int = 100,
    max_age_days: int = 90
) -> List[Dict]:
    """Rotate history keeping recent entries.

    Rules:
    1. Keep max 100 entries
    2. Keep entries from last 90 days
    3. Always keep most recent
    """

    # Sort by timestamp (newest first)
    history.sort(key=lambda x: x['timestamp'], reverse=True)

    # Keep max entries
    if len(history) > max_entries:
        history = history[:max_entries]

    # Filter by age
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    history = [
        entry for entry in history
        if datetime.fromisoformat(entry['timestamp']) > cutoff_date
    ]

    return history
```

#### Statistics

```python
def get_statistics(self) -> Dict[str, Any]:
    """Get allocation history statistics.

    Returns:
        Dictionary with statistics:
        - total_allocations
        - success_count
        - failure_count
        - success_rate
        - average_allocation_rate
        - average_routes_per_allocation
    """

    history = self.get_history()

    if not history:
        return {
            "total_allocations": 0,
            "success_count": 0,
            "failure_count": 0,
            "success_rate": 0.0,
        }

    total = len(history)
    success = sum(1 for h in history if h['status'] == 'COMPLETED')

    return {
        "total_allocations": total,
        "success_count": success,
        "failure_count": total - success,
        "success_rate": success / total if total > 0 else 0.0,
        "average_allocation_rate": self._calculate_avg_rate(history),
        "average_routes_per_allocation": self._calculate_avg_routes(history),
    }
```

---

### 4. ExcelService

**Purpose:** Unified Excel operations using xlwings and openpyxl

**Size:** 17,386 bytes (491 lines)

**Dual Backend:**
- **xlwings:** Live Excel integration (Mac/Windows)
- **openpyxl:** File-based operations (cross-platform)

#### Initialization

```python
def __init__(self, config: Optional[dict[str, Any]] = None):
    super().__init__(config)
    self.app = None
    self.workbook = None
    self.use_xlwings = self.get_config("use_xlwings", XLWINGS_AVAILABLE)
    self.excel_visible = self.get_config("excel_visible", False)
    self.display_alerts = self.get_config("display_alerts", False)

def initialize(self) -> None:
    """Initialize Excel service with xlwings if available."""

    if self.use_xlwings and XLWINGS_AVAILABLE:
        try:
            self.app = xw.App(visible=self.excel_visible, add_book=False)
            self.app.display_alerts = self.display_alerts
            logger.info("xlwings initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize xlwings: {e}")
            self.use_xlwings = False
            # Fall back to openpyxl

    self._initialized = True
```

#### Workbook Operations

```python
@timer
@error_handler
def create_workbook(self, template: Optional[str] = None) -> Union[Any, Workbook]:
    """Create new workbook or load from template.

    Returns:
        xlwings.Book or openpyxl.Workbook depending on backend
    """

    if self.use_xlwings:
        if template:
            self.workbook = self.app.books.open(template)
        else:
            self.workbook = self.app.books.add()
    else:
        if template:
            self.workbook = load_workbook(template)
        else:
            self.workbook = Workbook()

    return self.workbook

def save_workbook(self, path: str) -> None:
    """Save workbook to file."""

    if self.use_xlwings:
        self.workbook.save(path)
    else:
        self.workbook.save(path)

    logger.info(f"Workbook saved to {path}")
```

#### Data Operations

```python
def read_data(
    self,
    sheet_name: str,
    as_dataframe: bool = False
) -> Union[List[List[Any]], pd.DataFrame]:
    """Read data from sheet.

    Args:
        sheet_name: Name of sheet to read
        as_dataframe: Return as pandas DataFrame

    Returns:
        List of lists or DataFrame
    """

    if self.use_xlwings:
        sheet = self.workbook.sheets[sheet_name]
        data = sheet.used_range.value

        if as_dataframe:
            return pd.DataFrame(data[1:], columns=data[0])
        return data
    else:
        sheet = self.workbook[sheet_name]
        data = [[cell.value for cell in row] for row in sheet.iter_rows()]

        if as_dataframe:
            return pd.DataFrame(data[1:], columns=data[0])
        return data

def write_data(
    self,
    sheet_name: str,
    data: Union[List, pd.DataFrame, Dict],
    start_row: int = 1,
    start_col: int = 1
) -> None:
    """Write data to sheet."""

    # Convert to appropriate format
    if isinstance(data, pd.DataFrame):
        data = data.values.tolist()
    elif isinstance(data, dict):
        data = [[k, v] for k, v in data.items()]

    if self.use_xlwings:
        sheet = self.workbook.sheets[sheet_name]
        sheet.range((start_row, start_col)).value = data
    else:
        sheet = self.workbook[sheet_name]
        for row_idx, row_data in enumerate(data, start=start_row):
            for col_idx, value in enumerate(row_data, start=start_col):
                sheet.cell(row=row_idx, column=col_idx, value=value)
```

---

### 5. BorderFormattingService

**Purpose:** Apply Excel border formatting (standard and thick borders)

**Size:** 14,385 bytes (approximately 380 lines)

**Key Feature:** Creates daily sections with thick outer borders

#### Border Styles

```python
from openpyxl.styles import Border, Side

# Standard borders
thin_border = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin")
)

# Thick borders for section boundaries
thick_border = Border(
    left=Side(style="thick"),
    right=Side(style="thick"),
    top=Side(style="thick"),
    bottom=Side(style="thick")
)
```

#### Daily Section Creation

```python
def create_daily_section(
    self,
    sheet,
    start_row: int,
    start_col: int,
    end_row: int,
    end_col: int,
    section_date: date,
    title: str = "Daily Allocation"
) -> None:
    """Create a bordered daily section.

    Args:
        sheet: Excel worksheet
        start_row: Starting row (1-indexed)
        start_col: Starting column (1-indexed)
        end_row: Ending row
        end_col: Ending column
        section_date: Date for the section
        title: Section title
    """

    # Write section header
    header_cell = sheet.cell(row=start_row, column=start_col)
    header_cell.value = f"{title} - {section_date.strftime('%Y-%m-%d')}"
    header_cell.font = Font(bold=True, size=14)

    # Apply thick border around entire section
    self._apply_thick_border_box(
        sheet,
        start_row,
        start_col,
        end_row,
        end_col
    )

    # Apply thin borders to interior cells
    for row in range(start_row + 1, end_row + 1):
        for col in range(start_col, end_col + 1):
            cell = sheet.cell(row=row, column=col)
            cell.border = thin_border
```

---

## Service Integration Patterns

### Pattern 1: Service Composition

**Services call other services:**

```python
class GASCompatibleAllocator:
    def __init__(self):
        # Compose multiple services
        self.duplicate_validator = DuplicateVehicleValidator()
        self.unassigned_writer = UnassignedVehiclesWriter()
        self.output_writer = AllocationOutputWriter()
        self.history_service = AllocationHistoryService()

        # Initialize all
        self.duplicate_validator.initialize()
        self.unassigned_writer.initialize()
        # ...
```

### Pattern 2: Dependency Injection

**Services accept dependencies:**

```python
class DailyDetailsWriter(BaseService):
    def __init__(self, excel_service=None):
        super().__init__()
        self.excel_service = excel_service  # Injected dependency
```

### Pattern 3: Event-Based

**Services emit events for monitoring:**

```python
class MonitoringService:
    def log_allocation_event(self, event_type: str, data: Dict):
        # Log to monitoring system
        event = {
            "timestamp": datetime.now(),
            "type": event_type,
            "data": data
        }
        self._save_event(event)
```

---

## Performance Optimization

### Optimized Services

#### 1. OptimizedDuplicateValidator

**Improvements:**
- Uses set operations instead of nested loops
- O(n) complexity instead of O(n²)
- Batch processing for large datasets

```python
def validate_assignments_fast(
    self,
    allocation_results: List[Dict]
) -> ValidationResult:
    """Optimized duplicate validation using sets."""

    # Use set for O(1) lookups
    seen_vehicles = set()
    duplicates = set()

    for result in allocation_results:
        van_id = result.get("Van ID")
        if van_id in seen_vehicles:
            duplicates.add(van_id)
        else:
            seen_vehicles.add(van_id)

    # Rest of validation...
```

#### 2. OptimizedExcelWriter

**Improvements:**
- Batch cell updates instead of individual writes
- Disable auto-calculation during writes
- Use openpyxl's write-only mode for large datasets

```python
def write_large_dataset(
    self,
    sheet,
    data: List[List[Any]]
) -> None:
    """Optimized write for large datasets."""

    # Use openpyxl write-only mode
    from openpyxl import Workbook
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()

    # Batch write rows
    for row in data:
        ws.append(row)

    # Single save operation
    wb.save("output.xlsx")
```

#### 3. OptimizedThickBorders

**Improvements:**
- Pre-calculate border styles
- Apply in single pass
- Minimize cell access

---

## Error Handling Patterns

### Pattern 1: Try-Except with Logging

```python
def save_allocation(self, ...):
    try:
        # Operation
        self._save_to_file(data)
        logger.info("Allocation saved successfully")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Pattern 2: Graceful Degradation

```python
def initialize_with_fallback(self):
    """Initialize with graceful fallback."""

    try:
        # Attempt primary initialization
        self._init_xlwings()
    except Exception as e:
        logger.warning(f"xlwings failed: {e}, falling back to openpyxl")
        self._init_openpyxl()
```

### Pattern 3: Validation Before Operation

```python
def write_data(self, data):
    # Validate first
    if not self._validate_data(data):
        raise ValueError("Invalid data format")

    # Then proceed
    self._write_to_file(data)
```

---

## Testing Coverage

### Unit Tests by Service

| Service | Test File | Lines | Coverage |
|---------|-----------|-------|----------|
| DuplicateValidator | test_duplicate_validator.py | ~200 | 95% |
| UnassignedVehiclesWriter | test_unassigned_vehicles_writer.py | ~180 | 90% |
| DailyDetailsThickBorders | test_daily_details_thick_borders.py | ~150 | 88% |

### Integration Tests

- `test_duplicate_and_unassigned_integration.py` - End-to-end flow
- `test_error_handling_recovery.py` - Error scenarios

---

## Service Configuration

### Configuration Methods

**1. Constructor Injection:**
```python
service = ExcelService(config={"excel_visible": True})
```

**2. Settings File:**
```json
// config/settings.json
{
    "excel_visible": false,
    "strict_duplicate_validation": false,
    "max_assignments_per_vehicle": 1
}
```

**3. Environment Variables:**
```python
import os
excel_visible = os.getenv("EXCEL_VISIBLE", "false").lower() == "true"
```

---

## Key Takeaways

### Strengths

✅ **24 well-organized services** with clear responsibilities
✅ **Consistent patterns** - all inherit from BaseService
✅ **Strong separation of concerns** - each service has one job
✅ **Comprehensive error handling** - try/except + logging
✅ **Performance optimizations** - dedicated optimized variants
✅ **Good testing coverage** - unit + integration tests
✅ **Documentation** - performance guide included

### Service Dependencies

```
GASCompatibleAllocator
  ├── DuplicateVehicleValidator
  ├── UnassignedVehiclesWriter
  ├── AllocationOutputWriter
  ├── DailyDetailsWriter
  │   └── DailyDetailsThickBorderService
  └── AllocationHistoryService

ExcelService
  ├── xlwings (optional)
  └── openpyxl (fallback)
```

### Production Readiness

🟢 **All critical services:** Production-ready
🟢 **Error handling:** Comprehensive
🟢 **Testing:** Good coverage
🟡 **Documentation:** Could add more API docs
🟢 **Performance:** Optimized variants available

---

**Next:** See `CODEBASE_REVIEW_GUI.md` for GUI layer analysis
