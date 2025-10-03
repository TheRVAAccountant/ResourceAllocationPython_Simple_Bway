"""Window management utilities for bringing GUI to front across platforms."""

import platform
import sys

from loguru import logger


class WindowManager:
    """Cross-platform window management utilities."""

    @staticmethod
    def bring_to_front(window):
        """Bring the window to front and focus it.

        Args:
            window: The tkinter/customtkinter window object.
        """
        system = platform.system()

        try:
            # Common operations for all platforms
            window.lift()
            window.attributes("-topmost", True)
            window.after(100, lambda: window.attributes("-topmost", False))
            window.focus_force()

            # Platform-specific operations
            if system == "Darwin":  # macOS
                WindowManager._bring_to_front_macos(window)
            elif system == "Windows":
                WindowManager._bring_to_front_windows(window)
            elif system == "Linux":
                WindowManager._bring_to_front_linux(window)

            logger.info(f"Window brought to front on {system}")

        except Exception as e:
            logger.warning(f"Could not bring window to front: {e}")

    @staticmethod
    def _bring_to_front_macos(window):
        """macOS-specific window focusing."""
        try:
            # Use osascript to activate the application
            import os
            import subprocess

            # Get the process name
            process_name = "Python"  # Default for Python apps

            # Try to activate using AppleScript
            script = f"""
            tell application "System Events"
                set frontmost of the first process whose unix id is {os.getpid()} to true
            end tell
            """

            subprocess.run(["osascript", "-e", script], check=False)

            # Additional macOS-specific attributes
            window.attributes("-topmost", True)
            window.attributes("-topmost", False)

            # Force window to front using tkinter methods
            window.lift()
            window.tkraise()

        except Exception as e:
            logger.debug(f"macOS bring to front enhancement failed: {e}")

    @staticmethod
    def _bring_to_front_windows(window):
        """Windows-specific window focusing."""
        try:
            import ctypes
            from ctypes import wintypes

            # Get window handle
            hwnd = wintypes.HWND(window.winfo_id())

            # Windows API constants
            SW_SHOW = 5
            SW_RESTORE = 9

            # Get necessary Windows APIs
            user32 = ctypes.windll.user32

            # Check if window is minimized
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)

            # Set foreground window
            user32.SetForegroundWindow(hwnd)

            # Alternative method using SwitchToThisWindow
            user32.SwitchToThisWindow(hwnd, True)

        except Exception as e:
            logger.debug(f"Windows bring to front enhancement failed: {e}")

    @staticmethod
    def _bring_to_front_linux(window):
        """Linux-specific window focusing."""
        try:
            # X11 specific operations
            window.attributes("-topmost", True)
            window.after(10, lambda: window.attributes("-topmost", False))

            # Try using wmctrl if available
            import subprocess

            window_id = window.winfo_id()
            subprocess.run(["wmctrl", "-i", "-a", str(window_id)], check=False, capture_output=True)

        except Exception as e:
            logger.debug(f"Linux bring to front enhancement failed: {e}")

    @staticmethod
    def center_window(window, width=None, height=None):
        """Center window on screen.

        Args:
            window: The window to center.
            width: Window width (uses current if None).
            height: Window height (uses current if None).
        """
        window.update_idletasks()

        # Get window dimensions
        if width is None:
            width = window.winfo_width()
        if height is None:
            height = window.winfo_height()

        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Calculate center position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # Apply geometry
        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def make_window_urgent(window):
        """Make window demand attention (flash in taskbar).

        Args:
            window: The window to make urgent.
        """
        try:
            if platform.system() == "Windows":
                # Flash window in taskbar
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32
                hwnd = wintypes.HWND(window.winfo_id())

                # FLASHWINFO structure
                class FLASHWINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", wintypes.UINT),
                        ("hwnd", wintypes.HWND),
                        ("dwFlags", wintypes.DWORD),
                        ("uCount", wintypes.UINT),
                        ("dwTimeout", wintypes.DWORD),
                    ]

                FLASHW_ALL = 3
                FLASHW_TIMERNOFG = 12

                flash_info = FLASHWINFO(
                    ctypes.sizeof(FLASHWINFO),
                    hwnd,
                    FLASHW_ALL | FLASHW_TIMERNOFG,
                    3,  # Flash 3 times
                    0,
                )

                user32.FlashWindowEx(ctypes.byref(flash_info))

            elif platform.system() == "Darwin":  # macOS
                # Bounce dock icon
                import subprocess

                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to set frontmost of '
                        "the first process whose unix id is {} to true".format(
                            window.tk.eval("pid")
                        ),
                    ],
                    check=False,
                )

            elif platform.system() == "Linux":
                # Set urgency hint
                window.bell()

        except Exception as e:
            logger.debug(f"Could not make window urgent: {e}")

    @staticmethod
    def ensure_visible(window):
        """Ensure window is visible on screen (not off-screen).

        Args:
            window: The window to check and reposition if needed.
        """
        window.update_idletasks()

        # Get window position and size
        x = window.winfo_x()
        y = window.winfo_y()
        width = window.winfo_width()
        height = window.winfo_height()

        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # Check if window is off-screen and adjust
        adjusted = False

        if x < 0:
            x = 50
            adjusted = True
        elif x + width > screen_width:
            x = screen_width - width - 50
            adjusted = True

        if y < 0:
            y = 50
            adjusted = True
        elif y + height > screen_height:
            y = screen_height - height - 50
            adjusted = True

        if adjusted:
            window.geometry(f"+{x}+{y}")
            logger.info(f"Window repositioned to be visible: {x}, {y}")
