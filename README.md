# Resource Allocation Python System

A comprehensive Python-based resource allocation system with Excel integration, designed to manage fleet allocation, scheduling, and reporting. This is a Python implementation of the ResourceAllocationClaude Google Apps Script system.

## Features

- **Modern GUI Interface**: Full-featured desktop application with CustomTkinter
- **Advanced Allocation Engine**: Intelligent vehicle-to-driver allocation based on configurable rules
- **Excel Integration**: Seamless integration with Excel using xlwings and openpyxl
- **Daily Section Management**: Automatic creation of bordered daily sections in Excel
- **Border Formatting**: Sophisticated border formatting similar to the original Google Sheets implementation
- **Email Notifications**: Automated email notifications for allocation results
- **Validation System**: Comprehensive data validation and error handling
- **Caching Layer**: Performance optimization through intelligent caching
- **Modular Architecture**: Clean separation of concerns with service-based architecture
- **Real-time Dashboard**: Live metrics and allocation statistics
- **Data Management**: Built-in vehicle and driver data editor
- **Log Viewer**: Real-time system log monitoring and analysis
- **Settings Management**: Comprehensive configuration interface

## Installation

### Prerequisites

- Python 3.12 or higher
- Microsoft Excel (for xlwings integration)
- Git

### Setup

1. Clone the repository:
```bash
cd /Users/jeroncrooks/CascadeProjects/ResourceAllocationPython
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Graphical User Interface (GUI)

Launch the modern desktop application:

```bash
# Start the GUI application
python gui_app.py
```

The GUI provides:
- **Dashboard Tab**: Real-time metrics and allocation statistics
- **Allocation Tab**: Run allocations with visual feedback
- **Data Management Tab**: Edit vehicles and drivers
- **Log Viewer Tab**: Monitor system logs in real-time
- **Settings Tab**: Configure all application settings

### GUI Icon Behavior

- The window title bar and taskbar/dock icon are set from `assets/icons/amazon_package.ico` at app startup.
- Path resolution supports both running from source and PyInstaller bundles.
- macOS: Tk does not natively set the Dock icon. The app attempts a best‑effort Dock icon via AppKit if available. For a guaranteed Dock icon when distributing a `.app`, include an `.icns` in the bundle's `Info.plist`.
- If the icon cannot be loaded, the app logs a warning and falls back without affecting functionality.

### Quick Icon Smoke Test

You can run a quick, non-interactive smoke test that loads the icon and initializes the GUI window long enough to set icons, then immediately destroys it:

```bash
python scripts/smoke_icon_test.py
```

This prints a success message if the icon is found and applied without errors.

### Command Line Interface

The system also provides a CLI for automation:

```bash
# Show help
python -m src.main --help

# Create sample data
python -m src.main create-sample --output sample_data.xlsx

# Run allocation
python -m src.main allocate --input sample_data.xlsx --output results.xlsx --date 2025-01-04

# Show version
python -m src.main version
```

### Python API

```python
from src.main import ResourceAllocationApp
from datetime import date

# Initialize application
app = ResourceAllocationApp()

# Run allocation
app.run_allocation(
    input_file="input.xlsx",
    output_file="output.xlsx",
    allocation_date=date.today()
)
```

### Excel Template Structure

Input Excel file should have two sheets:

1. **Vehicles Sheet**:
   - Vehicle Number
   - Type (standard/premium/economy)
   - Location
   - Status
   - Priority (0-100)
   - Capacity
   - Notes

2. **Drivers Sheet**:
   - Employee ID
   - Name
   - Location
   - Status
   - Priority (low/medium/high)
   - Experience (years)
   - License Type
   - Max Vehicles
   - Notes

## Architecture

### Core Components

1. **Allocation Engine** (`src/core/allocation_engine.py`)
   - Implements core business logic
   - Rule-based allocation system
   - Optimization algorithms
   - Metrics tracking

2. **Excel Service** (`src/services/excel_service.py`)
   - Workbook operations
   - Data reading/writing
   - Style application
   - Formula management

3. **Border Formatting Service** (`src/services/border_formatting_service.py`)
   - Daily section creation
   - Thick border application
   - Conditional formatting
   - Cell highlighting

4. **Data Models** (`src/models/`)
   - Pydantic models for data validation
   - Type safety
   - Serialization/deserialization

### Service Architecture

```
┌─────────────────────────────────────────┐
│           Main Application              │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Allocation Engine               │
│  - Business Rules                       │
│  - Optimization                         │
│  - Validation                          │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│          Service Layer                  │
│  ┌──────────────┐  ┌──────────────┐   │
│  │Excel Service │  │Email Service │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │Border Service│  │Cache Service │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Excel Configuration
EXCEL_VISIBLE=False
EXCEL_DISPLAY_ALERTS=False

# Allocation Rules
MAX_VEHICLES_PER_DRIVER=3
MIN_VEHICLES_PER_DRIVER=1
PRIORITY_WEIGHT_FACTOR=1.5

# Email Settings
EMAIL_ENABLED=True
EMAIL_HOST=smtp.gmail.com
EMAIL_USERNAME=your-email@gmail.com
```

### Business Rules

The allocation engine uses configurable rules:

1. **Priority Assignment**: High-priority drivers get vehicles first
2. **Experience Based**: Experienced drivers get premium vehicles
3. **Balanced Distribution**: Even distribution among drivers
4. **Location Based**: Prefer same location matching

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_allocation_engine.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Migration from Google Apps Script

This Python implementation maintains compatibility with the original Google Apps Script system:

### Feature Parity

- ✅ Daily section creation with thick borders
- ✅ Allocation algorithm with business rules
- ✅ Email notifications
- ✅ Form data processing
- ✅ Validation and error handling
- ✅ Caching for performance

### Advantages of Python Version

1. **Performance**: Faster processing for large datasets
2. **Testing**: Comprehensive unit and integration tests
3. **Type Safety**: Strong typing with Pydantic models
4. **Flexibility**: Can run on any platform
5. **Integration**: Easy integration with other Python tools
6. **Version Control**: Better Git integration

### Migration Path

1. Export data from Google Sheets to Excel
2. Run Python allocation engine
3. Import results back to Google Sheets (if needed)

## Troubleshooting

### Common Issues

1. **xlwings not working on macOS**:
   ```bash
   # Install xlwings with conda
   conda install xlwings
   ```

2. **Excel not opening**:
   - Ensure Excel is installed
   - Check EXCEL_VISIBLE setting in .env

3. **Permission errors**:
   - Run as administrator (Windows)
   - Check file permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code quality checks
6. Submit a pull request

## License

This project is proprietary and confidential.

## Support

For issues and questions, please contact the Resource Allocation Team.

## GUI Features

### Dashboard
- Real-time allocation metrics
- System status monitoring
- Recent allocation history
- Service health indicators

### Allocation Management
- Visual allocation workflow
- Progress tracking
- Result visualization
- Export capabilities

### Data Management
- Interactive data tables
- CRUD operations for vehicles/drivers
- Import/Export functionality
- Data validation

### Settings
- Comprehensive configuration interface
- Import/Export settings
- Theme switching (Dark/Light mode)
- Advanced options

## Roadmap

- [x] Desktop GUI with CustomTkinter
- [ ] Web UI using Streamlit
- [ ] Real-time allocation updates
- [ ] Machine learning optimization
- [ ] Multi-location support
- [ ] Advanced reporting dashboard
- [ ] API endpoints for integration
- [ ] Database backend option
- [ ] Scheduling automation
- [ ] Drag-and-drop file support
- [ ] Multi-language support
