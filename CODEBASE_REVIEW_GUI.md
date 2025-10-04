# Codebase Review: GUI Layer

**Review Date:** October 3, 2025
**Focus:** GUI components and user interface (`src/gui/`)

---

## Overview

Modern desktop application built with **CustomTkinter** providing a complete GUI for resource allocation operations.

**Technology:** CustomTkinter 5.2.0+ (modern Tkinter alternative)
**Architecture:** Tab-based interface with 7 main tabs
**Theme Support:** Dark/Light mode switching

---

## GUI Structure

```
src/gui/
├── main_window.py              # Main application window (715 lines)
├── dashboard_tab.py            # Dashboard with history (23,398 bytes)
├── allocation_tab.py           # Main allocation interface (46,629 bytes)
├── data_management_tab.py      # CRUD operations (44,345 bytes)
├── scorecard_tab.py            # PDF scorecard viewer (15,513 bytes)
├── associate_listing_tab.py    # Associate management (19,982 bytes)
├── settings_tab.py             # Configuration UI (34,367 bytes)
├── log_viewer_tab.py           # Log monitoring (13,696 bytes)
├── monitoring_tab.py           # System monitoring (22,589 bytes)
├── components/                 # Reusable UI components
│   ├── history_card.py         # Allocation history cards (189 lines)
│   └── metrics_card.py         # Dashboard metrics
├── dialogs/                    # Modal dialogs
│   ├── allocation_details_modal.py  # History details (283 lines)
│   └── settings_dialog.py
├── utils/                      # GUI utilities
│   ├── theme.py                # Theme definitions
│   ├── window_manager.py       # Window management
│   └── validators.py           # Input validation
└── widgets/                    # Custom widgets
    ├── file_picker.py
    ├── data_table.py
    └── status_indicator.py
```

---

## Main Application Window

**File:** `main_window.py` (715 lines, 28,749 bytes)

### Window Configuration

```python
class ResourceAllocationGUI(ctk.CTk):
    """Main GUI application window."""

    def __init__(self):
        super().__init__()

        # Load company name from settings
        self.company_name = self._read_company_name_from_settings()
        self.title(self._compose_app_title(self.company_name))
        self.geometry("1400x1000")
        self.minsize(1200, 900)

        # Set application icons
        self._set_app_icons()

        # Initialize services
        self.initialize_services()

        # Setup UI
        self.setup_ui()
```

### Service Initialization

```python
def initialize_services(self):
    """Initialize all backend services."""
    self.allocation_engine = AllocationEngine()
    self.excel_service = ExcelService()
    self.border_service = BorderFormattingService()
    self.dashboard_data_service = DashboardDataService()
    self.data_management_service = DataManagementService()
    self.associate_service = AssociateService()
    self.scorecard_service = ScorecardService()

    # Initialize all services
    for service in [self.allocation_engine, self.excel_service, ...]:
        service.initialize()
```

### Tab Registration

```python
def setup_ui(self):
    """Setup the UI with tabbed interface."""

    # Create tab view
    self.tabview = ctk.CTkTabview(self)
    self.tabview.grid(row=1, column=0, sticky="nsew")

    # Add tabs
    self.dashboard_tab = DashboardTab(self.tabview.add("📊 Dashboard"))
    self.allocation_tab = AllocationTab(self.tabview.add("🚗 Allocation"))
    self.data_mgmt_tab = DataManagementTab(self.tabview.add("📋 Data"))
    self.scorecard_tab = ScorecardTab(self.tabview.add("📈 Scorecard"))
    self.associate_tab = AssociateListingTab(self.tabview.add("👥 Associates"))
    self.settings_tab = SettingsTab(self.tabview.add("⚙️ Settings"))
    self.log_tab = LogViewerTab(self.tabview.add("📜 Logs"))
```

---

## Tab Components

### 1. Dashboard Tab

**Purpose:** Display allocation history and metrics
**Size:** 23,398 bytes

**Features:**
- Card-based history display (last 10 allocations)
- Real-time metrics (vehicles, drivers, allocation rate)
- Refresh button for manual updates
- Color-coded status badges (✓ success, ⚠️ duplicates, ❌ error)

**Key Implementation:**
```python
class DashboardTab:
    def load_history(self):
        """Load and display allocation history."""
        history = self.history_service.get_history(limit=10)

        for entry in history:
            card = HistoryCard(
                self.history_frame,
                allocation_data=entry,
                on_details_click=self.show_details
            )
            card.pack(fill="x", padx=5, pady=5)
```

### 2. Allocation Tab

**Purpose:** Main allocation workflow interface
**Size:** 46,629 bytes (largest tab)

**Workflow:**
1. File selection (Day of Ops, Daily Routes, Vehicle Status)
2. Allocation engine selection
3. Run allocation button
4. Progress display
5. Results summary
6. Error/warning display

**Key Features:**
- File picker widgets with validation
- Engine selector dropdown
- Progress bar during allocation
- Results table with export capability
- Duplicate conflict display

### 3. Data Management Tab

**Purpose:** CRUD operations for vehicles and drivers
**Size:** 44,345 bytes (second largest)

**Features:**
- Interactive data tables (Treeview)
- Add/Edit/Delete operations
- Import/Export to Excel
- Search and filter
- Data validation

### 4. Scorecard Tab

**Purpose:** View Amazon DSP performance scorecards
**Size:** 15,513 bytes

**Features:**
- PDF file loading
- Delivery Associate performance table
- Tier-based color coding (Fantastic, Great, Fair, Poor)
- Search by DA name
- Export to CSV

**Implementation:**
```python
class ScorecardTab:
    def load_scorecard(self, pdf_path: str):
        """Load and display scorecard PDF."""
        scorecard_data = self.scorecard_service.load_scorecard(pdf_path)

        # Display in Treeview
        for da in scorecard_data.delivery_associates:
            tier_color = self._get_tier_color(da.tier)
            self.tree.insert("", "end", values=(
                da.rank, da.name, da.tier, da.delivered, ...
            ), tags=(tier_color,))
```

### 5. Settings Tab

**Purpose:** Application configuration
**Size:** 34,367 bytes

**Features:**
- All config options in one place
- Import/Export settings (JSON)
- Theme switching (Dark/Light)
- File path configuration
- Email settings
- Allocation rules

### 6. Log Viewer Tab

**Purpose:** Real-time log monitoring
**Size:** 13,696 bytes

**Features:**
- Live log tail
- Log level filtering
- Search functionality
- Auto-scroll toggle

### 7. Associate Listing Tab

**Purpose:** Associate management
**Size:** 19,982 bytes

**Features:**
- Associate roster display
- Contact information
- Performance metrics
- Filter and search

---

## Reusable Components

### HistoryCard Widget

**File:** `src/gui/components/history_card.py` (189 lines)

**Purpose:** Display single allocation history entry

```python
class HistoryCard(ctk.CTkFrame):
    """Card widget for allocation history."""

    def __init__(self, parent, allocation_data: Dict, on_details_click):
        super().__init__(parent)

        # Header with status badge
        self._create_header(allocation_data)

        # Metrics row
        self._create_metrics(allocation_data)

        # Details button
        self._create_details_button(on_details_click)

        # Hover effects
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)
```

**Visual Design:**
- Color-coded status badge
- Hover effects (background change)
- Compact metrics display
- Click-to-expand details

### AllocationDetailsModal

**File:** `src/gui/dialogs/allocation_details_modal.py` (283 lines)

**Purpose:** Show comprehensive allocation details

**Sections:**
1. Summary (status, timestamp, metrics)
2. Files (input file paths)
3. Breakdown (allocation results table)

---

## Theme System

**File:** `src/gui/utils/theme.py`

**Color Tokens:**
```python
ACCENTS = {
    "total_vehicles": ("#3498db", "#5dade2"),      # Blue
    "total_drivers": ("#2ecc71", "#58d68d"),       # Green
    "allocated": ("#27ae60", "#52be80"),           # Dark green
    "allocation_rate": ("#f39c12", "#f8b739"),     # Orange
    "unallocated": ("#e74c3c", "#ec7063"),         # Red
}

STATUS = {
    "active": ("#27ae60", "#52be80"),    # Green
    "disabled": ("#95a5a6", "#aab7b8"),  # Gray
    "inactive": ("#e67e22", "#eb984e"),  # Orange
}
```

**Usage:**
```python
def resolve_color(token: str) -> str:
    """Resolve color token to current theme."""
    appearance = ctk.get_appearance_mode()
    colors = ACCENTS.get(token, ("#000000", "#ffffff"))
    return colors[0] if appearance == "Light" else colors[1]
```

---

## Data Flow: GUI → Service → Core

### Example: Running Allocation

```
1. User clicks "Run Allocation" (AllocationTab)
   ↓
2. Tab validates file selections
   ↓
3. Tab calls allocation_tab.run_allocation()
   ↓
4. Tab creates progress dialog
   ↓
5. Tab calls GASCompatibleAllocator.allocate_resources()
   ↓
6. Allocator loads files via services
   ↓
7. Allocator performs allocation
   ↓
8. Allocator returns results
   ↓
9. Tab displays results in table
   ↓
10. Tab saves to history (AllocationHistoryService)
    ↓
11. Dashboard tab refreshes automatically
```

---

## GUI Best Practices

### 1. Separation of Concerns

```python
# BAD: GUI directly accessing files
def load_data(self):
    df = pd.read_excel("file.xlsx")  # Don't do this

# GOOD: GUI calls service
def load_data(self):
    df = self.data_service.load_file(self.file_path)
```

### 2. Error Handling

```python
def run_allocation(self):
    try:
        result = self.allocator.allocate_resources()
        self.show_success(result)
    except FileNotFoundError as e:
        self.show_error(f"File not found: {e}")
    except Exception as e:
        self.show_error(f"Allocation failed: {e}")
        logger.exception("Allocation error")
```

### 3. Async Operations

```python
def long_running_operation(self):
    """Run long operation without freezing UI."""

    # Show progress dialog
    self.progress_dialog = ProgressDialog(self)

    # Run in thread
    thread = threading.Thread(target=self._do_operation)
    thread.start()

def _do_operation(self):
    # Heavy work here
    result = self.allocator.allocate(...)

    # Update UI on main thread
    self.after(0, lambda: self.update_results(result))
```

---

## Icon Management

**Icon Path Resolution:**
```python
def _set_app_icons(self):
    """Set application icons for window and taskbar."""

    try:
        # Resolve icon path (supports both source and PyInstaller)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.parent

        icon_path = base_path / "assets" / "icons" / "amazon_package.ico"

        if icon_path.exists():
            self.iconbitmap(str(icon_path))

            # macOS Dock icon (AppKit)
            if sys.platform == 'darwin':
                try:
                    from AppKit import NSApplication, NSImage
                    app = NSApplication.sharedApplication()
                    image = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
                    app.setApplicationIconImage_(image)
                except ImportError:
                    pass
    except Exception as e:
        logger.warning(f"Could not load icon: {e}")
```

---

## GUI Testing

### Manual Testing

**Checklist:** `GUI_TESTING_CHECKLIST.md`

**Test Areas:**
1. File selection and validation
2. Allocation workflow end-to-end
3. Dashboard history display
4. Settings persistence
5. Theme switching
6. Error handling
7. Progress indicators

### No Automated GUI Tests

**Rationale:**
- GUI excluded from pytest coverage (`pyproject.toml`)
- Manual testing via checklist
- Integration tests cover backend

---

## Performance Considerations

### 1. Lazy Loading

```python
def load_scorecard_tab(self):
    """Lazy load scorecard data when tab is first opened."""
    if not self.scorecard_loaded:
        self.scorecard_tab.initialize()
        self.scorecard_loaded = True
```

### 2. Debouncing

```python
def on_search_changed(self, event):
    """Debounce search input to avoid excessive filtering."""
    if hasattr(self, '_search_timer'):
        self.after_cancel(self._search_timer)

    self._search_timer = self.after(300, self._perform_search)
```

### 3. Virtual Scrolling

For large data tables, consider virtual scrolling (not currently implemented).

---

## Key Takeaways

### Strengths

✅ **Clean tab-based architecture** - well-organized
✅ **Service integration** - proper separation of concerns
✅ **Theme support** - dark/light mode
✅ **Reusable components** - HistoryCard, modals
✅ **Good error handling** - user-friendly messages
✅ **Icon support** - cross-platform
✅ **Comprehensive tabs** - 7 functional tabs

### Areas for Improvement

⚠️ **No automated tests** - relies on manual testing
⚠️ **Large file sizes** - allocation_tab is 46KB
⚠️ **Threading** - could improve async handling
⚠️ **Accessibility** - no screen reader support

### Production Readiness

🟢 **Overall:** Production-ready
🟢 **Usability:** Intuitive interface
🟢 **Stability:** Error handling in place
🟡 **Testing:** Manual only
🟢 **Documentation:** Good training guide

---

**Next:** See `CODEBASE_REVIEW_TESTING.md` and `CODEBASE_REVIEW_SUMMARY.md`
