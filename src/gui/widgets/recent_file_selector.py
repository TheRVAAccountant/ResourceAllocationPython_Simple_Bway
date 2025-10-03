"""Recent File Selector widget combining entry, recent files dropdown, and browse button."""

import customtkinter as ctk
from tkinter import filedialog, StringVar
from pathlib import Path
from typing import Optional, Callable, List, Tuple
from loguru import logger

from src.utils.recent_files_manager import FileFieldType, RecentFilesManager
from src.gui.widgets.recent_files_popup import RecentFilesPopup


class RecentFileSelector(ctk.CTkFrame):
    """Enhanced file selector with recent files functionality."""
    
    def __init__(self, parent, field_type: FileFieldType, 
                 textvariable: StringVar,
                 placeholder_text: str = "Select file...",
                 filetypes: Optional[List[Tuple[str, str]]] = None,
                 initialfile: Optional[str] = None,
                 on_file_selected: Optional[Callable[[str], None]] = None,
                 **kwargs):
        callback = kwargs.pop("on_file_selected_callback", None)
        if on_file_selected is None and callback is not None:
            on_file_selected = callback
        """Initialize the recent file selector.
        
        Args:
            parent: Parent widget.
            field_type: Type of file field (for recent files tracking).
            textvariable: StringVar to bind to entry.
            placeholder_text: Placeholder text for entry.
            filetypes: File types for file dialog.
            initialfile: Initial filename for file dialog.
            on_file_selected: Optional callback when file is selected.
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.field_type = field_type
        self.textvariable = textvariable
        self.placeholder_text = placeholder_text
        self.filetypes = filetypes or [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        self.initialfile = initialfile
        self.on_file_selected_callback = on_file_selected
        self.recent_manager = RecentFilesManager()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create widgets
        self._create_widgets()
        
        # Recent files popup
        self.recent_popup = None
    
    def _create_widgets(self):
        """Create the selector widgets."""
        # Entry field
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.textvariable,
            placeholder_text=self.placeholder_text,
            height=40
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Recent files dropdown button
        self.recent_button = ctk.CTkButton(
            self,
            text="▼",
            width=40,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._toggle_recent_files
        )
        self.recent_button.grid(row=0, column=1, padx=(0, 5))
        
        # Add tooltip to recent button
        self._add_tooltip(self.recent_button, "Show recent files")
        
        # Browse button
        self.browse_button = ctk.CTkButton(
            self,
            text="Browse",
            width=100,
            height=40,
            command=self._browse_file
        )
        self.browse_button.grid(row=0, column=2)
        
        # Check if there are recent files and update button appearance
        self._update_recent_button_state()
    
    def _update_recent_button_state(self):
        """Update recent button appearance based on available files."""
        recent_files = self.recent_manager.get_recent_files(self.field_type)
        
        if recent_files:
            # Enable and show normal appearance
            self.recent_button.configure(
                state="normal",
                text_color=("gray10", "gray90")
            )
        else:
            # Disable with visual feedback
            self.recent_button.configure(
                state="disabled",
                text_color=("gray60", "gray40")
            )
    
    def _toggle_recent_files(self):
        """Toggle the recent files popup."""
        if self.recent_popup and self.recent_popup.winfo_exists():
            self.recent_popup.destroy()
            self.recent_popup = None
        else:
            self._show_recent_files()
    
    def _show_recent_files(self):
        """Show the recent files popup."""
        # Create popup positioned below the recent button
        self.recent_popup = RecentFilesPopup(
            self.winfo_toplevel(),
            field_type=self.field_type,
            on_file_selected=self._on_recent_file_selected,
            position_widget=self.recent_button
        )
        
        # Bind to destroy popup when clicking elsewhere
        def destroy_popup(event):
            widget = event.widget
            # Check if click is outside popup
            if (self.recent_popup and self.recent_popup.winfo_exists() and
                not str(widget).startswith(str(self.recent_popup))):
                self.recent_popup.destroy()
                self.recent_popup = None
                # Unbind this event
                self.winfo_toplevel().unbind("<Button-1>", bind_id)
        
        # Bind after popup is created
        self.after(100, lambda: setattr(self, '_popup_bind_id', 
                                       self.winfo_toplevel().bind("<Button-1>", destroy_popup, "+")))
    
    def _on_recent_file_selected(self, file_path: str):
        """Handle selection from recent files popup."""
        self.textvariable.set(file_path)
        
        # Update recent files (increment use count)
        self.recent_manager.add_recent_file(self.field_type, file_path)
        
        # Call callback if provided
        if self.on_file_selected_callback:
            self.on_file_selected_callback(file_path)
        
        logger.info(f"Selected recent file: {file_path}")
    
    def _browse_file(self):
        """Browse for file using file dialog."""
        # Get initial directory from current value or use home
        current_value = self.textvariable.get()
        if current_value and Path(current_value).exists():
            initialdir = str(Path(current_value).parent)
        else:
            initialdir = str(Path.home() / "Documents")
        
        # Show file dialog
        filename = filedialog.askopenfilename(
            title=f"Select {self._get_field_display_name()} File",
            initialdir=initialdir,
            initialfile=self.initialfile,
            filetypes=self.filetypes
        )
        
        if filename:
            self.textvariable.set(filename)
            
            # Add to recent files
            self.recent_manager.add_recent_file(self.field_type, filename)
            
            # Update recent button state
            self._update_recent_button_state()
            
            # Call callback if provided
            if self.on_file_selected_callback:
                self.on_file_selected_callback(filename)
            
            logger.info(f"Selected file via browse: {filename}")
    
    def _get_field_display_name(self) -> str:
        """Get display name for the field type."""
        display_names = {
            FileFieldType.DAY_OF_OPS: "Day of Ops",
            FileFieldType.DAILY_ROUTES: "Daily Routes",
            FileFieldType.DAILY_SUMMARY: "Daily Summary Log",
            FileFieldType.ASSOCIATE_LIST: "Associate Listing",
            FileFieldType.SCORECARD_PDF: "Scorecard PDF"
        }
        return display_names.get(self.field_type, "")
    
    def _add_tooltip(self, widget, text: str):
        """Add a simple tooltip to a widget."""
        def on_enter(event):
            # Create tooltip window
            tooltip = ctk.CTkToplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = ctk.CTkLabel(
                tooltip,
                text=text,
                fg_color=("gray10", "gray90"),
                text_color=("gray90", "gray10"),
                corner_radius=5
            )
            label.pack(padx=5, pady=2)
            
            # Store reference
            widget._tooltip = tooltip
        
        def on_leave(event):
            # Destroy tooltip
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                del widget._tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def get_file_path(self) -> str:
        """Get the current file path."""
        return self.textvariable.get()
    
    def set_file_path(self, path: str):
        """Set the file path programmatically."""
        self.textvariable.set(path)
        
        # Add to recent files if it exists
        if path and Path(path).exists():
            self.recent_manager.add_recent_file(self.field_type, path)
            self._update_recent_button_state()
    
    def clear(self):
        """Clear the current selection."""
        self.textvariable.set("")
    
    def set_state(self, state: str):
        """Set the state of all child widgets."""
        self.entry.configure(state=state)
        self.recent_button.configure(state=state if state == "disabled" else "normal")
        self.browse_button.configure(state=state)