class ResourceAllocationGUI:
    def __init__(self, root):  # noqa: ARG002
        # ...existing code...

        # Update window size configuration
        self.root.geometry("800x700")  # Increased height
        self.root.minsize(800, 650)  # Minimum size to show all components

        # ...existing code...
