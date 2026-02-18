# Testing Guide - Topspin Sample Manager

## Quick Start Testing

### 1. Launch the Application

From Topspin command line:
```
samples
```

Expected behavior:
- GUI window appears with title "NMR Sample Manager"
- Current directory should auto-navigate to your active dataset
- Status bar shows "Ready"

### 2. Create Your First Sample

1. Click **"New Sample"** button
2. Fill in the form (all fields optional):
   - Users: Click + to add user names
   - Sample Label: Give it a name (e.g., "lysozyme_test")
   - Sample Components: Click + to add, fill in name/concentration/labeling
   - Buffer: pH, components, solvent
   - NMR Tube: diameter, type, volume
3. Click **"Save"**

Expected behavior:
- New JSON file created: `YYYY-MM-DD_HHMMSS_lysozyme_test.json`
- Sample appears in left panel with `[ACTIVE]` status
- Status bar confirms save

### 3. Test Sample Editing

1. Select the sample from the list (click on it)
2. Click **"Edit"**
3. Modify some fields
4. Click **"Save"**

Expected behavior:
- File updated with new data
- `modified_timestamp` updated in metadata
- Sample list refreshes

### 4. Test Sample Duplication

1. Select a sample
2. Click **"Duplicate"**
3. Modify the label or other fields
4. Click **"Save"**

Expected behavior:
- New JSON file created with different timestamp
- Previous active sample auto-ejected
- New sample marked `[ACTIVE]`
- Old sample now shows `[EJECTED]`

### 5. Test Sample Ejection

1. Select an active sample
2. Click **"Eject (Virtual)"**

Expected behavior:
- `ejected_timestamp` added to metadata
- Sample status changes to `[EJECTED]` in list
- Status bar confirms ejection

### 6. Test Timeline View

1. Click **"Show Timeline"** button

Expected behavior:
- Timeline displays in chronological order
- Sample creation events shown
- Sample ejection events shown
- Experiment directories (integer folders with acqus) shown
- Experiment details shown (pulprog, nucleus, scans)

### 7. Test Experiment Opening

1. In timeline view, double-click on an experiment entry

Expected behavior:
- Experiment opens in Topspin (via `RE()` command)
- Status bar shows confirmation

### 8. Test Persistence

1. Close the GUI window (X button)
2. Run `samples` command again

Expected behavior:
- Same window reappears (not a new instance)
- State preserved (same directory, same selections)
- This confirms singleton pattern is working

### 9. Test Integration Commands

#### Auto-Inject (aij)

From Topspin command line:
```
aij
```

Expected behavior:
- Sample Manager window appears (or comes to front)
- New sample form appears
- Previous active sample auto-ejected
- Placeholder message about physical injection

#### Auto-Eject (aej)

From Topspin command line:
```
aej
```

Expected behavior:
- Sample Manager window appears
- Active sample found and ejected
- Placeholder message about physical ejection

### 10. Test Directory Navigation

1. Click **"Browse..."**
2. Select a different experiment directory
3. Verify sample list updates

Expected behavior:
- Directory label updates
- Sample list shows samples from new directory
- Timeline updates to show new directory content

## Troubleshooting

### Problem: "Sample Manager not running" when using aij/aej

**Solution**: Run `samples` command first to start the main application

### Problem: No samples appear in list

**Possible causes**:
1. No JSON files in current directory (create one with "New Sample")
2. Wrong directory selected (use "Browse" or "Current Dataset")
3. JSON files don't match naming convention

### Problem: Form doesn't appear or looks wrong

**Possible causes**:
1. Schema file missing: check `src/schemas/current/schema.json` exists
2. Schema file malformed: validate JSON syntax
3. Jython version incompatibility: confirm Jython 2.7.2

### Problem: Timeline shows no experiments

**Expected behavior**: Only directories with:
- Integer name (1, 2, 10, etc.)
- Containing `acqus` file

If your data structure is different, this may be normal.

### Problem: "AttributeError" or missing methods

**Solution**: Quit and restart
1. Click **"Quit"** button (this removes old instance)
2. Run `samples` again (creates fresh instance)

This happens during development when code is updated.

## Advanced Testing

### Test Schema Compliance

1. Create a sample with all field types:
   - String fields (labels, names)
   - Number fields (concentrations, pH)
   - Enum fields (dropdowns like isotopic labeling)
   - Array fields (multiple users, components)
   - Nested objects (Sample.Components)

2. Verify saved JSON matches schema structure

3. Try loading the JSON in the web app to test compatibility

### Test File Naming Edge Cases

Create samples with these labels:
- "Sample with spaces"
- "Special!@#$%Characters"
- "" (empty label)

Verify filenames are sanitized correctly.

### Test Auto-Ejection Logic

1. Create sample A (should be active)
2. Create sample B (should auto-eject A)
3. Verify only one sample is ever `[ACTIVE]`
4. Create sample C (should auto-eject B)
5. Check all timestamps are correct

### Test Timeline Sorting

1. Create samples at different times
2. Navigate to directory with multiple experiments
3. Verify timeline is truly chronological:
   - Old experiments before new samples
   - Creation before ejection for same sample
   - Correct timestamp parsing

### Test Error Handling

Try these deliberately problematic actions:
- Save sample without filling any fields (should work - all optional)
- Browse to non-existent directory
- Manually corrupt a JSON file and try to load it
- Delete schema file and restart app

Verify error messages are helpful and app doesn't crash.

## Performance Testing

### Large Directories

Test with directory containing:
- 100+ sample JSON files
- 50+ experiment folders
- Deep nesting

Verify:
- List loads without delay
- Timeline builds quickly
- No memory issues

### Rapid Operations

Test rapid clicking:
- Create multiple samples quickly
- Switch between samples rapidly
- Toggle between timeline and form view repeatedly

Verify:
- No race conditions
- UI remains responsive
- State stays consistent

## Compatibility Testing

### Web App Compatibility

1. Create sample in Jython app
2. Open same JSON in web app browser
3. Edit in web app
4. Reload in Jython app
5. Verify bidirectional compatibility

### Topspin Integration

1. Run from different dataset locations
2. Test `CURDATA()` navigation across different experiments
3. Verify `RE()` opens experiments correctly
4. Test with SampleJet rack positions if available

## Test Checklist

Print this checklist and mark off as you test:

**Basic Operations**
- [ ] Launch application
- [ ] Create new sample
- [ ] Edit sample
- [ ] Duplicate sample
- [ ] Eject sample (virtual)
- [ ] Browse directories
- [ ] Navigate to current dataset

**Form Functionality**
- [ ] Text input fields
- [ ] Number input fields
- [ ] Dropdown (enum) fields
- [ ] Array add/remove (Users)
- [ ] Array add/remove (Components)
- [ ] Nested objects work
- [ ] Data persists across save/load

**Timeline**
- [ ] Sample events appear
- [ ] Experiments detected
- [ ] Chronological sorting correct
- [ ] Double-click opens experiment
- [ ] Timeline updates with new samples

**Integration**
- [ ] aij command works
- [ ] aej command works
- [ ] Auto-ejection works
- [ ] Singleton persistence works
- [ ] Quit and restart works

**File System**
- [ ] JSON files created correctly
- [ ] Filename convention followed
- [ ] Timestamps correct (UTC ISO 8601)
- [ ] Schema version recorded
- [ ] Files readable by web app

**Error Handling**
- [ ] Missing directory handled gracefully
- [ ] Corrupt JSON handled gracefully
- [ ] Missing schema handled gracefully
- [ ] No active sample to eject handled gracefully

## Reporting Issues

When reporting issues, please include:
1. Topspin version
2. Jython version (should be 2.7.2)
3. Operating system
4. Exact error message (if any)
5. Steps to reproduce
6. Expected vs actual behavior
7. Sample JSON files (if relevant)

Check console output for detailed stack traces.
