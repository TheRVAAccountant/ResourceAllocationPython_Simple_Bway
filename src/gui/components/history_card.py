"""History card component for displaying allocation history entries."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

import customtkinter as ctk

from src.gui.utils.theme import resolve_color


class HistoryCard(ctk.CTkFrame):
    """Individual allocation history entry card with status indicators and details button.

    Displays:
    - Timestamp with icon
    - Status badge (Success/Error/Duplicates)
    - Key metrics (routes, allocated, rate)
    - Details button to view full information
    """

    def __init__(
        self, parent, entry: dict[str, Any], on_details_click: Callable | None = None, **kwargs
    ):
        """Initialize history card.

        Args:
            parent: Parent widget
            entry: History entry dict with keys:
                - timestamp: ISO format datetime
                - status: Status string
                - total_routes: Total routes
                - allocated_count: Allocated count
                - allocation_rate: Allocation rate percentage
                - duplicate_conflicts: Number of duplicates
                - error: Error message if any
            on_details_click: Callback when details button clicked
        """
        # Card styling
        super().__init__(
            parent,
            fg_color=resolve_color(("gray90", "gray20")),
            corner_radius=8,
            border_width=1,
            border_color=resolve_color(("gray70", "gray30")),
            **kwargs,
        )

        self.entry = entry
        self.on_details_click = on_details_click
        self.duplicate_count = self._resolve_duplicate_count(entry)

        # Configure grid
        self.grid_columnconfigure(0, weight=0)  # Icon
        self.grid_columnconfigure(1, weight=1)  # Content
        self.grid_columnconfigure(2, weight=0)  # Status + Details

        # Parse timestamp
        try:
            dt = datetime.fromisoformat(entry["timestamp"])
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = entry.get("timestamp", "Unknown")

        # Left: Timestamp with icon
        timestamp_frame = ctk.CTkFrame(self, fg_color="transparent")
        timestamp_frame.grid(row=0, column=0, padx=10, pady=8, sticky="w")

        icon_label = ctk.CTkLabel(timestamp_frame, text="🕐", font=("Arial", 16))
        icon_label.pack()

        time_label = ctk.CTkLabel(
            timestamp_frame,
            text=time_str,
            font=("Arial", 11),
            text_color=resolve_color(("gray30", "gray70")),
        )
        time_label.pack()

        # Center: Metrics
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        # Main metrics line
        total_routes = entry.get("total_routes", 0)
        allocated = entry.get("allocated_count", 0)
        unallocated = entry.get("unallocated_count", 0)
        rate = entry.get("allocation_rate", 0.0)

        metrics_text = f"Routes: {total_routes} | Allocated: {allocated} ({rate:.1f}%) | Unallocated: {unallocated}"

        metrics_label = ctk.CTkLabel(
            metrics_frame, text=metrics_text, font=("Arial", 12, "bold"), anchor="w"
        )
        metrics_label.pack(anchor="w", pady=(0, 2))

        # File info (truncated)
        files = entry.get("files", {})
        if files:
            # Show first file only (Day of Ops typically)
            first_file = next(iter(files.values()), "")
            if first_file:
                # Truncate long filenames
                from pathlib import Path

                filename = Path(first_file).name
                if len(filename) > 50:
                    filename = filename[:47] + "..."

                file_label = ctk.CTkLabel(
                    metrics_frame,
                    text=f"Files: {filename}",
                    font=("Arial", 10),
                    text_color=resolve_color(("gray40", "gray60")),
                    anchor="w",
                )
                file_label.pack(anchor="w")

        # Right: Status + Details button
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=10, pady=8, sticky="e")

        # Status badge
        status_frame = ctk.CTkFrame(
            right_frame, fg_color=self._get_status_color(), corner_radius=12, height=24
        )
        status_frame.pack(side="top", pady=(0, 5))

        status_label = ctk.CTkLabel(
            status_frame,
            text=self._get_status_text(),
            font=("Arial", 10, "bold"),
            text_color="white",
            padx=8,
            pady=2,
        )
        status_label.pack()

        # Details button
        if on_details_click:
            details_btn = ctk.CTkButton(
                right_frame,
                text="Details →",
                width=80,
                height=24,
                font=("Arial", 10),
                command=lambda: on_details_click(entry),
            )
            details_btn.pack(side="top")

        # Hover effect
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)

    def _get_status_color(self) -> str:
        """Get status badge color based on entry state."""
        if self.entry.get("error"):
            return resolve_color(("#e74c3c", "#c0392b"))  # Red
        if self.duplicate_count > 0:
            return resolve_color(("#f39c12", "#e67e22"))  # Orange
        return resolve_color(("#27ae60", "#229954"))  # Green

    def _get_status_text(self) -> str:
        """Get status badge text."""
        if self.entry.get("error"):
            return "❌ Error"
        if self.duplicate_count > 0:
            suffix = "Duplicates" if self.duplicate_count != 1 else "Duplicate"
            return f"⚠️ {self.duplicate_count} {suffix}"
        return "✓ Success"

    def _on_hover_enter(self, _event):
        """Handle mouse enter (hover effect)."""
        self.configure(border_color=resolve_color(("gray50", "gray40")))

    def _on_hover_leave(self, _event):
        """Handle mouse leave."""
        self.configure(border_color=resolve_color(("gray70", "gray30")))

    @staticmethod
    def _resolve_duplicate_count(entry: dict[str, Any]) -> int:
        """Safely resolve duplicate conflict count from mixed formats."""
        if entry is None:
            return 0
        normalized = entry.get("duplicate_conflicts_count")
        if isinstance(normalized, int):
            return max(normalized, 0)
        raw = entry.get("duplicate_conflicts")
        if isinstance(raw, int):
            return max(raw, 0)
        details = entry.get("duplicate_conflict_details")
        if isinstance(details, list | tuple | set):
            return len([item for item in details if item is not None])
        if isinstance(raw, list | tuple | set):
            return len([item for item in raw if item is not None])
        if not raw:
            return 0
        return 1
