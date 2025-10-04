# Separate Results File Feature - User Guide

## Overview

Starting with version 1.2.0, the Resource Management System now creates allocation results in a separate file in the `outputs` folder, instead of adding them to the Daily Summary Log. This change improves performance, organization, and makes it easier to share results.

## What's Changed

### Before (Old System)
- All results were added as new sheets to `Daily Summary Log 2025.xlsx`
- File grew larger with each allocation run
- Results mixed with operational data
- Difficult to share just the results

### After (New System)
- **Daily Summary Log**: Only contains Daily Details (historical record)
- **Results Files**: Created in `outputs/` folder as `Allocation_Results_YYYY-MM-DD.xlsx`
- Each results file contains:
  - "Results" sheet - Today's allocation results
  - "Unassigned Vehicles" sheet - Vehicles not assigned to routes

## How to Use

### Running an Allocation

1. **Start the allocation as usual**:
   - Select your three input files
   - Set the allocation date
   - Click "Run Allocation"

2. **What happens during allocation**:
   - Daily Details sheet in Daily Summary Log is updated (as before)
   - A new results file is created in the `outputs` folder
   - The GUI shows both file locations

3. **After allocation completes**:
   - You'll see a message showing where the results file was saved
   - Click "Open Results File" to view the results
   - The results file contains both allocated routes and unassigned vehicles

### File Locations

**Daily Summary Log** (same as before):
- Location: Your selected file path
- Contains: Daily Details with historical allocation data
- No longer contains Results sheets

**Results Files** (new):
- Location: `outputs/Allocation_Results_2025-08-05.xlsx`
- Contains: Results sheet and Unassigned Vehicles sheet
- New file created for each allocation date
- If you run multiple allocations on the same day, files are versioned (v2, v3, etc.)

## Benefits

1. **Better Performance**: Smaller files load and save faster
2. **Easy Sharing**: Share results without exposing operational data
3. **Better Organization**: Clear separation between operational and results data
4. **Easy Archival**: Delete old results files without affecting Daily Summary
5. **No File Bloat**: Daily Summary Log doesn't grow indefinitely

## GUI Changes

### New Button
- **"Open Results File"**: Opens the results file after allocation
- Located next to the Export Results button
- Only enabled after successful allocation

### Updated Messages
The allocation summary now shows:
```
FILES UPDATED:
  • Daily Summary Log: Daily Details sheet updated
  • Results File: outputs/Allocation_Results_2025-08-05.xlsx
    - Contains 'Results' and 'Unassigned Vehicles' sheets
```

## Frequently Asked Questions

**Q: Where are my old results sheets?**
A: Existing results sheets in your Daily Summary Log remain unchanged. Only new allocations use separate files.

**Q: Can I still access results from the Daily Summary Log?**
A: The Daily Details sheet still contains all allocation data. The separate Results file provides a cleaner view for sharing and reporting.

**Q: What if I run multiple allocations on the same day?**
A: The system automatically versions the files: `Allocation_Results_2025-08-05_v2.xlsx`, etc.

**Q: Can I change the output directory?**
A: Currently, all results files are saved to the `outputs` folder. This may be configurable in future versions.

**Q: How do I share results with others?**
A: Simply share the results file from the outputs folder. It contains everything needed without exposing your operational data.

## Tips

1. **Clean Up Old Results**: Periodically delete old results files from the outputs folder to save disk space
2. **Archive Important Results**: Copy important results files to a backup location
3. **Use Open After Allocation**: Check the "Open file after allocation" box to automatically view results
4. **Check File Location**: The GUI clearly shows where results are saved after each allocation

## Troubleshooting

**Results file not created?**
- Check that the `outputs` folder exists and is writable
- Look for error messages in the GUI
- Ensure you have sufficient disk space

**Can't find results file?**
- Check the allocation summary for the exact file path
- Look in the `outputs` folder in your application directory
- Use the "Open Results File" button in the GUI

**Excel won't open the file?**
- Ensure Excel is installed and set as the default for .xlsx files
- Try opening the file manually from the outputs folder
- Check file permissions

## Migration Notes

- No action required for existing users
- Old results sheets in Daily Summary Log are preserved
- New allocations automatically use the new system
- Daily Details continue to accumulate as before

For technical support or questions, please contact your system administrator.
