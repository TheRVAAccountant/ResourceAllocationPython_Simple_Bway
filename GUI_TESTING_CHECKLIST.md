# GUI Testing Checklist - Allocation History Feature

**Purpose**: Manual testing guide to verify allocation history feature works end-to-end

**Estimated Time**: 15-20 minutes

---

## Prerequisites

- [x] Phase 1 MVP code implemented
- [x] Manual tests pass (`tests/manual/test_allocation_history.py`)
- [x] Both engines initialize with history service
- [ ] Test Excel files available

---

## Test Scenarios

### 1. Clean Start Test (5 minutes)

**Goal**: Verify feature works from empty state

1. **Backup existing history**
   ```bash
   mv config/allocation_history.json config/allocation_history.json.backup
   ```

2. **Launch GUI**
   ```bash
   python gui_app.py
   ```

3. **Check Dashboard Tab**
   - [ ] Should show "No allocation history found" message
   - [ ] "🔄 Refresh" button should be visible
   - [ ] No cards displayed

4. **Run First Allocation**
   - [ ] Go to Allocation tab
   - [ ] Select test files:
     - Day of Ops: `2025-01-21-DVA2-CYCLE_1-DSP-DayOfOpsPlan.xlsx`
     - Daily Routes: `Routes_DVA2_2025-01-21_10_59 (EST).xlsx`
     - Vehicle Status: `Daily Summary Log 2025.xlsx`
   - [ ] Click "Run Allocation"
   - [ ] Wait for completion

5. **Verify First Card Appears**
   - [ ] Dashboard updates automatically
   - [ ] One HistoryCard appears
   - [ ] Card shows:
     - [ ] Timestamp (format: "Sep 29, 2025 6:23 PM")
     - [ ] Status badge (✓, ⚠️, or ❌)
     - [ ] Metrics row (routes/allocated/rate)
     - [ ] Engine name ("GASCompatibleAllocator")
     - [ ] "Details →" button

6. **Test Card Hover**
   - [ ] Hover over card
   - [ ] Background color changes (theme-aware)
   - [ ] Border appears

7. **Test Details Modal**
   - [ ] Click "Details →" button
   - [ ] Modal opens centered on window
   - [ ] Modal shows 3 sections:
     - [ ] Summary (metrics)
     - [ ] Files (3 file paths)
     - [ ] Breakdown (allocation results)
   - [ ] Click "Close" to dismiss

---

### 2. Multiple Allocations Test (5 minutes)

**Goal**: Verify multiple entries display correctly

1. **Run Second Allocation**
   - [ ] Use same files
   - [ ] Click "Run Allocation"
   - [ ] Wait for completion

2. **Verify Second Card**
   - [ ] Dashboard shows 2 cards
   - [ ] Cards stacked vertically
   - [ ] Scrollbar appears if needed
   - [ ] Newest card at top

3. **Run Third Allocation**
   - [ ] Repeat with same files
   - [ ] Verify 3 cards appear

4. **Test Refresh Button**
   - [ ] Click "🔄 Refresh" button
   - [ ] Cards reload
   - [ ] Count remains 3

---

### 3. Persistence Test (3 minutes)

**Goal**: Verify history persists across sessions

1. **Close Application**
   - [ ] Click X to close GUI
   - [ ] Verify window closes completely

2. **Verify JSON File**
   ```bash
   cat config/allocation_history.json | python -m json.tool | head -20
   ```
   - [ ] File exists
   - [ ] Contains JSON array
   - [ ] Has 3 entries

3. **Reopen Application**
   ```bash
   python gui_app.py
   ```

4. **Verify History Loaded**
   - [ ] Dashboard shows 3 cards immediately
   - [ ] Data matches previous session
   - [ ] Details modal still works

---

### 4. Statistics Test (2 minutes)

**Goal**: Verify statistics calculate correctly

1. **Check JSON Statistics**
   ```python
   python -c "
   from src.services.allocation_history_service import AllocationHistoryService
   service = AllocationHistoryService()
   service.initialize()
   stats = service.get_statistics()
   print(f'Total: {stats[\"total_allocations\"]}')
   print(f'Success Rate: {stats[\"success_rate\"]:.1f}%')
   print(f'Routes: {stats[\"total_routes_allocated\"]}')
   print(f'Vehicles: {stats[\"total_vehicles_allocated\"]}')
   "
   ```
   - [ ] Total allocations = 3
   - [ ] Success rate = 100.0%
   - [ ] Routes/vehicles > 0

---

### 5. Error Handling Test (3 minutes)

**Goal**: Verify error states display correctly

1. **Trigger Allocation Error**
   - [ ] Select invalid files (non-existent paths)
   - [ ] Click "Run Allocation"
   - [ ] Wait for error

2. **Verify Error Card**
   - [ ] Card appears with ❌ badge (red)
   - [ ] Error message visible in metrics
   - [ ] Details modal shows error text

3. **Verify Statistics Update**
   - [ ] Success rate decreases
   - [ ] Total allocations increases

---

### 6. Duplicate Conflicts Test (Optional, 3 minutes)

**Goal**: Verify duplicate warning badge

1. **Trigger Duplicate Conflict**
   - [ ] Use files with duplicate vehicle assignments
   - [ ] Run allocation
   - [ ] Proceed through duplicate dialog

2. **Verify Warning Card**
   - [ ] Card shows ⚠️ badge (orange)
   - [ ] Duplicate count visible
   - [ ] Details modal lists conflicts

---

## Edge Cases

### Large History Test (Optional)

1. **Generate Many Entries**
   ```python
   python tests/manual/test_allocation_history.py
   # Creates 3 entries, run 30+ times to exceed limit
   ```

2. **Verify Rotation**
   - [ ] Max 100 entries in JSON
   - [ ] Oldest entries removed
   - [ ] GUI shows last 10 by default

### Theme Test (Optional)

1. **Toggle Light/Dark Mode**
   - [ ] Switch theme in settings
   - [ ] Cards update colors
   - [ ] Badges remain visible
   - [ ] Hover effects still work

---

## Success Criteria

### Critical (Must Pass)

- [x] Empty state shows message
- [x] First allocation creates card
- [x] Multiple cards display correctly
- [x] Details modal opens and shows data
- [x] History persists after app restart
- [x] Statistics calculate correctly

### Important (Should Pass)

- [ ] Hover effects work
- [ ] Refresh button reloads
- [ ] Error states display correctly
- [ ] Duplicate warnings show
- [ ] Scrolling works with many entries

### Nice to Have (Optional)

- [ ] Performance smooth with 100 entries
- [ ] Theme switching works
- [ ] Rotation limits enforced
- [ ] No memory leaks over time

---

## Troubleshooting

### Issue: "No allocation history found"

**Causes**:
- History file doesn't exist
- File is empty `[]`
- Permission error reading file

**Solutions**:
1. Check `config/allocation_history.json` exists
2. Run manual test to populate
3. Check file permissions

### Issue: Cards not appearing after allocation

**Causes**:
- Dashboard not refreshing
- History service not saving
- Engine not integrated

**Solutions**:
1. Click "🔄 Refresh" button
2. Check logs for save errors
3. Verify engine has `history_service` attribute

### Issue: Modal shows wrong data

**Causes**:
- Entry dict missing fields
- get_history() returning raw entries

**Solutions**:
1. Check entry has `allocation_id`, `metrics` keys
2. Verify get_history() formatting layer

---

## Cleanup

### After Testing

1. **Restore Original History** (if backed up)
   ```bash
   mv config/allocation_history.json.backup config/allocation_history.json
   ```

2. **Or Keep Test Data**
   ```bash
   # Test history is valid, can keep it
   ls -lh config/allocation_history.json
   ```

3. **Document Issues**
   - [ ] Create GitHub issues for bugs found
   - [ ] Update this checklist with new scenarios
   - [ ] Note any UX improvements needed

---

## Results

**Date Tested**: _____________

**Tester**: _____________

**Overall Status**: ☐ Pass  ☐ Fail  ☐ Partial

**Critical Issues**: _____________

**Non-Critical Issues**: _____________

**Recommendations**: _____________

---

*Last Updated: September 29, 2025*  
*Version: 1.0 (Phase 1 MVP)*
