"""Test script to verify unassigned vehicles appear in output files."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.gas_compatible_allocator import GASCompatibleAllocator
import pandas as pd
from loguru import logger

# Enable debug logging
logger.remove()
logger.add(sys.stdout, level="DEBUG")


def test_unassigned_vehicles():
    """Test that unassigned vehicles appear correctly in output files."""
    print("\n=== Testing Unassigned Vehicles in Output Files ===\n")
    
    # Create test data
    create_test_data_with_extra_vehicles()
    
    # Initialize allocator
    allocator = GASCompatibleAllocator()
    
    # Load test data
    print("Loading test data...")
    allocator.load_day_of_ops("test_day_of_ops.xlsx")
    allocator.load_vehicle_status("test_vehicle_status.xlsx", sheet_name="Sheet1")
    allocator.load_daily_routes("test_daily_routes.xlsx")
    
    # Check loaded vehicles
    print(f"\nTotal vehicles loaded: {len(allocator.vehicle_status_data)}")
    operational_count = len(allocator.vehicle_status_data[
        allocator.vehicle_status_data["Opnal? Y/N"].str.upper() == "Y"
    ])
    print(f"Operational vehicles: {operational_count}")
    
    # Run allocation steps
    print("\nRunning allocation...")
    allocator.filter_bway_routes()
    allocator.allocate_vehicles_to_routes()
    allocator.update_with_driver_names()
    allocator.identify_unassigned_vehicles()
    
    # Check allocation results
    print(f"\nAllocation results:")
    print(f"- Routes allocated: {len(allocator.allocation_results)}")
    print(f"- Vehicles assigned: {len(allocator.assigned_van_ids)}")
    print(f"- Vehicles unassigned: {len(allocator.unassigned_vehicles)}")
    
    # Verify the math
    total_operational = operational_count
    total_assigned = len(allocator.assigned_van_ids)
    total_unassigned = len(allocator.unassigned_vehicles)
    
    print(f"\nVerification:")
    print(f"- Total operational: {total_operational}")
    print(f"- Total assigned: {total_assigned}")
    print(f"- Total unassigned: {total_unassigned}")
    print(f"- Sum (assigned + unassigned): {total_assigned + total_unassigned}")
    print(f"- Match? {total_operational == total_assigned + total_unassigned}")
    
    # Check unassigned vehicles details
    if not allocator.unassigned_vehicles.empty:
        print(f"\nUnassigned vehicles details:")
        print(allocator.unassigned_vehicles[["Van ID", "Type", "Staging Location", "Opnal? Y/N"]].head())
    
    # Create output file
    print("\nCreating output file...")
    daily_summary_path = "test_daily_summary.xlsx"
    create_daily_summary_file(daily_summary_path)
    
    # This should create the results file
    result, results_file_path = allocator.create_output_file(
        output_file=daily_summary_path
    )
    
    print(f"\nResults file created: {results_file_path}")
    
    # Read the unassigned vehicles sheet to verify
    if results_file_path and Path(results_file_path).exists():
        print(f"\nReading unassigned vehicles from output file...")
        
        try:
            unassigned_df = pd.read_excel(results_file_path, sheet_name="Unassigned Vehicles")
            print(f"\nUnassigned Vehicles sheet shape: {unassigned_df.shape}")
            print("\nUnassigned Vehicles sheet columns:")
            print(list(unassigned_df.columns))
            print("\nFirst few rows:")
            print(unassigned_df.head())
            
            # Check data completeness
            print("\nData completeness check:")
            for col in unassigned_df.columns:
                non_null_count = unassigned_df[col].notna().sum()
                print(f"  {col}: {non_null_count}/{len(unassigned_df)} non-null values")
                
        except Exception as e:
            print(f"Error reading Unassigned Vehicles sheet: {e}")
    
    # Clean up
    cleanup_test_files()
    if results_file_path and Path(results_file_path).exists():
        os.remove(results_file_path)


def create_test_data_with_extra_vehicles():
    """Create test Excel files with more vehicles than routes."""
    # Day of Ops with only 2 BWAY routes
    day_ops_data = pd.DataFrame({
        'Route Code': ['TEST1', 'TEST2', 'TEST3'],
        'DSP': ['BWAY', 'BWAY', 'OTHER'],
        'Service Type': ['Standard Parcel - Large Van', 'Standard Parcel - Extra Large Van - US', 'Standard Parcel - Large Van'],
        'Staging Location': ['STG.A.1', 'STG.B.2', 'STG.C.3'],
        'Wave': ['Wave 1 - 04:20', 'Wave 2 - 04:40', 'Wave 1 - 04:20']
    })
    day_ops_data.to_excel('test_day_of_ops.xlsx', sheet_name='Solution', index=False)
    
    # Vehicle Status with 6 operational vehicles (more than the 2 BWAY routes)
    vehicle_data = pd.DataFrame({
        'Van ID': ['VAN001', 'VAN002', 'VAN003', 'VAN004', 'VAN005', 'VAN006'],
        'Type': ['Large', 'Extra Large', 'Large', 'Extra Large', 'Large', 'Step Van'],
        'Staging Location': ['STG.A.1', 'STG.B.2', 'STG.A.1', 'STG.B.2', 'STG.C.3', 'STG.C.3'],
        'Opnal? Y/N': ['Y', 'Y', 'Y', 'Y', 'Y', 'N'],  # 5 operational, 1 not
        'VIN': ['VIN001', 'VIN002', 'VIN003', 'VIN004', 'VIN005', 'VIN006'],
        'Year': [2019, 2020, 2019, 2021, 2020, 2018],
        'Make': ['Ford', 'Ram', 'Ford', 'Ram', 'Ford', 'Freightliner'],
        'Model': ['Transit', 'ProMaster', 'Transit', 'ProMaster', 'Transit', 'Step Van'],
        'License Tag Number': ['ABC123', 'DEF456', 'GHI789', 'JKL012', 'MNO345', 'PQR678']
    })
    vehicle_data.to_excel('test_vehicle_status.xlsx', index=False)
    
    # Daily Routes with drivers for only 2 routes
    routes_data = pd.DataFrame({
        'Route': ['TEST1', 'TEST2'],
        'Driver Name': ['Driver One', 'Driver Two'],
        'Employee ID': ['EMP001', 'EMP002']
    })
    routes_data.to_excel('test_daily_routes.xlsx', sheet_name='Routes', index=False)


def create_daily_summary_file(path):
    """Create a test Daily Summary file."""
    from openpyxl import Workbook
    wb = Workbook()
    
    # Create Daily Details sheet
    daily_details = wb.active
    daily_details.title = "Daily Details"
    
    # Add headers (24 columns)
    headers = [
        "Date", "Route #", "Name", "Asset ID", "Van ID", "VIN", "GeoTab Code", "Type",
        "Vehicle Type", "Route Type", "Rescue", "1:40pm", "Pace 3:40", "4:15pm", "4:30pm",
        "Returned", "Offload Time", "# of DNRs", "# of Returns", "# of Not Received",
        "# of Routes", "# of Actual Routes", "Comments", "Problem Solver"
    ]
    
    for col, header in enumerate(headers, 1):
        daily_details.cell(row=1, column=col, value=header)
    
    wb.save(path)


def cleanup_test_files():
    """Clean up test files."""
    test_files = [
        'test_day_of_ops.xlsx',
        'test_vehicle_status.xlsx',
        'test_daily_routes.xlsx',
        'test_daily_summary.xlsx'
    ]
    
    for file in test_files:
        if Path(file).exists():
            os.remove(file)


if __name__ == "__main__":
    test_unassigned_vehicles()