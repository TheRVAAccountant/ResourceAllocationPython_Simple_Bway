"""Entry point for running the GUI as a module."""

import sys
from pathlib import Path

# Ensure the parent directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.main_window import main

if __name__ == "__main__":
    main()