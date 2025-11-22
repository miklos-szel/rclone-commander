"""Parser for rclone progress log output."""
import re
import logging
from typing import Optional, NamedTuple

logger = logging.getLogger(__name__)


class FileProgress(NamedTuple):
    """Progress data for a single file being transferred."""
    filename: str = ""
    percentage: int = 0
    size: str = ""
    speed: str = ""
    eta: str = ""


class ProgressData(NamedTuple):
    """Structured progress data extracted from rclone logs."""
    # Overall progress
    transferred_str: str = ""  # e.g., "15.031 MiB"
    total_str: str = ""  # e.g., "233.367 MiB"
    overall_percentage: int = 0  # e.g., 6
    overall_speed: str = ""  # e.g., "817.606 KiB/s"
    overall_eta: str = ""  # e.g., "4m33s"
    files_transferred: int = 0  # e.g., 0
    total_files: int = 0  # e.g., 1

    # Files currently being transferred (can be multiple)
    transferring_files: tuple = ()  # tuple of FileProgress instances


# Regex patterns for parsing rclone output
# Example: "Transferred:          15.031 MiB / 233.367 MiB, 6%, 817.606 KiB/s, ETA 4m33s"
TRANSFERRED_PATTERN = re.compile(
    r'Transferred:\s+([\d.]+\s+\w+)\s+/\s+([\d.]+\s+\w+),\s+(\d+)%,\s+([\d.]+\s+\w+/s),\s+ETA\s+(.+)'
)

# Example: "Transferred:            0 / 1, 0%"
FILES_PATTERN = re.compile(
    r'Transferred:\s+(\d+)\s+/\s+(\d+),\s+\d+%'
)

# Example: " * filename.mp4:  6% /233.367Mi, 817.618Ki/s, 4m33s"
TRANSFERRING_PATTERN = re.compile(
    r'\*\s+(.+?):\s+(\d+)%\s+/([\d.]+\w+),\s+([\d.]+\s*\w+/s),\s+(.+)'
)


def parse_progress_line(line: str, current_data: Optional[ProgressData] = None) -> Optional[ProgressData]:
    """Parse a single line from rclone log and update progress data.

    Args:
        line: A line from the rclone log file
        current_data: The current ProgressData to update (or None to create new)

    Returns:
        Updated ProgressData if the line contained progress info, None otherwise
    """
    if current_data is None:
        current_data = ProgressData()

    line = line.strip()

    # Try to match the transferred bytes line
    match = TRANSFERRED_PATTERN.search(line)
    if match:
        return current_data._replace(
            transferred_str=match.group(1),
            total_str=match.group(2),
            overall_percentage=int(match.group(3)),
            overall_speed=match.group(4),
            overall_eta=match.group(5)
        )

    # Try to match the files transferred line
    match = FILES_PATTERN.search(line)
    if match:
        return current_data._replace(
            files_transferred=int(match.group(1)),
            total_files=int(match.group(2))
        )

    # Try to match the current file transfer line
    match = TRANSFERRING_PATTERN.search(line)
    if match:
        return current_data._replace(
            current_file=match.group(1).strip(),
            file_percentage=int(match.group(2)),
            file_size=match.group(3),
            file_speed=match.group(4),
            file_eta=match.group(5).strip()
        )

    # Line didn't match any pattern
    return None


def parse_log_content(content: str) -> Optional[ProgressData]:
    """Parse multiple lines from rclone log and extract the latest progress.

    Args:
        content: Content from rclone log file (can be multiple lines)

    Returns:
        ProgressData with the latest progress information, or None if no progress found
    """
    progress = ProgressData()
    found_any = False
    transferring_files = []

    # We need to process the content in chunks to handle the "Transferring:" section
    # which lists multiple files at once
    lines = content.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Try to match the transferred bytes line
        match = TRANSFERRED_PATTERN.search(line)
        if match:
            progress = progress._replace(
                transferred_str=match.group(1),
                total_str=match.group(2),
                overall_percentage=int(match.group(3)),
                overall_speed=match.group(4),
                overall_eta=match.group(5)
            )
            found_any = True
            i += 1
            continue

        # Try to match the files transferred line
        match = FILES_PATTERN.search(line)
        if match:
            progress = progress._replace(
                files_transferred=int(match.group(1)),
                total_files=int(match.group(2))
            )
            found_any = True
            i += 1
            continue

        # Check for "Transferring:" section header
        if line.startswith("Transferring:") or "Transferring:" in line:
            # Clear previous transferring files when we see a new section
            transferring_files = []
            i += 1
            # Continue to parse file progress lines that follow
            continue

        # Try to match individual file transfer lines
        match = TRANSFERRING_PATTERN.search(line)
        if match:
            file_progress = FileProgress(
                filename=match.group(1).strip(),
                percentage=int(match.group(2)),
                size=match.group(3),
                speed=match.group(4),
                eta=match.group(5).strip()
            )
            # Add to list (avoid duplicates by filename)
            # Remove any existing entry with same filename first
            transferring_files = [f for f in transferring_files if f.filename != file_progress.filename]
            transferring_files.append(file_progress)
            found_any = True
            i += 1
            continue

        i += 1

    # Update progress with the collected transferring files
    if transferring_files:
        progress = progress._replace(transferring_files=tuple(transferring_files))

    return progress if found_any else None


def tail_log_file(log_path: str, last_position: int = 0) -> tuple[str, int]:
    """Read new content from a log file since last position.

    Args:
        log_path: Path to the log file
        last_position: Last read position in the file

    Returns:
        Tuple of (new_content, new_position)
    """
    try:
        with open(log_path, 'r') as f:
            f.seek(last_position)
            new_content = f.read()
            new_position = f.tell()
            return new_content, new_position
    except FileNotFoundError:
        # Log file doesn't exist yet
        return "", last_position
    except Exception as e:
        logger.error(f"Error reading log file {log_path}: {e}")
        return "", last_position
