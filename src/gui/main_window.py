"""Main GUI window for Resource Allocation System."""

import sys
import os
from pathlib import Path
from typing import Optional
import threading
from datetime import datetime
import customtkinter as ctk
from loguru import logger
from tkinter import messagebox
import tkinter as tk
from PIL import Image, ImageTk

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.dashboard_tab import DashboardTab
from src.gui.allocation_tab import AllocationTab
from src.gui.data_management_tab import DataManagementTab
from src.gui.utils import WindowManager
from src.gui.settings_tab import SettingsTab
from src.gui.log_viewer_tab import LogViewerTab
from src.core.allocation_engine import AllocationEngine
from src.services.excel_service import ExcelService
from src.services.border_formatting_service import BorderFormattingService
from src.services.dashboard_data_service import DashboardDataService
from src.services.data_management_service import DataManagementService


# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class ResourceAllocationGUI(ctk.CTk):
    """Main GUI application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Window configuration
        self.title("Resource Allocation System")
        self.geometry("1400x1000")
        self.minsize(1200, 900)
        
        # Set application icons (title bar and taskbar/dock where supported)
        self._set_app_icons()
        
        # Center window on screen
        self.center_window()
        
        # Services
        self.allocation_engine = None
        self.excel_service = None
        self.border_service = None
        self.dashboard_data_service = None
        self.data_management_service = None
        self.current_allocation_result = None
        
        # Initialize services
        self.initialize_services()
        
        # Setup UI
        self.setup_ui()
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Main content
        self.grid_rowconfigure(2, weight=0)  # Status bar
        self.grid_columnconfigure(0, weight=1)
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start status update thread
        self.update_status()
        
        # Bring window to front
        self.after(100, self._bring_to_front)
        
        logger.info("GUI Application initialized")
    
    def center_window(self):
        """Center the window on the screen."""
        self.update_idletasks()
        width = 1400
        height = 1000
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _bring_to_front(self):
        """Bring the window to front and focus it."""
        try:
            # Use WindowManager for cross-platform support
            WindowManager.bring_to_front(self)
            
            # Ensure window is visible on screen
            WindowManager.ensure_visible(self)
            
            # Make window urgent if it's not already in front
            if not self.focus_displayof():
                WindowManager.make_window_urgent(self)
                
        except Exception as e:
            logger.warning(f"Could not bring window to front: {e}")
            # Fallback to basic methods
            self.lift()
            self.focus_force()
    
    def initialize_services(self):
        """Initialize backend services."""
        try:
            config = {
                "max_vehicles_per_driver": 3,
                "min_vehicles_per_driver": 1,
                "excel_visible": False,
                "use_xlwings": False,  # Use openpyxl for GUI
            }
            
            self.allocation_engine = AllocationEngine(config)
            self.allocation_engine.initialize()
            
            self.excel_service = ExcelService(config)
            self.excel_service.initialize()

            self.border_service = BorderFormattingService(config)
            self.border_service.initialize()

            # Read-only dashboard data provider
            self.dashboard_data_service = DashboardDataService()
            # Read-only data management data provider
            self.data_management_service = DataManagementService()
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            messagebox.showerror("Initialization Error", str(e))
    
    def setup_ui(self):
        """Setup the user interface."""
        # Create header
        self.create_header()
        
        # Create main content area with tabs
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create application header."""
        header_frame = ctk.CTkFrame(self, height=80, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Logo/Icon placeholder
        logo_frame = ctk.CTkFrame(header_frame, width=80, height=80, corner_radius=0)
        logo_frame.grid(row=0, column=0, padx=10, pady=10)
        logo_frame.grid_propagate(False)
        
        # Load header icon image from high‑resolution assets where possible; fallback to emoji
        try:
            header_path = self._resolve_header_image_path()
            pil_img = Image.open(header_path).convert("RGBA")
            # Resize with high quality for crisp display
            try:
                pil_img = pil_img.resize((64, 64), Image.LANCZOS)
            except Exception:
                pil_img = pil_img.resize((64, 64))
            # Use a consistent displayed size for the header logo
            self._header_ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
            logo_label = ctk.CTkLabel(logo_frame, text="", image=self._header_ctk_image)
            logo_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception as e:
            logger.warning(f"Falling back to emoji header icon: {e}")
            logo_label = ctk.CTkLabel(
                logo_frame,
                text="📦",
                font=ctk.CTkFont(size=40)
            )
            logo_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title and subtitle
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Resource Allocation System",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Vehicle Fleet Management & Allocation",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Theme toggle button
        self.appearance_mode_button = ctk.CTkButton(
            header_frame,
            text="🌙",
            width=40,
            height=40,
            corner_radius=20,
            command=self.toggle_appearance_mode,
            font=ctk.CTkFont(size=20)
        )
        self.appearance_mode_button.grid(row=0, column=2, padx=20, pady=20)

    def _resolve_icon_path(self) -> Path:
        """Resolve absolute path to the base window icon (.ico for cross‑platform Tk).

        Supports both running from source and PyInstaller bundles.
        """
        # If running in PyInstaller bundle
        if hasattr(sys, "_MEIPASS"):
            base = Path(getattr(sys, "_MEIPASS"))
            candidate = base / "assets" / "icons" / "amazon_package.ico"
            if candidate.exists():
                return candidate
        # Running from source; project root is three levels up from this file
        project_root = Path(__file__).resolve().parent.parent.parent
        ico = project_root / "assets" / "icons" / "amazon_package.ico"
        if not ico.exists():
            raise FileNotFoundError(f"Icon not found at {ico}")
        return ico

    def _resolve_header_image_path(self) -> Path:
        """Resolve the best available image file for the header logo.

        Preference order (highest first): app.icns (macOS, will read as image),
        app_1024.png, amazon_package.png, amazon_dsp.png, then fallback to
        converting the .ico returned by _resolve_icon_path().
        """
        # Base directory handling for source and bundled runs
        if hasattr(sys, "_MEIPASS"):
            base = Path(getattr(sys, "_MEIPASS"))
            icons = base / "assets" / "icons"
        else:
            icons = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

        candidates = [
            icons / "app.icns",
            icons / "app_1024.png",
            icons / "amazon_package.png",
            icons / "amazon_dsp.png",
        ]
        for p in candidates:
            if p.exists():
                return p

        # Fallback: convert ICO to a temporary PNG so Pillow can load cleanly
        try:
            import tempfile
            ico = self._resolve_icon_path()
            tmp_png = Path(tempfile.gettempdir()) / "resource_allocation_header.png"
            Image.open(ico).save(tmp_png, format="PNG")
            return tmp_png
        except Exception as e:
            raise FileNotFoundError(f"No suitable header image found: {e}")

    def _set_app_icons(self):
        """Set window title bar icon and taskbar/dock icon where supported.

        - Windows: uses iconbitmap(.ico) and iconphoto for various sizes; sets AppUserModelID.
        - macOS/Linux: uses iconphoto; on macOS attempt to set dock icon via AppKit if available.
        Safe fallbacks ensure no functional regression if anything fails.
        """
        try:
            ico_path = self._resolve_icon_path()

            # Prepare Tk PhotoImages at common sizes
            sizes = [16, 32, 64, 128]
            # Prefer a high-resolution PNG for crisp scaling if available; fallback to .ico
            project_root = Path(__file__).resolve().parent.parent.parent
            png_candidates = [
                project_root / "assets" / "icons" / "app_1024.png",
                project_root / "assets" / "icons" / "amazon_package.png",
                project_root / "assets" / "icons" / "amazon_dsp.png",
            ]
            src_for_photo = next((p for p in png_candidates if p.exists()), ico_path)
            pil = Image.open(src_for_photo).convert("RGBA")
            self._icon_images = []  # keep references
            for sz in sizes:
                resized = pil.copy()
                try:
                    # high-quality resize where available
                    resized = resized.resize((sz, sz), Image.LANCZOS)
                except Exception:
                    resized = resized.resize((sz, sz))
                self._icon_images.append(ImageTk.PhotoImage(resized))

            # Set window icon for Tk (works on Linux/macOS; complements Windows)
            try:
                self.iconphoto(True, *self._icon_images)
            except Exception as e:
                logger.debug(f"iconphoto failed: {e}")

            # Platform-specific enhancements
            platform_name = sys.platform
            if platform_name.startswith("win"):
                # Use native .ico for title/taskbar; set AppUserModelID for consistency
                try:
                    self.iconbitmap(str(ico_path))
                except Exception as e:
                    logger.debug(f"iconbitmap failed: {e}")

                try:
                    import ctypes
                    app_id = "com.resourceallocation.app"
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                except Exception as e:
                    logger.debug(f"Setting AppUserModelID failed: {e}")

            elif platform_name == "darwin":
                # Prefer a high‑resolution icon for a crisp Dock image. Use AppKit if available.
                try:
                    from AppKit import NSApplication, NSImage
                    project_root = Path(__file__).resolve().parent.parent.parent
                    icons = project_root / "assets" / "icons"

                    # Build a list of candidates, highest quality first
                    candidates: list[Path] = [
                        icons / "app.icns",
                        icons / "app_1024.png",
                        icons / "amazon_package.png",
                        icons / "amazon_dsp.png",
                    ]

                    icon_for_dock: Path | None = next((p for p in candidates if p.exists()), None)

                    # Fallback: convert the existing .ico into a temp PNG if needed
                    if icon_for_dock is None:
                        try:
                            import tempfile
                            tmp_png = Path(tempfile.gettempdir()) / "resource_allocation_icon.png"
                            pil.copy().save(tmp_png, format="PNG")
                            icon_for_dock = tmp_png
                            logger.debug(f"macOS dock fallback using temp PNG: {icon_for_dock}")
                        except Exception as conv_e:
                            logger.debug(f"ICO→PNG fallback failed: {conv_e}")

                    if icon_for_dock is not None:
                        app = NSApplication.sharedApplication()
                        nsimg = NSImage.alloc().initWithContentsOfFile_(str(icon_for_dock))
                        if nsimg:
                            app.setApplicationIconImage_(nsimg)
                            logger.info(f"macOS Dock icon set from: {icon_for_dock}")
                except Exception as e:
                    # If AppKit (pyobjc) is not installed or something else fails, skip silently
                    logger.debug(f"macOS dock icon enhancement skipped: {e}")
            else:
                # Linux usually picks up from iconphoto; nothing extra required
                pass

            logger.info("Application icons initialized")
        except Exception as e:
            logger.warning(f"Could not set application icons: {e}")
    
    def create_main_content(self):
        """Create main content area with tabs."""
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(main_frame, corner_radius=10)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("🏠 Dashboard")
        self.tabview.add("🚗 Allocation")
        self.tabview.add("📊 Data Management")
        self.tabview.add("📜 Logs")
        self.tabview.add("⚙️ Settings")
        
        # Initialize tab contents
        self.dashboard_tab = DashboardTab(
            self.tabview.tab("🏠 Dashboard"),
            self.allocation_engine,
            dashboard_data_service=self.dashboard_data_service
        )
        
        self.allocation_tab = AllocationTab(
            self.tabview.tab("🚗 Allocation"),
            self.allocation_engine,
            self.excel_service,
            self.border_service
        )

        # Allow dashboard to read the currently selected Daily Summary path
        try:
            self.dashboard_tab.set_daily_summary_path_getter(
                lambda: self.allocation_tab.daily_summary_path.get()
            )
            self.dashboard_tab.set_daily_routes_path_getter(
                lambda: self.allocation_tab.daily_routes_path.get()
            )
        except Exception as e:
            logger.debug(f"Unable to wire Daily Summary getter to dashboard: {e}")
        
        self.data_management_tab = DataManagementTab(
            self.tabview.tab("📊 Data Management"),
            self.excel_service,
            data_service=self.data_management_service
        )
        
        self.log_viewer_tab = LogViewerTab(
            self.tabview.tab("📜 Logs")
        )
        
        self.settings_tab = SettingsTab(
            self.tabview.tab("⚙️ Settings"),
            self.allocation_engine,
            self.excel_service
        )

        # Allow Data Management tab to read the Daily Summary path
        try:
            self.data_management_tab.set_daily_summary_path_getter(
                lambda: self.allocation_tab.daily_summary_path.get()
            )
            # Provide allocated vehicles from most recent result (Allocation tab preferred)
            def _allocated_vehicles_getter():
                try:
                    # Prefer current AllocationTab result (GAS-compatible flow)
                    if getattr(self.allocation_tab, "current_result", None):
                        allocs = self.allocation_tab.current_result.allocations or {}
                        return {vid for vids in allocs.values() for vid in vids}
                except Exception:
                    pass
                try:
                    # Fallback to AllocationEngine history if any
                    hist = self.allocation_engine.get_history()
                    if hist:
                        allocs = hist[-1].allocations or {}
                        return {vid for vids in allocs.values() for vid in vids}
                except Exception:
                    pass
                return set()
            self.data_management_tab.set_allocated_vehicles_getter(_allocated_vehicles_getter)
        except Exception as e:
            logger.debug(f"Unable to wire Daily Summary getter to data tab: {e}")
        
        # Set default tab
        self.tabview.set("🏠 Dashboard")
    
    def create_status_bar(self):
        """Create status bar at bottom."""
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        self.status_indicator.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Memory usage
        self.memory_label = ctk.CTkLabel(
            status_frame,
            text="Memory: -- MB",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.memory_label.grid(row=0, column=2, padx=10, pady=5)
        
        # Time
        self.time_label = ctk.CTkLabel(
            status_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.time_label.grid(row=0, column=3, padx=10, pady=5)
    
    def toggle_appearance_mode(self):
        """Toggle between light and dark mode."""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.appearance_mode_button.configure(text="☀️")
        else:
            ctk.set_appearance_mode("Dark")
            self.appearance_mode_button.configure(text="🌙")
    
    def update_status(self):
        """Update status bar information."""
        try:
            # Update time
            self.time_label.configure(text=datetime.now().strftime("%H:%M:%S"))
            
            # Update memory usage
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.configure(text=f"Memory: {memory_mb:.1f} MB")
            
            # Update dashboard if visible
            if self.tabview.get() == "🏠 Dashboard":
                self.dashboard_tab.update_metrics()
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
        
        # Schedule next update
        self.after(1000, self.update_status)
    
    def set_status(self, message: str, status_type: str = "info"):
        """Set status message.
        
        Args:
            message: Status message to display.
            status_type: Type of status (info, success, warning, error).
        """
        self.status_label.configure(text=message)
        
        color_map = {
            "info": "blue",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        
        color = color_map.get(status_type, "gray")
        self.status_indicator.configure(text_color=color)
    
    def show_notification(self, title: str, message: str, notification_type: str = "info"):
        """Show notification to user.
        
        Args:
            title: Notification title.
            message: Notification message.
            notification_type: Type of notification.
        """
        if notification_type == "error":
            messagebox.showerror(title, message)
        elif notification_type == "warning":
            messagebox.showwarning(title, message)
        elif notification_type == "success":
            messagebox.showinfo(title, message)
        else:
            messagebox.showinfo(title, message)
    
    def on_closing(self):
        """Handle window closing event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                # Cleanup services
                if self.excel_service:
                    self.excel_service.cleanup()
                if self.allocation_engine:
                    self.allocation_engine.cleanup()
                if self.border_service:
                    self.border_service.cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self.destroy()
                sys.exit(0)


def main():
    """Main entry point for GUI application."""
    app = ResourceAllocationGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
