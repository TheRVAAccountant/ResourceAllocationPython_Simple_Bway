# Google Apps Script vs Python Implementation Comparison

## Overview
This document compares the Google Apps Script (GAS) and Python implementations of the Resource Management System, highlighting differences and ensuring compatibility.

## Input File Requirements

### Google Apps Script Expected Structure

#### Primary File: Daily Summary Log
- **Filename Pattern**: `Daily Summary Log {YEAR}.xlsx`
- **Required Sheets**:
  1. **Vehicle Log**: Vehicle inventory data
     - Columns: Van ID, VIN, GeoTab Code, Branded or Rental, Location, Status, Priority, Notes
  2. **Employees**: Driver information
     - Columns: Employee ID (Col A), Name (Col B), Location, Status, Priority, Experience, License Type, Notes
  3. **Daily Details**: Daily allocation records with thick border formatting
     - Columns: Date, Van ID, VIN, GeoTab Code, Driver ID, Name, Route Type, Route Number, Start Time, End Time, 
       1:40pm, 3:00pm, 4:20pm, 5:40pm, 7:00pm, 8:20pm, Stops Remaining, Packages Remaining, Notes, Status, Unique Identifier
  4. **Route Types**: Route configuration
     - Columns: Route Type, Description, Priority, Max Stops, Max Packages

#### Upload Dialog Files
The GAS upload dialog (UploadDialog.html) expects two files:
1. **Day of Ops XLSX**: Operational data for the day
2. **Daily Routes XLSX**: Route assignments

### Python Application Structure

#### Original Python Naming
- **Vehicles** sheet (instead of "Vehicle Log")
  - Columns: Vehicle Number, Type, Location, Status, Priority, Capacity
- **Drivers** sheet (instead of "Employees")
  - Columns: Employee ID, Name, Location, Status, Priority, Experience, License Type

#### Updated Python Compatibility
The Python application now supports BOTH naming conventions:
- Automatically detects sheet names: "Vehicles" or "Vehicle Log"
- Automatically detects: "Drivers" or "Employees"
- Adapts column names based on detected sheet type

## Key Differences

### 1. Sheet Naming Conventions
| Purpose | Google Apps Script | Python (Original) | Python (Updated) |
|---------|-------------------|-------------------|------------------|
| Vehicles | Vehicle Log | Vehicles | Both supported |
| Drivers | Employees | Drivers | Both supported |
| Daily Records | Daily Details | Daily Details | Daily Details |

### 2. Column Naming Differences
| Data Type | GAS Column | Python Column | Notes |
|-----------|------------|---------------|-------|
| Vehicle ID | Van ID | Vehicle Number | Auto-detected |
| Driver ID | Employee ID | Employee ID | Same |
| Driver Name | Name | Name | Same |

### 3. Border Formatting
- **GAS**: Uses thick borders to separate daily sections in Daily Details
- **Python**: Implements BorderFormattingService to match GAS formatting

### 4. Form Integration
- **GAS**: Integrates with Google Forms for delivery pace tracking
- **Python**: GUI-based input without form integration

## Output File Naming

### Google Apps Script
- Fixed naming: Updates existing `Daily Summary Log {YEAR}.xlsx`
- Creates sheets like "Results", "Unassigned Vans"

### Python Application (Updated)
- Dynamic naming: `Allocation_Results_{YYYY-MM-DD}_{HH-MM}.xlsx`
- Example: `Allocation_Results_2025-01-04_14-30.xlsx`
- User can override with custom name

## Template Files Created

### For Google Apps Script Compatibility
1. **Daily_Summary_Log_2025.xlsx**: Main template matching GAS structure
2. **Day_of_Ops.xlsx**: Operational data input file
3. **Daily_Routes.xlsx**: Route assignment input file

### For Python Application
1. **Resource_Allocation_Template.xlsx**: Uses Python naming conventions
2. Supports both naming conventions automatically

## Usage Instructions

### Creating Templates
```bash
# Create all templates
python src/utils/create_template.py

# Create only GAS-compatible templates
python src/utils/create_template.py --gas

# Create only Python-compatible templates
python src/utils/create_template.py --python
```

### Running the Python Application
```bash
# With GUI
python gui_app.py

# The application will:
# 1. Auto-detect sheet naming convention
# 2. Load data from either format
# 3. Generate output with timestamp
```

## Validation and Error Handling

The Python application now includes:
1. **Sheet detection**: Automatically identifies which naming convention is used
2. **Error messages**: Clear feedback when required sheets are missing
3. **Column mapping**: Adapts to different column names between systems
4. **Format preservation**: Maintains thick border formatting like GAS

## Migration Path

To migrate from Google Apps Script to Python:
1. Export your Daily Summary Log from Google Sheets as .xlsx
2. Run the Python application
3. Select the exported file as input
4. The app will auto-detect the GAS format and process accordingly

## Compatibility Matrix

| Feature | GAS | Python | Compatible |
|---------|-----|--------|------------|
| Vehicle Log/Vehicles sheet | ✓ | ✓ | ✓ |
| Employees/Drivers sheet | ✓ | ✓ | ✓ |
| Daily Details sheet | ✓ | ✓ | ✓ |
| Thick border formatting | ✓ | ✓ | ✓ |
| Dynamic file naming | ✗ | ✓ | N/A |
| Google Forms integration | ✓ | ✗ | ✗ |
| Excel automation | ✗ | ✓ | N/A |
| Email notifications | ✓ | ✓ | ✓ |

## Summary

The Python implementation has been updated to be fully compatible with Google Apps Script file formats while maintaining its own conventions. Key improvements include:

1. **Dual Format Support**: Reads both GAS and Python sheet naming conventions
2. **Dynamic Naming**: Output files include timestamps for better organization
3. **Template Generation**: Utility to create compatible templates for both systems
4. **Clear Error Messages**: Helpful feedback when file format issues occur
5. **Border Formatting**: Matches GAS thick border daily sections

This ensures seamless transition between the two systems while maintaining data integrity and visual consistency.