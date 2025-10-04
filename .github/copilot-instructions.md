# Copilot Instructions - Resource Allocation Python System

## System Overview

**Business Purpose**: Production fleet management system for daily delivery operations - allocates vehicles to drivers based on route requirements.

**Critical Context**: This is a **Python re-implementation of a Google Apps Script (GAS) system**. Exact behavioral and formatting compatibility with the original GAS workflow is paramount - operators depend on precise Excel output matching existing templates.

## Architecture & Core Components

### Service-Oriented Architecture
```
src/
├── core/                           # Business logic
│   ├── allocation_engine.py        # General allocation algorithms
│   ├── gas_compatible_allocator.py # GAS workflow implementation (PRIMARY)
│   └── base_service.py             # Service base pattern
├── services/                       # Specialized services
│   ├── excel_service.py            # Excel I/O (xlwings + openpyxl)
│   ├── daily_details_writer.py    # 24-column output formatter
│   ├── duplicate_validator.py     # Assignment conflict detection
│   └── unassigned_vehicles_writer.py # Unallocated vehicle reporting
├── models/                         # Pydantic data models
├── gui/                            # CustomTkinter desktop app
└── utils/                          # Helpers
```

**Pattern**: All services inherit from `BaseService` (abstract base class with `initialize()`, `validate()`, `cleanup()` lifecycle methods). Use `@timer` and `@error_handler` decorators from `base_service.py` for performance monitoring and structured error handling.

## Critical Business Logic

### GAS-Compatible Allocation Workflow (PRIMARY SYSTEM)

The `GASCompatibleAllocator` in `src/core/gas_compatible_allocator.py` is the **production allocation engine**. It implements exact Google Apps Script logic:

**3-File Input Workflow**:
1. **Day of Ops** (`Solution` sheet): Route definitions, service types, DSP assignments
2. **Daily Routes**: Driver-to-route mappings
3. **Daily Summary Log**: Vehicle status (input) AND results output destination

**Allocation Rules** (strict order):
```python
# 1. Filter: Only DSP = "BWAY" routes
# 2. Filter: Only vehicles with Opnal? Y/N = "Y"
# 3. Service Type → Van Type mapping:
SERVICE_TYPE_TO_VAN_TYPE = {
    "Standard Parcel - Extra Large Van - US": "Extra Large",
    "Standard Parcel - Large Van": "Large",
    "Standard Parcel Step Van - US": "Step Van"
}
# Special: "Nursery Route Level X" → "Large"
# 4. First-Come-First-Served (no optimization algorithms)
```

**Output Sheets** (writes to Daily Summary Log):
- **Daily Details**: 24-column historical accumulation (exact GAS format)
- **MM-DD-YY Results**: Today's allocations (11 columns)
- **MM-DD-YY Available & Unassigned**: Unallocated vehicles

### Excel Template Compliance

**Non-negotiable**: Excel output must match exact GAS formatting. The system has comprehensive documentation in `docs/GAS_COMPLIANCE_SUMMARY.md` and `docs/GAS_FIELD_MAPPING_ANALYSIS.md`.

**Key constraints**:
- 24-column Daily Details structure (see `DailyDetailsWriter.DAILY_DETAILS_COLUMNS`)
- Teal headers (#46BDC6), thick borders around daily sections
- Unique identifiers: `Date|Route|Driver|VanID` format
- Vehicle Log sheet integration for VIN/GeoTab/Type fields
- Append-only writes (never overwrite existing data)

### Data Validation

**Duplicate Vehicle Detection**: Critical safety feature preventing double-allocation. See `src/services/duplicate_validator.py`.

```python
# Before writing results, ALWAYS validate:
validator = DuplicateVehicleValidator()
result = validator.validate_allocations(allocation_results)
if result.has_duplicates():
    # Handle conflict - system shows detailed resolution UI
```

## Development Workflows

### Running Allocations

**GUI (Primary Interface)**:
```bash
python gui_app.py
# Allocation Tab: 3-file workflow with progress tracking
# Dashboard Tab: Real-time metrics
```

**Programmatic**:
```python
from src.core.gas_compatible_allocator import GASCompatibleAllocator

allocator = GASCompatibleAllocator()
result = allocator.run_full_allocation(
    day_of_ops_file="path/to/DayOfOps.xlsx",
    daily_routes_file="path/to/DailyRoutes.xlsx",
    vehicle_status_file="path/to/DailySummary.xlsx",  # Also output destination
    output_file="path/to/DailySummary.xlsx"           # Same file as input
)
```

### Testing

**Fixture-based pytest**: All fixtures in `tests/conftest.py` (579 lines of sample data generators).

```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test suites
pytest tests/unit/test_duplicate_validator.py  # Unit tests
pytest tests/integration/                       # Integration tests
pytest tests/performance/                       # Performance benchmarks
```

**Test data generation**: Use `create_gas_test_files.py` for sample Excel files.

### Code Quality Tools

```bash
# Auto-format (100 char line length)
black src/ tests/

# Lint and check
ruff check src/ tests/
mypy src/ --strict

# Sort imports
isort src/ tests/
```

**Configuration**: See `pyproject.toml` for Black/isort/mypy settings.

## Project-Specific Conventions

### Pydantic Models for Everything
All data structures use Pydantic for validation:
- `src/models/allocation.py`: Core domain models (Vehicle, Driver, AllocationRequest, AllocationResult)
- `src/models/excel.py`: Excel styling and structure
- Use `Field()` with validators for business rules

**Example**:
```python
from pydantic import BaseModel, Field, validator

class AllocationResult(BaseModel):
    request_id: str  # NOTE: Not allocation_id (common error)
    status: AllocationStatus
    # ... full validation logic in model
```

### Logging with loguru

```python
from loguru import logger

# Service initialization
logger.info("Initializing AllocationEngine")

# Performance tracking (auto via @timer decorator)
logger.debug(f"allocate_vehicles took 2.3451 seconds")

# Errors (auto via @error_handler decorator)
logger.error(f"Error in process_allocation: Invalid vehicle type")
```

Logs: `logs/resource_allocation_{time}.log` (7-day retention, daily rotation)

### Configuration Management

- Environment variables: `.env` file (use `python-dotenv`)
- User settings: `config/settings.json` (GUI preferences, file paths)
- Recent files: `config/recent_files.json` (GUI state)

### GUI Theme System

CustomTkinter with centralized theme tokens in `src/gui/utils/theme.py`:
```python
# Color tokens: (light_mode, dark_mode) tuples
ACCENTS = {
    "total_vehicles": ("#1f77b4", "#3498db"),
    "allocated": ("#2ca02c", "#27ae60"),
    # ... resolve via resolve_color()
}
```

## Performance Requirements

- **Allocation Processing**: <30 seconds for 1000 routes
- **Excel Loading**: <10 seconds for multi-file workflow
- **Memory**: <2GB peak for large datasets
- **Test Coverage**: >95% for new code

## Common Pitfalls

1. **Field name mismatch**: AllocationResult uses `request_id`, not `allocation_id` (Pydantic error)
2. **Excel formatting**: Always use `openpyxl` for styling (xlwings for live Excel only)
3. **Duplicate prevention**: Must validate BEFORE writing to Daily Details
4. **Route Type vs Vehicle Type**: Two different "type" fields - see `GAS_COMPLIANCE_SUMMARY.md`
5. **File overwrite**: Daily Summary Log is both input and output - use append mode

## Key Documentation

When modifying core logic, reference:
- `docs/GAS_IMPLEMENTATION_SUMMARY.md` - Complete GAS workflow spec
- `docs/GAS_COMPLIANCE_SUMMARY.md` - Field mapping and compliance details
- `CLAUDE.md` - Historical project context (comprehensive)
- `tests/conftest.py` - All test fixtures and sample data

## Success Criteria for Changes

1. ✅ **Functional**: Exact GAS workflow match (validate against sample files)
2. ✅ **Performance**: Meet benchmarks (use `@timer` decorator)
3. ✅ **Tested**: >95% coverage with integration tests
4. ✅ **Excel Compliance**: Output validates against template structure
5. ✅ **Type Safe**: Pass `mypy --strict` checks

**Remember**: This system runs daily operational planning. Reliability and exact output formatting are more important than clever optimization. When in doubt, match the GAS behavior exactly.
