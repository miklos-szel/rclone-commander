# rclone-commander TUI

A dual-pane TUI file manager for rclone.

**Version:** 0.1.2
**License:** GPLv3
**Copyright:** (C) 2025 Miklos Mukka Szel <contact@miklos-szel.com>

## Requirements and features

- Support reading from rclone.conf (option to choose default remote)
- **Local filesystem access via rclone**: Add `[local]` remote to rclone.conf
  ```ini
  [local]
  type = local
  ```
- Copy, move, delete, make directory with function key commands (F5/F6/F7/F8)
- Directory navigation with arrows and Enter key
- Configurable rclone location
- For testing: `export RCLONE_CONFIG=/home/test/rclone.conf`
- Color support in terminal
- Multi-file select with Space or Insert for batch operations
- Mouse support for navigation
- Progress bars for file operations

## Navigation Features

- **Up/Down arrows**: Move cursor one item at a time
- **Left/Right arrows**: Fast scroll (1/2 screen at a time)
- **Enter key**: Navigate into directories, or go to parent with ".."
  - When exiting a directory, cursor automatically positions on that directory
- **Mouse clicks**: Click on any row to navigate (same as Enter)
- **Space/Insert**: Toggle selection with inverted colors, auto-advance cursor
- **Tab**: Switch between left and right panels
- **".." entry**: Always shown at top when not at root directory (for local: when not at "/")
- **Multi-select**: Select multiple files before Copy/Move/Delete operations
- **Root navigation**: Local filesystem can navigate from root "/" to browse entire system

## Selection Visual Indicator

Selected files and directories are shown with **inverted colors**:
- **Selected directories**: Black text on blue background
- **Selected files**: Black text on white background
- No marker characters that could cut off filenames
- Full filename always visible
- **Selections automatically cleared after successful copy/move operations**

## File Size Display

- **Right-aligned column**: 15-character fixed width
- **Left-aligned content**: File sizes displayed left-aligned within the column
- **Always visible**: Positioned consistently at the right edge of each pane
- **Format**: Human-readable sizes (B, KB, MB, GB, TB, PB)

## Key Bindings

### Function Keys (Primary)
- **F5**: Copy selected files to opposite panel (with progress bar)
- **F6**: Move selected files to opposite panel (with progress bar)
- **F7**: Make new directory (cursor positions on created directory)
- **F8**: Delete selected files (with progress bar)
- **F10**: Select remote (change current panel's remote)

### Navigation Keys
- **Up/Down**: Move cursor one item
- **Left/Right**: Fast scroll (1/2 screen at a time)
- **Enter**: Open directory or navigate to parent (..)
- **Tab**: Switch between left/right panels
- **Space/Insert**: Toggle file selection
- **Q**: Quit application

### Panel Operations
- **Ctrl+U**: Swap panels (exchange left and right panel contents)

## File Operations

### Parallel Transfer Support
- Supports multiple files being transferred simultaneously (configurable with `--transfers` flag)
- Progress updates in real-time from rclone's stats output
- Compact display optimized for 6 parallel transfers


## Configuration

### App Configuration File
**Bundled Location:** `src/rclone_commander/config/rclone-commander.ini` (ships with package)
**User Override:** `~/.config/rclone-commander/rclone-commander.ini` (highest priority)

**Config Search Priority:**
1. User config: `~/.config/rclone-commander/rclone-commander.ini` (recommended for customization)
2. Package config: `<package>/config/rclone-commander.ini` (bundled default)


Required for local filesystem access:
```ini
[local]
type = local
```


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
✅ Fast scrolling (left/right arrows = 1/2 screen)
✅ Debug logging with full command visibility
✅ Configuration file support (INI format)
✅ **Partial file cleanup** after cancelled operations
✅ **File sizes displayed** in 15-char right column, left-aligned
✅ Automatic panel refresh after operations
✅ Footer with key binding hints
✅ **Selections cleared after successful copy/move**
✅ **Full filesystem browsing from root** (/) for local remote
✅ **Configurable local starting path** (home, root, or custom)
✅ **Config bundled with package** (no manual setup needed)
✅ **User config override** via ~/.config/rclone-commander/
✅ **GPLv3 licensed** with proper headers in all source files
✅ **Build automation** with Makefile and venv support

## Recent Changes (v0.1.2)

### Version 0.1.2
- Add Makefile for build automation with venv support
- Enhance .gitignore with comprehensive build artifact coverage
- All build commands use isolated virtual environment

### Version 0.1.1
- Restructure config to be bundled with package
- Config search priority: user config → package config → legacy
- Change license from MIT to GPLv3
- Add GPLv3 headers to all source files
- Add configurable `local_default_path` option
- Clear selections after successful copy/move operations
- Improve file size column (15-char width, left-aligned)
- Enable full filesystem browsing from root (/) for local remote
- Proper root directory handling (hide ".." at "/")
- Update all offset calculations for root navigation
- Config ships with pip install (no manual setup needed)
