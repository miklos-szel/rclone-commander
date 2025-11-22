# Rclone Commander Usage Guide

## Navigation

### Arrow Keys
- **Up/Down Arrows**: Move cursor between files and directories
- **Tab**: Switch between left and right panels
- **Ctrl+U**: Swap the contents of left and right panels

### Directory Navigation
- **Enter**: Navigate into a directory or open a file
  - When on a directory: Enter that directory
  - When on "..": Go to parent directory (one level up)
  - The ".." entry appears at the top when you're in a subdirectory

### File Selection
- **Space** or **Insert**: Toggle selection of current item
  - Selected items are marked with a green arrow (▶)
  - After toggling, cursor moves to next item
  - Multiple files can be selected for batch operations

## File Operations

### Copy (F5)
- Copies selected file(s) from active panel to the other panel
- Multiple selected files will all be copied

### Move (F6)
- Moves selected file(s) from active panel to the other panel
- Multiple selected files will all be moved

### Delete (F8 or Delete key)
- Deletes selected file(s) from active panel
- Multiple selected files will all be deleted

### Remote Selection (F10)
- Opens a modal dialog to select a different remote
- Use arrow keys to navigate remotes
- Press Enter to select a remote
- Press Esc or Q to cancel

## Panel Display

### File List
- Directories are shown in **bold blue** with a trailing slash (/)
- Files are shown in normal text with their size in parentheses
- The current remote and path are shown in the panel border (e.g., "local:/Users/username")

### Active Panel
- The active panel has a colored border (accent color)
- All file operations affect the active panel
- Switch panels with Tab

## Configuration

All settings are configurable via `config/app_config.ini`:
- Default remotes for left and right panels
- Key bindings
- Display options (colors, borders, etc.)
- Behavior options (confirmations, auto-refresh, etc.)

## Environment Variables

- `RCLONE_CONFIG`: Path to your rclone configuration file
- `RCLONE_PATH`: Path to the rclone binary (defaults to system rclone)

## Quick Reference

| Key | Action |
|-----|--------|
| ↑↓ | Navigate files |
| Enter | Open directory / Go to parent (..) |
| Tab | Switch panels |
| Ctrl+U | Swap panels |
| Space/Insert | Select/Unselect file |
| F5 | Copy |
| F6 | Move |
| F8 | Delete |
| F10 | Select remote |
| Q | Quit |
