"""Configuration management for rclone commander.

Copyright (C) 2025 Miklos Mukka Szel <contact@miklos-szel.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import configparser
from typing import Dict, List, Optional, NamedTuple
from pathlib import Path


class AppConfig(NamedTuple):
    """Application configuration settings."""
    # General
    default_left_remote: str
    default_right_remote: str
    local_default_path: str
    app_title: str
    debug: bool
    extra_rclone_flags: str
    local_remote_prompted: bool
    # Display
    color_scheme: str
    show_hidden: bool
    size_format: str
    border_style: str
    active_border_color: str
    inactive_border_color: str
    # Behavior
    confirm_copy: bool
    confirm_move: bool
    confirm_delete: bool
    confirm_overwrite: bool
    follow_symlinks: bool
    auto_refresh: int
    progress_log_retention: int
    progress_stats_interval: str
    # Key bindings
    key_quit: str
    key_switch_panel: str
    key_swap_panels: str
    key_copy: str
    key_move: str
    key_make_directory: str
    key_delete: str
    key_navigate: str
    key_select_remote: str
    key_toggle_select: str
    key_refresh_panel: str
    key_show_dir_size: str
    # Status bar labels
    label_copy: str
    label_move: str
    label_delete: str
    label_remotes: str
    label_select: str
    label_switch: str
    label_quit: str


def get_rclone_path() -> str:
    """Get rclone executable path from environment or default."""
    return os.environ.get('RCLONE_PATH', 'rclone')


def get_config_path() -> str:
    """Get rclone config file path from environment or default."""
    return os.environ.get('RCLONE_CONFIG',
                         os.path.expanduser('~/.config/rclone/rclone.conf'))


def get_app_config_path() -> str:
    """Get application config file path.

    Search priority:
    1. User config: ~/.config/rclone-commander/rclone-commander.ini (highest priority)
    2. Package config: <package>/config/rclone-commander.ini (bundled default)
    3. Legacy locations: config/rclone-commander.ini, ./rclone-commander.ini (backwards compatibility)
    """
    # 1. User config directory (highest priority)
    user_config_dir = os.path.expanduser('~/.config/rclone-commander/')
    user_config = os.path.join(user_config_dir, 'rclone-commander.ini')
    if os.path.exists(user_config):
        return user_config

    # 2. Package config (bundled with installation)
    package_dir = os.path.dirname(os.path.abspath(__file__))
    package_config = os.path.join(package_dir, 'config', 'rclone-commander.ini')
    if os.path.exists(package_config):
        return package_config

    # 3. Legacy location - config/ directory (backwards compatibility)
    legacy_config_dir = os.path.join(os.getcwd(), 'config', 'rclone-commander.ini')
    if os.path.exists(legacy_config_dir):
        return legacy_config_dir

    # 4. Legacy location - current directory (backwards compatibility)
    legacy_local = os.path.join(os.getcwd(), 'rclone-commander.ini')
    if os.path.exists(legacy_local):
        return legacy_local

    # Fallback: Return package config path (will be created on first run if needed)
    return package_config


def load_app_config() -> AppConfig:
    """Load application configuration from rclone-commander.ini."""
    config_path = get_app_config_path()

    # Default values
    defaults = {
        # General
        'default_left_remote': '',
        'default_right_remote': 'local',
        'local_default_path': '',  # Empty means home directory
        'app_title': 'Rclone Commander',
        'debug': 'false',
        'extra_rclone_flags': '',
        'local_remote_prompted': 'false',
        # Display
        'color_scheme': 'dark',
        'show_hidden': 'true',
        'size_format': 'auto',
        'border_style': 'solid',
        'active_border_color': 'accent',
        'inactive_border_color': 'primary',
        # Behavior
        'confirm_copy': 'true',
        'confirm_move': 'true',
        'confirm_delete': 'true',
        'confirm_overwrite': 'true',
        'follow_symlinks': 'false',
        'auto_refresh': '0',
        'progress_log_retention': '5',
        'progress_stats_interval': '1s',
        # Key bindings
        'quit': 'q',
        'switch_panel': 'tab',
        'swap_panels': 'ctrl+u',
        'copy': 'f5',
        'move': 'f6',
        'make_directory': 'f7',
        'delete': 'f8,delete',
        'navigate': 'enter',
        'select_remote': 'f10',
        'toggle_select': 'space,insert',
        'refresh_panel': 'ctrl+r',
        'show_dir_size': 'ctrl+i',
        # Status bar labels
        'copy_label': 'Copy',
        'move_label': 'Move',
        'delete_label': 'Delete',
        'remotes_label': 'Remotes',
        'select_label': 'Select',
        'switch_label': 'Switch',
        'quit_label': 'Quit',
    }

    if os.path.exists(config_path):
        parser = configparser.ConfigParser()
        parser.read(config_path)

        return AppConfig(
            # General
            default_left_remote=parser.get('General', 'default_left_remote', fallback=defaults['default_left_remote']),
            default_right_remote=parser.get('General', 'default_right_remote', fallback=defaults['default_right_remote']),
            local_default_path=parser.get('General', 'local_default_path', fallback=defaults['local_default_path']),
            app_title=parser.get('General', 'app_title', fallback=defaults['app_title']),
            debug=parser.getboolean('General', 'debug', fallback=defaults['debug'] == 'true'),
            extra_rclone_flags=parser.get('General', 'extra_rclone_flags', fallback=defaults['extra_rclone_flags']),
            local_remote_prompted=parser.getboolean('General', 'local_remote_prompted', fallback=defaults['local_remote_prompted'] == 'true'),
            # Display
            color_scheme=parser.get('Display', 'color_scheme', fallback=defaults['color_scheme']),
            show_hidden=parser.getboolean('Display', 'show_hidden', fallback=defaults['show_hidden'] == 'true'),
            size_format=parser.get('Display', 'size_format', fallback=defaults['size_format']),
            border_style=parser.get('Display', 'border_style', fallback=defaults['border_style']),
            active_border_color=parser.get('Display', 'active_border_color', fallback=defaults['active_border_color']),
            inactive_border_color=parser.get('Display', 'inactive_border_color', fallback=defaults['inactive_border_color']),
            # Behavior
            confirm_copy=parser.getboolean('Behavior', 'confirm_copy', fallback=defaults['confirm_copy'] == 'true'),
            confirm_move=parser.getboolean('Behavior', 'confirm_move', fallback=defaults['confirm_move'] == 'true'),
            confirm_delete=parser.getboolean('Behavior', 'confirm_delete', fallback=defaults['confirm_delete'] == 'true'),
            confirm_overwrite=parser.getboolean('Behavior', 'confirm_overwrite', fallback=defaults['confirm_overwrite'] == 'true'),
            follow_symlinks=parser.getboolean('Behavior', 'follow_symlinks', fallback=defaults['follow_symlinks'] == 'true'),
            auto_refresh=parser.getint('Behavior', 'auto_refresh', fallback=int(defaults['auto_refresh'])),
            progress_log_retention=parser.getint('Behavior', 'progress_log_retention', fallback=int(defaults['progress_log_retention'])),
            progress_stats_interval=parser.get('Behavior', 'progress_stats_interval', fallback=defaults['progress_stats_interval']),
            # Key bindings
            key_quit=parser.get('KeyBindings', 'quit', fallback=defaults['quit']),
            key_switch_panel=parser.get('KeyBindings', 'switch_panel', fallback=defaults['switch_panel']),
            key_swap_panels=parser.get('KeyBindings', 'swap_panels', fallback=defaults['swap_panels']),
            key_copy=parser.get('KeyBindings', 'copy', fallback=defaults['copy']),
            key_move=parser.get('KeyBindings', 'move', fallback=defaults['move']),
            key_make_directory=parser.get('KeyBindings', 'make_directory', fallback=defaults['make_directory']),
            key_delete=parser.get('KeyBindings', 'delete', fallback=defaults['delete']),
            key_navigate=parser.get('KeyBindings', 'navigate', fallback=defaults['navigate']),
            key_select_remote=parser.get('KeyBindings', 'select_remote', fallback=defaults['select_remote']),
            key_toggle_select=parser.get('KeyBindings', 'toggle_select', fallback=defaults['toggle_select']),
            key_refresh_panel=parser.get('KeyBindings', 'refresh_panel', fallback=defaults['refresh_panel']),
            key_show_dir_size=parser.get('KeyBindings', 'show_dir_size', fallback=defaults['show_dir_size']),
            # Status bar labels
            label_copy=parser.get('StatusBar', 'copy_label', fallback=defaults['copy_label']),
            label_move=parser.get('StatusBar', 'move_label', fallback=defaults['move_label']),
            label_delete=parser.get('StatusBar', 'delete_label', fallback=defaults['delete_label']),
            label_remotes=parser.get('StatusBar', 'remotes_label', fallback=defaults['remotes_label']),
            label_select=parser.get('StatusBar', 'select_label', fallback=defaults['select_label']),
            label_switch=parser.get('StatusBar', 'switch_label', fallback=defaults['switch_label']),
            label_quit=parser.get('StatusBar', 'quit_label', fallback=defaults['quit_label']),
        )
    else:
        # Return defaults if config doesn't exist
        return AppConfig(
            # General
            default_left_remote=defaults['default_left_remote'],
            default_right_remote=defaults['default_right_remote'],
            local_default_path=defaults['local_default_path'],
            app_title=defaults['app_title'],
            debug=defaults['debug'] == 'true',
            extra_rclone_flags=defaults['extra_rclone_flags'],
            local_remote_prompted=defaults['local_remote_prompted'] == 'true',
            # Display
            color_scheme=defaults['color_scheme'],
            show_hidden=defaults['show_hidden'] == 'true',
            size_format=defaults['size_format'],
            border_style=defaults['border_style'],
            active_border_color=defaults['active_border_color'],
            inactive_border_color=defaults['inactive_border_color'],
            # Behavior
            confirm_copy=defaults['confirm_copy'] == 'true',
            confirm_move=defaults['confirm_move'] == 'true',
            confirm_delete=defaults['confirm_delete'] == 'true',
            confirm_overwrite=defaults['confirm_overwrite'] == 'true',
            follow_symlinks=defaults['follow_symlinks'] == 'true',
            auto_refresh=int(defaults['auto_refresh']),
            progress_log_retention=int(defaults['progress_log_retention']),
            progress_stats_interval=defaults['progress_stats_interval'],
            # Key bindings
            key_quit=defaults['quit'],
            key_switch_panel=defaults['switch_panel'],
            key_swap_panels=defaults['swap_panels'],
            key_copy=defaults['copy'],
            key_move=defaults['move'],
            key_make_directory=defaults['make_directory'],
            key_delete=defaults['delete'],
            key_navigate=defaults['navigate'],
            key_select_remote=defaults['select_remote'],
            key_toggle_select=defaults['toggle_select'],
            key_refresh_panel=defaults['refresh_panel'],
            key_show_dir_size=defaults['show_dir_size'],
            # Status bar labels
            label_copy=defaults['copy_label'],
            label_move=defaults['move_label'],
            label_delete=defaults['delete_label'],
            label_remotes=defaults['remotes_label'],
            label_select=defaults['select_label'],
            label_switch=defaults['switch_label'],
            label_quit=defaults['quit_label'],
        )


def load_remotes(config_path: str) -> Dict[str, Dict[str, str]]:
    """Load remotes from rclone configuration file."""
    if not os.path.exists(config_path):
        return {}

    parser = configparser.ConfigParser()
    parser.read(config_path)

    remotes = {}
    for section in parser.sections():
        remotes[section] = dict(parser[section])

    return remotes


def get_remote_names(remotes: Dict[str, Dict[str, str]]) -> List[str]:
    """Get list of configured remote names."""
    return list(remotes.keys())


def get_remote_info(remotes: Dict[str, Dict[str, str]], remote: str) -> Optional[Dict[str, str]]:
    """Get configuration for a specific remote."""
    return remotes.get(remote)


def has_local_remote(config_path: str) -> bool:
    """Check if [local] remote exists in rclone configuration."""
    if not os.path.exists(config_path):
        return False

    parser = configparser.ConfigParser()
    parser.read(config_path)
    return parser.has_section('local')


def add_local_remote(config_path: str) -> bool:
    """Add [local] section to rclone.conf.

    Returns True if successfully added, False if already exists or error.
    Creates the config file and parent directory if they don't exist.
    """
    try:
        # Create parent directory if it doesn't exist
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        parser = configparser.ConfigParser()

        # Read existing config if it exists
        if os.path.exists(config_path):
            parser.read(config_path)

        # Check if [local] already exists
        if parser.has_section('local'):
            return False

        # Add [local] section
        parser.add_section('local')
        parser.set('local', 'type', 'local')

        # Write back to file
        with open(config_path, 'w') as f:
            parser.write(f)

        return True
    except Exception as e:
        # Log error but don't crash
        print(f"Error adding [local] remote: {e}")
        return False


def get_user_app_config_path() -> str:
    """Get the user's app config path (for writing settings).

    Returns the user config path (~/.config/rclone-commander/rclone-commander.ini).
    This is the preferred location for writing user preferences.
    """
    user_config_dir = os.path.expanduser('~/.config/rclone-commander/')
    return os.path.join(user_config_dir, 'rclone-commander.ini')


def mark_local_remote_prompted() -> bool:
    """Mark that we've prompted the user about [local] remote.

    Writes the flag to user's app config file.
    Returns True if successful, False otherwise.
    """
    try:
        user_config_path = get_user_app_config_path()
        user_config_dir = os.path.dirname(user_config_path)

        # Create user config directory if it doesn't exist
        if not os.path.exists(user_config_dir):
            os.makedirs(user_config_dir, exist_ok=True)

        # If user config doesn't exist, copy from package config or create new
        if not os.path.exists(user_config_path):
            # Try to copy from current config
            current_config = get_app_config_path()
            if os.path.exists(current_config):
                import shutil
                shutil.copy(current_config, user_config_path)

        # Load and update the config
        parser = configparser.ConfigParser()
        parser.read(user_config_path)

        # Ensure [General] section exists
        if not parser.has_section('General'):
            parser.add_section('General')

        # Set the flag
        parser.set('General', 'local_remote_prompted', 'true')

        # Write back
        with open(user_config_path, 'w') as f:
            parser.write(f)

        return True
    except Exception as e:
        print(f"Error marking local remote as prompted: {e}")
        return False
