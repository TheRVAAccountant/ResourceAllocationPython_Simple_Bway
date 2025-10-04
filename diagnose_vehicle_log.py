"""Diagnostic script to check Vehicle Log structure and data."""

import sys
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def diagnose_vehicle_log(file_path: str):
    """Diagnose Vehicle Log sheet structure and data."""
    print(f"\n{'='*60}")
    print("Vehicle Log Diagnostic Report")
    print(f"{'='*60}\n")

    try:
        # Check if file exists
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return

        # List all sheets in the file
        xl_file = pd.ExcelFile(file_path)
        print(f"📋 Sheets in file: {xl_file.sheet_names}\n")

        # Check if Vehicle Log sheet exists
        if "Vehicle Log" not in xl_file.sheet_names:
            print("❌ 'Vehicle Log' sheet not found!")
            print("   Available sheets:", xl_file.sheet_names)
            return

        # Load Vehicle Log sheet
        df = pd.read_excel(file_path, sheet_name="Vehicle Log")
        print("✅ Vehicle Log sheet found and loaded")
        print(f"   Total rows: {len(df)}")
        print(f"   Total columns: {len(df.columns)}\n")

        # Display all column names
        print("📊 Column names in Vehicle Log:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. '{col}'")
        print()

        # Check for key columns
        key_columns = ["Van ID", "VIN", "GeoTab", "GeoTab Code", "Type", "Branded or Rental"]
        print("🔍 Checking for key columns:")
        for col in key_columns:
            if col in df.columns:
                non_empty = df[col].notna().sum()
                print(f"   ✅ '{col}' - Found ({non_empty}/{len(df)} non-empty values)")
            else:
                print(f"   ❌ '{col}' - Not found")
        print()

        # Show sample data for first 5 vehicles
        print("📄 Sample data (first 5 rows):")
        columns_to_show = [
            col
            for col in df.columns
            if any(
                keyword in col.lower()
                for keyword in ["van", "vin", "geotab", "type", "brand", "rental"]
            )
        ]
        if columns_to_show:
            print(df[columns_to_show].head())
        else:
            print(df.head())
        print()

        # Check specific vehicles from the screenshot
        test_vans = ["BW106", "BW26", "BW2", "BW3", "BW4"]
        print("🔎 Checking specific vehicles from screenshot:")

        van_id_col = None
        for col in df.columns:
            if col.lower().strip() == "van id":
                van_id_col = col
                break

        if van_id_col:
            for van in test_vans:
                vehicle_data = df[df[van_id_col] == van]
                if not vehicle_data.empty:
                    print(f"\n   Vehicle {van}:")
                    for col in columns_to_show:
                        if col in vehicle_data.columns:
                            value = vehicle_data.iloc[0][col]
                            print(f"     {col}: {value}")
                else:
                    print(f"\n   Vehicle {van}: Not found in Vehicle Log")
        else:
            print("   ❌ Could not find 'Van ID' column")

        # Also check Vehicle Status sheet
        print("\n" + "=" * 60)
        print("📋 Checking Vehicle Status sheet:")
        if "Vehicle Status" in xl_file.sheet_names:
            vs_df = pd.read_excel(file_path, sheet_name="Vehicle Status")
            print(f"✅ Vehicle Status sheet found with {len(vs_df)} rows")
            print(f"   Columns: {list(vs_df.columns)[:10]}...")  # First 10 columns

            # Check if test vans exist in Vehicle Status
            van_col = None
            for col in vs_df.columns:
                if "van" in col.lower() and "id" in col.lower():
                    van_col = col
                    break

            if van_col:
                for van in test_vans[:3]:  # Check first 3
                    if van in vs_df[van_col].values:
                        print(f"   ✅ {van} found in Vehicle Status")
                    else:
                        print(f"   ❌ {van} NOT found in Vehicle Status")

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Ask user for the Daily Summary Log file path
    print("Vehicle Log Diagnostic Tool")
    print("-" * 30)

    file_path = input("Enter the path to your Daily Summary Log 2025.xlsx file: ").strip()

    if not file_path:
        # Use a default path if known
        file_path = "Daily Summary Log 2025.xlsx"
        print(f"Using default path: {file_path}")

    diagnose_vehicle_log(file_path)
