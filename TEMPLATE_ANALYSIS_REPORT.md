# Daily Summary Log 2025.xlsx - Template Structure Analysis Report

**File Analyzed:** `/Users/jeroncrooks/CascadeProjects/ResourceAllocationPython/Daily Summary Log 2025.xlsx`
**Analysis Date:** August 4, 2025
**File Size:** 0.23 MB

## Executive Summary

The Daily Summary Log 2025.xlsx file serves as the master template for resource allocation output files. It contains 28 sheets with three main categories:

1. **Daily Details** - Main comprehensive tracking sheet
2. **Date-specific sheets** - Daily results and availability tracking
3. **Configuration sheets** - Reference data and system settings

## Sheet Structure Overview

### 1. Daily Details Sheet (Primary Output Format)

**Purpose:** Central tracking sheet for all daily allocation activities

**Dimensions:** 1,085 rows × 42 columns (24 active data columns)

**Key Characteristics:**
- **Headers:** Bold, teal background (#46BDC6)
- **Data Format:** Tabular with consistent formatting
- **Primary Key:** Date + Route # combination

#### Column Structure (24 columns):

| # | Column Name | Data Type | Excel Format | Purpose |
|---|-------------|-----------|--------------|---------|
| 1 | Date | datetime | mm/dd/yyyy | Allocation date |
| 2 | Route # | string | - | Route identifier (CX1, CX2, etc.) |
| 3 | Name | string | - | Employee full name |
| 4 | Asset ID | string | - | Asset identifier |
| 5 | Van ID | string | - | Vehicle identifier (BW prefix) |
| 6 | VIN | string | - | Vehicle identification number |
| 7 | GeoTab Code | string | - | GPS tracking code |
| 8 | Type | string | - | Service type |
| 9 | Vehicle Type | string | - | Vehicle classification |
| 10 | Route Type | string | - | Route classification |
| 11 | Rescue | string | - | Rescue assignment (optional) |
| 12-16 | Delivery Pace [Time] | float | 0.00 | Delivery progress tracking |
| 17 | RTS TIME | time | h:mm am/pm | Return to station time |
| 18 | Pkg. Delivered | integer | 0 | Package delivery count |
| 19 | Pkg. Returned | integer | 0 | Package return count |
| 20 | Route Notes | string | - | Additional notes |
| 21 | Week Number | float | 0 | Week identifier |
| 22 | Unique Identifier | string | - | Composite unique key |
| 23 | Vehicle Inspection | string | - | Inspection status |
| 24 | Route Completion | string | - | Completion status |

#### Sample Data Pattern:
```
Date: 2025-02-26 00:00:00
Route #: CX9
Name: Marquis Thomas
Asset ID: BW2
Van ID: BW2
...
```

### 2. Date-Specific Sheets

#### Available & Unassigned Sheets
**Format:** `MM-DD-YY - Available & Unassign`
**Purpose:** Track vehicles not assigned to routes

**Dimensions:** 11 rows × 15 columns

**Column Structure:**
1. Van ID
2. Year
3. Make
4. Model
5. Style
6. Type
7. License Tag Number
8. License Tag State
9. Ownership
10. VIN
11. Van Type
12. Issue
13. Date GROUNDED
14. Date UNGROUNDED
15. Opnal? Y/N

#### Results Sheets
**Format:** `MM-DD-YY - Results`
**Purpose:** Daily allocation results

**Dimensions:** 18 rows × 11 columns

**Column Structure:**
1. Route Code
2. Service Type
3. DSP
4. Wave (time format: h:mm am/pm)
5. Staging Location
6. Van ID
7. Device Name
8. Van Type
9. Operational
10. Associate Name
11. Unique Identifier

### 3. Configuration/Reference Sheets

| Sheet Name | Purpose | Key Columns |
|------------|---------|-------------|
| Employees | Employee master data | Employee ID, Full Name, Status, Email, Department |
| Route Types | Route classifications | Route Type |
| Vehicle Status | Vehicle master data | Van ID, Year, Make, Model, Style |
| System Configuration | System settings | Category, Path, Value, Type |
| System Logs | Application logs | Timestamp, Level, Message |
| Form Management | Form definitions | Form ID, Name, Status |
| Vehicle Log | Vehicle history | Van ID, Date, Event, Notes |
| Gas Cards | Fuel card assignments | Card ID, Van ID, Status |

## Formatting Standards

### Header Formatting
- **Font:** Calibri, 11pt, Bold
- **Background:** Teal (#46BDC6)
- **Text Color:** Black
- **Alignment:** Center
- **Borders:** Thin borders around cells

### Data Formatting
- **Font:** Calibri, 11pt, Regular
- **Date Format:** mm/dd/yyyy
- **Time Format:** h:mm am/pm
- **Number Format:** Preserve decimal places as needed
- **Borders:** Applied to Daily Details sheet for data separation

## Naming Conventions

### Sheet Names
- Main sheet: "Daily Details"
- Daily sheets: "MM-DD-YY - Description"
- Configuration: Descriptive names (e.g., "Employees", "Route Types")

### Data Conventions
- **Route Codes:** CX prefix + number (CX1, CX2, CX3, etc.)
- **Vehicle IDs:** BW prefix + number (BW1, BW2, BW100, etc.)
- **Staging Locations:** STG.G.X format (STG.G.1, STG.G.2, etc.)
- **Unique Identifiers:** Composite format (Route-Date-Sequence)

## Implementation Requirements

### Essential Features
1. **Exact Column Matching:** Preserve all column headers and order
2. **Formatting Consistency:** Apply template formatting (colors, fonts, borders)
3. **Data Type Preservation:** Maintain proper Excel data types
4. **Number Format Preservation:** Keep Excel number formats for dates/times
5. **Sheet Naming:** Follow MM-DD-YY format for date-specific sheets

### Data Validation
- Date fields must be valid datetime objects
- Route codes must follow CX prefix pattern
- Vehicle IDs must follow BW prefix pattern
- Required fields must not be empty
- Time formats must be properly formatted

### Performance Considerations
- Large data sets (1000+ rows in Daily Details)
- Multiple sheets per workbook (28 sheets in template)
- Complex formatting requirements
- Excel file size optimization

## Key Insights

### Primary Usage Patterns
1. **Daily Details** serves as the master record for all allocation activities
2. **Date-specific sheets** provide focused views for individual days
3. **Configuration sheets** maintain reference data
4. **System sheets** track operational logs and errors

### Data Relationships
- Van ID links across Available & Unassigned and Results sheets
- Route codes connect Daily Details and Results sheets
- Employee names appear in both Daily Details and Results
- Unique Identifiers provide traceability across sheets

### Quality Indicators
- Consistent formatting across all active sheets
- Proper data types for all fields
- Comprehensive column coverage for business needs
- Logical sheet organization and naming

## Recommendations for Output File Generation

### Must-Have Features
1. **Template Fidelity:** Match the exact structure and formatting
2. **Data Integrity:** Ensure all required fields are populated
3. **Format Consistency:** Apply proper Excel formatting
4. **Sheet Organization:** Create sheets in logical order
5. **Performance:** Optimize for large data sets

### Best Practices
1. Use the provided `TemplateStructure` class for consistent formatting
2. Validate data before writing to ensure template compliance
3. Apply formatting after data population for better performance
4. Test with sample data to verify template accuracy
5. Implement error handling for missing or invalid data

### Code Implementation
The analysis includes three Python scripts:
- `analyze_template_structure.py` - Comprehensive structure analysis
- `focused_structure_analysis.py` - Key pattern identification
- `template_structure_guide.py` - Implementation templates and sample generation

Use these scripts as the foundation for building output files that match the Daily Summary Log template exactly.

---

**Analysis Tools Created:**
- `/Users/jeroncrooks/CascadeProjects/ResourceAllocationPython/analyze_template_structure.py`
- `/Users/jeroncrooks/CascadeProjects/ResourceAllocationPython/focused_structure_analysis.py`
- `/Users/jeroncrooks/CascadeProjects/ResourceAllocationPython/template_structure_guide.py`
- `/Users/jeroncrooks/CascadeProjects/ResourceAllocationPython/sample_template_output.xlsx`

**Report Generated:** August 4, 2025