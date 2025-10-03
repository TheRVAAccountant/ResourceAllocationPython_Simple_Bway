import tkinter as tk
from tkinter import ttk

# Initialize the main window
root = tk.Tk()
root.title("Resource Allocation Application")

# Update window geometry settings
root.geometry("1300x950")  # Increased height from default to 800px
root.minsize(1200, 950)    # Set minimum height to prevent cutting off buttons

# Create a notebook (tabbed interface)
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Add tabs to the notebook
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text='Tab 1')

tab2 = ttk.Frame(notebook)
notebook.add(tab2, text='Tab 2')

# Add content to the tabs
label1 = tk.Label(tab1, text="This is Tab 1")
label1.pack(pady=20)

label2 = tk.Label(tab2, text="This is Tab 2")
label2.pack(pady=20)

# Start the main event loop
root.mainloop()