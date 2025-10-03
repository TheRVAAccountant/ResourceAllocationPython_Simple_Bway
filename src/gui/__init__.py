"""GUI components for the Resource Management System."""

# Lazy imports to avoid circular dependencies
# Import these explicitly when needed

__all__ = [
    "ResourceAllocationGUI",
    "DashboardTab",
    "AllocationTab",
    "DataManagementTab",
    "SettingsTab",
    "LogViewerTab",
]


def __getattr__(name):
    """Lazy import of GUI components."""
    if name == "ResourceAllocationGUI":
        from src.gui.main_window import ResourceAllocationGUI

        return ResourceAllocationGUI
    elif name == "DashboardTab":
        from src.gui.dashboard_tab import DashboardTab

        return DashboardTab
    elif name == "AllocationTab":
        from src.gui.allocation_tab import AllocationTab

        return AllocationTab
    elif name == "DataManagementTab":
        from src.gui.data_management_tab import DataManagementTab

        return DataManagementTab
    elif name == "SettingsTab":
        from src.gui.settings_tab import SettingsTab

        return SettingsTab
    elif name == "LogViewerTab":
        from src.gui.log_viewer_tab import LogViewerTab

        return LogViewerTab
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
