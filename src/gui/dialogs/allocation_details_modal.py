"""Allocation details modal dialog for displaying comprehensive allocation information."""

from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk
from loguru import logger

from src.gui.utils.theme import resolve_color


class AllocationDetailsModal(ctk.CTkToplevel):
    """Modal dialog showing detailed allocation information.

    Displays:
    - Summary metrics
    - Files used
    - Allocation breakdown
    - Export options
    """

    def __init__(self, parent, entry: dict[str, Any], **kwargs):
        """Initialize allocation details modal.

        Args:
            parent: Parent window
            entry: History entry dict with allocation details
        """
        super().__init__(parent, **kwargs)

        self.entry = entry

        # Window configuration
        self.title(f"Allocation Details: {self._format_timestamp()}")
        self.geometry("700x600")
        self.minsize(600, 500)

        # Center on parent
        self._center_on_parent(parent)

        # Modal behavior
        self.transient(parent)
        self.grab_set()

        # Setup UI
        self.setup_ui()

        # Focus on window
        self.focus()

    def setup_ui(self):
        """Setup the modal UI."""
        # Configure grid
        self.grid_rowconfigure(0, weight=1)  # Content area
        self.grid_rowconfigure(1, weight=0)  # Button area
        self.grid_columnconfigure(0, weight=1)

        # Main content area (scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Build sections
        self._build_summary_section()
        self._build_files_section()
        self._build_breakdown_section()

        # Button area
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=0)
        button_frame.grid_columnconfigure(2, weight=0)

        # Export button (placeholder for future)
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="📥 Export Details",
            width=140,
            command=self._export_details,
            state="disabled",  # TODO: Implement export
        )
        self.export_btn.grid(row=0, column=1, padx=5)

        # Close button
        close_btn = ctk.CTkButton(button_frame, text="Close", width=100, command=self.destroy)
        close_btn.grid(row=0, column=2, padx=5)

    def _build_summary_section(self):
        """Build summary metrics section."""
        section_frame = self._create_section_frame("📋 Summary")

        # Metrics
        total_routes = self.entry.get("total_routes", 0)
        allocated = self.entry.get("allocated_count", 0)
        unallocated = self.entry.get("unallocated_count", 0)
        rate = self.entry.get("allocation_rate", 0.0)
        duplicates = self._resolve_duplicate_count()
        duplicate_details = self._resolve_duplicate_details()

        metrics = [
            ("Total Routes:", str(total_routes)),
            ("Successfully Allocated:", f"{allocated} ({rate:.1f}%)"),
            ("Unallocated Vehicles:", str(unallocated)),
            ("Duplicate Conflicts:", str(duplicates)),
            ("Engine Used:", self.entry.get("engine", "Unknown")),
            ("Request ID:", self.entry.get("request_id", "N/A")),
        ]

        # Show error if present
        error = self.entry.get("error")
        if error:
            metrics.append(("Error:", error))

        for label_text, value_text in metrics:
            row_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            row_frame.grid_columnconfigure(0, weight=0)
            row_frame.grid_columnconfigure(1, weight=1)

            label = ctk.CTkLabel(
                row_frame, text=label_text, font=("Arial", 12, "bold"), anchor="w", width=180
            )
            label.grid(row=0, column=0, sticky="w")

            value = ctk.CTkLabel(row_frame, text=value_text, font=("Arial", 12), anchor="w")
            value.grid(row=0, column=1, sticky="w", padx=(10, 0))

        if duplicate_details:
            details_preview = ", ".join(str(item) for item in duplicate_details[:5])
            if len(duplicate_details) > 5:
                details_preview += " …"
            details_label = ctk.CTkLabel(
                section_frame,
                text=f"Duplicate Details: {details_preview}",
                font=("Arial", 10),
                text_color=resolve_color(("gray40", "gray60")),
                justify="left",
                anchor="w",
            )
            details_label.pack(fill="x", pady=(6, 0), padx=4)

    def _build_files_section(self):
        """Build files used section."""
        section_frame = self._create_section_frame("📁 Files Used")

        files = self.entry.get("files", {})
        if not files:
            no_files_label = ctk.CTkLabel(
                section_frame,
                text="No file information available",
                font=("Arial", 11),
                text_color="gray",
            )
            no_files_label.pack(pady=5)
            return

        # Display each file
        file_labels = {
            "day_of_ops": "Day of Ops:",
            "daily_routes": "Daily Routes:",
            "vehicle_status": "Vehicle Status:",
        }

        for key, label_text in file_labels.items():
            if key in files:
                filepath = files[key]
                filename = Path(filepath).name

                row_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=3)
                row_frame.grid_columnconfigure(0, weight=0)
                row_frame.grid_columnconfigure(1, weight=1)

                label = ctk.CTkLabel(
                    row_frame, text=label_text, font=("Arial", 11, "bold"), anchor="w", width=120
                )
                label.grid(row=0, column=0, sticky="w")

                value = ctk.CTkLabel(row_frame, text=filename, font=("Arial", 11), anchor="w")
                value.grid(row=0, column=1, sticky="w", padx=(10, 0))

                # Tooltip with full path
                self._create_tooltip(value, filepath)

    def _build_breakdown_section(self):
        """Build allocation breakdown section."""
        section_frame = self._create_section_frame("📊 Allocation Details")

        # Check if detailed results are available
        detailed = self.entry.get("detailed_results", [])

        if not detailed:
            info_label = ctk.CTkLabel(
                section_frame,
                text="Detailed breakdown not available\n(Enable 'detailed_storage' in settings for full results)",
                font=("Arial", 11),
                text_color="gray",
                justify="center",
            )
            info_label.pack(pady=10)
        else:
            # Show summary of detailed results
            summary_label = ctk.CTkLabel(
                section_frame,
                text=f"Showing first {min(len(detailed), 10)} allocations:",
                font=("Arial", 11, "bold"),
            )
            summary_label.pack(anchor="w", pady=(0, 5))

            # Display in textbox for scrolling
            details_text = ctk.CTkTextbox(section_frame, height=150, font=("Courier", 10))
            details_text.pack(fill="both", expand=True)

            for i, result in enumerate(detailed[:10], 1):
                route = result.get("Route Code", "Unknown")
                driver = result.get("Associate Name", "N/A")
                vehicle = result.get("Van ID", "N/A")
                details_text.insert("end", f"{i}. {route} → {driver} (Vehicle: {vehicle})\n")

            details_text.configure(state="disabled")

    def _create_section_frame(self, title: str) -> ctk.CTkFrame:
        """Create a section frame with title."""
        # Title
        title_label = ctk.CTkLabel(
            self.scroll_frame, text=title, font=("Arial", 14, "bold"), anchor="w"
        )
        title_label.pack(fill="x", pady=(10, 5))

        # Separator
        separator = ctk.CTkFrame(self.scroll_frame, height=2, fg_color="gray")
        separator.pack(fill="x", pady=(0, 10))

        # Content frame
        content_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10)

        return content_frame

    def _format_timestamp(self) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(self.entry["timestamp"])
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return self.entry.get("timestamp", "Unknown")

    def _center_on_parent(self, parent):
        """Center modal on parent window."""
        self.update_idletasks()

        # Get parent position and size
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Get modal size
        modal_width = 700
        modal_height = 600

        # Calculate centered position
        x = parent_x + (parent_width - modal_width) // 2
        y = parent_y + (parent_height - modal_height) // 2

        # Ensure on screen
        x = max(0, x)
        y = max(0, y)

        self.geometry(f"{modal_width}x{modal_height}+{x}+{y}")

    def _create_tooltip(self, widget, text: str):
        """Create tooltip for widget (simplified version)."""

        # Simple tooltip: show in status when hovering
        # Full implementation would use a Toplevel window
        def on_enter(_event):
            logger.debug(f"Tooltip: {text}")

        widget.bind("<Enter>", on_enter)

    def _resolve_duplicate_count(self) -> int:
        """Resolve duplicate conflict count regardless of original format."""
        normalized = self.entry.get("duplicate_conflicts_count")
        if isinstance(normalized, int):
            return max(normalized, 0)
        raw = self.entry.get("duplicate_conflicts")
        if isinstance(raw, int):
            return max(raw, 0)
        details = self._resolve_duplicate_details()
        if details:
            return len(details)
        if isinstance(raw, list | tuple | set):
            return len([item for item in raw if item is not None])
        if not raw:
            return 0
        return 1

    def _resolve_duplicate_details(self) -> list[Any]:
        """Return normalized duplicate conflict detail list."""
        details = self.entry.get("duplicate_conflict_details")
        if isinstance(details, list):
            return [item for item in details if item is not None]
        if isinstance(details, tuple | set):
            return [item for item in details if item is not None]
        raw = self.entry.get("duplicate_conflicts")
        if isinstance(raw, list):
            return [item for item in raw if item is not None]
        if isinstance(raw, tuple | set):
            return [item for item in raw if item is not None]
        return []

    def _export_details(self):
        """Export details to file (placeholder for Phase 2)."""
        messagebox.showinfo(
            "Export Details",
            "Export functionality will be available in Phase 2.\n"
            "This will generate an Excel report with full allocation details.",
            parent=self,
        )
