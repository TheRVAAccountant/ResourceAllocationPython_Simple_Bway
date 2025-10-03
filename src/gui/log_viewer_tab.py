"""Log viewer tab for Resource Allocation GUI."""

import queue
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from loguru import logger


class LogViewerTab:
    """Log viewer tab implementation."""

    def __init__(self, parent):
        """Initialize log viewer tab.

        Args:
            parent: Parent widget.
        """
        self.parent = parent
        self.log_queue = queue.Queue()
        self.auto_scroll = True
        self.log_level_filter = "ALL"

        # Configure grid
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        # Create UI elements
        self.setup_ui()

        # Start log monitoring
        self.start_log_monitoring()

    def setup_ui(self):
        """Setup log viewer UI."""
        # Header with controls
        self.create_header()

        # Log display area
        self.create_log_display()

        # Status bar
        self.create_status_bar()

    def create_header(self):
        """Create header with log controls."""
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame, text="System Logs", font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Controls frame
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e")

        # Log level filter
        level_label = ctk.CTkLabel(controls_frame, text="Level:")
        level_label.grid(row=0, column=0, padx=5)

        self.level_combo = ctk.CTkComboBox(
            controls_frame,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            width=100,
            command=self.filter_logs,
        )
        self.level_combo.set("ALL")
        self.level_combo.grid(row=0, column=1, padx=5)

        # Search entry
        search_label = ctk.CTkLabel(controls_frame, text="Search:")
        search_label.grid(row=0, column=2, padx=(20, 5))

        self.search_entry = ctk.CTkEntry(
            controls_frame, width=200, placeholder_text="Search logs..."
        )
        self.search_entry.grid(row=0, column=3, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_logs)

        # Control buttons
        self.clear_button = ctk.CTkButton(
            controls_frame, text="🗑️ Clear", width=80, command=self.clear_logs
        )
        self.clear_button.grid(row=0, column=4, padx=5)

        self.export_button = ctk.CTkButton(
            controls_frame, text="📤 Export", width=80, command=self.export_logs
        )
        self.export_button.grid(row=0, column=5, padx=5)

        self.pause_button = ctk.CTkButton(
            controls_frame, text="⏸️ Pause", width=80, command=self.toggle_pause
        )
        self.pause_button.grid(row=0, column=6, padx=5)

    def create_log_display(self):
        """Create log display area."""
        # Main log frame
        log_frame = ctk.CTkFrame(self.parent)
        log_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        # Log text widget with syntax highlighting
        self.log_text = ctk.CTkTextbox(
            log_frame,
            corner_radius=5,
            font=ctk.CTkFont(
                family="Consolas" if "win" in str(Path.home()) else "Courier", size=11
            ),
            wrap="none",
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Configure tags for different log levels
        self.configure_log_tags()

        # Options panel
        options_frame = ctk.CTkFrame(log_frame, height=40)
        options_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

        # Auto-scroll checkbox
        self.auto_scroll_checkbox = ctk.CTkCheckBox(
            options_frame, text="Auto-scroll", command=self.toggle_auto_scroll
        )
        self.auto_scroll_checkbox.select()
        self.auto_scroll_checkbox.grid(row=0, column=0, padx=10, pady=5)

        # Show timestamps checkbox
        self.timestamps_checkbox = ctk.CTkCheckBox(options_frame, text="Show timestamps")
        self.timestamps_checkbox.select()
        self.timestamps_checkbox.grid(row=0, column=1, padx=10, pady=5)

        # Word wrap checkbox
        self.wrap_checkbox = ctk.CTkCheckBox(
            options_frame, text="Word wrap", command=self.toggle_wrap
        )
        self.wrap_checkbox.grid(row=0, column=2, padx=10, pady=5)

        # Line numbers checkbox
        self.line_numbers_checkbox = ctk.CTkCheckBox(options_frame, text="Line numbers")
        self.line_numbers_checkbox.grid(row=0, column=3, padx=10, pady=5)

    def create_status_bar(self):
        """Create status bar with log statistics."""
        status_frame = ctk.CTkFrame(self.parent, height=30)
        status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        status_frame.grid_columnconfigure(3, weight=1)

        # Log count
        self.log_count_label = ctk.CTkLabel(
            status_frame, text="Total: 0 logs", font=ctk.CTkFont(size=12)
        )
        self.log_count_label.grid(row=0, column=0, padx=10, pady=5)

        # Level counts
        self.level_counts_label = ctk.CTkLabel(
            status_frame,
            text="DEBUG: 0 | INFO: 0 | WARNING: 0 | ERROR: 0",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
        )
        self.level_counts_label.grid(row=0, column=1, padx=10, pady=5)

        # File info
        self.file_info_label = ctk.CTkLabel(
            status_frame,
            text="Log file: resource_allocation.log",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
        )
        self.file_info_label.grid(row=0, column=2, padx=10, pady=5)

        # Last update
        self.last_update_label = ctk.CTkLabel(
            status_frame,
            text="Last update: Never",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
        )
        self.last_update_label.grid(row=0, column=3, sticky="e", padx=10, pady=5)

    def configure_log_tags(self):
        """Configure text tags for log level coloring."""
        # This would configure colors for different log levels
        # Note: CTkTextbox doesn't support tags like tkinter Text widget
        # In a real implementation, we might need to use a regular tkinter Text widget
        # or find another way to implement syntax highlighting
        pass

    def start_log_monitoring(self):
        """Start monitoring log files."""

        def monitor_thread():
            """Thread function to monitor logs."""
            # In a real implementation, this would tail the log file
            # and add new entries to the queue
            import time

            levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
            messages = [
                "System initialized successfully",
                "Loading configuration from file",
                "Connecting to Excel service",
                "Allocation engine started",
                "Processing allocation request",
                "Validation completed",
                "Results exported to file",
                "Cache cleared",
                "Service cleanup initiated",
            ]

            count = 0
            while True:
                time.sleep(2)  # Simulate log entries
                if not self.pause_button.cget("text").startswith("▶️"):  # If not paused
                    level = levels[count % len(levels)]
                    message = messages[count % len(messages)]
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    log_entry = f"[{timestamp}] [{level:8}] {message}"
                    self.log_queue.put((level, log_entry))
                    count += 1

        thread = threading.Thread(target=monitor_thread, daemon=True)
        thread.start()

        # Start processing queue
        self.process_log_queue()

    def process_log_queue(self):
        """Process log queue and update display."""
        try:
            while not self.log_queue.empty():
                level, entry = self.log_queue.get_nowait()

                # Apply filter
                if self.log_level_filter != "ALL" and level != self.log_level_filter:
                    continue

                # Add to display
                self.add_log_entry(level, entry)

                # Update statistics
                self.update_statistics()

        except queue.Empty:
            pass

        # Schedule next check
        self.parent.after(100, self.process_log_queue)

    def add_log_entry(self, _level: str, entry: str):
        """Add log entry to display.

        Args:
            level: Log level.
            entry: Log entry text.
        """
        # Add timestamp if enabled
        if not self.timestamps_checkbox.get() and "] [" in entry:
            # Remove timestamp from entry
            entry = entry.split("] [", 1)[1]
            entry = "[" + entry

        # Add line number if enabled
        if self.line_numbers_checkbox.get():
            line_count = len(self.log_text.get("1.0", "end").split("\n"))
            entry = f"{line_count:4d} | {entry}"

        # Add to text widget
        self.log_text.insert("end", entry + "\n")

        # Auto-scroll if enabled
        if self.auto_scroll:
            self.log_text.see("end")

        # Limit log size (keep last 10000 lines)
        lines = self.log_text.get("1.0", "end").split("\n")
        if len(lines) > 10000:
            self.log_text.delete("1.0", "2.0")

    def update_statistics(self):
        """Update log statistics."""
        # Count logs by level
        text = self.log_text.get("1.0", "end")
        lines = text.split("\n")
        total = len([line for line in lines if line.strip()])
        debug_count = len([line for line in lines if "DEBUG" in line])
        info_count = len([line for line in lines if "INFO" in line])
        warning_count = len([line for line in lines if "WARNING" in line])
        error_count = len([line for line in lines if "ERROR" in line])

        self.log_count_label.configure(text=f"Total: {total} logs")
        self.level_counts_label.configure(
            text=(
                f"DEBUG: {debug_count} | INFO: {info_count} | "
                f"WARNING: {warning_count} | ERROR: {error_count}"
            )
        )
        self.last_update_label.configure(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")

        self.level_filters["DEBUG"].configure(
            command=lambda level_name="DEBUG": self.filter_logs(level_name)
        )
        self.level_filters["INFO"].configure(
            command=lambda level_name="INFO": self.filter_logs(level_name)
        )
        self.level_filters["WARNING"].configure(
            command=lambda level_name="WARNING": self.filter_logs(level_name)
        )
        self.level_filters["ERROR"].configure(
            command=lambda level_name="ERROR": self.filter_logs(level_name)
        )

    def filter_logs(self, level: str):
        """Filter logs by level.

        Args:
        """
        self.log_level_filter = level
        logger.info(f"Log filter set to: {level}")

    def search_logs(self, _event):
        """Search logs for text.

        Args:
            event: Key event.
        """
        search_text = self.search_entry.get()
        if search_text:
            # Highlight matching text
            # In a real implementation, this would highlight matches
            logger.info(f"Searching logs for: {search_text}")

    def clear_logs(self):
        """Clear log display."""
        self.log_text.delete("1.0", "end")
        self.update_statistics()
        logger.info("Log display cleared")

    def export_logs(self):
        """Export logs to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Logs",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")],
        )

        if filename:
            with open(filename, "w") as f:
                f.write(self.log_text.get("1.0", "end"))
            logger.info(f"Logs exported to: {filename}")

    def toggle_pause(self):
        """Toggle log monitoring pause."""
        if self.pause_button.cget("text").startswith("⏸️"):
            self.pause_button.configure(text="▶️ Resume")
            logger.info("Log monitoring paused")
        else:
            self.pause_button.configure(text="⏸️ Pause")
            logger.info("Log monitoring resumed")

    def toggle_auto_scroll(self):
        """Toggle auto-scroll."""
        self.auto_scroll = self.auto_scroll_checkbox.get()
        if self.auto_scroll:
            self.log_text.see("end")

    def toggle_wrap(self):
        """Toggle word wrap."""
        if self.wrap_checkbox.get():
            # Note: CTkTextbox doesn't directly support wrap configuration
            # This would need custom implementation
            pass
