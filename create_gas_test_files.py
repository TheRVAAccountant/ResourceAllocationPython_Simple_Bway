"""Create test files matching GAS input format for testing."""

import pandas as pd
from datetime import datetime, time
import random


def create_day_of_ops_file():
    """Create a sample Day of Ops file matching GAS format."""
    
    data = {
        "Route Code": [
            "DUL4-5-001", "DUL4-5-002", "DUL4-5-003", "DUL4-5-004", "DUL4-5-005",
            "DUL4-5-006", "DUL4-5-007", "DUL4-5-008", "DUL4-5-009", "DUL4-5-010",
            "CX1", "CX2", "CX3", "CX4", "CX5"
        ],
        "Service Type": [
            "Standard Parcel - Large Van",
            "Standard Parcel - Extra Large Van - US",
            "Standard Parcel - Large Van",
            "Standard Parcel Step Van - US",
            "Nursery Route Level 1",
            "Standard Parcel - Large Van",
            "Standard Parcel - Extra Large Van - US",
            "Nursery Route Level 2",
            "Standard Parcel - Large Van",
            "Standard Parcel Step Van - US",
            "Standard Parcel - Large Van",
            "Standard Parcel - Extra Large Van - US",
            "Standard Parcel - Large Van",
            "Standard Parcel Step Van - US",
            "Nursery Route Level 3"
        ],
        "DSP": [
            "BWAY", "BWAY", "BWAY", "BWAY", "BWAY",
            "BWAY", "OTHER", "BWAY", "BWAY", "OTHER",
            "BWAY", "BWAY", "OTHER", "BWAY", "BWAY"
        ],
        "Wave": [
            "8:00 AM", "8:00 AM", "8:30 AM", "8:30 AM", "9:00 AM",
            "9:00 AM", "9:30 AM", "9:30 AM", "10:00 AM", "10:00 AM",
            "8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM", "10:00 AM"
        ],
        "Staging Location": [
            "STG.G.1", "STG.G.1", "STG.G.2", "STG.G.2", "STG.G.3",
            "STG.G.3", "STG.G.4", "STG.G.4", "STG.G.5", "STG.G.5",
            "STG.G.1", "STG.G.2", "STG.G.3", "STG.G.4", "STG.G.5"
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel with "Solution" sheet
    with pd.ExcelWriter("Day_of_Ops_TEST.xlsx") as writer:
        df.to_excel(writer, sheet_name="Solution", index=False)
    
    print("Created: Day_of_Ops_TEST.xlsx")
    print(f"  - {len(df)} routes total")
    print(f"  - {len(df[df['DSP'] == 'BWAY'])} BWAY routes")
    print(f"  - Service types: {df['Service Type'].unique()[:3]}...")
    
    return df


def create_daily_routes_file():
    """Create a sample Daily Routes file matching GAS format."""
    
    data = {
        "Route code": [
            "DUL4-5-001", "DUL4-5-002", "DUL4-5-003", "DUL4-5-004", "DUL4-5-005",
            "DUL4-5-006", "DUL4-5-007", "DUL4-5-008", "DUL4-5-009", "DUL4-5-010",
            "CX1", "CX2", "CX3", "CX4", "CX5"
        ],
        "Driver name": [
            "John Smith", "Jane Doe", "Bob Johnson", "Alice Williams", "Charlie Brown",
            "Diana Prince", "Edward Norton", "Frank Castle", "Grace Kelly", "Henry Ford",
            "Isaac Newton", "Julia Roberts", "Kevin Hart", "Linda Hamilton", "Michael Jordan"
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel with "Routes" sheet
    with pd.ExcelWriter("Daily_Routes_TEST.xlsx") as writer:
        df.to_excel(writer, sheet_name="Routes", index=False)
    
    print("\nCreated: Daily_Routes_TEST.xlsx")
    print(f"  - {len(df)} driver assignments")
    
    return df


def create_vehicle_status_file():
    """Create a sample Vehicle Status sheet in Daily Summary format."""
    
    # Create various vehicle types
    vehicles = []
    
    # Large vans
    for i in range(1, 8):
        vehicles.append({
            "Van ID": f"VAN{i:03d}",
            "Year": 2023,
            "Make": "Ford",
            "Model": "Transit",
            "Style": "Van",
            "Type": "Large",
            "License Tag Number": f"ABC{i:03d}",
            "License Tag State": "GA",
            "Ownership": "Owned",
            "VIN": f"1FTBW2XG{i:05d}",
            "Van Type": "Large",
            "Issue": "",
            "Date GROUNDED": "",
            "Date UNGROUNDED": "",
            "Opnal? Y/N": "Y" if i <= 6 else "N"
        })
    
    # Extra Large vans
    for i in range(8, 12):
        vehicles.append({
            "Van ID": f"VAN{i:03d}",
            "Year": 2023,
            "Make": "Mercedes",
            "Model": "Sprinter",
            "Style": "Van",
            "Type": "Extra Large",
            "License Tag Number": f"XYZ{i:03d}",
            "License Tag State": "GA",
            "Ownership": "Leased",
            "VIN": f"WD3PF4CC{i:05d}",
            "Van Type": "Extra Large",
            "Issue": "",
            "Date GROUNDED": "",
            "Date UNGROUNDED": "",
            "Opnal? Y/N": "Y" if i <= 10 else "N"
        })
    
    # Step Vans
    for i in range(12, 15):
        vehicles.append({
            "Van ID": f"VAN{i:03d}",
            "Year": 2022,
            "Make": "Freightliner",
            "Model": "P700",
            "Style": "Step Van",
            "Type": "Step Van",
            "License Tag Number": f"STP{i:03d}",
            "License Tag State": "GA",
            "Ownership": "Owned",
            "VIN": f"4UZAANDV{i:05d}",
            "Van Type": "Step Van",
            "Issue": "",
            "Date GROUNDED": "",
            "Date UNGROUNDED": "",
            "Opnal? Y/N": "Y"
        })
    
    df = pd.DataFrame(vehicles)
    
    # Create a Daily Summary file with Vehicle Status sheet
    with pd.ExcelWriter("Daily_Summary_TEST.xlsx") as writer:
        # Add Vehicle Status sheet
        df.to_excel(writer, sheet_name="Vehicle Status", index=False)
        
        # Add empty Daily Details sheet
        daily_details_headers = [
            "Date", "Route #", "Name", "Asset ID", "Van ID", "VIN", "GeoTab Code",
            "Type", "Vehicle Type", "Route Type", "Rescue", "Delivery Pace 1:40pm",
            "Delivery Pace 3:40pm", "Delivery Pace 5:40pm", "Delivery Pace 7:40pm",
            "Delivery Pace 9:40pm", "RTS TIME", "Pkg. Delivered", "Pkg. Returned",
            "Route Notes", "Week Number", "Unique Identifier", "Vehicle Inspection",
            "Route Completion"
        ]
        daily_details_df = pd.DataFrame(columns=daily_details_headers)
        daily_details_df.to_excel(writer, sheet_name="Daily Details", index=False)
    
    print("\nCreated: Daily_Summary_TEST.xlsx")
    print(f"  - {len(df)} vehicles total")
    print(f"  - {len(df[df['Opnal? Y/N'] == 'Y'])} operational")
    print(f"  - Types: {df[df['Opnal? Y/N'] == 'Y']['Type'].value_counts().to_dict()}")
    
    return df


def create_all_test_files():
    """Create all test files for GAS-compatible allocation."""
    print("=" * 60)
    print("Creating GAS-Compatible Test Files")
    print("=" * 60)
    
    # Create the three required files
    day_of_ops = create_day_of_ops_file()
    daily_routes = create_daily_routes_file()
    vehicle_status = create_vehicle_status_file()
    
    print("\n" + "=" * 60)
    print("Test Files Created Successfully!")
    print("=" * 60)
    print("\nFiles created:")
    print("1. Day_of_Ops_TEST.xlsx - Routes requiring vehicles")
    print("2. Daily_Routes_TEST.xlsx - Driver assignments")
    print("3. Daily_Summary_TEST.xlsx - Vehicle inventory")
    
    # Show expected allocation summary
    print("\n" + "=" * 60)
    print("Expected Allocation Results:")
    print("=" * 60)
    
    # Count BWAY routes by type
    bway_routes = day_of_ops[day_of_ops["DSP"] == "BWAY"]
    
    route_types = {
        "Large": len(bway_routes[
            (bway_routes["Service Type"] == "Standard Parcel - Large Van") |
            (bway_routes["Service Type"].str.contains("Nursery Route Level"))
        ]),
        "Extra Large": len(bway_routes[
            bway_routes["Service Type"] == "Standard Parcel - Extra Large Van - US"
        ]),
        "Step Van": len(bway_routes[
            bway_routes["Service Type"] == "Standard Parcel Step Van - US"
        ])
    }
    
    # Count operational vehicles by type
    operational = vehicle_status[vehicle_status["Opnal? Y/N"] == "Y"]
    vehicle_types = operational["Type"].value_counts().to_dict()
    
    print("\nBWAY Routes by Type:")
    for van_type, count in route_types.items():
        print(f"  {van_type}: {count} routes")
    
    print("\nOperational Vehicles by Type:")
    for van_type, count in vehicle_types.items():
        print(f"  {van_type}: {count} vehicles")
    
    print("\nExpected Allocations:")
    for van_type in ["Large", "Extra Large", "Step Van"]:
        routes_need = route_types.get(van_type, 0)
        vehicles_have = vehicle_types.get(van_type, 0)
        allocated = min(routes_need, vehicles_have)
        unassigned = vehicles_have - allocated
        print(f"  {van_type}: {allocated} allocated, {unassigned} unassigned vehicles")
    
    return day_of_ops, daily_routes, vehicle_status


if __name__ == "__main__":
    create_all_test_files()