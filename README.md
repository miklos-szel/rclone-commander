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
│   └── app_config.ini       # Application configuration
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

All configuration is stored in `config/app_config.ini`. Copy and modify this file to customize your experience.

### General Settings

```ini
[General]
# Default remote for left panel (leave empty for local)
default_left_remote =
# Default remote for right panel (leave empty for first from rclone.conf)
default_right_remote =
# Application title
app_title = Rclone Commander
# Extra rclone flags for all operations
extra_rclone_flags = --transfers 6 --checkers 6
```

**Default Panel Behavior:**
- **Left panel**: Defaults to `local` filesystem
- **Right panel**: Defaults to first remote from `rclone.conf`

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

## Keyboard Shortcuts

Default key bindings (customizable in config):

### Navigation
- **↑/↓ Arrow Keys** - Move cursor one item at a time
- **←/→ Arrow Keys** - Fast scroll (10 items at a time)
- **Enter** - Open directory or go to parent (..)
- **Tab** - Switch between left and right panel
- **Space/Insert** - Toggle file/directory selection
- **Mouse Click** - Navigate to clicked item

### File Operations
- **F5** - Copy selected items to other panel (with progress)
- **F6** - Move selected items to other panel (with progress)
- **F7** - Create new directory
- **F8/Delete** - Delete selected items (with progress)
- **F10** - Show available remotes and switch
- **ESC** - Cancel ongoing operation

### Panel Operations
- **Ctrl+U** - Swap panels (exchange left/right contents)
- **Ctrl+R** - Refresh current panel
- **Ctrl+I** - Show directory size

### Application
- **Q** - Quit application

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

Configure in `~/.config/rclone/rclone.conf`:
```ini
[local]
type = local
```

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
2. Ensure the remote name in config/app_config.ini matches your rclone.conf
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

MIT License - see LICENSE file for details

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
