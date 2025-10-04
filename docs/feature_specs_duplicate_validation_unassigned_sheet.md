# Feature Specifications: Duplicate Vehicle Assignment Validation & Unassigned Vehicles Sheet

## Executive Summary

This document outlines the technical specifications for two critical features to enhance the Resource Management System:

1. **Duplicate Vehicle Assignment Validation**: Detect and warn when a vehicle is assigned to multiple routes/drivers
2. **Unassigned Vehicles Sheet**: Create a dedicated sheet showing all unassigned vehicles after each allocation run

## Feature 1: Duplicate Vehicle Assignment Validation

### Overview
Implement validation to detect when the same vehicle is assigned to multiple routes or drivers, preventing operational conflicts and ensuring data integrity.

### Business Requirements
- Detect duplicate vehicle assignments during allocation process
- Display clear warnings in GUI when duplicates are detected
- Mark duplicates in Excel output with visual indicators
- Provide detailed information about conflicting assignments
- Allow allocation to continue with warnings (non-blocking)

### Technical Specifications

#### 1.1 Detection Logic
```python
class DuplicateVehicleValidator:
    """Validates for duplicate vehicle assignments across routes/drivers."""

    def validate_allocations(self, allocation_results: List[Dict]) -> ValidationResult:
        """
        Check for duplicate vehicle assignments.

        Returns:
            ValidationResult with:
            - is_valid: False if duplicates found
            - duplicates: Dict[vehicle_id, List[assignment_details]]
            - warnings: List of warning messages
        """
```

#### 1.2 Data Structure for Tracking
```python
@dataclass
class VehicleAssignment:
    vehicle_id: str
    route_code: str
    driver_name: str
    service_type: str
    wave: str
    staging_location: str
    assignment_timestamp: datetime

@dataclass
class DuplicateAssignment:
    vehicle_id: str
    assignments: List[VehicleAssignment]
    conflict_level: str  # "warning", "error"
    resolution_suggestion: str
```

#### 1.3 Integration Points

##### In GASCompatibleAllocator
- Add validation after `allocate_vehicles_to_routes()`
- Track assignments in a dictionary during allocation
- Return validation warnings in AllocationResult

##### In AllocationEngine
- Enhance existing `validate_allocation()` method
- Add duplicate tracking to allocation process
- Include warnings in AllocationMetrics

##### In Excel Output
- Add "Validation Warnings" column to Results sheet
- Highlight duplicate assignments with yellow background
- Create summary of duplicates in Daily Details

##### In GUI (allocation_tab.py)
- Display warning dialog when duplicates detected
- Show duplicate count in results summary
- Add option to export duplicate report

### Acceptance Criteria

1. **Detection Accuracy**
   - ✓ System detects 100% of duplicate vehicle assignments
   - ✓ No false positives for valid single assignments
   - ✓ Performance impact < 100ms for 1000 routes

2. **User Notification**
   - ✓ GUI shows modal warning with duplicate details
   - ✓ Warning includes vehicle ID, routes, and drivers affected
   - ✓ User can acknowledge and continue allocation

3. **Excel Integration**
   - ✓ Duplicate assignments highlighted in yellow
   - ✓ "Validation Status" column shows "DUPLICATE" for affected rows
   - ✓ Tooltip/comment shows conflicting assignments

4. **Reporting**
   - ✓ Summary section in results showing duplicate count
   - ✓ Detailed duplicate report exportable as CSV
   - ✓ Warnings logged with timestamp and details

## Feature 2: Unassigned Vehicles Sheet

### Overview
Create a dedicated Excel sheet that shows all operational vehicles that were not assigned during the allocation process, updated with each allocation run.

### Business Requirements
- Create sheet named "MM-DD-YY Available & Unassigned"
- Include all operational vehicles not assigned to routes
- Show vehicle details (ID, type, status, location, etc.)
- Update sheet with each allocation run
- Maintain historical sheets for tracking

### Technical Specifications

#### 2.1 Sheet Structure
```
Columns:
- Van ID (A)
- Vehicle Type (B)
- Operational Status (C)
- Last Known Location (D)
- Days Since Last Assignment (E)
- VIN (F)
- GeoTab Code (G)
- Branded or Rental (H)
- Notes (I)
- Unassigned Date (J)
- Unassigned Time (K)
```

#### 2.2 Implementation Classes
```python
class UnassignedVehiclesWriter:
    """Manages creation and update of unassigned vehicles sheet."""

    def create_unassigned_sheet(
        self,
        workbook: Workbook,
        unassigned_vehicles: pd.DataFrame,
        vehicle_log_dict: Dict[str, Dict],
        allocation_date: date
    ) -> None:
        """Create or update unassigned vehicles sheet."""

    def format_unassigned_sheet(self, worksheet: Worksheet) -> None:
        """Apply formatting to unassigned vehicles sheet."""

    def calculate_days_since_assignment(
        self,
        vehicle_id: str,
        historical_data: pd.DataFrame
    ) -> int:
        """Calculate days since vehicle was last assigned."""
```

#### 2.3 Integration Points

##### In GASCompatibleAllocator
- Call `identify_unassigned_vehicles()` after allocation
- Pass unassigned data to sheet writer
- Include vehicle details from Vehicle Log

##### In DailyDetailsWriter
- Add method to create unassigned sheet
- Apply consistent formatting with other sheets
- Handle sheet naming with date format

##### In Excel Service
- Support for creating new sheets with specific names
- Apply formatting and borders
- Set column widths and filters

### Sheet Formatting Specifications

1. **Header Row**
   - Bold font, size 11
   - Dark blue background (RGB: 0, 32, 96)
   - White text
   - Center alignment
   - AutoFilter enabled

2. **Data Rows**
   - Alternating row colors (white/light gray)
   - Borders around all cells
   - Date/time formatting for timestamps
   - Number formatting for days count

3. **Column Widths**
   - Van ID: 12
   - Vehicle Type: 15
   - Operational Status: 12
   - Other columns: Auto-fit

### Acceptance Criteria

1. **Sheet Creation**
   - ✓ Sheet created with correct name format "MM-DD-YY Available & Unassigned"
   - ✓ All unassigned operational vehicles included
   - ✓ No assigned vehicles appear in sheet

2. **Data Completeness**
   - ✓ All specified columns populated where data available
   - ✓ Vehicle Log data (VIN, GeoTab) correctly mapped
   - ✓ Days since assignment calculated accurately

3. **Formatting**
   - ✓ Headers formatted as specified
   - ✓ AutoFilter enabled on data range
   - ✓ Print-friendly layout with proper margins

4. **Updates**
   - ✓ New sheet created for each allocation run
   - ✓ Historical sheets preserved
   - ✓ Sheet added to Daily Summary Log file

## Implementation Approach

### Phase 1: Duplicate Validation (Week 1)
1. Implement validator class and data structures
2. Integrate with GASCompatibleAllocator
3. Add GUI warnings and dialogs
4. Update Excel output with validation columns

### Phase 2: Unassigned Sheet (Week 2)
1. Create UnassignedVehiclesWriter class
2. Integrate with allocation workflow
3. Implement formatting specifications
4. Add historical tracking logic

### Phase 3: Testing & Refinement (Week 3)
1. Unit tests for both features
2. Integration testing with real data
3. Performance optimization
4. User acceptance testing

## Technical Considerations

### Performance
- Duplicate checking: O(n) complexity using hash maps
- Sheet creation: < 2 seconds for 500 vehicles
- Memory usage: Minimal increase (< 10MB)

### Error Handling
- Graceful handling of missing vehicle data
- Recovery from Excel write failures
- Clear error messages for users

### Backwards Compatibility
- Existing allocation logic unchanged
- New features are additive only
- No breaking changes to APIs

## Testing Strategy

### Unit Tests
```python
def test_duplicate_detection():
    """Test duplicate vehicle assignment detection."""

def test_unassigned_sheet_creation():
    """Test unassigned vehicles sheet creation."""

def test_validation_warnings():
    """Test warning generation and display."""
```

### Integration Tests
- Full allocation workflow with duplicates
- Excel file generation and validation
- GUI interaction testing

### Edge Cases
- Empty unassigned list
- All vehicles assigned
- Missing vehicle log data
- Large datasets (1000+ vehicles)

## Rollback Plan
Both features can be disabled via configuration:
```python
ENABLE_DUPLICATE_VALIDATION = True
ENABLE_UNASSIGNED_SHEET = True
```

## Success Metrics
- Zero undetected duplicate assignments
- 100% accuracy in unassigned vehicle tracking
- < 5% increase in allocation processing time
- Positive user feedback on clarity of warnings

## Future Enhancements
1. Auto-resolution suggestions for duplicates
2. Unassigned vehicle trends dashboard
3. Email alerts for critical duplicates
4. API endpoint for duplicate checking
