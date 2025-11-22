"""Wrapper for rclone commands.

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
import subprocess
import json
import os
import logging
from typing import List, Dict, Optional, NamedTuple
from datetime import datetime

logger = logging.getLogger(__name__)


class FileEntry(NamedTuple):
    """Represents a file or directory entry."""
    name: str
    path: str
    size: int
    modified: str
    is_dir: bool
    mime_type: str = ""


def format_size(size: int, is_dir: bool = False) -> str:
    """Format file size in human-readable format."""
    if is_dir:
        return "<DIR>"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"


def run_rclone_command(rclone_path: str, config_path: Optional[str], args: List[str], extra_flags: str = "") -> subprocess.CompletedProcess:
    """Run an rclone command."""
    cmd = [rclone_path]
    if config_path:
        cmd.extend(['--config', config_path])

    # Add extra flags if provided
    if extra_flags:
        # Split by whitespace to handle multiple flags
        cmd.extend(extra_flags.split())

    cmd.extend(args)

    # Log the full command for debugging
    logger.debug("=" * 80)
    logger.debug("🚀 EXECUTING RCLONE COMMAND:")
    logger.debug(f"   {' '.join(cmd)}")
    logger.debug("=" * 80)

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Log the result
    logger.debug(f"   Return code: {result.returncode}")
    if result.stdout:
        logger.debug(f"   stdout: {result.stdout[:500]}")  # First 500 chars
    if result.stderr:
        logger.debug(f"   stderr: {result.stderr[:500]}")  # First 500 chars
    logger.debug("=" * 80)

    return result


def list_directory(rclone_path: str, config_path: Optional[str], remote: str, path: str = "", extra_flags: str = "") -> List[FileEntry]:
    """List files and directories in a remote path.

    All remotes including 'local' are now handled uniformly through rclone.
    Ensure [local] is configured in your rclone.conf as type=local.
    """

    remote_path = f"{remote}:{path}" if path else f"{remote}:"

    result = run_rclone_command(rclone_path, config_path, [
        'lsjson',
        '--no-mimetype',
        '--no-modtime',
        remote_path
    ], extra_flags)

    if result.returncode != 0:
        return []

    try:
        entries = json.loads(result.stdout)
        return [
            FileEntry(
                name=entry.get('Name', ''),
                path=entry.get('Path', ''),
                size=entry.get('Size', 0),
                modified=entry.get('ModTime', ''),
                is_dir=entry.get('IsDir', False),
                mime_type=entry.get('MimeType', '')
            )
            for entry in entries
        ]
    except json.JSONDecodeError:
        return []


def copy_file(rclone_path: str, config_path: Optional[str], source: str, dest: str, extra_flags: str = "") -> bool:
    """Copy a file or directory using rclone."""
    logger.debug(f"copy_file: source='{source}', dest='{dest}'")

    result = run_rclone_command(rclone_path, config_path, ['copy', source, dest], extra_flags)
    logger.debug(f"copy_file: rclone returncode={result.returncode}")
    if result.returncode != 0:
        logger.debug(f"copy_file: stderr={result.stderr}")
    return result.returncode == 0


def move_file(rclone_path: str, config_path: Optional[str], source: str, dest: str, extra_flags: str = "") -> bool:
    """Move a file or directory using rclone."""
    logger.debug(f"move_file: source='{source}', dest='{dest}'")

    result = run_rclone_command(rclone_path, config_path, ['move', source, dest], extra_flags)
    logger.debug(f"move_file: rclone returncode={result.returncode}")
    if result.returncode != 0:
        logger.debug(f"move_file: stderr={result.stderr}")
    return result.returncode == 0


def delete_file(rclone_path: str, config_path: Optional[str], path: str, is_dir: bool = False, extra_flags: str = "") -> bool:
    """Delete a file or directory using rclone."""
    logger.debug(f"delete_file: path='{path}', is_dir={is_dir}")

    cmd = ['purge', path] if is_dir else ['delete', path]
    result = run_rclone_command(rclone_path, config_path, cmd, extra_flags)
    logger.debug(f"delete_file: rclone returncode={result.returncode}")
    if result.returncode != 0:
        logger.debug(f"delete_file: stderr={result.stderr}")
    return result.returncode == 0


def make_directory(rclone_path: str, config_path: Optional[str], path: str, extra_flags: str = "") -> bool:
    """Create a directory."""
    result = run_rclone_command(rclone_path, config_path, ['mkdir', path], extra_flags)
    return result.returncode == 0


def get_directory_size(rclone_path: str, config_path: Optional[str], path: str, extra_flags: str = "") -> Optional[Dict]:
    """Get size information for a directory using rclone size --json."""
    logger.debug(f"get_directory_size: path='{path}'")

    result = run_rclone_command(rclone_path, config_path, ['size', '--json', path], extra_flags)
    logger.debug(f"get_directory_size: rclone returncode={result.returncode}")

    if result.returncode != 0:
        logger.debug(f"get_directory_size: stderr={result.stderr}")
        return None

    try:
        size_info = json.loads(result.stdout)
        logger.debug(f"get_directory_size: count={size_info.get('count')}, bytes={size_info.get('bytes')}")
        return size_info
    except json.JSONDecodeError as e:
        logger.debug(f"get_directory_size: JSON decode error={e}")
        return None


def cleanup_old_logs(logs_dir: str = "logs", keep_count: int = 5) -> None:
    """Clean up old rclone log files, keeping only the most recent ones.

    Args:
        logs_dir: Directory containing log files
        keep_count: Number of most recent log files to keep
    """
    try:
        if not os.path.exists(logs_dir):
            return

        # Get all .log files in the directory
        log_files = []
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(logs_dir, filename)
                # Get modification time
                mtime = os.path.getmtime(filepath)
                log_files.append((filepath, mtime))

        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x[1], reverse=True)

        # Delete all but the most recent keep_count files
        for filepath, _ in log_files[keep_count:]:
            try:
                os.remove(filepath)
                logger.debug(f"Deleted old log file: {filepath}")
            except Exception as e:
                logger.error(f"Failed to delete log file {filepath}: {e}")

    except Exception as e:
        logger.error(f"Error cleaning up log files: {e}")


def run_rclone_with_progress(
    rclone_path: str,
    config_path: Optional[str],
    args: List[str],
    extra_flags: str = "",
    stats_interval: str = "1s"
) -> tuple[subprocess.Popen, str]:
    """Run an rclone command with progress logging.

    Args:
        rclone_path: Path to rclone executable
        config_path: Path to rclone config file
        args: Command arguments
        extra_flags: Extra flags to pass to rclone
        stats_interval: Stats update interval (e.g., "1s", "500ms")

    Returns:
        Tuple of (process, log_file_path)
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Generate unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    operation = args[0] if args else "operation"
    log_filename = f"rclone_{operation}_{timestamp}.log"
    log_path = os.path.join(logs_dir, log_filename)

    cmd = [rclone_path]
    if config_path:
        cmd.extend(['--config', config_path])

    # Add extra flags if provided
    if extra_flags:
        cmd.extend(extra_flags.split())

    # Add progress-specific flags
    cmd.extend([
        '--stats', stats_interval,
        '--log-file', log_path,
        '--log-level', 'INFO',
        '--no-update-modtime'  # Prevent unnecessary updates
    ])

    cmd.extend(args)

    # Log the full command for debugging
    logger.debug("=" * 80)
    logger.debug("🚀 EXECUTING RCLONE COMMAND WITH PROGRESS:")
    logger.debug(f"   {' '.join(cmd)}")
    logger.debug(f"   Log file: {log_path}")
    logger.debug("=" * 80)

    # Start the process in the background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return process, log_path
