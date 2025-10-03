#!/usr/bin/env python3
"""Script to fix test fixture references."""

import re
from pathlib import Path

def fix_fixture_references(file_path):
    """Fix fixture references in test files."""
    content = file_path.read_text()
    
    # Define fixture mappings
    replacements = [
        # Duplicate validator tests
        (r'def test_[^(]*\(self, validator,', r'def test_\g<0>'.replace('validator,', 'duplicate_validator,')),
        (r'validator\.', 'duplicate_validator.'),
        (r'sample_allocations', 'sample_allocation_results'),
        
        # Unassigned writer tests  
        (r'def test_[^(]*\(self, writer,', r'def test_\g<0>'.replace('writer,', 'unassigned_writer,')),
        (r'writer\.', 'unassigned_writer.'),
        (r'sample_unassigned_vehicles\b', 'sample_unassigned_vehicles_df'),
        
        # Thick borders tests
        (r'def test_[^(]*\(self, thick_border_service,', r'def test_\g<0>'),
        
        # General fixture updates
        (r'tmp_path', 'temp_dir'),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Additional specific fixes
    if 'test_duplicate_validator.py' in str(file_path):
        # Fix specific method calls
        content = content.replace('result = validator.validate_allocations(sample_allocations)', 
                                 'result = duplicate_validator.validate_allocations(sample_allocation_results)')
        content = content.replace('result = validator.validate_allocations(allocations)', 
                                 'result = duplicate_validator.validate_allocations(allocations)')
        content = content.replace('validator = DuplicateVehicleValidator', 
                                 'validator = DuplicateVehicleValidator')
        content = content.replace('validator.validate_allocations', 
                                 'validator.validate_allocations')  # Keep local variables as is
    
    file_path.write_text(content)
    print(f"Fixed fixtures in {file_path}")

def main():
    """Main function to fix all test files."""
    test_dir = Path("tests")
    
    for test_file in test_dir.rglob("test_*.py"):
        if test_file.name in ['test_duplicate_validator.py', 'test_unassigned_vehicles_writer.py']:
            fix_fixture_references(test_file)
    
    print("Test fixture references updated!")

if __name__ == "__main__":
    main()

import tkinter as tk

def create_window():
    root = tk.Tk()
    root.title("Resource Management System")
    
    # Set larger window size to display all components
    root.geometry("1300x800")  # Increased height to 800 pixels
    root.minsize(1200, 750)    # Prevent resizing below this to keep buttons visible
    
    # ...existing code...