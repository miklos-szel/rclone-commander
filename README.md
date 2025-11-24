# rclone-commander

A dual-pane TUI (Text User Interface) file manager for rclone.

## Features

- **Dual-pane interface** - Navigate two locations simultaneously
- **Parallel file transfers** - Transfer up to 6 files at once with individual progress bars
- **Real-time progress** - Global and per-file transfer statistics (bytes, speed, ETA)
- **Multi-select support** - Select multiple files/directories with Space or Insert
- **File operations** - Copy (F5), Move (F6), Delete (F8) with live progress tracking
- **Arrow key navigation** - Navigate directories with cursor memory
- **Smart features** - Auto-refresh, partial file cleanup, right-aligned file sizes
- **Color terminal support** - Rich colored interface with visual selection feedback
- **Fully configurable** - All settings, key bindings, and colors customizable
- **Remote support** - Works with all rclone remotes
- **Local filesystem support** - Unified local/remote access via rclone

## Project Structure

```
rclone-commander/
├── config/
│   └── rclone-commander.ini # Application configuration
├── src/
│   └── rclone_commander/
│       ├── __init__.py
│       ├── main.py          # Main application
│       ├── config.py        # Configuration management
│       ├── rclone_wrapper.py # Rclone command wrappers
│       └── progress_parser.py # Progress parsing
├── docs/                     # Documentation
├── rclone-commander.py      # Entry point
├── run.sh                   # Convenience wrapper script
├── requirements.txt         # Python dependencies
├── rclone.conf              # Rclone remotes configuration
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rclone-commander
```

2. Ensure rclone is installed:
```bash
which rclone
```

3. The `run.sh` script will automatically set up a virtual environment and install dependencies.

## Usage

### Quick Start

```bash
# Run with default remote from config
./run.sh

# Run and set specific remote
./run.sh rclonecommander

# With custom rclone config
export RCLONE_CONFIG=/path/to/rclone.conf
./run.sh
```

### Manual Run

```bash
# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the application
python3 rclone-commander.py

# Or run as module
python3 -m src.rclone_commander.main
```

## Configuration

rclone-commander includes a default configuration file bundled with the package. You can customize settings by creating your own config file.

**Config file locations** (in priority order):
1. `~/.config/rclone-commander/rclone-commander.ini` - User-specific config (recommended for customization)
2. `<package>/config/rclone-commander.ini` - Default config bundled with installation
3. `config/rclone-commander.ini` - Legacy location (backwards compatibility)

To customize settings, copy the default config to your user directory:
```bash
mkdir -p ~/.config/rclone-commander/
cp <package-location>/config/rclone-commander.ini ~/.config/rclone-commander/
# Edit with your preferred editor
nano ~/.config/rclone-commander/rclone-commander.ini
```

### General Settings

```ini
[General]
# Default remote for left panel (leave empty for local)
default_left_remote =
# Default remote for right panel (leave empty for first from rclone.conf)
default_right_remote =
# Default starting path for local remote (leave empty for home directory, use / for root)
local_default_path =
# Application title
app_title = Rclone Commander
# Extra rclone flags for all operations
extra_rclone_flags = --transfers 6 --checkers 6
```

**Default Panel Behavior:**
- **Left panel**: Defaults to `local` filesystem
- **Right panel**: Defaults to first remote from `rclone.conf`
- **Local starting path**:
  - Empty (`local_default_path =`) - Starts at user's home directory
  - Root (`local_default_path = /`) - Starts at filesystem root, allows browsing entire system
  - Custom (`local_default_path = /path/to/dir`) - Starts at specified directory

### Display Settings

```ini
[Display]
# Color scheme: dark, light, or auto
color_scheme = dark
# Show hidden files
show_hidden = true
# File size format: auto, bytes, KB, MB, GB
size_format = auto
# Border styles
border_style = solid
active_border_color = accent
inactive_border_color = primary
```

### Behavior Settings

```ini
[Behavior]
# Confirmation prompts
confirm_delete = true
confirm_overwrite = true
# Follow symbolic links
follow_symlinks = false
# Auto-refresh interval in seconds (0 to disable)
auto_refresh = 0
```

### Custom Key Bindings

```ini
[KeyBindings]
quit = q
switch_panel = tab
swap_panels = ctrl+u
copy = f5
move = f6
make_directory = f7
delete = f8,delete
navigate = enter
select_remote = f10
toggle_select = space,insert
refresh_panel = ctrl+r
show_dir_size = ctrl+i
```

## Navigation & Key Bindings

### Navigation Features

| Feature | Key/Action | Description |
|---------|-----------|-------------|
| **Cursor Movement** | Up/Down arrows | Move cursor one item at a time |
| **Fast Scroll** | Left/Right arrows | Scroll 1/2 screen at a time |
| **Open Directory** | Enter or Mouse click | Navigate into directories or open files |
| **Parent Directory** | Enter on ".." | Go to parent directory (cursor positions on previous directory) |
| **Panel Switch** | Tab | Switch focus between left and right panels |
| **File Selection** | Space or Insert | Toggle selection with inverted colors, auto-advance cursor |
| **Multi-Select** | Space/Insert (multiple) | Select multiple files before Copy/Move/Delete operations |
| **Root Navigation** | Enter on "/" | Local filesystem can navigate from root to browse entire system |
| **".." Entry** | Automatic | Always shown at top when not at root (hidden at "/" for local) |

### Selection Visual Indicators

| Item Type | Visual Style | Description |
|-----------|-------------|-------------|
| **Selected Directory** | Black text on blue background | Inverted colors for visibility |
| **Selected File** | Black text on white background | Inverted colors for visibility |
| **Filename Display** | Full filename visible | No marker characters that cut off filenames |
| **Auto-Clear** | After copy/move | Selections automatically cleared after successful operations |

### File Size Display

| Property | Value | Description |
|----------|-------|-------------|
| **Column Width** | 15 characters | Fixed width, right-aligned |
| **Content Alignment** | Left-aligned | File sizes displayed left-aligned within column |
| **Position** | Right edge of pane | Always visible and consistently positioned |
| **Format** | Human-readable | B, KB, MB, GB, TB, PB |

### Key Bindings

#### Function Keys (Primary Operations)

| Key | Operation | Description |
|-----|-----------|-------------|
| **F5** | Copy | Copy selected files to opposite panel (with progress bar) |
| **F6** | Move | Move selected files to opposite panel (with progress bar) |
| **F7** | Make Directory | Create new directory (cursor positions on created directory) |
| **F8** | Delete | Delete selected files (with progress bar) |
| **F10** | Select Remote | Show remote selection dialog (change current panel's remote) |
| **ESC** | Cancel | Cancel ongoing operation |

#### Navigation Keys

| Key | Action | Description |
|-----|--------|-------------|
| **Up/Down** | Cursor movement | Move cursor one item |
| **Left/Right** | Fast scroll | Scroll 1/2 screen at a time |
| **Enter** | Navigate | Open directory or navigate to parent (..) |
| **Tab** | Switch panel | Switch between left/right panels |
| **Space/Insert** | Toggle selection | Toggle file selection with inverted colors |
| **Mouse Click** | Navigate | Click on any row to navigate (same as Enter) |

#### Panel Operations

| Key | Operation | Description |
|-----|-----------|-------------|
| **Ctrl+U** | Swap Panels | Exchange left and right panel contents |
| **Ctrl+R** | Refresh Panel | Refresh current panel listing |
| **Ctrl+I** | Directory Size | Show size information for selected directory |

#### Application Control

| Key | Action | Description |
|-----|--------|-------------|
| **Q** | Quit | Exit application |

> **Note:** All key bindings are customizable in the `[KeyBindings]` section of `rclone-commander.ini`

## Rclone Configuration

The application reads from your rclone configuration file. By default, it looks for:
- `~/.config/rclone/rclone.conf`

You can override this with the `RCLONE_CONFIG` environment variable.

### Example rclone.conf:

```ini
[myremote]
type = sftp
host = example.com
user = username
port = 22

[backblaze]
type = b2
account = your_account_id
key = your_application_key

#local is necessary if you want to browse your local dirs
[local]
type = local

```

## Multi-Select Operations

1. Navigate to a file/directory
2. Press **Space** or **Insert** to select (inverted colors appear)
   - **Directories**: Black text on blue background
   - **Files**: Black text on white background
3. Navigate to more items and select them (cursor auto-advances)
4. Press **F5** (copy), **F6** (move), or **F8** (delete)
5. All selected items will be processed with real-time progress

If no items are selected, operations work on the currently highlighted item.

## Remote Selection

Press **F10** to open the remote selection dialog:
- Shows all available remotes from your rclone.conf
- Includes "local" for browsing local filesystem
- Centered modal dialog
- Navigate with arrow keys, press Enter to select
- Press Esc or Q to cancel

## Local Filesystem

The "local" remote uses rclone's `local` backend for unified operation handling. This provides:
- Consistent behavior across local and remote operations
- Same progress tracking for all transfers
- Unified path handling and error reporting
- Full filesystem access - can navigate from root (/) to browse entire system
- Configurable starting directory (home, root, or custom path)

Configure in `~/.config/rclone/rclone.conf`:
```ini
[local]
type = local
```

By default, the local remote starts at your home directory. To start at the filesystem root (/) or a custom directory, set `local_default_path` in `config/rclone-commander.ini`.

## Environment Variables

- `RCLONE_CONFIG` - Path to rclone configuration file
- `RCLONE_PATH` - Path to rclone executable (default: `rclone`)

## Development

### Code Style

The project uses functional programming style with minimal OOP. Textual framework requires some class usage for UI widgets, but business logic is implemented functionally.

## Troubleshooting

### Empty Panels

If both panels show empty:
1. Check that your rclone.conf has valid remotes configured
2. Ensure the remote name in config/rclone-commander.ini matches your rclone.conf
3. Try switching to "local" remote with F10

### Permission Errors

If you see permission errors when listing directories:
- Check file/directory permissions
- Ensure rclone remote credentials are correct

### Module Import Errors

If you see import errors:
- Use the `run.sh` script which handles paths correctly
- Ensure all files are in the correct directory structure

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Credits

Built with:
- [Textual](https://github.com/Textualize/textual) - Modern TUI framework
- [rclone](https://rclone.org/) - Cloud storage sync tool
