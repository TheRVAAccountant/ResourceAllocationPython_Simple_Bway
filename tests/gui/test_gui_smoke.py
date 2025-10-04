"""Basic GUI smoke tests to catch critical regressions."""

import importlib
import sys
import tkinter as tk
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_services():
    """Mock available backend services to avoid dependencies."""
    module = importlib.import_module("src.gui.main_window")
    service_names = [
        "AllocationEngine",
        "ExcelService",
        "BorderFormattingService",
        "DashboardDataService",
        "DataManagementService",
        "AssociateService",
        "ScorecardService",
    ]

    with ExitStack() as stack:
        for name in service_names:
            if hasattr(module, name):
                stack.enter_context(patch(f"src.gui.main_window.{name}"))

        stack.enter_context(patch("src.gui.main_window.messagebox.askokcancel", return_value=True))
        stack.enter_context(patch("src.gui.main_window.sys.exit"))
        yield


@pytest.mark.gui
def test_main_window_initializes(mock_services):  # noqa: ARG001
    """Test that main window can be created without errors."""
    try:
        from src.gui.main_window import ResourceAllocationGUI

        # Create window (don't show it)
        app = ResourceAllocationGUI()

        # Verify window exists
        assert app is not None
        assert app.winfo_exists()

        # Verify basic properties
        assert app.title() is not None
        assert app.geometry() is not None

        # Destroy window
        app.destroy()

    except Exception as e:
        pytest.fail(f"Main window initialization failed: {e}")


@pytest.mark.gui
def test_all_tabs_exist(mock_services):  # noqa: ARG001
    """Test that all expected tabs are created."""
    from src.gui.main_window import ResourceAllocationGUI

    app = ResourceAllocationGUI()

    try:
        # Check that tabview exists
        assert hasattr(app, "tabview")

        # Check that key tabs exist
        assert hasattr(app, "dashboard_tab")
        assert hasattr(app, "allocation_tab")
        assert hasattr(app, "data_management_tab")
        assert hasattr(app, "settings_tab")

        if hasattr(app, "data_mgmt_tab"):
            assert app.data_mgmt_tab is app.data_management_tab

    finally:
        app.destroy()


@pytest.mark.gui
def test_services_initialized(mock_services):  # noqa: ARG001
    """Test that all services are initialized."""
    from src.gui.main_window import ResourceAllocationGUI

    app = ResourceAllocationGUI()

    try:
        # Verify services exist
        assert app.allocation_engine is not None
        assert app.excel_service is not None
        assert app.border_service is not None
        assert app.dashboard_data_service is not None

    finally:
        app.destroy()


@pytest.mark.gui
def test_icon_loading_does_not_crash():
    """Test that icon loading failures don't crash the app."""
    from src.gui.main_window import ResourceAllocationGUI

    with patch("src.gui.main_window.Path.exists", return_value=False):
        # Should not crash even if icon doesn't exist
        app = ResourceAllocationGUI()

        try:
            assert app is not None
        finally:
            app.destroy()


@pytest.mark.gui
def test_window_closes_cleanly(mock_services):  # noqa: ARG001
    """Test that window closes without errors."""
    from src.gui.main_window import ResourceAllocationGUI

    app = ResourceAllocationGUI()

    try:
        # Simulate close event
        app.on_closing()

        # Window should be destroyed
        assert not app.winfo_exists()

    except tk.TclError:
        # Expected when window is already destroyed
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "gui"])
