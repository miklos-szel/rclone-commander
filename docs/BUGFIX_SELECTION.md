# Selection Bug Fix

## Problem

When pressing Space to select a file, the wrong file was getting marked with the selection indicator (green ▶). For example:
- User presses Space on `.esp/` (directory)
- Instead, `.config/` (different directory) gets marked

## Root Cause

The bug was in the `set_entries()` method in `src/rclonecommander/main.py`.

### What Was Happening

1. **Display rows were sorted**: Directories first (alphabetically), then files (alphabetically)
2. **Internal `self.entries` array was unsorted**: Stored in the original order from filesystem
3. **Index mismatch**: When calculating `actual_index = cursor_row - offset`, the index pointed to the wrong entry in the unsorted array

### Example

Visual display order:
```
Row 0: .clother/       (display position 0)
Row 1: .claude.json    (display position 1)
Row 2: .lazyssh/       (display position 2)
Row 3: .config/        (display position 3)  <- Displayed here
```

But internal `self.entries` array:
```
Index 0: .clother/
Index 1: .claude.json
Index 2: .lazyssh/
Index 3: .config/      <- Was at index 3
Index 4: ...
```

Wait, that matches! Let me check the logs again...

Actually, the issue was more subtle. The directories were sorted when added to the display, but the original unsorted `entries` list was stored. The sorted display had:
```
Row 6: .config/    <- Visual position in sorted display
```

But `self.entries[3]` was actually `.config` in the **unsorted** array order!

## Solution

Changed `set_entries()` to store entries in the **same sorted order** as they appear in the display:

```python
# Sort directories first, then files - THIS ORDER MUST MATCH THE DISPLAY
dirs = sorted([e for e in entries if e.is_dir], key=lambda x: x.name.lower())
files = sorted([e for e in entries if not e.is_dir], key=lambda x: x.name.lower())

# Store sorted entries so indices match the display
self.entries = dirs + files
```

Now when the display shows a directory at row N, the corresponding entry is at index N in `self.entries`.

## Files Changed

- `src/rclonecommander/main.py`: Fixed `set_entries()` to store sorted entries (line 78-112)

## Result

✓ Pressing Space on a file/directory now correctly marks that item
✓ Selection indicator (green ▶) appears on the intended item
✓ Display order always shows directories first, then files (both alphabetically)
✓ Internal array order matches display order

## Additional Improvements

Added comprehensive debug logging to help diagnose similar issues:
- Logs every entry added with its row position and index
- Logs selection operations with before/after states
- Logs cursor position and offset calculations
- Can be enabled via `config/app_config.ini` or `RCLONE_DEBUG` environment variable
