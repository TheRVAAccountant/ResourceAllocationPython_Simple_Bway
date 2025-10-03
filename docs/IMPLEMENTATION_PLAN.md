# Implementation Plan: Daily Details Sheet Layout & GAS Compatibility

## Overview
This plan outlines the implementation of the Daily Details sheet layout matching Google Apps Script (GAS) format and ensuring consistent allocation processing between both systems.

## Phase 1: Data Model Updates

### 1.1 Update AllocationResult Model
**File**: `src/models/allocation.py`

Add new fields to match GAS Results sheet:
```python
class AllocationResult(BaseModel):
    # Existing fields
    allocations: dict[str, list[str]]
    unallocated_vehicles: list[str]
    
    # New fields for GAS compatibility
    route_code: str          # Route # (e.g., "DUL4-5-002")
    service_type: str        # Route Type (e.g., "Standard")
    dsp: str                 # Delivery Service Provider
    wave: str                # Wave assignment
    staging_location: str    # Staging area
    device_name: str         # Asset ID/Device
    van_type: str           # Vehicle Type
    operational: bool        # Operational status
    unique_identifier: str   # Date|Route|Device|VanID
```

### 1.2 Extend Vehicle and Driver Models
**Files**: `src/models/allocation.py`

Add GAS-specific fields:
```python
class Vehicle:
    # Add new fields
    vin: str
    geotab_code: str
    brand_or_rental: str  # "Branded" or "Rental"
    
class Driver:
    # Add new fields
    route_type: str
    wave: str
    staging_location: str
```

## Phase 2: Daily Details Writer Implementation

### 2.1 Create DailyDetailsWriter Class
**New File**: `src/services/daily_details_writer.py`

```python
class DailyDetailsWriter:
    """Handles writing allocation results to Daily Details sheet format."""
    
    DAILY_DETAILS_COLUMNS = [
        "Date", "Van", "VIN", "GeoTab", "UID", "Unique Identifier",
        "Name", "Route Type", "Route", "1:40pm", "3:00pm", "4:20pm",
        "5:40pm", "7:00pm", "8:20pm", "CC", "PC", "Location", "Area",
        "CSNP", "RD", "EOD", "Comments", "Additional Column"
    ]
    
    def __init__(self, excel_service):
        self.excel_service = excel_service
        
    def write_daily_details(self, workbook, allocations, date):
        """Write allocations to Daily Details sheet."""
        
    def create_results_sheet(self, workbook, allocations, date):
        """Create MM-DD-YY Results sheet."""
        
    def create_unassigned_sheet(self, workbook, unassigned, date):
        """Create MM-DD-YY Available & Unassigned sheet."""
        
    def generate_unique_identifier(self, date, route, device, van_id):
        """Generate unique identifier: Date|Route|Device|VanID."""
        return f"{date}|{route}|{device}|{van_id}"
```

### 2.2 Column Mapping Configuration
**New File**: `src/config/column_mappings.py`

```python
# Map Python fields to Daily Details columns
DAILY_DETAILS_MAPPING = {
    "Date": lambda r: r.allocation_date,
    "Van": lambda r: r.van_id,
    "VIN": lambda r: r.vin,
    "GeoTab": lambda r: r.geotab_code,
    "UID": lambda r: r.driver_id,
    "Unique Identifier": lambda r: r.unique_identifier,
    "Name": lambda r: r.driver_name,
    "Route Type": lambda r: r.service_type,
    "Route": lambda r: r.route_code,
    # Time columns initially empty
    "1:40pm": lambda r: "",
    "3:00pm": lambda r: "",
    # ... etc
}

# Results sheet columns (11 columns)
RESULTS_COLUMNS = [
    "Route Code", "Service Type", "DSP", "Wave", 
    "Staging Location", "Van ID", "Device Name",
    "Van Type", "Operational", "Associate Name",
    "Unique Identifier"
]
```

## Phase 3: Excel Service Updates

### 3.1 Modify ExcelService
**File**: `src/services/excel_service.py`

Add methods for GAS-compatible operations:
```python
def append_to_sheet(self, sheet_name, data, skip_duplicates=True):
    """Append data to existing sheet, checking for duplicates."""
    
def create_dated_sheet(self, base_name, date, suffix="Results"):
    """Create sheet with MM-DD-YY format."""
    sheet_name = f"{date.strftime('%m-%d-%y')} {suffix}"
    return self.create_sheet(sheet_name)
    
def apply_daily_details_formatting(self, sheet):
    """Apply GAS-style formatting to Daily Details."""
    # Teal headers (#46BDC6)
    # Thin borders
    # Bold headers
```

## Phase 4: Allocation Processing Updates

### 4.1 Update Allocation Tab
**File**: `src/gui/allocation_tab.py`

Modify `write_output` method:
```python
def write_output(self, output_file, result, allocation_date):
    """Write allocation results in GAS-compatible format."""
    
    # Option 1: Create new file with all sheets
    if self.create_new_file.get():
        self.excel_service.create_workbook()
        writer = DailyDetailsWriter(self.excel_service)
        
        # Create Daily Details sheet
        writer.write_daily_details(workbook, result, allocation_date)
        
        # Create dated Results sheet
        writer.create_results_sheet(workbook, result, allocation_date)
        
        # Create Unassigned sheet if needed
        if result.unallocated_vehicles:
            writer.create_unassigned_sheet(workbook, result, allocation_date)
            
    # Option 2: Append to existing Daily Summary Log
    else:
        self.excel_service.open_workbook(output_file)
        writer = DailyDetailsWriter(self.excel_service)
        
        # Append to Daily Details
        writer.append_daily_details(workbook, result, allocation_date)
        
        # Add new dated sheets
        writer.create_results_sheet(workbook, result, allocation_date)
```

### 4.2 Add Output Mode Selection
**File**: `src/gui/allocation_tab.py`

Add radio buttons for output mode:
```python
# Output mode selection
self.output_mode = StringVar(value="new")

new_file_radio = ctk.CTkRadioButton(
    config_frame,
    text="Create New File",
    variable=self.output_mode,
    value="new"
)

append_radio = ctk.CTkRadioButton(
    config_frame,
    text="Update Existing Daily Summary Log",
    variable=self.output_mode,
    value="append"
)
```

## Phase 5: Allocation Logic Alignment

### 5.1 Match GAS Allocation Process
**File**: `src/core/allocation_engine.py`

Ensure allocation logic matches GAS:
1. Load vehicles from Vehicle Log/Vehicles
2. Load drivers from Employees/Drivers
3. Process route assignments
4. Generate unique identifiers
5. Create Results with 11 columns
6. Update Daily Details with 24 columns
7. Track unassigned vehicles separately

### 5.2 Implement Vehicle Log Dictionary
```python
def build_vehicle_dictionary(self, vehicles_df):
    """Build dictionary matching GAS vehicleLogDict."""
    vehicle_dict = {}
    for _, row in vehicles_df.iterrows():
        van_id = row.get("Van ID", row.get("Vehicle Number"))
        vehicle_dict[van_id] = {
            "vin": row.get("VIN", ""),
            "geotab": row.get("GeoTab Code", ""),
            "brand_or_rental": row.get("Branded or Rental", "")
        }
    return vehicle_dict
```

## Phase 6: Testing & Validation

### 6.1 Create Test Suite
**New File**: `tests/test_gas_compatibility.py`

```python
def test_daily_details_format():
    """Test Daily Details sheet has correct 24 columns."""
    
def test_unique_identifier_generation():
    """Test unique ID format: Date|Route|Device|VanID."""
    
def test_results_sheet_format():
    """Test Results sheet has correct 11 columns."""
    
def test_duplicate_prevention():
    """Test that duplicate allocations are prevented."""
```

### 6.2 Comparison Script
**New File**: `scripts/compare_outputs.py`

```python
def compare_gas_vs_python_output(gas_file, python_file):
    """Compare outputs from both systems for consistency."""
    # Compare Daily Details structure
    # Compare Results sheets
    # Verify unique identifiers
    # Check formatting
```

## Implementation Timeline

### Week 1: Foundation
- [ ] Update data models (AllocationResult, Vehicle, Driver)
- [ ] Create DailyDetailsWriter class
- [ ] Implement column mappings

### Week 2: Core Implementation
- [ ] Update ExcelService with GAS methods
- [ ] Modify allocation tab for new output format
- [ ] Implement append mode

### Week 3: Testing & Polish
- [ ] Create test suite
- [ ] Run comparison tests
- [ ] Fix any compatibility issues
- [ ] Update documentation

## Key Considerations

### 1. Backward Compatibility
- Maintain support for existing Python format
- Add toggle for GAS compatibility mode

### 2. Performance
- Batch writes for large allocations
- Efficient duplicate checking

### 3. Data Integrity
- Validate all required fields
- Ensure unique identifiers are truly unique
- Preserve existing data when appending

### 4. User Experience
- Clear options for output format
- Progress indicators for long operations
- Helpful error messages

## Success Criteria

1. ✅ Python output matches GAS Daily Details format (24 columns)
2. ✅ Dated Results sheets created (MM-DD-YY format)
3. ✅ Unique identifiers prevent duplicates
4. ✅ Can append to existing Daily Summary Log
5. ✅ Vehicle details (VIN, GeoTab) populated from Vehicle Log
6. ✅ Unassigned vehicles tracked separately
7. ✅ Headers formatted with teal background (#46BDC6)
8. ✅ All test cases pass

## Risk Mitigation

### Risk 1: Data Loss
**Mitigation**: Always backup before appending, offer undo functionality

### Risk 2: Format Incompatibility
**Mitigation**: Extensive testing with real GAS outputs

### Risk 3: Performance Issues
**Mitigation**: Optimize for batch operations, add progress bars

## Next Steps

1. Review and approve implementation plan
2. Begin Phase 1: Data Model Updates
3. Set up development branch for GAS compatibility
4. Schedule testing with actual Daily Summary Log files