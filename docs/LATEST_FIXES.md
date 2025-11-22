# Latest Fixes - November 21, 2025

## Issues Fixed

### 1. Cursor Position When Exiting Directory ✓

**Problem:** When entering a directory and then going back up with "..", the cursor would be at the top instead of on the directory you just left.

**Solution:**
- Added `_last_dir_entered` tracking to FileListView
- When navigating up with "..", stores the directory name we're leaving
- In `set_entries()`, searches for that directory and positions cursor on it
- Uses `move_cursor(row=target_row)` to position correctly

**Files Changed:**
- `src/rclonecommander/main.py` (lines 66, 114-140, 167-171)

### 2. Key Bindings Changed for macOS Compatibility ✓

**Problem:** F-keys (F5/F6/F8/F10) don't work reliably on macOS due to system shortcuts.

**Solution:** Added Ctrl+ alternatives as primary keys:
- **Ctrl+C** - Copy (in addition to F5)
- **Ctrl+X** - Move (in addition to F6)
- **Ctrl+D** - Delete (in addition to F8/Delete)
- **Ctrl+R** - Select Remote (in addition to F10)
- **Ctrl+U** - Swap panels (unchanged)

Status bar updated to show: `^C=Copy | ^X=Move | ^D=Delete | ^R=Remotes`

**Files Changed:**
- `config/app_config.ini` (key bindings section)
- `src/rclonecommander/main.py` (status bar line 485)

### 3. Debug Logging for Operations ✓

**Problem:** Copy/Move/Delete/Swap operations had no debug output, making it hard to diagnose issues.

**Solution:** Added comprehensive debug logging to all operations:

**action_copy logs:**
- Source and destination panels
- Number of entries selected
- Each file being copied with full paths
- Success/failure result for each operation

**action_move logs:**
- Same as copy, plus both panels refreshed

**action_delete logs:**
- File path being deleted
- Whether it's a directory or file
- Success/failure result

**action_swap_panels logs:**
- Before swap: shows remotes and paths
- After swap: shows new configuration

**action_select_remote logs:**
- Available remotes list
- Current remote
- Selected remote

**Files Changed:**
- `src/rclonecommander/main.py` (all operation methods)

### 4. Default Remote Configuration ✓

**Problem:** Left panel was set to "rclone" remote, but it should show local filesystem.

**Solution:**
- Changed config to: left=local, right=rclone
- This matches typical file manager behavior (local on left)

**Files Changed:**
- `config/app_config.ini` (lines 3-5)

### 5. Remote Listing Debug Support ✓

**Problem:** Remote selection wasn't logging what remotes were available.

**Solution:**
- Added logging to show available remotes
- Logs current remote before switch
- Logs selected remote after switch
- Helps diagnose when remote list is empty

**Files Changed:**
- `src/rclonecommander/main.py` (action_select_remote method)

## Testing Recommendations

With debug mode enabled (`debug = true` in config), test the following:

### Cursor Position
1. Navigate into a directory
2. Press Enter on ".." to go back
3. Verify cursor is on the directory you just left
4. Check log for: "Found last dir 'dirname' at row X"

### Copy/Move/Delete
1. Select a file with Space
2. Try Ctrl+C to copy to opposite panel
3. Check debug log for:
   - "action_copy: START"
   - "src_path: remote:path/file"
   - "dst_path: remote:path"
   - "result: SUCCESS or FAILED"

### Panel Swap
1. Try Ctrl+U to swap panels
2. Check log shows before/after state
3. Verify panels actually swap

### Remote Selection
1. Press Ctrl+R
2. Check log shows available remotes
3. If list is empty, check rclone.conf path

## Debug Log Patterns to Look For

Success pattern:
```
action_copy: START
action_copy: src_panel=local, dst_panel=rclone
action_copy: 1 entries selected
action_copy: Copying 'filename.txt'
  src_path: local:path/filename.txt
  dst_path: rclone:path
  result: SUCCESS
action_copy: Successfully copied 1 item(s)
action_copy: END
```

Failure pattern:
```
action_copy: START
action_copy: No active panel
```

or

```
  result: FAILED
action_copy: Aborting due to failure
```

## Known Limitations

1. Ctrl+C for copy may be unusual - consider changing if it conflicts
2. Remote selection needs rclone configured properly
3. Swap panels doesn't swap the active panel focus (intentional)

## Files Modified Summary

- `src/rclonecommander/main.py` - Major changes
- `config/app_config.ini` - Key bindings and defaults
- `CLAUDE.md` - Documentation updates
- `LATEST_FIXES.md` - This file
