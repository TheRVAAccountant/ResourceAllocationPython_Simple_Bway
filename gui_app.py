#!/usr/bin/env python
"""GUI Application launcher for Resource Management System."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.main_window import main  # noqa: E402

if __name__ == "__main__":
    main()
