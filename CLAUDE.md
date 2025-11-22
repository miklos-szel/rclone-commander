# rclone-commander TUI

A dual-pane TUI file manager for rclone.

## Requirements

- Support reading from rclone.conf (option to choose default remote)
- **Local filesystem access via rclone**: Add `[local]` remote to rclone.conf
  ```ini
  [local]
  type = local
  ```
- Copy, move, delete, make directory with function key commands (F5/F6/F7/F8)
- Directory navigation with arrows and Enter key
- Configurable rclone location
- For testing: `export RCLONE_CONFIG=/Users/p/Projects/rclonecommander/rclone.conf`
- Color support in terminal
- Multi-file select with Space or Insert for batch operations
- Non-OOP Python code (functional style preferred)
- Mouse support for navigation
- Progress bars for file operations

## Implementation

- Python with Textual library
- Functional programming style (minimal OOP)
- Multi-select support with visual indicators (inverted colors)
- Dual-pane interface with focus tracking
- Arrow key navigation (up/down cursor movement)
- Left/Right arrows for fast scrolling (10 rows at a time)
- Enter key or mouse click to open directories
- ".." entry at top for parent directory navigation
- Space/Insert keys to toggle file selection
- Progress modals for copy/move/delete operations
- All operations use rclone uniformly (including local filesystem)

## Navigation Features

- **Up/Down arrows**: Move cursor one item at a time
- **Left/Right arrows**: Fast scroll (page up/down 10 items)
- **Enter key**: Navigate into directories, or go to parent with ".."
  - When exiting a directory, cursor automatically positions on that directory
- **Mouse clicks**: Click on any row to navigate (same as Enter)
- **Space/Insert**: Toggle selection with inverted colors, auto-advance cursor
- **Tab**: Switch between left and right panels
- **".." entry**: Always shown at top when not at root directory
- **Multi-select**: Select multiple files before Copy/Move/Delete operations

## Selection Visual Indicator

Selected files and directories are shown with **inverted colors**:
- **Selected directories**: Black text on blue background
- **Selected files**: Black text on white background
- No marker characters that could cut off filenames
- Full filename always visible

## Key Bindings

### Function Keys (Primary)
- **F5**: Copy selected files to opposite panel (with progress bar)
- **F6**: Move selected files to opposite panel (with progress bar)
- **F7**: Make new directory (cursor positions on created directory)
- **F8**: Delete selected files (with progress bar)
- **F10**: Select remote (change current panel's remote)

### Navigation Keys
- **Up/Down**: Move cursor one item
- **Left/Right**: Fast scroll (10 items at a time, like Page Up/Down)
- **Enter**: Open directory or navigate to parent (..)
- **Tab**: Switch between left/right panels
- **Space/Insert**: Toggle file selection
- **Q**: Quit application

### Panel Operations
- **Ctrl+U**: Swap panels (exchange left and right panel contents)

## File Operations

All file operations show progress modals with:
- **Global progress**: Overall transfer progress (bytes transferred, speed, ETA)
- **Parallel file transfers**: Shows up to 6 files being transferred simultaneously
  - Each file shows: filename, progress bar, size, speed, and ETA
  - Automatically scrolls if more than 6 files
- **File counter**: Tracks completed vs total files
- **Cancel button**: ESC to cancel operation

### Parallel Transfer Support
- Supports multiple files being transferred simultaneously (configurable with `--transfers` flag)
- Progress updates in real-time from rclone's stats output
- Compact display optimized for 6 parallel transfers

### Copy (F5)
- Copies selected files (or current file if none selected) from active panel to opposite panel
- For directories: Creates directory at destination and copies contents
- For files: Copies to destination directory
- Shows progress for each file

### Move (F6)
- Moves selected files from active panel to opposite panel
- Same behavior as copy, but removes source files after transfer
- Shows progress for each file

### Make Directory (F7)
- Creates new directory in active panel's current location
- Opens input dialog for directory name
- After creation, cursor automatically positions on the new directory
- Uses rclone mkdir command

### Delete (F8)
- Deletes selected files/directories in active panel
- Uses rclone delete for files, rclone purge for directories
- Shows progress for each file

### Partial File Cleanup
When a copy/move operation is cancelled:
- **For files**: Searches for `.partial` files in the destination directory
- **For directories**: Recursively searches all subdirectories for `.partial` files
- Prompts to delete partial files to clean up incomplete transfers
- Partial files follow pattern: `filename.ext.RANDOM.partial`

## Panel Management

### Focus Tracking
- Active panel is automatically tracked when you click or interact with it
- Active panel has bright border (accent color)
- Inactive panel has dim border (primary color)
- File operations always work on the active panel

### Remote Selection (F10)
- Shows modal with list of available remotes (including "local")
- Select remote to switch current panel to that remote
- Cursor marker shows currently selected remote

### Panel Swap (Ctrl+U)
- Exchanges the contents of left and right panels
- Swaps remotes, paths, and all panel state
- Useful for reversing the copy/move direction

## Display Order

Files are always displayed in the following order:
1. ".." (parent directory) - shown at top when not at root
2. Directories - sorted alphabetically (A-Z)
3. Files - sorted alphabetically (A-Z)

This is a standard ordering used by dual-pane file managers.

## Configuration

### App Configuration File
Location: `config/app_config.ini`

Key sections:
- **[General]**: Default remotes, app title, debug mode, rclone flags
  - `default_left_remote`: Left panel remote (empty = local)
  - `default_right_remote`: Right panel remote (empty = first from rclone.conf)
  - `extra_rclone_flags`: Additional flags for all rclone operations (e.g., `--transfers 6`)
- **[KeyBindings]**: Customizable key mappings (F5/F6/F7/F8, etc.)
- **[Display]**: Color scheme, border style, size format
- **[Behavior]**: Confirmations, auto-refresh, symlink handling

### Default Panel Behavior
- **Left panel**: Defaults to `local` filesystem (unless configured otherwise)
- **Right panel**: Defaults to first remote from `rclone.conf` (unless configured otherwise)

### Rclone Configuration
Location: `~/.config/rclone/rclone.conf` (or set via `RCLONE_CONFIG`)

Required for local filesystem access:
```ini
[local]
type = local
```

## Debug Mode

Debug logging can be enabled in two ways:
1. Set `debug = true` in `config/app_config.ini` under [General]
2. Set environment variable `RCLONE_DEBUG=1` (overrides config)

When enabled, detailed logs are written to `rclonecommander_debug.log`.

Debug logs include:
- All key presses and their matched actions
- Every rclone command executed with full arguments
- File operation progress and results
- Path transformations and normalizations
- Panel focus changes
- Selection state changes

## Architecture

### Unified Rclone Handling
All file operations go through rclone uniformly:
- Local filesystem accessed via rclone's `local` remote type
- No special casing for local vs remote operations
- Consistent behavior across all remote types
- All operations: `rclone lsjson`, `rclone copy`, `rclone move`, `rclone delete`, `rclone purge`, `rclone mkdir`

### Path Handling
- **Local panel initialization**: Starts at home directory with absolute path
- **Remote panels**: Start at root (empty path)
- **Navigation**: Relative paths joined with current path
- **Operations**: Full rclone paths (e.g., `local:/Users/p/file.txt`, `remote:path/to/file`)

### Selection Management
- Selections tracked per panel in a Set
- Selections cleared when navigating to different directory
- Inverted colors indicate selected state
- If no selections, operations work on current cursor item

### Focus Management
- Each FileListView reports focus changes via `on_focus()` event
- App tracks active panel automatically
- No manual focus management needed
- Copy/move operations respect active panel

## Testing

```bash
# Set rclone config location
export RCLONE_CONFIG=/path/to/rclone.conf

# Enable debug logging
export RCLONE_DEBUG=1

# Run the app
python3 rclone-commander.py

# Or run as module
source venv/bin/activate
python3 -m src.rclone_commander.main
```

## User Interface

- **Dual-pane layout**: Left and right file panels
- **Footer**: Shows available key bindings and shortcuts
- **Progress modals**: Pop-up windows for file operations with real-time progress
- **Confirmation dialogs**: For destructive operations (delete, overwrite)
- **Input dialogs**: For creating directories and other inputs

## Common Workflows

### Copy files from remote to local
1. Left panel: Navigate to remote directory
2. Right panel: Navigate to local destination
3. Select files with Space in left panel
4. Press F5 to copy
5. Watch progress bar
6. Files appear in right panel

### Create and populate new directory
1. Navigate to desired location
2. Press F7, type directory name
3. Cursor lands on new directory
4. Press Enter to open it
5. Switch to other panel (Tab)
6. Select files to copy
7. Press F5 to copy into new directory

### Fast navigation through long lists
1. Press Right arrow to jump down 10 items
2. Press Left arrow to jump up 10 items
3. Much faster than holding down arrow key

### Multi-file operations
1. Press Space on first file (inverted colors)
2. Press Space on more files
3. Press F5/F6/F8 for batch operation
4. Progress bar shows each file being processed

## Known Limitations

- F-key availability depends on terminal configuration (macOS Terminal may need function key mode)
- Some terminals may capture Ctrl key combinations

## Features Implemented

✅ Dual-pane file browser with rclone integration
✅ Local and remote filesystem support (unified through rclone)
✅ Directory navigation with cursor memory
✅ Multi-file selection with visual feedback (inverted colors)
✅ Copy/Move/Delete with real-time progress tracking
✅ **Parallel file transfers** (up to 6 files simultaneously)
✅ **Global and per-file progress** display (bytes, speed, ETA)
✅ Make directory with auto-cursor positioning
✅ Remote switching (F10)
✅ Panel swapping (Ctrl+U)
✅ Focus tracking with visual indicators
✅ Mouse support for navigation
✅ Fast scrolling (left/right arrows = 10 items)
✅ Debug logging with full command visibility
✅ Configuration file support (INI format)
✅ **Partial file cleanup** after cancelled operations
✅ **Right-aligned file sizes** for easy reading
✅ Automatic panel refresh after operations
✅ Footer with key binding hints
