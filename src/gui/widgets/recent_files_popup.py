"""Recent Files Popup widget for displaying recent file selections."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from loguru import logger

from src.utils.recent_files_manager import FileFieldType, RecentFileInfo, RecentFilesManager


class RecentFilesPopup(ctk.CTkToplevel):
    """Popup window showing recent files for selection."""

    def __init__(
        self,
        parent,
        field_type: FileFieldType,
        on_file_selected: Callable[[str], None],
        position_widget=None,
        **kwargs,
    ):
        """Initialize recent files popup.

        Args:
            parent: Parent widget.
            field_type: Type of file field.
            on_file_selected: Callback when file is selected.
            position_widget: Widget to position popup relative to.
        """
        super().__init__(parent, **kwargs)

        self.field_type = field_type
        self.on_file_selected = on_file_selected
        self.recent_manager = RecentFilesManager()

        # Configure window
        self.title("")  # No title bar text
        self.geometry("450x300")
        self.resizable(False, False)

        # Remove window decorations for dropdown style
        self.overrideredirect(True)

        # Make it transient and grab focus
        self.transient(parent)

        # Configure appearance
        self.configure(fg_color=("gray95", "gray10"))

        # Position relative to widget
        if position_widget:
            self._position_relative_to_widget(position_widget)
        else:
            self._center_on_parent(parent)

        # Create UI
        self._create_ui()

        # Load and display recent files
        self._load_recent_files()

        # Bind events
        self._bind_events()

        # Focus on popup
        self.focus_set()

    def _position_relative_to_widget(self, widget):
        """Position popup below the given widget."""
        # Get widget position
        widget_x = widget.winfo_rootx()
        widget_y = widget.winfo_rooty()
        widget_height = widget.winfo_height()

        # Position below widget
        self.geometry(f"+{widget_x}+{widget_y + widget_height + 5}")

    def _center_on_parent(self, parent):
        """Center popup on parent window."""
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 225
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 150
        self.geometry(f"+{x}+{y}")

    def _create_ui(self):
        """Create the popup UI."""
        # Main container with border
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Header
        header_frame = ctk.CTkFrame(main_frame, height=40, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)

        # Title with icon
        title_text = self._get_field_display_name()
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"📁 Recent {title_text} Files",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)

        # Close button
        close_button = ctk.CTkButton(
            header_frame,
            text="✕",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray80", "gray20"),
            command=self.destroy,
        )
        close_button.pack(side="right")

        # Separator
        separator = ctk.CTkFrame(main_frame, height=2, fg_color=("gray80", "gray20"))
        separator.pack(fill="x", padx=10, pady=5)

        # Scrollable frame for file list
        self.files_frame = ctk.CTkScrollableFrame(
            main_frame, corner_radius=0, fg_color="transparent"
        )
        self.files_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Bottom buttons frame
        bottom_frame = ctk.CTkFrame(main_frame, height=40, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))

        # Clear button
        self.clear_button = ctk.CTkButton(
            bottom_frame,
            text="🗑️ Clear All",
            width=100,
            height=30,
            command=self._clear_recent_files,
        )
        self.clear_button.pack(side="left", padx=(0, 5))

        # Refresh button
        refresh_button = ctk.CTkButton(
            bottom_frame, text="🔄 Refresh", width=100, height=30, command=self._load_recent_files
        )
        refresh_button.pack(side="left")

    def _get_field_display_name(self) -> str:
        """Get display name for the field type."""
        display_names = {
            FileFieldType.DAY_OF_OPS: "Day of Ops",
            FileFieldType.DAILY_ROUTES: "Daily Routes",
            FileFieldType.DAILY_SUMMARY: "Daily Summary Log",
        }
        return display_names.get(self.field_type, "File")

    def _load_recent_files(self):
        """Load and display recent files."""
        # Clear existing items
        for widget in self.files_frame.winfo_children():
            widget.destroy()

        # Get recent files
        recent_files = self.recent_manager.get_recent_files(self.field_type)

        if not recent_files:
            # Show empty message
            empty_label = ctk.CTkLabel(
                self.files_frame,
                text="No recent files",
                text_color=("gray50", "gray50"),
                font=ctk.CTkFont(size=14),
            )
            empty_label.pack(pady=50)
            self.clear_button.configure(state="disabled")
            return

        # Enable clear button
        self.clear_button.configure(state="normal")

        # Create file items
        for file_info in recent_files:
            self._create_file_item(file_info)

    def _create_file_item(self, file_info: RecentFileInfo):
        """Create a file item in the list."""
        # Item frame
        item_frame = ctk.CTkFrame(
            self.files_frame,
            height=60,
            corner_radius=5,
            fg_color=("gray90", "gray20") if file_info.exists else ("gray85", "gray25"),
        )
        item_frame.pack(fill="x", pady=2)
        item_frame.pack_propagate(False)

        # Make entire frame clickable
        if file_info.exists:
            item_frame.bind("<Button-1>", lambda _event: self._select_file(file_info.path))
            item_frame.bind(
                "<Enter>", lambda _event: item_frame.configure(fg_color=("gray85", "gray25"))
            )
            item_frame.bind(
                "<Leave>", lambda _event: item_frame.configure(fg_color=("gray90", "gray20"))
            )

        # Content frame
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # File icon and name
        name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        name_frame.pack(fill="x")

        # Icon
        icon = "📄" if file_info.exists else "🚫"
        icon_label = ctk.CTkLabel(name_frame, text=icon, font=ctk.CTkFont(size=16), width=25)
        icon_label.pack(side="left")

        # File name
        name_label = ctk.CTkLabel(
            name_frame,
            text=file_info.display_name or Path(file_info.path).name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
            text_color=("gray10", "gray90") if file_info.exists else ("gray50", "gray50"),
        )
        name_label.pack(side="left", fill="x", expand=True)

        # Make labels clickable too
        if file_info.exists:
            icon_label.bind("<Button-1>", lambda _event: self._select_file(file_info.path))
            name_label.bind("<Button-1>", lambda _event: self._select_file(file_info.path))

        # Path and metadata frame
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x")

        # Folder icon and path
        path_label = ctk.CTkLabel(
            info_frame,
            text=f"📂 {self.recent_manager.get_display_path(file_info.path, 40)}",
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color=("gray40", "gray60"),
        )
        path_label.pack(side="left", fill="x", expand=True)

        if file_info.exists:
            path_label.bind("<Button-1>", lambda _event: self._select_file(file_info.path))

        # Last used and usage info
        try:
            last_used = datetime.fromisoformat(file_info.last_used)
            days_ago = (datetime.now() - last_used).days
            if days_ago == 0:
                time_text = "Today"
            elif days_ago == 1:
                time_text = "Yesterday"
            else:
                time_text = f"{days_ago} days ago"
        except (ValueError, TypeError, AttributeError):
            time_text = "Unknown"

        # Usage count
        use_text = f"Used {file_info.use_count}x" if file_info.use_count > 1 else ""

        meta_text = f"{time_text}" + (f" • {use_text}" if use_text else "")
        meta_label = ctk.CTkLabel(
            info_frame, text=meta_text, font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        )
        meta_label.pack(side="right", padx=5)

        # Remove button (only for missing files)
        if not file_info.exists:
            remove_button = ctk.CTkButton(
                item_frame,
                text="Remove",
                width=60,
                height=25,
                font=ctk.CTkFont(size=11),
                command=lambda: self._remove_file(file_info.path),
            )
            remove_button.place(relx=0.95, rely=0.5, anchor="e")

    def _select_file(self, file_path: str):
        """Handle file selection."""
        logger.info(f"Selected recent file: {file_path}")
        self.on_file_selected(file_path)
        self.destroy()

    def _remove_file(self, file_path: str):
        """Remove a file from recent files."""
        self.recent_manager.remove_recent_file(self.field_type, file_path)
        self._load_recent_files()

    def _clear_recent_files(self):
        """Clear all recent files for this field type."""
        # Confirm dialog
        if ctk.messagebox.askyesno(
            "Clear Recent Files",
            f"Are you sure you want to clear all recent {self._get_field_display_name()} files?",
        ):
            self.recent_manager.clear_recent_files(self.field_type)
            self._load_recent_files()

    def _bind_events(self):
        """Bind keyboard and mouse events."""
        # Close on Escape
        self.bind("<Escape>", lambda _event: self.destroy())

        # Close when clicking outside
        self.bind("<FocusOut>", self._check_focus_out)

    def _check_focus_out(self, _event):
        """Check if focus moved outside the popup."""
        # Get the widget that received focus
        focused = self.focus_get()

        # If focus is not on this window or its children, close
        if focused is None or not str(focused).startswith(str(self)):
            self.destroy()
