"""Quick smoke test for GUI icon setup.

This script initializes the ResourceAllocationGUI, triggers icon setup,
and immediately destroys the window. It verifies that the icon asset is
found and that no errors occur while applying it.
"""

import sys
from pathlib import Path


def main():
    # Ensure project root on sys.path for direct execution
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

    from src.gui.main_window import ResourceAllocationGUI

    app = ResourceAllocationGUI()

    # Basic validations: internal attributes created by icon setup
    ok_images = hasattr(app, "_icon_images") and len(getattr(app, "_icon_images", [])) > 0
    ok_header = hasattr(app, "_header_ctk_image")

    # Briefly update idle tasks so Tk applies icon state
    app.update_idletasks()

    # Destroy immediately to avoid leaving a window open
    app.destroy()

    if ok_images and ok_header:
        print("Icon smoke test: SUCCESS (images loaded and header image set)")
        sys.exit(0)
    else:
        print("Icon smoke test: PARTIAL (window created, but images/header not confirmed)")
        sys.exit(1)


if __name__ == "__main__":
    main()
