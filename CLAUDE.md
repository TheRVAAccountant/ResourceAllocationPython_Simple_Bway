# Resource Allocation Python System - Project Context

This file provides essential context for all Claude Code agents working on the Resource Management System.

## Project Overview

**System Purpose**: Fleet management and vehicle-to-driver allocation for delivery operations
**Migration Context**: Python implementation of Google Apps Script (GAS) system
**Business Critical**: Handles daily operational planning for delivery routes and vehicle assignments
**Architecture**: Service-oriented Python application with Excel integration and desktop GUI

## Current System Architecture

### Core Components
```
src/
├── core/                    # Business logic and allocation algorithms
│   ├── allocation_engine.py # Main allocation algorithm implementation
│   ├── gas_compatible_allocator.py # GAS workflow compatibility layer
│   └── base_service.py     # Service base classes
├── models/                  # Pydantic data models
│   ├── allocation.py       # AllocationResult, AllocationRequest models
│   ├── excel.py           # Excel data structure models
│   └── email.py           # Email notification models
├── services/               # External service integrations
│   ├── excel_service.py   # Excel file operations (xlwings/openpyxl)
│   ├── border_formatting_service.py # Excel formatting and styling
│   └── email_service.py   # Email notification service
├── gui/                    # CustomTkinter desktop application
│   ├── main_window.py     # Main application window
│   ├── allocation_tab.py  # Allocation workflow interface
│   ├── dashboard_tab.py   # Metrics and monitoring dashboard
│   └── settings_tab.py    # Configuration management
└── utils/                  # Utility functions and helpers
```

### Data Flow Architecture
```
Excel Files → Data Validation → Allocation Engine → Results Generation → Excel Output
     ↓              ↓                   ↓                  ↓              ↓
Day of Ops    Business Rules    Priority Matching    Daily Details   Updated Files
Daily Routes  Type Validation   Vehicle Assignment   Results Sheet   Email Alerts
Daily Summary Error Handling    Driver Mapping       Unassigned      GUI Updates
```

## Business Logic & Domain Knowledge

### Resource Allocation Rules
1. **Priority-Based Assignment**: High-priority drivers get first choice of available vehicles
2. **Service Type Matching**: Match vehicle types to service requirements
   - "Standard Parcel - Extra Large Van - US" → "Extra Large" vehicles
   - "Standard Parcel - Large Van" → "Large" vehicles  
   - "Standard Parcel Step Van - US" → "Step Van" vehicles
   - "Nursery Route Level X" → "Large" vehicles
3. **Experience Weighting**: Experienced drivers get premium vehicles
4. **Location Preferences**: Same-location matching when possible
5. **Balanced Distribution**: Ensure fair workload across drivers

### Excel Workflow (GAS-Compatible)
**Input Files**:
- **Day of Ops Excel**: Route definitions, service types, DSP assignments
- **Daily Routes Excel**: Driver-to-route mappings
- **Daily Summary Log**: Vehicle status AND output destination

**Output Behavior**:
- Updates Daily Summary Log with results (no separate output file)
- Creates/updates three sheets:
  1. **Daily Details**: Historical accumulation of all allocations
  2. **MM-DD-YY Results**: Today's allocation results  
  3. **MM-DD-YY Available & Unassigned**: Unassigned vehicles

### Key Business Constraints
- DSP filtering: Only process routes where DSP = "BWAY"
- Vehicle operational status: Only assign vehicles where "Opnal?" = "Y"
- Route code format: CX1, CX2, CX3, etc.
- Vehicle ID format: BW1, BW2, BW100, etc.
- Staging location format: STG.G.1, STG.G.2, etc.

## Technical Specifications

### Technology Stack
- **Python**: 3.12+ with modern typing and async support
- **Excel Integration**: xlwings (interactive), openpyxl (formatting)
- **Data Models**: Pydantic for validation and type safety
- **GUI Framework**: CustomTkinter for modern desktop interface
- **Data Processing**: pandas with Excel optimization
- **Logging**: loguru for structured logging
- **Configuration**: python-dotenv for environment management

### Performance Requirements
- **Allocation Processing**: <30 seconds for 1000 routes
- **Excel File Loading**: <10 seconds for typical multi-file workflow
- **Memory Usage**: <2GB peak for large datasets
- **GUI Responsiveness**: <100ms response for user interactions
- **Template Compliance**: Exact formatting match for business workflows

### Quality Standards
- **Test Coverage**: >95% for all new code
- **Type Safety**: Full mypy compliance with strict mode
- **Code Quality**: Black formatting, ruff linting, isort imports
- **Documentation**: Comprehensive docstrings and technical docs
- **Error Handling**: Graceful handling of Excel file corruption and edge cases

## Current Development Context

### Recent Fixes & Improvements
- **Pydantic Validation Fix**: Resolved AllocationResult field name mismatch (request_id vs allocation_id)
- **GAS Workflow Compatibility**: Implemented exact Google Apps Script workflow matching
- **GUI Integration**: Updated to support 3-file input workflow with proper progress tracking
- **Template Analysis**: Comprehensive Excel template structure analysis and compliance

### Active Challenges
- **Excel Template Compliance**: Maintaining exact formatting and structure requirements
- **Performance Optimization**: Large dataset processing and memory management
- **Multi-file Workflow**: Complex coordination between 3 different Excel files
- **Error Recovery**: Robust handling of real-world Excel file variations
- **User Experience**: Simplifying complex workflows for daily operators

### Development Priorities
1. **Stability**: Robust error handling and recovery mechanisms
2. **Performance**: Optimization for production-scale datasets
3. **User Experience**: Intuitive workflows and clear error messaging
4. **Testing**: Comprehensive coverage for complex integration scenarios
5. **Documentation**: Clear operational procedures and user guides

## Agent Guidance

### For All Agents
- **Business Context First**: Always consider operational impact and user experience
- **Excel Integration Critical**: Maintain exact template compliance and formatting
- **Performance Matters**: Optimize for production scale (1000+ routes daily)
- **Error Handling Required**: Robust handling of real-world data variations
- **Testing Essential**: Comprehensive coverage for business-critical functionality

### Code Standards
- Use type hints and Pydantic models for all data structures
- Implement comprehensive error handling with structured logging
- Follow existing architectural patterns and service separation
- Maintain backward compatibility with existing Excel workflows
- Include performance monitoring and optimization considerations

### File Locations & Patterns
- **Core Business Logic**: `src/core/` directory
- **Excel Integration**: `src/services/excel_service.py` and related
- **GUI Components**: `src/gui/` with CustomTkinter patterns
- **Data Models**: `src/models/` with Pydantic validation
- **Tests**: `tests/unit/` and `tests/integration/` with pytest
- **Configuration**: `.env` files and `pyproject.toml` settings

### Success Criteria
- **Functional**: All business requirements met with exact workflow matching
- **Performance**: Meets production performance requirements
- **Quality**: High code quality with comprehensive testing
- **Usability**: Intuitive user experience for daily operators
- **Maintainable**: Clean architecture with clear documentation
- **Reliable**: Robust error handling and production stability

Remember: This is a business-critical system that handles daily operational planning. Always prioritize reliability, performance, and user experience while maintaining the exact Excel workflow requirements that operators depend on.
