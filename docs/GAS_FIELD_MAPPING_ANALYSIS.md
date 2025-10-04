# GAS vs Python Field Mapping Analysis

## Overview
This document provides a comprehensive comparison of how fields are populated in the Google Apps Script (GAS) allocation system versus the Python implementation, with specific focus on route type mapping and ensuring complete field parity.

## Key Finding: Route Type vs Vehicle Type
**IMPORTANT**: There are two different "type" concepts in the system:
1. **Route Type** (Daily Details column): This is the **Service Type** from Day of Ops (e.g., "Standard Parcel - Large Van")
2. **Vehicle Type** (allocation logic): This is the mapped van type (e.g., "Large", "Extra Large", "Step Van")

## Field-by-Field Comparison

| Column # | Field Name | GAS Population | Python Current | Status | Action Required |
|----------|------------|----------------|----------------|---------|-----------------|
| 1 | Date | Current date (MM/dd/yyyy) | ✓ Current date | ✅ Match | None |
| 2 | Route # | Route Code from Day of Ops | ✓ Route Code from Day of Ops | ✅ Match | None |
| 3 | Name | Associate Name from Daily Routes | ✓ Associate Name from Daily Routes | ✅ Match | None |
| 4 | Asset ID | Device Name (same as Van ID) | ✓ Van ID | ✅ Match | None |
| 5 | Van ID | Assigned Van ID | ✓ Van ID | ✅ Match | None |
| 6 | VIN | From Vehicle Log lookup | ❌ From vehicle_log_dict if available | ⚠️ Partial | Need Vehicle Log sheet integration |
| 7 | GeoTab Code | From Vehicle Log lookup | ❌ From vehicle_log_dict if available | ⚠️ Partial | Need Vehicle Log sheet integration |
| 8 | Type | "Branded" or "Rental" from Vehicle Log | ❌ Uses vehicle_type instead | ❌ Wrong | Fix to use Vehicle Log data |
| 9 | Vehicle Type | Van Type from allocation | ✓ Van Type | ✅ Match | None |
| 10 | Route Type | **Service Type from Day of Ops** | ❌ "Standard" or "Nursery" | ❌ Wrong | Fix to use actual Service Type |
| 11 | Rescue | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 12-16 | Delivery Pace (5 columns) | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 17 | RTS TIME | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 18 | Pkg. Delivered | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 19 | Pkg. Returned | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 20 | Route Notes | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 21 | Week Number | Calculated from date | ✓ Calculated | ✅ Match | None |
| 22 | Unique Identifier | Date\|Route\|Driver\|Van | ✓ Same format | ✅ Match | None |
| 23 | Vehicle Inspection | Empty (form-populated) | ✓ Empty | ✅ Match | None |
| 24 | Route Completion | Empty (form-populated) | ✓ Empty | ✅ Match | None |

## Critical Fixes Required

### 1. Route Type Field (Column 10)
**Current Python**: Determines as "Standard" or "Nursery" based on service type
**GAS Behavior**: Directly uses Service Type from Day of Ops
**Fix**: Pass through the actual Service Type value

### 2. Type Field (Column 8)
**Current Python**: Uses vehicle_type (e.g., "Large", "Extra Large")
**GAS Behavior**: Uses "Branded" or "Rental" from Vehicle Log
**Fix**: Implement Vehicle Log lookup

### 3. Vehicle Log Integration
**Current Python**: Optional vehicle_log_dict parameter partially implemented
**GAS Behavior**: Always looks up VIN, GeoTab, and Type from Vehicle Log sheet
**Fix**: Add Vehicle Log sheet reading to GAS allocator

## Service Type Mapping Logic

### GAS Implementation:
```javascript
// For allocation (determining which van type is needed)
function getVanType(serviceType) {
  var mapping = {
    "Standard Parcel - Extra Large Van - US": "Extra Large",
    "Standard Parcel - Large Van": "Large",
    "Standard Parcel Step Van - US": "Step Van"
  };

  if (serviceType && serviceType.indexOf("Nursery Route Level") !== -1) {
    return "Large";
  }

  return mapping[serviceType] || null;
}

// For Daily Details population
// Route Type = Service Type (direct pass-through, no transformation)
```

### Python Implementation (Current):
```python
# Correctly maps for allocation
SERVICE_TYPE_TO_VAN_TYPE = {
    "Standard Parcel - Extra Large Van - US": "Extra Large",
    "Standard Parcel - Large Van": "Large",
    "Standard Parcel Step Van - US": "Step Van"
}

# Incorrectly transforms for Daily Details
route_type = "Standard"
if service_type and "Nursery" in service_type:
    route_type = "Nursery"
```

## Implementation Plan

### Phase 1: Fix Route Type Population
- Update `_prepare_allocation_rows` to use Service Type directly
- Remove the transformation logic for route_type

### Phase 2: Add Vehicle Log Integration
- Add Vehicle Log sheet reading to GAS allocator
- Create proper vehicle_log_dict with all fields
- Update Type field to use "Branded"/"Rental" classification

### Phase 3: Testing & Validation
- Create test cases with known GAS outputs
- Verify all 24 fields match exactly
- Test edge cases (missing data, non-standard service types)

## Data Flow Summary

```
Day of Ops (Solution sheet)
├── Route Code → Daily Details "Route #"
├── Service Type → Daily Details "Route Type" (direct)
└── Service Type → Van Type mapping → Vehicle allocation

Daily Routes (Routes sheet)
└── Route Code → Driver Name → Daily Details "Name"

Vehicle Status
└── Van ID + Type + Operational → Available vehicles for allocation

Vehicle Log (Daily Summary)
├── Van ID → VIN → Daily Details "VIN"
├── Van ID → GeoTab → Daily Details "GeoTab Code"
└── Van ID → Branded/Rental → Daily Details "Type"
```

## Next Steps
1. Implement route type fix (immediate)
2. Add Vehicle Log sheet integration
3. Update field mappings to match GAS exactly
4. Create comprehensive tests
5. Document any remaining differences
