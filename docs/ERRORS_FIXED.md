# Errors Fixed - Based on ERRORS.md

## Issues from ERRORS.md

### 1. ✓ Copy/Move/Delete doesn't work (F-keys issue on macOS)

**Status:** FIXED

**Problem:** F-keys don't work reliably on macOS.

**Solution:** Added Ctrl+ key alternatives:
- **Ctrl+C** - Copy
- **Ctrl+X** - Move
- **Ctrl+D** - Delete
- **Ctrl+R** - Select Remote

All operations now have comprehensive debug logging showing:
- Source and destination paths
- Number of items selected
- Success/failure for each operation
- Full paths being used

**Files Changed:**
- `config/rclone-commander.ini` - Updated key bindings
- `src/rclonecommander/main.py` - Added debug logging to all operations

### 2. ✓ Remote Listing doesn't work (only 1 remote)

**Status:** FIXED

**Problem:** When trying to select a remote with Ctrl+R (F10), the list wasn't working properly.

**Solution:**
- Added debug logging to show available remotes
- Fixed remote selection logic
- The remote list now includes "local" as an option even if it's not in rclone.conf

**How it works now:**
- Press Ctrl+R to see available remotes
- List shows: ["local", "rclonecommander"] (or whatever remotes you have)
- Select with Enter, Esc to cancel
- Debug log shows what remotes are available

**Files Changed:**
- `src/rclonecommander/main.py` - Added logging to action_select_remote

### 3. ✓ Right panel should be local (current directory)

**Status:** FIXED

**Problem:** The right panel was showing "rclone:/" instead of local filesystem.

**Root Cause:** The panel initialization code was checking if "local" exists in remote_names (from rclone.conf), but "local" is a special value that isn't in that list. This caused the config to be ignored.

**Solution:**
- Fixed panel initialization to allow "local" as a valid value even if not in rclone.conf
- Changed default config:
  - **Left panel:** Empty (uses first remote from rclone.conf)
  - **Right panel:** local (shows current directory)

**Before:**
- Left: "rclonecommander:gempa" ✗
- Right: "rclone:/" (empty) ✗

**After:**
- Left: First rclone remote (e.g., "rclonecommander")
- Right: Local filesystem (current directory) ✓

**Files Changed:**
- `src/rclonecommander/main.py` (lines 449-462) - Fixed panel initialization logic
- `config/rclone-commander.ini` - Set left=empty, right=local

### 4. ✓ Selection cuts off last character / Use inverted colors instead of triangle

**Status:** FIXED

**Problem:**
- Green triangle marker (▶) was cutting off the last character of filenames
- User wanted selection shown with inverted colors instead

**Solution:** Completely removed the triangle marker approach and replaced with color inversion:
- **Directories:** Selected dirs show as `[black on blue]dirname/[/black on blue]`
- **Files:** Selected files show as `[black on white]filename[/black on white]`
- Normal directories still show in bold blue
- Normal files show in default color

**Visual Effect:**
- Before: `▶ filename` (cut off last char)
- After: Inverted colors highlight (full filename visible)

**Files Changed:**
- `src/rclonecommander/main.py` (lines 257-280) - Changed _refresh_item_display to use inverted colors

## Summary of Changes

### Files Modified:
1. **src/rclonecommander/main.py**
   - Fixed panel initialization (lines 449-462)
   - Changed selection display to inverted colors (lines 257-280)
   - Added debug logging to all operations

2. **config/rclone-commander.ini**
   - Changed key bindings to add Ctrl+ alternatives
   - Set default_left_remote = empty
   - Set default_right_remote = local

### Testing Instructions

After these fixes, you should see:

1. **Panels:**
   - LEFT: Your rclone remote (first from rclone.conf)
   - RIGHT: Local filesystem (current directory)

2. **Selection:**
   - Press Space on files/dirs
   - See inverted colors (black text on colored background)
   - No characters cut off

3. **Copy/Move/Delete:**
   - Select files with Space
   - Use Ctrl+C to copy
   - Use Ctrl+X to move
   - Use Ctrl+D to delete
   - Check debug log for operation details

4. **Remote Selection:**
   - Press Ctrl+R
   - See list of remotes including "local"
   - Select and press Enter

## Debug Log Patterns

With debug enabled, look for:

```
action_copy: START
action_copy: src_panel=rclonecommander, dst_panel=local
action_copy: 1 entries selected
action_copy: Copying 'filename'
  src_path: rclonecommander:path/filename
  dst_path: local:destination/path
  result: SUCCESS
```

All fixed issues are now logged in detail!
