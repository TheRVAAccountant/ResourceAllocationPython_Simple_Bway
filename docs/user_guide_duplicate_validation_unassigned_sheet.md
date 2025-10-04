# User Guide: Duplicate Validation & Unassigned Vehicles Sheet

## Overview

The Resource Management System now includes two important features to improve operational efficiency and data integrity:

1. **Duplicate Vehicle Assignment Validation** - Automatically detects when a vehicle is assigned to multiple routes
2. **Unassigned Vehicles Sheet** - Creates a dedicated sheet showing all unassigned vehicles after each allocation

## Feature 1: Duplicate Vehicle Assignment Validation

### What It Does

The system automatically checks for vehicles that have been assigned to multiple routes or drivers. This helps prevent:
- Operational conflicts where one vehicle is expected in multiple places
- Driver confusion about vehicle assignments
- Scheduling and logistics issues

### How It Works

1. **During Allocation**: The system tracks all vehicle assignments as they're made
2. **Validation Check**: After allocation completes, it checks for any duplicates
3. **Warning Display**: If duplicates are found, you'll see:
   - A warning dialog in the GUI
   - Marked rows in the Excel output
   - A summary count in the results

### What You'll See

#### In the GUI

When duplicates are detected, you'll see:
- A warning dialog listing the duplicate assignments
- The results summary will show a count of duplicates
- Example: "⚠️ Duplicate Assignments: 3"

![Duplicate Warning Dialog Example]
```
⚠️ Duplicate Vehicle Assignments Detected:

• Vehicle BW1 assigned to multiple routes: CX1, CX4 (Drivers: John Smith, Alice Brown)
• Vehicle BW5 assigned to multiple routes: CX2, CX3 (Drivers: Jane Doe, Bob Johnson)

These duplicates have been marked in the Excel output.
```

#### In Excel Output

Duplicates are marked in the Results sheet with:
- **Validation Status** column: Shows "DUPLICATE" for affected rows
- **Validation Warning** column: Details of the conflict
- **Yellow highlighting** on duplicate rows (if formatting is enabled)

### How to Resolve Duplicates

1. Review the warning message to identify conflicting assignments
2. Check the Excel Results sheet for details
3. Manually reassign vehicles to resolve conflicts
4. Re-run allocation if needed

## Feature 2: Unassigned Vehicles Sheet

### What It Does

After each allocation, the system creates a dedicated sheet showing all operational vehicles that were not assigned to any route. This helps with:
- Fleet utilization tracking
- Maintenance scheduling for idle vehicles
- Capacity planning
- Quick identification of available backup vehicles

### Sheet Details

The unassigned vehicles sheet includes:

| Column | Description |
|--------|-------------|
| Van ID | Vehicle identifier (e.g., BW10) |
| Vehicle Type | Type of vehicle (Large, Extra Large, Step Van) |
| Operational Status | Whether vehicle is operational (Y/N) |
| Last Known Location | Vehicle's last location |
| Days Since Last Assignment | How long vehicle has been unassigned |
| VIN | Vehicle Identification Number |
| GeoTab Code | GPS tracking device code |
| Branded or Rental | Ownership type |
| Notes | Any additional notes |
| Unassigned Date | Date when marked as unassigned |
| Unassigned Time | Time when marked as unassigned |

### Sheet Naming

The sheet is automatically named with the allocation date:
- Format: `MM-DD-YY Available & Unassigned`
- Example: `01-05-25 Available & Unassigned`

### Using the Unassigned Sheet

1. **Daily Review**: Check this sheet after each allocation to see available vehicles
2. **Maintenance Planning**: Use idle vehicles for scheduled maintenance
3. **Backup Planning**: Know which vehicles are available for emergency use
4. **Fleet Analysis**: Track patterns of underutilized vehicles

## Configuration Options

### Duplicate Validation Settings

In the system configuration, you can control:
- **Strict Mode**: Whether duplicates should block allocation completion
- **Max Assignments**: Maximum vehicles allowed per driver (default: 1)

### Unassigned Sheet Options

- **Include Non-Operational**: Whether to show non-operational vehicles
- **Historical Tracking**: Calculate days since last assignment

## Best Practices

### For Duplicate Prevention

1. **Review Input Data**: Check Day of Ops and Daily Routes for errors before allocation
2. **Monitor Warnings**: Don't ignore duplicate warnings - resolve them promptly
3. **Regular Audits**: Periodically review allocation patterns for systemic issues

### For Fleet Utilization

1. **Daily Monitoring**: Check unassigned vehicles daily
2. **Trend Analysis**: Look for vehicles frequently unassigned
3. **Capacity Planning**: Use data to right-size your fleet
4. **Maintenance Windows**: Schedule maintenance for consistently unassigned vehicles

## Troubleshooting

### Common Issues

**Q: Why am I seeing so many duplicates?**
- Check if you have more routes than available vehicles
- Verify vehicle operational status is correctly set
- Ensure service type mappings are correct

**Q: The unassigned sheet is empty but I know vehicles weren't used**
- Verify vehicles are marked as operational (Opnal? Y/N = "Y")
- Check that vehicle data is properly loaded
- Ensure DSP filter isn't excluding vehicles

**Q: Days Since Last Assignment shows 0 for all vehicles**
- This requires historical data to be available
- The feature will populate over time as allocation history builds

### Getting Help

If you encounter issues:
1. Check the allocation log for detailed error messages
2. Verify all input files have the required columns
3. Contact support with:
   - Screenshot of any error messages
   - Sample of your input files
   - Description of the issue

## Summary

These features work together to:
- **Prevent Conflicts**: Catch duplicate assignments before they cause operational issues
- **Improve Utilization**: Track and manage unassigned vehicles effectively
- **Enhance Visibility**: Provide clear reporting on allocation issues and fleet status

By using these features effectively, you can improve operational efficiency, reduce errors, and better manage your fleet resources.
