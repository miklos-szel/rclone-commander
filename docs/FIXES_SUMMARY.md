# Fixes Summary - November 21, 2025

## Issues Fixed

### 1. File Selection Bug ✓

**Problem:** Pressing Space to select a file was marking the wrong file/directory.

**Root Cause:** The display showed entries in sorted order (directories first A-Z, then files A-Z), but the internal `self.entries` array stored them in unsorted filesystem order. This caused index mismatches when converting cursor row to entry index.

**Solution:** Modified `set_entries()` in `src/rclonecommander/main.py` to store entries in the same sorted order as displayed:
```python
dirs = sorted([e for e in entries if e.is_dir], key=lambda x: x.name.lower())
files = sorted([e for e in entries if not e.is_dir], key=lambda x: x.name.lower())
self.entries = dirs + files  # Now matches display order
```

**Files Changed:**
- `src/rclonecommander/main.py` (lines 78-112)

### 2. Debug Configuration ✓

**Problem:** Debug mode could only be enabled via environment variable, not persisted in config.

**Solution:** Added `debug` option to configuration system:
- Added to `config/rclone-commander.ini` under [General]
- Added to `AppConfig` class in `src/rclonecommander/config.py`
- Added `setup_debug_logging()` function in `src/rclonecommander/main.py`
- Environment variable `RCLONE_DEBUG` still works and overrides config file

**Files Changed:**
- `config/rclone-commander.ini` (added `debug = false`)
- `src/rclonecommander/config.py` (added debug field and loading)
- `src/rclonecommander/main.py` (setup_debug_logging function)

### 3. Navigation Features (Already Working) ✓

Verified that the following already work correctly:
- Arrow keys for navigation
- Enter to navigate into directories
- ".." entry for parent navigation
- Mouse clicks on rows
- Space/Insert to toggle selection

## Display Order Standardization ✓

The application now consistently displays entries in this order:
1. ".." (parent directory) - when not at root
2. Directories - sorted alphabetically (case-insensitive)
3. Files - sorted alphabetically (case-insensitive)

This is a standard ordering used by dual-pane file managers.

## Debug Logging Added ✓

Comprehensive debug logging now tracks:
- Entry loading with row positions and indices
- Selection operations with before/after states
- Cursor position and offset calculations
- All display refresh operations

Enable debug mode:
- Config: `debug = true` in `config/rclone-commander.ini`
- Environment: `export RCLONE_DEBUG=1`
- Log file: `rclonecommander_debug.log`

## Testing

All changes verified with:
- Syntax checks: ✓ All files compile
- Unit tests: ✓ `test_sorting_fix.py` passes
- Debug logging: ✓ Produces detailed trace logs

## Documentation Updated

- `CLAUDE.md` - Added display order and debug mode sections
- `DEBUG_GUIDE.md` - Updated with config file option
- `BUGFIX_SELECTION.md` - Detailed explanation of the selection bug fix
- `FIXES_SUMMARY.md` - This document
- `NAVIGATION_FIXES.md` - Earlier navigation features

## Ready for Testing

The application is ready for testing with all fixes applied:
```bash
# Test with debug enabled
export RCLONE_DEBUG=1
export RCLONE_CONFIG=/Users/p/Projects/rclonecommander/rclone.conf
python3 rclonecommander.py
```

Expected behavior:
1. Files display in correct order (dirs first, then files, both A-Z)
2. Space/Insert marks the correct file under cursor
3. Enter navigates into directories or up to parent
4. Debug log shows detailed trace of all operations
