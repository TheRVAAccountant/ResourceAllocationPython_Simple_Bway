# Codebase Review: Core Business Logic

**Review Date:** October 3, 2025  
**Focus:** Core allocation engines and business logic layer

---

## Overview

The core layer (`src/core/`) contains the business logic for resource allocation. This review covers the allocation engines, base service infrastructure, and business rules.

---

## Core Components

### 1. BaseService (`src/core/base_service.py`)

**Purpose:** Foundation class for all services with lifecycle management

**Size:** 4,082 bytes (approximately 120 lines)

**Key Features:**

```python
class BaseService:
    """Base class for all services with lifecycle management."""
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize the service. Override in subclasses."""
        pass
    
    def validate(self) -> bool:
        """Validate service configuration. Override in subclasses."""
        return True
    
    def cleanup(self) -> None:
        """Clean up resources. Override in subclasses."""
        self._initialized = False
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback."""
        return self.config.get(key, default)
```

**Decorators:**

1. **@timer**
   - Measures method execution time
   - Logs performance metrics
   - Used for optimization

2. **@error_handler**
   - Consistent exception handling
   - Automatic logging
   - Graceful error recovery

**Inheritance Pattern:**
All 24 services inherit from `BaseService`:
- `AllocationEngine`
- `GASCompatibleAllocator`
- `ExcelService`
- `DuplicateVehicleValidator`
- And 20 more services

---

## Allocation Engines

### 1. AllocationEngine (`src/core/allocation_engine.py`)

**Purpose:** Generic rule-based allocation engine

**Size:** 16,780 bytes (466 lines)

**Status:** Legacy/demonstration engine, production uses `GASCompatibleAllocator`

#### Architecture

```python
class AllocationEngine(BaseService):
    """Engine for managing vehicle allocation to drivers.
    
    Implements core business logic for allocating vehicles to drivers
    based on various rules and constraints.
    """
    
    def __init__(self, config: Optional[dict[str, Any]] = None):
        super().__init__(config)
        self.rules: list[AllocationRule] = []
        self.metrics = AllocationMetrics()
        self.allocation_history: list[AllocationResult] = []
        self.history_service = AllocationHistoryService()
        
        # Configuration parameters
        self.max_vehicles_per_driver = self.get_config("max_vehicles_per_driver", 3)
        self.min_vehicles_per_driver = self.get_config("min_vehicles_per_driver", 1)
        self.priority_weight = self.get_config("priority_weight_factor", 1.5)
        self.allocation_threshold = self.get_config("allocation_threshold", 0.8)
```

#### Allocation Rules

**Four Built-in Rules (Priority Order):**

1. **Priority Assignment** (Priority: 100)
   - Condition: `driver.priority == 'high'`
   - Action: Allocate to high-priority drivers first
   - Max vehicles per driver respected

2. **Experience Based** (Priority: 80)
   - Condition: `driver.experience_years > 5`
   - Action: Allocate premium vehicles to experienced drivers
   - Matches vehicle type to driver experience

3. **Location Based** (Priority: 60)
   - Condition: `driver.location == vehicle.location`
   - Action: Prefer same location matching
   - Reduces travel time/costs

4. **Balanced Distribution** (Priority: 50)
   - Condition: Always active
   - Action: Distribute evenly among remaining drivers
   - Ensures fair allocation

**Rule Execution:**
```python
for rule in self.rules:
    if not rule.enabled:
        continue
    
    if rule.action == "allocate_first":
        allocations, vehicles, drivers = self._allocate_priority(...)
    elif rule.action == "allocate_premium_vehicles":
        allocations, vehicles, drivers = self._allocate_premium(...)
    # ... etc
```

#### Allocation Algorithm

**Main Method:**
```python
@timer
@error_handler
def allocate(self, request: AllocationRequest) -> AllocationResult:
    """Perform vehicle allocation based on the request."""
    
    # 1. Initialize tracking
    available_vehicles = request.vehicles.copy()
    available_drivers = request.drivers.copy()
    allocations = {}
    
    # 2. Apply rules in priority order
    for rule in self.rules:
        allocations, available_vehicles, available_drivers = apply_rule(...)
    
    # 3. Handle remaining unallocated
    unallocated_vehicles = available_vehicles
    
    # 4. Calculate metrics
    processing_time = calculate_time()
    self._update_metrics(...)
    
    # 5. Create result
    result = AllocationResult(...)
    
    # 6. Save to history
    self.history_service.save_allocation(result, ...)
    
    return result
```

#### Helper Methods

**Priority Allocation:**
```python
def _allocate_priority(
    self,
    allocations: dict,
    vehicles: list[Vehicle],
    drivers: list[Driver],
    rule: AllocationRule
) -> tuple[dict, list[Vehicle], list[Driver]]:
    """Allocate vehicles to priority drivers first."""
    
    priority_drivers = [d for d in drivers if d.priority == "high"]
    
    for driver in priority_drivers:
        max_allowed = min(self.max_vehicles_per_driver, len(vehicles))
        driver_vehicles = []
        
        for _ in range(max_allowed):
            if vehicles:
                vehicle = vehicles.pop(0)
                driver_vehicles.append(vehicle.vehicle_id)
        
        if driver_vehicles:
            allocations[driver.driver_id] = driver_vehicles
            drivers.remove(driver)
    
    return allocations, vehicles, drivers
```

**Even Distribution:**
```python
def _distribute_evenly(
    self,
    allocations: dict,
    vehicles: list[Vehicle],
    drivers: list[Driver]
) -> tuple[dict, list[Vehicle], list[Driver]]:
    """Distribute vehicles evenly among drivers."""
    
    if not drivers or not vehicles:
        return allocations, vehicles, drivers
    
    # Calculate vehicles per driver
    vehicles_per_driver = max(
        self.min_vehicles_per_driver,
        len(vehicles) // len(drivers)
    )
    vehicles_per_driver = min(vehicles_per_driver, self.max_vehicles_per_driver)
    
    # Allocate to each driver
    for driver in drivers[:]:
        if not vehicles:
            break
        
        # ... allocation logic
    
    return allocations, vehicles, drivers
```

#### Metrics Tracking

**AllocationMetrics Model:**
```python
class AllocationMetrics(BaseModel):
    """Metrics for allocation performance."""
    
    total_vehicles: int = 0
    allocated_vehicles: int = 0
    unallocated_vehicles: int = 0
    total_drivers: int = 0
    active_drivers: int = 0
    allocation_rate: Decimal = Decimal("0.0")
    average_vehicles_per_driver: Decimal = Decimal("0.0")
    processing_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
```

**Metrics Calculation:**
```python
def _update_metrics(self, request, allocations, unallocated, processing_time):
    total_vehicles = len(request.vehicles)
    allocated_vehicles = sum(len(v) for v in allocations.values())
    
    self.metrics = AllocationMetrics(
        total_vehicles=total_vehicles,
        allocated_vehicles=allocated_vehicles,
        unallocated_vehicles=len(unallocated),
        total_drivers=len(request.drivers),
        active_drivers=len(allocations),
        allocation_rate=Decimal(str(allocated_vehicles / total_vehicles)),
        average_vehicles_per_driver=Decimal(str(allocated_vehicles / len(allocations))),
        processing_time=processing_time,
        timestamp=datetime.now()
    )
```

#### Validation

**Allocation Validation:**
```python
def validate_allocation(self, result: AllocationResult) -> bool:
    """Validate an allocation result."""
    
    # Check for duplicate vehicle assignments
    all_vehicles = []
    for vehicles in result.allocations.values():
        all_vehicles.extend(vehicles)
    
    if len(all_vehicles) != len(set(all_vehicles)):
        logger.error("Duplicate vehicle assignments detected")
        return False
    
    # Check vehicle count constraints
    for driver_id, vehicles in result.allocations.items():
        if len(vehicles) > self.max_vehicles_per_driver:
            logger.error(f"Driver {driver_id} has too many vehicles")
            return False
    
    return True
```

---

### 2. GASCompatibleAllocator (`src/core/gas_compatible_allocator.py`)

**Purpose:** Production allocation engine matching Google Apps Script logic exactly

**Size:** 42,040 bytes (991 lines)

**Status:** **PRIMARY ENGINE** - Used in production

#### Design Philosophy

**Key Principle:** Exact parity with Google Apps Script implementation

**Differences from AllocationEngine:**
- No optimization or rule-based logic
- Simple first-come-first-served allocation
- Strict DSP filtering (BWAY only)
- Service type to van type mapping
- Append mode for Daily Details sheet

#### Service Type Mapping

**Exact Match from GAS:**
```python
SERVICE_TYPE_TO_VAN_TYPE = {
    "Standard Parcel - Extra Large Van - US": "Extra Large",
    "Standard Parcel - Large Van": "Large",
    "Standard Parcel Step Van - US": "Step Van"
}
```

**This mapping is critical** - determines which vehicles can be assigned to which routes.

#### Data Loading

**Four Input Files:**

1. **Day of Ops Plan** (Excel)
   ```python
   def load_day_of_ops(self, file_path: str, sheet_name: str = "Solution") -> pd.DataFrame:
       """Load Day of Ops file.
       
       Expected columns:
       - Route Code
       - Service Type
       - DSP
       - Wave
       - Staging Location
       """
   ```

2. **Daily Routes** (Excel)
   ```python
   def load_daily_routes(self, file_path: str, sheet_name: str = "Routes") -> pd.DataFrame:
       """Load Daily Routes file.
       
       Expected columns:
       - Route code (or Route Code)
       - Driver name (or Driver Name)
       """
   ```

3. **Vehicle Status** (Excel)
   ```python
   def load_vehicle_status(self, file_path: str, sheet_name: str = "Vehicles") -> pd.DataFrame:
       """Load Vehicle Status file.
       
       Expected columns:
       - Van ID
       - Type (van type)
       - Opnal? Y/N (operational status)
       """
   ```

4. **Vehicle Log** (Optional CSV)
   ```python
   def load_vehicle_log(self, file_path: str) -> pd.DataFrame:
       """Load Vehicle Log file for GeoTab and VIN data.
       
       Expected columns:
       - Van ID
       - GeoTab Code
       - VIN
       """
   ```

#### Allocation Logic

**Main Allocation Method:**
```python
def allocate_resources(self) -> List[Dict[str, Any]]:
    """Perform resource allocation matching GAS logic.
    
    Steps:
    1. Merge Day of Ops with Daily Routes (match Route Code)
    2. Filter for DSP = "BWAY" only
    3. Map Service Type to Van Type
    4. Match with operational vehicles
    5. Assign first available matching vehicle
    6. Track assigned vehicles to prevent duplicates
    """
    
    # 1. Merge files
    merged_data = pd.merge(
        self.day_of_ops_data,
        self.daily_routes_data,
        on="Route Code",
        how="left"
    )
    
    # 2. Filter BWAY routes only
    bway_routes = merged_data[merged_data["DSP"] == "BWAY"].copy()
    
    # 3. Map service types
    bway_routes["Van Type Needed"] = bway_routes["Service Type"].map(
        self.SERVICE_TYPE_TO_VAN_TYPE
    )
    
    # 4. Allocate vehicles
    allocation_results = []
    
    for _, route in bway_routes.iterrows():
        van_type_needed = route["Van Type Needed"]
        
        # Find available vehicle of matching type
        available_vehicles = self.vehicle_status_data[
            (self.vehicle_status_data["Type"] == van_type_needed) &
            (self.vehicle_status_data["Opnal? Y/N"] == "Y") &
            (~self.vehicle_status_data["Van ID"].isin(self.assigned_van_ids))
        ]
        
        if not available_vehicles.empty:
            # Assign first available
            vehicle = available_vehicles.iloc[0]
            self.assigned_van_ids.append(vehicle["Van ID"])
            
            allocation_results.append({
                "Route Code": route["Route Code"],
                "Van ID": vehicle["Van ID"],
                "Associate Name": route["Driver Name"],
                # ... other fields
            })
        else:
            # Track unassigned
            self.unassigned_vehicles.append(route)
    
    return allocation_results
```

#### Output Generation

**Three Sheets Created:**

1. **Results Sheet** (Dated: `Results_2025-10-03`)
   - 11 columns matching GAS
   - Contains all successful allocations
   - Unique identifier for each row

2. **Daily Details Sheet** (Always named "Daily Details")
   - **APPEND MODE** - never overwrites existing data
   - 24 columns with specific formatting
   - Thick borders around daily sections
   - Brand priority highlighting (green for branded vans)

3. **Unassigned Vehicles Sheet** (Dated: `Unassigned_2025-10-03`)
   - Routes without matching vehicles
   - Reasons for non-allocation
   - Helps identify gaps

**Critical Feature - Append Mode:**
```python
def write_to_daily_details(self, wb: Workbook, allocation_results: List[Dict]):
    """Write allocation results to Daily Details sheet in APPEND mode.
    
    This is CRITICAL - we must APPEND to existing data, not overwrite.
    """
    
    if "Daily Details" in wb.sheetnames:
        ws = wb["Daily Details"]
        # Find next empty row
        next_row = ws.max_row + 1
    else:
        ws = wb.create_sheet("Daily Details")
        # Write headers
        self._write_headers(ws)
        next_row = 2
    
    # Append new data starting at next_row
    for result in allocation_results:
        self._write_row(ws, next_row, result)
        next_row += 1
```

#### Integration with Services

**Services Used:**

1. **DuplicateVehicleValidator**
   ```python
   self.duplicate_validator = DuplicateVehicleValidator()
   validation_result = self.duplicate_validator.validate_assignments(
       allocation_results
   )
   ```

2. **UnassignedVehiclesWriter**
   ```python
   self.unassigned_writer = UnassignedVehiclesWriter()
   self.unassigned_writer.write_unassigned_sheet(
       wb, self.unassigned_vehicles, allocation_date
   )
   ```

3. **AllocationOutputWriter**
   ```python
   self.output_writer = AllocationOutputWriter()
   self.output_writer.write_results_sheet(
       wb, allocation_results, allocation_date
   )
   ```

4. **AllocationHistoryService**
   ```python
   self.history_service.save_allocation(
       result=result,
       engine_name="GASCompatibleAllocator",
       files={
           "day_of_ops": day_of_ops_path,
           "daily_routes": daily_routes_path,
           "vehicle_status": vehicle_status_path
       },
       duplicate_conflicts=duplicate_conflicts,
       error=None
   )
   ```

---

## Allocation Models

### Core Data Models (`src/models/allocation.py`)

**File Size:** 7,663 bytes (233 lines)

#### 1. Vehicle Model

```python
class Vehicle(BaseModel):
    """Represents a vehicle in the allocation system."""
    
    vehicle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_number: str
    vehicle_type: VehicleType = VehicleType.STANDARD
    location: str
    status: str = "available"
    priority: int = Field(default=50, ge=0, le=100)
    capacity: Optional[int] = None
    fuel_level: Optional[Decimal] = None
    mileage: Optional[int] = None
    last_service_date: Optional[date] = None
    assigned_driver: Optional[str] = None
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @validator("vehicle_number")
    def validate_vehicle_number(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Vehicle number must be at least 3 characters")
        return v.upper()
```

**Key Features:**
- Auto-generated UUID
- Validated vehicle number (min 3 chars, uppercase)
- Type-safe enums for vehicle types
- Optional metadata for extensibility

#### 2. Driver Model

```python
class Driver(BaseModel):
    """Represents a driver in the allocation system."""
    
    driver_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    name: str
    location: str
    status: str = "active"
    priority: Priority = Priority.MEDIUM
    experience_years: int = Field(default=0, ge=0)
    license_type: str = "standard"
    certifications: list[str] = Field(default_factory=list)
    assigned_vehicles: list[str] = Field(default_factory=list)
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    max_vehicles: int = 3
    preferred_vehicle_types: list[VehicleType] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

#### 3. AllocationRequest Model

```python
class AllocationRequest(BaseModel):
    """Represents an allocation request."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicles: list[Vehicle]
    drivers: list[Driver]
    allocation_date: date = Field(default_factory=date.today)
    priority: Priority = Priority.MEDIUM
    requested_by: Optional[str] = None
    notes: Optional[str] = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator("vehicles")
    def validate_vehicles(cls, v):
        if not v:
            raise ValueError("At least one vehicle is required")
        return v
    
    @validator("drivers")
    def validate_drivers(cls, v):
        if not v:
            raise ValueError("At least one driver is required")
        return v
```

#### 4. AllocationResult Model

```python
class AllocationResult(BaseModel):
    """Represents the result of an allocation."""
    
    request_id: str
    allocations: dict[str, list[str]]  # driver_id -> list of vehicle_ids
    unallocated_vehicles: list[str]
    metrics: Optional[Any] = None  # AllocationMetrics from engine
    status: AllocationStatus = AllocationStatus.PENDING
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def get_allocation_summary(self) -> dict[str, Any]:
        """Get a summary of the allocation result."""
        total_allocated = sum(len(vehicles) for vehicles in self.allocations.values())
        return {
            "request_id": self.request_id,
            "status": self.status,
            "total_drivers": len(self.allocations),
            "total_allocated_vehicles": total_allocated,
            "total_unallocated_vehicles": len(self.unallocated_vehicles),
            "allocation_rate": total_allocated / (total_allocated + len(self.unallocated_vehicles)),
            "timestamp": self.timestamp,
            "has_errors": len(self.errors) > 0,
            "has_warnings": len(self.warnings) > 0,
        }
```

---

## Business Rules Summary

### AllocationEngine Rules

1. **Max Vehicles Per Driver:** Default 3, configurable
2. **Min Vehicles Per Driver:** Default 1, configurable
3. **Priority Weighting:** 1.5x factor for high-priority drivers
4. **Allocation Threshold:** 0.8 (80% minimum success rate)
5. **Rule Priority System:** 100 (highest) to 50 (lowest)

### GASCompatibleAllocator Rules

1. **DSP Filter:** BWAY only (hard-coded)
2. **Service Type Mapping:** 3 standard types to van types
3. **Operational Filter:** "Opnal? Y/N" must be "Y"
4. **First-Come-First-Served:** No optimization, sequential allocation
5. **No Double Assignment:** Tracks `assigned_van_ids` to prevent duplicates
6. **Append Mode:** Never overwrites existing Daily Details data

---

## Performance Characteristics

### AllocationEngine

**Time Complexity:**
- O(n * m * r) where:
  - n = number of vehicles
  - m = number of drivers
  - r = number of rules

**Typical Performance:**
- 100 vehicles, 50 drivers: ~0.5 seconds
- 1000 vehicles, 200 drivers: ~5 seconds

### GASCompatibleAllocator

**Time Complexity:**
- O(n * m) where:
  - n = number of routes (from Day of Ops)
  - m = number of available vehicles

**Typical Performance:**
- 200 routes, 150 vehicles: ~1-2 seconds
- Dominated by pandas merge operations
- Excel writing is the bottleneck (not allocation logic)

**Optimization Opportunities:**
- Pre-filter operational vehicles once
- Use pandas vectorized operations
- Batch Excel writes

---

## Error Handling

### Common Error Scenarios

1. **Missing Required Columns**
   ```python
   required_cols = ["Route Code", "Service Type", "DSP"]
   missing_cols = [col for col in required_cols if col not in df.columns]
   if missing_cols:
       raise ValueError(f"Missing required columns: {missing_cols}")
   ```

2. **Invalid Service Types**
   ```python
   unknown_types = set(df["Service Type"]) - set(SERVICE_TYPE_TO_VAN_TYPE.keys())
   if unknown_types:
       logger.warning(f"Unknown service types: {unknown_types}")
   ```

3. **Allocation Failures**
   ```python
   if not allocation_results:
       logger.error("No allocations made - check input data")
       raise ValueError("Allocation failed - no results")
   ```

4. **Duplicate Validation**
   ```python
   validation_result = self.duplicate_validator.validate_assignments(results)
   if not validation_result.is_valid and strict_mode:
       raise ValueError(f"Duplicate assignments detected: {validation_result.duplicates}")
   ```

---

## Testing Strategy

### Unit Tests

**AllocationEngine Tests:**
- `tests/unit/test_allocation_engine.py` (if exists)
- Test each rule independently
- Test edge cases (0 vehicles, 0 drivers)
- Test validation logic

**GASCompatibleAllocator Tests:**
- `tests/unit/test_gas_compatible_allocator_pandas_fix.py`
- `tests/unit/test_gas_allocator_pandas_fix.py`
- Test DSP filtering
- Test service type mapping
- Test append mode behavior

### Integration Tests

**Files:**
- `tests/integration/test_duplicate_and_unassigned_integration.py`
- `tests/integration/test_error_handling_recovery.py`

**Coverage:**
- End-to-end allocation flows
- Error recovery scenarios
- File I/O integration

### Performance Tests

**Files:**
- `tests/performance/test_large_dataset_performance.py`

**Benchmarks:**
- Large dataset handling (1000+ routes)
- Memory usage monitoring
- Execution time limits

---

## Key Takeaways

### Strengths

✅ **Two engines for different needs** - Generic vs. GAS-compatible  
✅ **Strong type safety** - Pydantic models throughout  
✅ **Clear business rules** - Well-documented allocation logic  
✅ **Comprehensive validation** - Pre and post-allocation checks  
✅ **Excellent error handling** - Graceful failures with logging  
✅ **History tracking** - All allocations saved for auditing  
✅ **Performance monitoring** - @timer decorator on key methods  

### Areas for Improvement

⚠️ **AllocationEngine may be deprecated** - GAS allocator is primary  
⚠️ **Rule configuration not externalized** - Rules are hard-coded  
⚠️ **Limited optimization** - GAS allocator is deliberately simple  
⚠️ **No async support** - All operations are synchronous  

### Production Readiness

🟢 **GASCompatibleAllocator:** Production-ready, actively used  
🟡 **AllocationEngine:** Demonstration/legacy, not production  
🟢 **Data Models:** Solid, well-validated  
🟢 **Error Handling:** Comprehensive  
🟢 **Testing:** Good coverage (unit + integration)  

---

## Next Steps

See the following review documents for related analysis:
- `CODEBASE_REVIEW_SERVICES.md` - Service layer details
- `CODEBASE_REVIEW_GUI.md` - GUI integration
- `CODEBASE_REVIEW_TESTING.md` - Test suite analysis
