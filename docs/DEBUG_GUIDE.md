# Debug Mode Guide

## Enabling Debug Mode

There are two ways to enable debug mode:

### Method 1: Config File (Persistent)

Edit `config/app_config.ini` and set:

```ini
[General]
debug = true
```

### Method 2: Environment Variable (Temporary Override)

Set the `RCLONE_DEBUG` environment variable (this overrides the config file):

```bash
export RCLONE_DEBUG=1
export RCLONE_CONFIG=/Users/p/Projects/rclonecommander/rclone.conf
python3 rclonecommander.py
```

Or run in one line:

```bash
RCLONE_DEBUG=1 RCLONE_CONFIG=/Users/p/Projects/rclonecommander/rclone.conf python3 rclonecommander.py
```

**Note:** The environment variable takes priority over the config file setting.

## Debug Log File

When debug mode is enabled, all debug information is written to:
- **File**: `rclonecommander_debug.log` (in the current directory)
- **Format**: Timestamped entries with module, level, and message

## What Gets Logged

### File List Operations
- **set_entries()**: When directories are loaded
  - Number of entries
  - Current path
  - Each row added with its position
  - Whether ".." was added

### Selection Operations
- **action_toggle_select()**: When Space/Insert is pressed
  - Current cursor row
  - Cursor movement

- **toggle_selection()**: The actual selection logic
  - Cursor position
  - Current path
  - Number of entries
  - Offset calculation
  - Actual index calculation
  - Selected items before/after
  - Entry name being toggled

- **_refresh_all_items()**: When the display is refreshed
  - Offset value
  - Each row being refreshed
  - Selection status for each entry

- **_refresh_item_display()**: Individual row updates
  - Row index
  - Entry name
  - Whether marker is shown

## Example Log Output

```
2025-11-21 10:30:15 - __main__ - INFO - ================================
2025-11-21 10:30:15 - __main__ - INFO - RcloneCommander DEBUG MODE ENABLED
2025-11-21 10:30:15 - __main__ - INFO - ================================
2025-11-21 10:30:16 - __main__ - DEBUG - set_entries: Loading 25 entries
2025-11-21 10:30:16 - __main__ - DEBUG - set_entries: current_path='/home/user'
2025-11-21 10:30:16 - __main__ - DEBUG - set_entries: Added '..' row at position 0
2025-11-21 10:30:16 - __main__ - DEBUG - set_entries: Added file '.bashrc' at row 1
...
2025-11-21 10:30:20 - __main__ - DEBUG - ============================================================
2025-11-21 10:30:20 - __main__ - DEBUG - toggle_selection: START
2025-11-21 10:30:20 - __main__ - DEBUG -   cursor_row: 5
2025-11-21 10:30:20 - __main__ - DEBUG -   current_path: '/home/user'
2025-11-21 10:30:20 - __main__ - DEBUG -   num entries: 25
2025-11-21 10:30:20 - __main__ - DEBUG -   selected_items before: set()
2025-11-21 10:30:20 - __main__ - DEBUG -   offset: 1
2025-11-21 10:30:20 - __main__ - DEBUG -   actual_index: 4
2025-11-21 10:30:20 - __main__ - DEBUG -   entry at index 4: '.wget-hsts'
2025-11-21 10:30:20 - __main__ - DEBUG -   ADDING selection: '.wget-hsts'
2025-11-21 10:30:20 - __main__ - DEBUG -   selected_items after: {'.wget-hsts'}
2025-11-21 10:30:20 - __main__ - DEBUG -   Calling _refresh_all_items()
2025-11-21 10:30:20 - __main__ - DEBUG - toggle_selection: END
2025-11-21 10:30:20 - __main__ - DEBUG - ============================================================
```

## Testing Steps

1. Enable debug mode
2. Run the application
3. Navigate to a directory with files
4. Try selecting files with Space/Insert
5. Exit the application
6. Review `rclonecommander_debug.log`

## Disabling Debug Mode

Simply don't set the `RCLONE_DEBUG` variable, or set it to 0:

```bash
unset RCLONE_DEBUG
# or
export RCLONE_DEBUG=0
```

## Analyzing Issues

When reporting issues, include:
1. The exact steps you took
2. The relevant section of `rclonecommander_debug.log`
3. What you expected vs what happened
