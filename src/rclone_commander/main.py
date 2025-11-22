#!/usr/bin/env python3
"""rclone-commander - A dual-pane TUI file manager for rclone."""
import os
import logging
import threading
import time
import asyncio
from typing import Optional, List, Dict, Set

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container, Grid, Center
from textual.widgets import Header, Footer, Static, ListView, ListItem, Label, Button, DataTable, ProgressBar, Input
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.worker import Worker, WorkerState
from rich.text import Text

from . import config
from . import rclone_wrapper
from . import progress_parser

# Logger placeholder - will be configured after loading config
logger = logging.getLogger(__name__)

def setup_debug_logging(enabled: bool) -> None:
    """Setup debug logging based on config or environment variable."""
    # Environment variable overrides config file
    debug_env = os.environ.get('RCLONE_DEBUG', '').lower() in ('1', 'true', 'yes')
    debug_enabled = debug_env or enabled

    if debug_enabled:
        logging.basicConfig(
            filename='rclone-cmd_debug.log',
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True  # Reconfigure if already configured
        )
        logger.setLevel(logging.DEBUG)
        logger.info("=" * 80)
        logger.info("rclone-cmd DEBUG MODE ENABLED")
        logger.info(f"  Enabled by: {'environment variable' if debug_env else 'config file'}")
        logger.info("=" * 80)
    else:
        logger.addHandler(logging.NullHandler())
        logger.setLevel(logging.WARNING)


class FileListView(DataTable):
    """A data table for displaying files and directories."""

    BORDER_TITLE = "Files"
    current_path = reactive("")
    remote_name = reactive("")

    BINDINGS = [
        Binding("enter", "select_cursor", "Open", show=False),
        Binding("space,insert", "toggle_select", "Select", show=False),
        Binding("shift+up", "toggle_select_up", "Select Up", show=False),
        Binding("shift+down", "toggle_select_down", "Select Down", show=False),
        Binding("left", "page_up", "Page Up", show=False),
        Binding("right", "page_down", "Page Down", show=False),
    ]

    def __init__(self, remote: str = "", rclone_path: str = "", config_path: str = "", extra_flags: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote_name = remote
        # For local remote, start at home directory with absolute path
        # This ensures rclone interprets paths correctly
        if remote.lower() == "local":
            import os
            self.current_path = os.path.expanduser("~")
            logger.debug(f"FileListView.__init__: local remote, starting at '{self.current_path}'")
        else:
            self.current_path = ""
        self.entries: List[rclone_wrapper.FileEntry] = []
        self.selected_items: Set[str] = set()
        self._rclone_path = rclone_path
        self._config_path = config_path
        self._extra_flags = extra_flags
        self._needs_initial_load = True
        self.show_header = False
        self.cursor_type = "row"
        self._last_dir_entered = ""  # Track last directory we entered
        # Add columns in __init__ so they're ready before mount
        # Name column takes most of the space, Size column gets fixed width
        self.add_column("Name", width=None)
        self.add_column("Size", width=15)

    def on_mount(self) -> None:
        """Load initial directory listing when mounted."""
        if self._needs_initial_load and self._rclone_path:
            self._needs_initial_load = False
            # Load data immediately in on_mount
            entries = rclone_wrapper.list_directory(
                self._rclone_path,
                self._config_path,
                self.remote_name,
                self.current_path,
                self._extra_flags
            )
            self.set_entries(entries)

    def on_focus(self) -> None:
        """Handle focus event - notify parent app which panel is active."""
        logger.debug(f"FileListView.on_focus: {self.remote_name} panel got focus")
        # Find the parent FilePanel and then the parent RcloneCommander app
        app = self.app
        if isinstance(app, RcloneCommander):
            parent_panel = self.parent
            if parent_panel == app.left_panel:
                logger.debug(f"FileListView.on_focus: Setting active_panel to LEFT")
                app.active_panel = app.left_panel
            elif parent_panel == app.right_panel:
                logger.debug(f"FileListView.on_focus: Setting active_panel to RIGHT")
                app.active_panel = app.right_panel

    def watch_current_path(self, path: str) -> None:
        """React to path changes."""
        self.border_title = f"{self.remote_name}:{path}" if path else f"{self.remote_name}:/"

    def set_entries(self, entries: List[rclone_wrapper.FileEntry]) -> None:
        """Update the file list with new entries."""
        logger.debug(f"set_entries: Loading {len(entries)} entries")
        logger.debug(f"set_entries: current_path='{self.current_path}'")
        logger.debug(f"set_entries: _last_dir_entered='{self._last_dir_entered}'")

        # Sort directories first, then files - THIS ORDER MUST MATCH THE DISPLAY
        dirs = sorted([e for e in entries if e.is_dir], key=lambda x: x.name.lower())
        files = sorted([e for e in entries if not e.is_dir], key=lambda x: x.name.lower())

        # Store sorted entries so indices match the display
        self.entries = dirs + files
        logger.debug(f"set_entries: Stored {len(self.entries)} sorted entries (dirs={len(dirs)}, files={len(files)})")

        self.selected_items.clear()

        # Clear existing rows
        self.clear()

        # Add parent directory if not at root
        offset = 0
        if self.current_path:
            self.add_row("[cyan]..[/cyan]", "")
            logger.debug("set_entries: Added '..' row at position 0")
            offset = 1

        # Find the row for the last directory we came from
        target_row = 0
        if self._last_dir_entered:
            for i, entry in enumerate(self.entries):
                if entry.name == self._last_dir_entered:
                    target_row = i + offset
                    logger.debug(f"set_entries: Found last dir '{self._last_dir_entered}' at row {target_row}")
                    break
            self._last_dir_entered = ""  # Clear after use

        row_num = offset
        for i, entry in enumerate(self.entries):
            if entry.is_dir:
                name_text = f"[bold blue]{entry.name}/[/bold blue]"
                self.add_row(name_text, "")
                logger.debug(f"set_entries: Added dir '{entry.name}' at row {row_num} (index {i})")
            else:
                size = rclone_wrapper.format_size(entry.size, entry.is_dir)
                name_text = entry.name
                # Right-align the size column
                size_text = Text(size, style="dim", justify="right")
                self.add_row(name_text, size_text)
                logger.debug(f"set_entries: Added file '{entry.name}' at row {row_num} (index {i})")
            row_num += 1

        # Position cursor on target row
        if target_row > 0 and target_row < self.row_count:
            self.move_cursor(row=target_row)
            logger.debug(f"set_entries: Moved cursor to row {target_row}")

    def action_select_cursor(self) -> None:
        """Handle Enter key - navigate into directory or open file."""
        self.post_message(self.RowSelected(self, self.cursor_row, self.cursor_row))

    def action_toggle_select(self) -> None:
        """Handle Space/Insert key - toggle selection and move down."""
        logger.debug(f"action_toggle_select: TRIGGERED at cursor_row={self.cursor_row}")
        self.toggle_selection()
        # Move to next item
        if self.cursor_row >= 0 and self.cursor_row < self.row_count - 1:
            logger.debug(f"action_toggle_select: Moving cursor down from {self.cursor_row}")
            self.action_cursor_down()
            logger.debug(f"action_toggle_select: Cursor now at {self.cursor_row}")

    def action_toggle_select_up(self) -> None:
        """Handle Shift+Up key - toggle selection and move up."""
        logger.debug(f"action_toggle_select_up: TRIGGERED at cursor_row={self.cursor_row}")
        self.toggle_selection()
        # Move to previous item
        if self.cursor_row > 0:
            logger.debug(f"action_toggle_select_up: Moving cursor up from {self.cursor_row}")
            self.action_cursor_up()
            logger.debug(f"action_toggle_select_up: Cursor now at {self.cursor_row}")

    def action_toggle_select_down(self) -> None:
        """Handle Shift+Down key - toggle selection and move down."""
        logger.debug(f"action_toggle_select_down: TRIGGERED at cursor_row={self.cursor_row}")
        self.toggle_selection()
        # Move to next item
        if self.cursor_row >= 0 and self.cursor_row < self.row_count - 1:
            logger.debug(f"action_toggle_select_down: Moving cursor down from {self.cursor_row}")
            self.action_cursor_down()
            logger.debug(f"action_toggle_select_down: Cursor now at {self.cursor_row}")

    def action_page_up(self) -> None:
        """Handle Left arrow - scroll up 1/2 screen."""
        # Move up half screen (or to top)
        page_size = max(1, self.size.height // 2)
        new_row = max(0, self.cursor_row - page_size)
        self.move_cursor(row=new_row)
        logger.debug(f"action_page_up: Moved from row {self.cursor_row + page_size} to {new_row} (page_size={page_size})")

    def action_page_down(self) -> None:
        """Handle Right arrow - scroll down 1/2 screen."""
        # Move down half screen (or to bottom)
        page_size = max(1, self.size.height // 2)
        new_row = min(self.row_count - 1, self.cursor_row + page_size)
        self.move_cursor(row=new_row)
        logger.debug(f"action_page_down: Moved from row {self.cursor_row - page_size} to {new_row} (page_size={page_size})")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection (Enter key or mouse click on row)."""
        # Prevent the event from bubbling to prevent double-handling
        event.stop()

        cursor_row = event.cursor_row
        if cursor_row < 0:
            return

        # Handle ".." (parent directory)
        if self.current_path and cursor_row == 0:
            # Remember the directory name we're leaving
            dir_parts = self.current_path.rstrip('/').split('/')
            if dir_parts:
                self._last_dir_entered = dir_parts[-1]
                logger.debug(f"on_row_selected: Going up, will position on '{self._last_dir_entered}'")

            self.current_path = navigate_up(self.current_path)
            entries = rclone_wrapper.list_directory(
                self._rclone_path,
                self._config_path,
                self.remote_name,
                self.current_path,
                self._extra_flags
            )
            self.set_entries(entries)
            return

        # Navigate into directory
        offset = 1 if self.current_path else 0
        actual_index = cursor_row - offset

        if 0 <= actual_index < len(self.entries):
            entry = self.entries[actual_index]
            if entry.is_dir:
                logger.debug(f"on_row_selected: Entering directory '{entry.name}'")
                new_path = os.path.join(self.current_path, entry.name)
                self.current_path = new_path
                entries = rclone_wrapper.list_directory(
                    self._rclone_path,
                    self._config_path,
                    self.remote_name,
                    self.current_path,
                    self._extra_flags
                )
                self.set_entries(entries)

    def toggle_selection(self) -> None:
        """Toggle selection of current item."""
        logger.debug("=" * 60)
        logger.debug("toggle_selection: START")
        logger.debug(f"  cursor_row: {self.cursor_row}")
        logger.debug(f"  current_path: '{self.current_path}'")
        logger.debug(f"  num entries: {len(self.entries)}")
        logger.debug(f"  selected_items before: {self.selected_items}")

        if not self.entries or self.cursor_row < 0:
            logger.debug("  ABORT: No entries or invalid cursor")
            return

        # Don't allow selection on ".." row
        offset = 1 if self.current_path else 0
        logger.debug(f"  offset: {offset}")

        if self.current_path and self.cursor_row == 0:
            logger.debug("  ABORT: Cursor on '..' row")
            return

        actual_index = self.cursor_row - offset
        logger.debug(f"  actual_index: {actual_index}")

        if actual_index < 0 or actual_index >= len(self.entries):
            logger.debug(f"  ABORT: Index {actual_index} out of bounds [0, {len(self.entries)})")
            return

        entry = self.entries[actual_index]
        logger.debug(f"  entry at index {actual_index}: '{entry.name}'")

        if entry.name in self.selected_items:
            logger.debug(f"  REMOVING selection: '{entry.name}'")
            self.selected_items.remove(entry.name)
        else:
            logger.debug(f"  ADDING selection: '{entry.name}'")
            self.selected_items.add(entry.name)

        logger.debug(f"  selected_items after: {self.selected_items}")

        # Refresh the entire table to ensure markers are in sync
        logger.debug("  Calling _refresh_all_items()")
        self._refresh_all_items()
        logger.debug("toggle_selection: END")
        logger.debug("=" * 60)

    def _refresh_all_items(self) -> None:
        """Refresh all items to update selection markers."""
        offset = 1 if self.current_path else 0
        logger.debug(f"_refresh_all_items: offset={offset}, entries={len(self.entries)}")

        for i, entry in enumerate(self.entries):
            row_index = i + offset
            logger.debug(f"  Refreshing row {row_index}: '{entry.name}' (selected={entry.name in self.selected_items})")
            self._refresh_item_display(row_index, entry)

    def _refresh_item_display(self, row_index: int, entry: rclone_wrapper.FileEntry) -> None:
        """Refresh the display of a single item."""
        is_selected = entry.name in self.selected_items

        # Use inverted colors for selected items instead of a marker
        if entry.is_dir:
            if is_selected:
                name = f"[black on blue]{entry.name}/[/black on blue]"
            else:
                name = f"[bold blue]{entry.name}/[/bold blue]"
            size = ""
        else:
            size_str = rclone_wrapper.format_size(entry.size, entry.is_dir)
            if is_selected:
                name = f"[black on white]{entry.name}[/black on white]"
            else:
                name = entry.name
            # Right-align the size column
            size = Text(size_str, style="dim", justify="right")

        logger.debug(f"_refresh_item_display: row={row_index}, name='{entry.name}', selected={'YES' if is_selected else 'NO'}")

        # Update the row
        self.update_cell_at((row_index, 0), name)
        self.update_cell_at((row_index, 1), size)

    def get_selected_entries(self) -> List[rclone_wrapper.FileEntry]:
        """Get all selected entries, or current entry if none selected."""
        if self.selected_items:
            return [e for e in self.entries if e.name in self.selected_items]

        # If nothing selected, return current entry
        if not self.entries or self.cursor_row < 0:
            return []

        offset = 1 if self.current_path else 0
        actual_index = self.cursor_row - offset

        if 0 <= actual_index < len(self.entries):
            return [self.entries[actual_index]]

        return []


class FilePanel(Vertical):
    """A panel containing file list and path display."""

    def __init__(self, remote: str = "", rclone_path: str = "", config_path: str = "", extra_flags: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote = remote
        self.file_list: Optional[FileListView] = None
        self._rclone_path = rclone_path
        self._config_path = config_path
        self._extra_flags = extra_flags

    def compose(self) -> ComposeResult:
        """Compose the file panel."""
        self.file_list = FileListView(
            remote=self.remote,
            rclone_path=self._rclone_path,
            config_path=self._config_path,
            extra_flags=self._extra_flags
        )
        yield self.file_list


class RemoteSelectionScreen(ModalScreen):
    """Modal screen for selecting remotes."""

    CSS = """
    RemoteSelectionScreen {
        align: center middle;
    }

    #remote-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #remote-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #remote-list {
        width: 100%;
        height: auto;
        max-height: 15;
        border: solid $primary;
        margin-bottom: 1;
    }

    #remote-instructions {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Cancel"),
        Binding("q", "dismiss", "Cancel"),
    ]

    def __init__(self, remotes: List[str], current_remote: str):
        super().__init__()
        self.remotes = ["local"] + remotes  # Add local as an option
        self.current_remote = current_remote

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        with Container(id="remote-dialog"):
            yield Static("Select Remote", id="remote-title")
            # Must yield ListView first, then populate in on_mount
            yield ListView(id="remote-list")
            yield Static("Press Enter to select, Esc to cancel", id="remote-instructions")

    def on_mount(self) -> None:
        """Populate the list after mounting."""
        remote_list = self.query_one("#remote-list", ListView)
        for remote in self.remotes:
            marker = "[green]►[/green] " if remote == self.current_remote else "  "
            remote_list.append(ListItem(Label(f"{marker}{remote}")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle remote selection."""
        index = event.list_view.index
        if index is not None and 0 <= index < len(self.remotes):
            selected_remote = self.remotes[index]
            self.dismiss(selected_remote)

    def action_dismiss(self) -> None:
        """Dismiss without selection."""
        self.dismiss(None)


class ProgressModal(ModalScreen):
    """Modal screen showing file operation progress."""

    CSS = """
    ProgressModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.3);
    }

    #progress-dialog {
        width: 90;
        height: 36;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #progress-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .progress-section-title {
        width: 100%;
        text-style: bold;
        margin-top: 0;
        margin-bottom: 0;
        height: 1;
    }

    #progress-overall-stats {
        width: 100%;
        content-align: center middle;
        margin-bottom: 0;
        color: $text-muted;
        height: 1;
    }

    #progress-counter {
        width: 100%;
        content-align: center middle;
        margin-bottom: 0;
        color: $text-muted;
        height: 1;
    }

    #file-progress-container {
        width: 100%;
        height: 18;
        margin-top: 0;
        overflow-y: auto;
    }

    .file-progress-item {
        width: 100%;
        height: auto;
        margin-bottom: 0;
        padding: 0;
    }

    .file-progress-name {
        width: 100%;
        content-align: left middle;
        color: $accent;
        height: 1;
    }

    .file-progress-bar {
        width: 100%;
        height: 1;
    }

    .file-progress-stats {
        width: 100%;
        content-align: left middle;
        color: $text-muted;
        height: 1;
    }

    ProgressBar {
        width: 100%;
        margin-bottom: 0;
    }

    #cancel-button-container {
        width: 100%;
        height: auto;
        align: center bottom;
        margin-top: 2;
    }

    #cancel-button {
        width: 20;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel_operation", "Cancel", show=True),
    ]

    def __init__(self, operation: str, total_files: int):
        super().__init__()
        self.operation = operation  # "Copying", "Moving", "Deleting"
        self.total_files = total_files
        self.current_file_num = 0
        self.current_filename = ""
        self.process = None  # Will be set by the operation
        self.stop_event = None  # Will be set by the operation
        self.cancelled = False
        self.current_dst_path = None  # Track destination for cleanup

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        with Container(id="progress-dialog"):
            yield Static(self.operation, id="progress-title")

            # Overall progress section (always shown)
            yield Static("Overall Progress", classes="progress-section-title")
            yield ProgressBar(total=100, show_eta=False, id="progress-overall-bar")
            yield Static("", id="progress-overall-stats")

            # File counter
            yield Static(f"File 0 of {self.total_files}", id="progress-counter")

            # Container for individual file progress bars (dynamic)
            yield Vertical(id="file-progress-container")

            # Cancel button
            with Container(id="cancel-button-container"):
                yield Button("Cancel (Esc)", variant="error", id="cancel-button")

    def update_progress(self, filename: str, file_num: int) -> None:
        """Update the progress display (basic mode - for backward compatibility).

        This is used when detailed rclone progress data is not yet available.
        """
        self.current_filename = filename
        self.current_file_num = file_num

        # Update file counter
        self.query_one("#progress-counter", Static).update(f"File {file_num} of {self.total_files}")

        # Don't update overall progress bar here - let rclone stats handle it
        # This prevents showing 100% when starting a single file transfer

        # Show a simple file progress in the container
        container = self.query_one("#file-progress-container", Vertical)
        container.remove_children()

        # Add a simple file name display
        file_container = Vertical(classes="file-progress-item")
        file_name = Static(f"[cyan]{filename}[/cyan]", classes="file-progress-name")

        # Mount the container first, then its children
        container.mount(file_container)
        file_container.mount(file_name)

    def update_from_progress_data(self, progress_data, file_num: int) -> None:
        """Update the progress display from parsed rclone progress data.

        Args:
            progress_data: ProgressData from progress_parser
            file_num: Current file number (1-indexed)
        """
        from . import progress_parser

        # Update overall progress bar (always shown)
        if progress_data.overall_percentage > 0:
            self.query_one("#progress-overall-bar", ProgressBar).update(progress=progress_data.overall_percentage)

        # Build overall stats string
        overall_stats_parts = []
        if progress_data.transferred_str and progress_data.total_str:
            overall_stats_parts.append(f"{progress_data.transferred_str} / {progress_data.total_str}")
        if progress_data.overall_speed:
            overall_stats_parts.append(f"Speed: {progress_data.overall_speed}")
        if progress_data.overall_eta:
            overall_stats_parts.append(f"ETA: {progress_data.overall_eta}")

        if overall_stats_parts:
            overall_stats = " | ".join(overall_stats_parts)
            self.query_one("#progress-overall-stats", Static).update(overall_stats)

        # Update file counter
        counter_text = f"File {file_num} of {self.total_files}"
        if progress_data.files_transferred > 0:
            counter_text = f"{progress_data.files_transferred} / {progress_data.total_files} files completed"
        self.query_one("#progress-counter", Static).update(counter_text)

        # Update individual file progress bars
        container = self.query_one("#file-progress-container", Vertical)

        # Clear existing widgets
        container.remove_children()

        # Add progress widgets for each transferring file
        if progress_data.transferring_files:
            for file_prog in progress_data.transferring_files:
                # Create a container for this file's progress
                file_container = Vertical(classes="file-progress-item")

                # Mount the container first
                container.mount(file_container)

                # File name
                file_name = Static(f"[cyan]{file_prog.filename}[/cyan]", classes="file-progress-name")
                file_container.mount(file_name)

                # Progress bar
                progress_bar = ProgressBar(total=100, show_eta=False, classes="file-progress-bar")
                progress_bar.update(progress=file_prog.percentage)
                file_container.mount(progress_bar)

                # Stats line
                stats_parts = []
                if file_prog.percentage > 0:
                    stats_parts.append(f"{file_prog.percentage}%")
                if file_prog.size:
                    stats_parts.append(f"Size: {file_prog.size}")
                if file_prog.speed:
                    stats_parts.append(f"Speed: {file_prog.speed}")
                if file_prog.eta:
                    stats_parts.append(f"ETA: {file_prog.eta}")

                if stats_parts:
                    stats_text = " | ".join(stats_parts)
                    stats_widget = Static(stats_text, classes="file-progress-stats")
                    file_container.mount(stats_widget)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel button press."""
        if event.button.id == "cancel-button":
            self.action_cancel_operation()

    def action_cancel_operation(self) -> None:
        """Cancel the ongoing operation."""
        logger.debug("ProgressModal: Cancel requested")
        self.cancelled = True

        # Kill the rclone process
        if self.process:
            try:
                self.process.kill()
                logger.debug("ProgressModal: Killed rclone process")
            except Exception as e:
                logger.error(f"ProgressModal: Failed to kill process: {e}")

        # Signal the monitor thread to stop
        if self.stop_event:
            self.stop_event.set()

        # Update UI
        self.query_one("#progress-title", Static).update(f"{self.operation} - CANCELLED")
        self.update_status_text("Operation cancelled by user")

    def update_status_text(self, message: str) -> None:
        """Update a status message in the modal."""
        self.query_one("#progress-overall-stats", Static).update(f"[red]{message}[/red]")


class ConfirmationModal(ModalScreen[bool]):
    """Modal screen for confirming file operations."""

    CSS = """
    ConfirmationModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.3);
    }

    #confirm-dialog {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }

    #confirm-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #confirm-message {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }

    #confirm-details {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-bottom: 1;
    }

    #confirm-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #confirm-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("n", "cancel", "No"),
        Binding("y", "confirm", "Yes"),
    ]

    def __init__(self, operation: str, num_files: int, num_dirs: int, total_size: int):
        super().__init__()
        self.operation = operation  # "Copy", "Move", "Delete"
        self.num_files = num_files
        self.num_dirs = num_dirs
        self.total_size = total_size

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        # Format the details message
        items = []
        if self.num_files > 0:
            items.append(f"{self.num_files} file{'s' if self.num_files != 1 else ''}")
        if self.num_dirs > 0:
            items.append(f"{self.num_dirs} director{'ies' if self.num_dirs != 1 else 'y'}")

        items_str = " and ".join(items)

        with Container(id="confirm-dialog"):
            yield Static(f"Confirm {self.operation}", id="confirm-title")
            yield Static(f"[bold]{self.operation} {items_str}?[/bold]", id="confirm-message")
            # Only show size if it's greater than 0
            if self.total_size > 0:
                size_str = rclone_wrapper.format_size(self.total_size)
                yield Static(f"Total size: {size_str}", id="confirm-details")
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes", variant="primary", id="yes-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "yes-button":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        """Confirm the operation."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel the operation."""
        self.dismiss(False)


class DirectorySizeModal(ModalScreen):
    """Modal screen for showing directory size information."""

    CSS = """
    DirectorySizeModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.3);
    }

    #dirsize-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }

    #dirsize-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #dirsize-name, #dirsize-files, #dirsize-size {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }

    #dirsize-instructions {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close"),
        Binding("enter", "dismiss_modal", "Close"),
    ]

    def __init__(self, dir_name: str, file_count: int, total_size: int):
        super().__init__()
        self.dir_name = dir_name
        self.file_count = file_count
        self.total_size = total_size

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        size_str = rclone_wrapper.format_size(self.total_size)

        with Container(id="dirsize-dialog"):
            yield Static("Directory Size", id="dirsize-title")
            yield Static(f"[bold]{self.dir_name}[/bold]", id="dirsize-name")
            yield Static(f"Files: {self.file_count}", id="dirsize-files")
            yield Static(f"Total Size: {size_str}", id="dirsize-size")
            yield Static("Press Enter or Esc to close", id="dirsize-instructions")

    def action_dismiss_modal(self) -> None:
        """Dismiss the modal."""
        self.dismiss()


class QuickSearchModal(ModalScreen[Optional[str]]):
    """Modal screen for quick file/directory search."""

    CSS = """
    QuickSearchModal {
        align: center top;
        background: rgba(0, 0, 0, 0.3);
    }

    #search-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
        margin-top: 2;
    }

    #search-input {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        with Container(id="search-dialog"):
            yield Input(placeholder="Search: type to filter...", id="search-input")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        self.query_one(Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes - return the search text."""
        # Notify parent with the current search term
        self.dismiss(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission."""
        self.dismiss(event.value)

    def action_cancel(self) -> None:
        """Cancel search."""
        self.dismiss(None)


class MakeDirectoryModal(ModalScreen[str]):
    """Modal screen for creating a new directory."""

    CSS = """
    MakeDirectoryModal {
        align: center middle;
    }

    #mkdir-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }

    #mkdir-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #mkdir-input {
        width: 100%;
        margin-bottom: 1;
    }

    #mkdir-instructions {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        with Container(id="mkdir-dialog"):
            yield Static("Create New Directory", id="mkdir-title")
            yield Input(placeholder="Directory name...", id="mkdir-input")
            yield Static("Press Enter to create, Esc to cancel", id="mkdir-instructions")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle directory name submission."""
        dirname = event.value.strip()
        if dirname:
            self.dismiss(dirname)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel directory creation."""
        self.dismiss(None)


def monitor_progress_log(app: App, log_path: str, progress_modal: ProgressModal, file_num: int, stop_event: threading.Event) -> None:
    """Monitor rclone log file and update progress modal in background thread.

    Args:
        app: The Textual app instance (for call_from_thread)
        log_path: Path to the rclone log file
        progress_modal: The ProgressModal to update
        file_num: Current file number (1-indexed)
        stop_event: Threading event to signal when to stop monitoring
    """
    last_position = 0
    wait_count = 0
    max_wait = 10  # Wait up to 10 seconds for log file to appear

    logger.debug(f"monitor_progress_log: Starting monitor for {log_path}")

    while not stop_event.is_set():
        try:
            # Read new content from log file
            new_content, last_position = progress_parser.tail_log_file(log_path, last_position)

            if new_content:
                # Reset wait counter if we got data
                wait_count = 0

                # Parse the progress data
                progress_data = progress_parser.parse_log_content(new_content)

                if progress_data:
                    # Update the modal from the main thread
                    app.call_from_thread(progress_modal.update_from_progress_data, progress_data, file_num)
                    app.call_from_thread(app.refresh)
            else:
                # No new content - check if we should keep waiting
                wait_count += 1
                if wait_count > max_wait and last_position == 0:
                    # Log file hasn't appeared yet after max_wait seconds
                    logger.warning(f"monitor_progress_log: Log file {log_path} not found after {max_wait}s")
                    break

            # Sleep briefly before next check
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"monitor_progress_log: Error reading log: {e}")
            time.sleep(1)  # Wait longer on error

    logger.debug(f"monitor_progress_log: Stopped monitor for {log_path}")


class RcloneCommander(App):
    """Main TUI application for rclone."""

    # Disable Textual's command palette feature
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: $surface;
    }

    FileListView {
        border: solid $primary;
        height: 100%;
        width: 1fr;
    }

    FileListView:focus {
        border: solid $accent;
    }

    Horizontal {
        height: 1fr;
    }

    FilePanel {
        width: 1fr;
        height: 100%;
    }
    """

    def __init__(self):
        super().__init__()
        self.config_path = config.get_config_path()
        self.rclone_path = config.get_rclone_path()
        self.remotes = config.load_remotes(self.config_path)
        self.app_config = config.load_app_config()

        # Setup debug logging based on config
        setup_debug_logging(self.app_config.debug)

        # NOTE: Bindings are now registered dynamically in on_mount() using bind() method
        # Setting self.BINDINGS here doesn't work properly with Textual

        # Log all configured bindings (these will be registered in on_mount)
        logger.debug("=" * 80)
        logger.debug("KEY BINDINGS CONFIGURED:")
        logger.debug(f"  Copy:   {self.app_config.key_copy} -> action_copy")
        logger.debug(f"  Move:   {self.app_config.key_move} -> action_move")
        logger.debug(f"  Delete: {self.app_config.key_delete} -> action_delete")
        logger.debug(f"  Remote: {self.app_config.key_select_remote} -> action_select_remote")
        logger.debug(f"  Switch: {self.app_config.key_switch_panel} -> action_switch_panel")
        logger.debug(f"  Swap:   {self.app_config.key_swap_panels} -> action_swap_panels")
        logger.debug(f"  Quit:   {self.app_config.key_quit} -> quit")
        logger.debug("=" * 80)

        self.left_panel: Optional[FilePanel] = None
        self.right_panel: Optional[FilePanel] = None
        self.active_panel: Optional[FilePanel] = None

        # Set default remotes from app config
        remote_names = config.get_remote_names(self.remotes)

        # Left panel: use config default, or local
        # "local" is always valid even if not in rclone.conf
        self.left_remote = self.app_config.default_left_remote if self.app_config.default_left_remote else "local"

        # Right panel: use config default, or first available remote from rclone.conf, or local
        if self.app_config.default_right_remote:
            self.right_remote = self.app_config.default_right_remote
        elif remote_names:
            self.right_remote = remote_names[0]
        else:
            self.right_remote = "local"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with Horizontal():
            self.left_panel = FilePanel(
                remote=self.left_remote,
                rclone_path=self.rclone_path,
                config_path=self.config_path,
                extra_flags=self.app_config.extra_rclone_flags,
                id="left-panel"
            )
            yield self.left_panel

            self.right_panel = FilePanel(
                remote=self.right_remote,
                rclone_path=self.rclone_path,
                config_path=self.config_path,
                extra_flags=self.app_config.extra_rclone_flags,
                id="right-panel"
            )
            yield self.right_panel

        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount."""
        self.title = self.app_config.app_title
        self.active_panel = self.left_panel

        # Register bindings dynamically using bind() method
        # This is necessary because BINDINGS as instance attr doesn't work properly
        logger.debug("=" * 80)
        logger.debug("REGISTERING DYNAMIC BINDINGS:")

        self.bind(self.app_config.key_quit, "quit", description=self.app_config.label_quit)
        logger.debug(f"  Registered: {self.app_config.key_quit} -> quit")

        self.bind(self.app_config.key_switch_panel, "switch_panel", description=self.app_config.label_switch)
        logger.debug(f"  Registered: {self.app_config.key_switch_panel} -> switch_panel")

        self.bind(self.app_config.key_swap_panels, "swap_panels", description="Swap Panels")
        logger.debug(f"  Registered: {self.app_config.key_swap_panels} -> swap_panels")

        self.bind(self.app_config.key_copy, "copy", description=self.app_config.label_copy)
        logger.debug(f"  Registered: {self.app_config.key_copy} -> copy")

        self.bind(self.app_config.key_move, "move", description=self.app_config.label_move)
        logger.debug(f"  Registered: {self.app_config.key_move} -> move")

        self.bind(self.app_config.key_make_directory, "make_directory", description="Make Dir")
        logger.debug(f"  Registered: {self.app_config.key_make_directory} -> make_directory")

        self.bind(self.app_config.key_delete, "delete", description=self.app_config.label_delete)
        logger.debug(f"  Registered: {self.app_config.key_delete} -> delete")

        self.bind(self.app_config.key_select_remote, "select_remote", description=self.app_config.label_remotes)
        logger.debug(f"  Registered: {self.app_config.key_select_remote} -> select_remote")

        self.bind(self.app_config.key_refresh_panel, "refresh_panel", description="Refresh")
        logger.debug(f"  Registered: {self.app_config.key_refresh_panel} -> refresh_panel")

        self.bind("slash", "quick_search", description="Search")
        logger.debug(f"  Registered: slash (/) -> quick_search")

        self.bind(self.app_config.key_show_dir_size, "show_dir_size", description="Dir Size")
        logger.debug(f"  Registered: {self.app_config.key_show_dir_size} -> show_dir_size")

        logger.debug("=" * 80)

        # FileListView widgets will load their own content in their on_mount
        # Just set focus to the left panel
        if self.left_panel and self.left_panel.file_list:
            self.left_panel.file_list.focus()

    def on_key(self, event) -> None:
        """Log all key presses for debugging."""
        from textual.events import Key

        logger.debug("=" * 80)
        logger.debug(f"🔑 KEY EVENT DETECTED:")
        logger.debug(f"  event.key = '{event.key}'")
        logger.debug(f"  type(event.key) = {type(event.key)}")

        if hasattr(event, 'character'):
            logger.debug(f"  event.character = '{event.character}'")
        if hasattr(event, 'is_printable'):
            logger.debug(f"  event.is_printable = {event.is_printable}")
        if hasattr(event, 'name'):
            logger.debug(f"  event.name = '{event.name}'")

        logger.debug("")
        logger.debug("📋 CONFIGURED BINDINGS:")

        # Check which action this should trigger
        bindings_map = {
            self.app_config.key_copy: "copy",
            self.app_config.key_move: "move",
            self.app_config.key_delete: "delete",
            self.app_config.key_select_remote: "select_remote",
            self.app_config.key_quit: "quit",
            self.app_config.key_switch_panel: "switch_panel",
            self.app_config.key_swap_panels: "swap_panels"
        }

        for key_binding, action_name in bindings_map.items():
            logger.debug(f"  {action_name:20s} -> {key_binding}")
            # Split on comma and strip whitespace
            binding_keys = [k.strip() for k in key_binding.split(',')]
            for binding_key in binding_keys:
                if event.key == binding_key:
                    logger.debug(f"    ✓✓✓ EXACT MATCH: '{event.key}' == '{binding_key}'")
                    logger.debug(f"    >>> Should trigger action_{action_name}()")
                else:
                    logger.debug(f"    ✗ No match: '{event.key}' != '{binding_key}'")

        logger.debug("=" * 80)

    def action_switch_panel(self) -> None:
        """Switch between left and right panels."""
        if self.active_panel == self.left_panel:
            self.active_panel = self.right_panel
            if self.right_panel and self.right_panel.file_list:
                self.right_panel.file_list.focus()
        else:
            self.active_panel = self.left_panel
            if self.left_panel and self.left_panel.file_list:
                self.left_panel.file_list.focus()

    def action_swap_panels(self) -> None:
        """Swap the contents of left and right panels."""
        logger.debug("=" * 60)
        logger.debug("action_swap_panels: START")

        if not self.left_panel or not self.right_panel:
            logger.debug("action_swap_panels: Missing left or right panel")
            return

        if not self.left_panel.file_list or not self.right_panel.file_list:
            logger.debug("action_swap_panels: Missing file_list in panels")
            return

        logger.debug(f"  Before swap:")
        logger.debug(f"    left: {self.left_panel.remote}:{self.left_panel.file_list.current_path}")
        logger.debug(f"    right: {self.right_panel.remote}:{self.right_panel.file_list.current_path}")

        # Swap remote names
        temp_remote = self.left_panel.remote
        self.left_panel.remote = self.right_panel.remote
        self.right_panel.remote = temp_remote

        # Swap file list remotes
        temp_remote_name = self.left_panel.file_list.remote_name
        self.left_panel.file_list.remote_name = self.right_panel.file_list.remote_name
        self.right_panel.file_list.remote_name = temp_remote_name

        # Swap current paths
        temp_path = self.left_panel.file_list.current_path
        self.left_panel.file_list.current_path = self.right_panel.file_list.current_path
        self.right_panel.file_list.current_path = temp_path

        logger.debug(f"  After swap:")
        logger.debug(f"    left: {self.left_panel.remote}:{self.left_panel.file_list.current_path}")
        logger.debug(f"    right: {self.right_panel.remote}:{self.right_panel.file_list.current_path}")

        # Refresh both panels
        refresh_panel(self.left_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
        refresh_panel(self.right_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)

        self.update_status("Panels swapped")
        logger.debug("action_swap_panels: END")
        logger.debug("=" * 60)

    def action_copy(self) -> None:
        """Copy selected files/directories."""
        logger.debug("=" * 80)
        logger.debug("ACTION CALLED: action_copy")
        logger.debug("=" * 80)
        logger.debug("action_copy: START")

        if not self.active_panel:
            logger.debug("action_copy: No active panel")
            return

        src_panel = self.active_panel
        dst_panel = self.right_panel if self.active_panel == self.left_panel else self.left_panel

        logger.debug(f"action_copy: src_panel={src_panel.remote}, dst_panel={dst_panel.remote if dst_panel else 'None'}")

        # Log selection state of BOTH panels for debugging
        if self.left_panel and self.left_panel.file_list:
            logger.debug(f"action_copy: LEFT panel ({self.left_panel.remote}) selections: {self.left_panel.file_list.selected_items}")
            logger.debug(f"action_copy: LEFT panel is_active: {self.active_panel == self.left_panel}")
        if self.right_panel and self.right_panel.file_list:
            logger.debug(f"action_copy: RIGHT panel ({self.right_panel.remote}) selections: {self.right_panel.file_list.selected_items}")
            logger.debug(f"action_copy: RIGHT panel is_active: {self.active_panel == self.right_panel}")

        if not dst_panel or not src_panel.file_list or not dst_panel.file_list:
            logger.debug("action_copy: Missing dst_panel or file_lists")
            return

        entries = src_panel.file_list.get_selected_entries()
        logger.debug(f"action_copy: {len(entries)} entries from ACTIVE panel")

        if not entries:
            logger.debug("action_copy: No entries to copy")
            return

        # Calculate counts and size for confirmation
        num_files = sum(1 for e in entries if not e.is_dir)
        num_dirs = sum(1 for e in entries if e.is_dir)
        total_size = sum(e.size for e in entries if not e.is_dir)

        # Show confirmation if configured
        if self.app_config.confirm_copy:
            async def handle_confirmation(confirmed: Optional[bool]) -> None:
                if not confirmed:
                    logger.debug("action_copy: User cancelled")
                    self.update_status("Copy cancelled")
                    return
                # Run the copy operation as a worker
                self.run_worker(self._do_copy_operation_async(src_panel, dst_panel, entries), exclusive=True)

            self.push_screen(
                ConfirmationModal("Copy", num_files, num_dirs, total_size),
                handle_confirmation
            )
        else:
            # Run the copy operation as a worker
            self.run_worker(self._do_copy_operation_async(src_panel, dst_panel, entries), exclusive=True)

        logger.debug("action_copy: END")
        logger.debug("=" * 60)

    def _find_partial_files_recursive(self, remote: str, dir_path: str) -> List[tuple[str, str]]:
        """Recursively find all .partial files in a directory.

        Returns:
            List of tuples (file_path, full_rclone_path) for each partial file found
        """
        partial_files = []

        try:
            entries = rclone_wrapper.list_directory(
                self.rclone_path,
                self.config_path,
                remote,
                dir_path,
                self.app_config.extra_rclone_flags
            )

            for entry in entries:
                if entry.is_dir:
                    # Recursively search subdirectories
                    subdir_path = os.path.join(dir_path, entry.name) if dir_path else entry.name
                    partial_files.extend(self._find_partial_files_recursive(remote, subdir_path))
                elif entry.name.endswith(".partial"):
                    # Found a partial file
                    file_path = os.path.join(dir_path, entry.name) if dir_path else entry.name
                    full_path = f"{remote}:{file_path}"
                    partial_files.append((entry.name, full_path))
                    logger.debug(f"_find_partial_files_recursive: Found {full_path}")
        except Exception as e:
            logger.error(f"_find_partial_files_recursive: Error scanning {remote}:{dir_path}: {e}")

        return partial_files

    async def _cleanup_partial_file(self, file_path: Optional[str], filename: str, is_directory: bool = False) -> None:
        """Ask user if they want to delete the partial file after cancellation.

        Rclone creates partial files with pattern: filename.ext.RANDOM.partial
        Example: IMG_9366.mp4.4f20d3fc.partial

        For directory copies, recursively searches for all .partial files in the destination directory.
        """
        if not file_path:
            return

        logger.debug(f"_cleanup_partial_file: Looking for partial files (is_directory={is_directory})")

        # Parse the file_path to get remote and directory
        # Format: "remote:path/to/file" or "remote:"
        parts = file_path.split(':', 1)
        if len(parts) != 2:
            logger.error(f"_cleanup_partial_file: Invalid path format: {file_path}")
            return

        remote = parts[0]
        full_path = parts[1]

        partial_files = []

        if is_directory:
            # For directory copies, recursively find all .partial files in the destination directory
            logger.debug(f"_cleanup_partial_file: Searching recursively in {remote}:{full_path}")
            partial_files = self._find_partial_files_recursive(remote, full_path)
        else:
            # For file copies, look for partial files in the same directory
            dir_path = os.path.dirname(full_path) if full_path else ""

            entries = rclone_wrapper.list_directory(
                self.rclone_path,
                self.config_path,
                remote,
                dir_path,
                self.app_config.extra_rclone_flags
            )

            # Find partial files matching pattern: filename.*.partial
            for entry in entries:
                if entry.name.startswith(filename + ".") and entry.name.endswith(".partial"):
                    file_path_full = f"{remote}:{os.path.join(dir_path, entry.name)}" if dir_path else f"{remote}:{entry.name}"
                    partial_files.append((entry.name, file_path_full))
                    logger.debug(f"_cleanup_partial_file: Found partial file: {entry.name}")

        if not partial_files:
            logger.debug(f"_cleanup_partial_file: No partial files found")
            return

        # Create a simple confirmation modal
        async def handle_cleanup(confirmed: Optional[bool]) -> None:
            if confirmed:
                deleted_count = 0
                for filename, partial_path in partial_files:
                    logger.debug(f"_cleanup_partial_file: Deleting {partial_path}")
                    success = rclone_wrapper.delete_file(
                        self.rclone_path,
                        self.config_path,
                        partial_path,
                        is_dir=False,
                        extra_flags=self.app_config.extra_rclone_flags
                    )
                    if success:
                        deleted_count += 1

                if deleted_count > 0:
                    self.update_status(f"Deleted {deleted_count} partial file(s)")
                else:
                    self.update_status(f"Failed to delete partial files")
            else:
                logger.debug("_cleanup_partial_file: User chose to keep partial file(s)")

        # Show confirmation dialog
        self.push_screen(
            ConfirmationModal("Delete Partial File", len(partial_files), 0, 0),
            handle_cleanup
        )

    async def _do_copy_operation_async(self, src_panel: FilePanel, dst_panel: FilePanel, entries: List[rclone_wrapper.FileEntry]) -> None:
        """Perform the actual copy operation with real-time progress (async version)."""
        # Show progress modal
        progress_modal = ProgressModal("Copying Files", len(entries))
        self.push_screen(progress_modal)

        # Cleanup old logs first
        rclone_wrapper.cleanup_old_logs("logs", self.app_config.progress_log_retention)

        try:
            for i, entry in enumerate(entries, 1):
                # Update basic progress
                progress_modal.update_progress(entry.name, i)

                src_path = build_path(src_panel.remote, src_panel.file_list.current_path, entry.name)
                # For directories, include the dir name in destination so it creates the dir
                # For files, just use the destination directory
                if entry.is_dir:
                    dst_path = build_path(dst_panel.remote, dst_panel.file_list.current_path, entry.name)
                else:
                    dst_path = build_path(dst_panel.remote, dst_panel.file_list.current_path, "")

                # Track destination for potential cleanup (both files and directories)
                partial_file_path = build_path(dst_panel.remote, dst_panel.file_list.current_path, entry.name)
                progress_modal.current_dst_path = partial_file_path

                logger.debug(f"_do_copy_operation: Copying '{entry.name}' ({i}/{len(entries)}) (is_dir={entry.is_dir})")
                logger.debug(f"  src_path: {src_path}")
                logger.debug(f"  dst_path: {dst_path}")

                # Start rclone with progress logging
                process, log_path = rclone_wrapper.run_rclone_with_progress(
                    self.rclone_path,
                    self.config_path,
                    ['copy', src_path, dst_path],
                    self.app_config.extra_rclone_flags,
                    self.app_config.progress_stats_interval
                )

                # Set process handle on modal so cancel button can kill it
                progress_modal.process = process

                # Start background log monitor
                stop_event = threading.Event()
                progress_modal.stop_event = stop_event
                monitor_thread = threading.Thread(
                    target=monitor_progress_log,
                    args=(self, log_path, progress_modal, i, stop_event),
                    daemon=True
                )
                monitor_thread.start()

                # Poll the process asynchronously - this allows the UI to remain responsive
                return_code = None
                while return_code is None:
                    # Check if user cancelled
                    if progress_modal.cancelled:
                        logger.debug("_do_copy_operation: Operation cancelled by user")
                        stop_event.set()
                        monitor_thread.join(timeout=2)
                        self.pop_screen()

                        # Ask user about cleaning up partial files (works for both files and directories)
                        await self._cleanup_partial_file(progress_modal.current_dst_path, entry.name, entry.is_dir)

                        # Refresh destination panel to show any files that were copied before cancellation
                        refresh_panel(dst_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)

                        self.update_status("Copy cancelled")
                        return

                    return_code = process.poll()
                    if return_code is None:
                        # Still running - sleep briefly using asyncio
                        await asyncio.sleep(0.1)

                # Stop the monitor
                stop_event.set()
                monitor_thread.join(timeout=2)

                logger.debug(f"  result: {'SUCCESS' if return_code == 0 else 'FAILED'} (code={return_code})")

                if return_code != 0:
                    self.pop_screen()  # Dismiss progress modal
                    # Refresh destination panel to show any files that were copied before failure
                    refresh_panel(dst_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
                    self.update_status(f"Failed to copy {entry.name}")
                    logger.debug("_do_copy_operation: Aborting due to failure")
                    return

            # Success - dismiss modal
            self.pop_screen()
            self.update_status(f"Copied {len(entries)} item(s)")
            logger.debug(f"_do_copy_operation: Successfully copied {len(entries)} item(s)")
            refresh_panel(dst_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
        except Exception as e:
            # Ensure modal is dismissed on error
            self.pop_screen()
            logger.error(f"_do_copy_operation: Exception: {e}")
            raise

    def action_move(self) -> None:
        """Move selected files/directories."""
        logger.debug("=" * 80)
        logger.debug("ACTION CALLED: action_move")
        logger.debug("=" * 80)
        logger.debug("action_move: START")

        if not self.active_panel:
            logger.debug("action_move: No active panel")
            return

        src_panel = self.active_panel
        dst_panel = self.right_panel if self.active_panel == self.left_panel else self.left_panel

        logger.debug(f"action_move: src_panel={src_panel.remote}, dst_panel={dst_panel.remote if dst_panel else 'None'}")

        if not dst_panel or not src_panel.file_list or not dst_panel.file_list:
            logger.debug("action_move: Missing dst_panel or file_lists")
            return

        entries = src_panel.file_list.get_selected_entries()
        logger.debug(f"action_move: {len(entries)} entries selected")

        if not entries:
            logger.debug("action_move: No entries to move")
            return

        # Calculate counts and size for confirmation
        num_files = sum(1 for e in entries if not e.is_dir)
        num_dirs = sum(1 for e in entries if e.is_dir)
        total_size = sum(e.size for e in entries if not e.is_dir)

        # Show confirmation if configured
        if self.app_config.confirm_move:
            async def handle_confirmation(confirmed: Optional[bool]) -> None:
                if not confirmed:
                    logger.debug("action_move: User cancelled")
                    self.update_status("Move cancelled")
                    return
                # Run the move operation as a worker
                self.run_worker(self._do_move_operation_async(src_panel, dst_panel, entries), exclusive=True)

            self.push_screen(
                ConfirmationModal("Move", num_files, num_dirs, total_size),
                handle_confirmation
            )
        else:
            # Run the move operation as a worker
            self.run_worker(self._do_move_operation_async(src_panel, dst_panel, entries), exclusive=True)

        logger.debug("action_move: END")
        logger.debug("=" * 60)

    async def _do_move_operation_async(self, src_panel: FilePanel, dst_panel: FilePanel, entries: List[rclone_wrapper.FileEntry]) -> None:
        """Perform the actual move operation with real-time progress (async version)."""
        # Show progress modal
        progress_modal = ProgressModal("Moving Files", len(entries))
        self.push_screen(progress_modal)

        # Cleanup old logs first
        rclone_wrapper.cleanup_old_logs("logs", self.app_config.progress_log_retention)

        try:
            for i, entry in enumerate(entries, 1):
                # Update basic progress
                progress_modal.update_progress(entry.name, i)

                src_path = build_path(src_panel.remote, src_panel.file_list.current_path, entry.name)
                # For directories, include the dir name in destination so it creates the dir
                # For files, just use the destination directory
                if entry.is_dir:
                    dst_path = build_path(dst_panel.remote, dst_panel.file_list.current_path, entry.name)
                else:
                    dst_path = build_path(dst_panel.remote, dst_panel.file_list.current_path, "")

                # Track destination for potential cleanup (both files and directories)
                partial_file_path = build_path(dst_panel.remote, dst_panel.file_list.current_path, entry.name)
                progress_modal.current_dst_path = partial_file_path

                logger.debug(f"_do_move_operation: Moving '{entry.name}' ({i}/{len(entries)}) (is_dir={entry.is_dir})")
                logger.debug(f"  src_path: {src_path}")
                logger.debug(f"  dst_path: {dst_path}")

                # Start rclone with progress logging
                process, log_path = rclone_wrapper.run_rclone_with_progress(
                    self.rclone_path,
                    self.config_path,
                    ['move', src_path, dst_path],
                    self.app_config.extra_rclone_flags,
                    self.app_config.progress_stats_interval
                )

                # Set process handle on modal so cancel button can kill it
                progress_modal.process = process

                # Start background log monitor
                stop_event = threading.Event()
                progress_modal.stop_event = stop_event
                monitor_thread = threading.Thread(
                    target=monitor_progress_log,
                    args=(self, log_path, progress_modal, i, stop_event),
                    daemon=True
                )
                monitor_thread.start()

                # Poll the process asynchronously - this allows the UI to remain responsive
                return_code = None
                while return_code is None:
                    # Check if user cancelled
                    if progress_modal.cancelled:
                        logger.debug("_do_move_operation: Operation cancelled by user")
                        stop_event.set()
                        monitor_thread.join(timeout=2)
                        self.pop_screen()

                        # Ask user about cleaning up partial files (works for both files and directories)
                        await self._cleanup_partial_file(progress_modal.current_dst_path, entry.name, entry.is_dir)

                        # Refresh both panels to show any files that were moved before cancellation
                        refresh_panel(src_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
                        refresh_panel(dst_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)

                        self.update_status("Move cancelled")
                        return

                    return_code = process.poll()
                    if return_code is None:
                        # Still running - sleep briefly using asyncio
                        await asyncio.sleep(0.1)

                # Stop the monitor
                stop_event.set()
                monitor_thread.join(timeout=2)

                logger.debug(f"  result: {'SUCCESS' if return_code == 0 else 'FAILED'} (code={return_code})")

                if return_code != 0:
                    self.pop_screen()  # Dismiss progress modal
                    # Refresh both panels to show any files that were moved before failure
                    refresh_panel(src_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
                    refresh_panel(dst_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
                    self.update_status(f"Failed to move {entry.name}")
                    logger.debug("_do_move_operation: Aborting due to failure")
                    return

            # Success - dismiss modal
            self.pop_screen()
            self.update_status(f"Moved {len(entries)} item(s)")
            logger.debug(f"_do_move_operation: Successfully moved {len(entries)} item(s)")
            refresh_panel(src_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
            refresh_panel(dst_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
        except Exception as e:
            # Ensure modal is dismissed on error
            self.pop_screen()
            logger.error(f"_do_move_operation: Exception: {e}")
            raise

    def action_delete(self) -> None:
        """Delete selected files/directories."""
        logger.debug("=" * 80)
        logger.debug("ACTION CALLED: action_delete")
        logger.debug("=" * 80)
        logger.debug("action_delete: START")

        if not self.active_panel or not self.active_panel.file_list:
            logger.debug("action_delete: No active panel or file_list")
            return

        # Log detailed selection state
        file_list = self.active_panel.file_list
        logger.debug(f"action_delete: Active panel remote='{self.active_panel.remote}'")
        logger.debug(f"action_delete: Active panel path='{file_list.current_path}'")
        logger.debug(f"action_delete: Active panel cursor_row={file_list.cursor_row}")
        logger.debug(f"action_delete: Selected items in active panel: {file_list.selected_items}")
        logger.debug(f"action_delete: Total entries in active panel: {len(file_list.entries)}")

        entries = file_list.get_selected_entries()
        logger.debug(f"action_delete: {len(entries)} entries returned by get_selected_entries()")
        if entries:
            logger.debug(f"action_delete: Entry names: {[e.name for e in entries]}")

        if not entries:
            logger.debug("action_delete: No entries to delete")
            return

        # Calculate counts and size for confirmation
        num_files = sum(1 for e in entries if not e.is_dir)
        num_dirs = sum(1 for e in entries if e.is_dir)
        total_size = sum(e.size for e in entries if not e.is_dir)

        # Show confirmation if configured
        if self.app_config.confirm_delete:
            async def handle_confirmation(confirmed: Optional[bool]) -> None:
                if not confirmed:
                    logger.debug("action_delete: User cancelled")
                    self.update_status("Delete cancelled")
                    return
                self._do_delete_operation(entries)

            self.push_screen(
                ConfirmationModal("Delete", num_files, num_dirs, total_size),
                handle_confirmation
            )
        else:
            self._do_delete_operation(entries)

        logger.debug("action_delete: END")
        logger.debug("=" * 60)

    def _do_delete_operation(self, entries: List[rclone_wrapper.FileEntry]) -> None:
        """Perform the actual delete operation."""
        # Remember cursor position before deletion
        file_list = self.active_panel.file_list
        old_cursor_row = file_list.cursor_row

        # Show progress modal
        progress_modal = ProgressModal("Deleting Files", len(entries))
        self.push_screen(progress_modal)

        try:
            for i, entry in enumerate(entries, 1):
                # Update progress display
                progress_modal.update_progress(entry.name, i)
                progress_modal.refresh()  # Force refresh of the modal
                self.refresh()  # Force UI update

                file_path = build_path(
                    self.active_panel.remote,
                    self.active_panel.file_list.current_path,
                    entry.name
                )

                logger.debug(f"_do_delete_operation: Deleting '{entry.name}' ({i}/{len(entries)}) (is_dir={entry.is_dir})")
                logger.debug(f"  file_path: {file_path}")

                success = rclone_wrapper.delete_file(self.rclone_path, self.config_path, file_path, entry.is_dir, self.app_config.extra_rclone_flags)

                logger.debug(f"  result: {'SUCCESS' if success else 'FAILED'}")

                if not success:
                    self.pop_screen()  # Dismiss progress modal
                    self.update_status(f"Failed to delete {entry.name}")
                    logger.debug("_do_delete_operation: Aborting due to failure")
                    return

            # Success - dismiss modal
            self.pop_screen()
            self.update_status(f"Deleted {len(entries)} item(s)")
            logger.debug(f"_do_delete_operation: Successfully deleted {len(entries)} item(s)")
        except Exception as e:
            # Ensure modal is dismissed on error
            self.pop_screen()
            logger.error(f"_do_delete_operation: Exception: {e}")
            raise

        # Refresh panel
        refresh_panel(self.active_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)

        # Restore cursor position (keep it on the same row, which will now show the next file)
        # Make sure we don't go past the end of the list
        if file_list.row_count > 0:
            new_cursor_row = min(old_cursor_row, file_list.row_count - 1)
            file_list.move_cursor(row=new_cursor_row)
            logger.debug(f"_do_delete_operation: Restored cursor to row {new_cursor_row}")

    def action_make_directory(self) -> None:
        """Create a new directory in the active panel."""
        logger.debug("=" * 80)
        logger.debug("ACTION CALLED: action_make_directory")
        logger.debug("=" * 80)

        if not self.active_panel or not self.active_panel.file_list:
            logger.debug("action_make_directory: No active panel")
            return

        async def handle_mkdir(dirname: Optional[str]) -> None:
            """Handle the directory name input."""
            if not dirname:
                logger.debug("action_make_directory: Cancelled")
                return

            logger.debug(f"action_make_directory: Creating directory '{dirname}'")

            # Build the full path for the new directory
            dir_path = build_path(
                self.active_panel.remote,
                self.active_panel.file_list.current_path,
                dirname
            )

            logger.debug(f"action_make_directory: Path: {dir_path}")

            success = rclone_wrapper.make_directory(self.rclone_path, self.config_path, dir_path, self.app_config.extra_rclone_flags)

            if success:
                self.update_status(f"Created directory: {dirname}")
                logger.debug("action_make_directory: SUCCESS")

                # Refresh panel to show the new directory
                refresh_panel(self.active_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)

                # Position cursor on the newly created directory
                file_list = self.active_panel.file_list
                offset = 1 if file_list.current_path else 0  # Account for ".." row

                # Find the new directory in the entries
                for i, entry in enumerate(file_list.entries):
                    if entry.name == dirname and entry.is_dir:
                        target_row = i + offset
                        file_list.move_cursor(row=target_row)
                        logger.debug(f"action_make_directory: Cursor positioned on '{dirname}' at row {target_row}")
                        break
            else:
                self.update_status(f"Failed to create directory: {dirname}")
                logger.debug("action_make_directory: FAILED")

        # Show the input dialog
        self.push_screen(MakeDirectoryModal(), handle_mkdir)

    def action_select_remote(self) -> None:
        """Show remote selection dialog."""
        logger.debug("=" * 60)
        logger.debug("action_select_remote: START")

        remote_names = config.get_remote_names(self.remotes)
        logger.debug(f"action_select_remote: Available remotes: {remote_names}")

        current_remote = self.active_panel.remote if self.active_panel else ""
        logger.debug(f"action_select_remote: Current remote: {current_remote}")

        async def handle_remote_selection(selected: Optional[str]) -> None:
            """Handle the remote selection result."""
            logger.debug(f"handle_remote_selection: Selected: {selected}")

            if selected and self.active_panel and self.active_panel.file_list:
                logger.debug(f"  Switching from '{self.active_panel.remote}' to '{selected}'")
                self.active_panel.remote = selected
                self.active_panel.file_list.remote_name = selected
                self.active_panel.file_list.current_path = ""
                refresh_panel(self.active_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
                self.update_status(f"Switched to remote: {selected}")
            else:
                logger.debug("  Selection cancelled or invalid")

        logger.debug("action_select_remote: Pushing RemoteSelectionScreen")
        self.push_screen(
            RemoteSelectionScreen(remote_names, current_remote),
            handle_remote_selection
        )
        logger.debug("action_select_remote: END")
        logger.debug("=" * 60)

    def action_refresh_panel(self) -> None:
        """Refresh the active panel."""
        logger.debug("=" * 60)
        logger.debug("action_refresh_panel: START")

        if not self.active_panel or not self.active_panel.file_list:
            logger.debug("action_refresh_panel: No active panel")
            return

        logger.debug(f"action_refresh_panel: Refreshing {self.active_panel.remote}")
        refresh_panel(self.active_panel, self.rclone_path, self.config_path, self.app_config.extra_rclone_flags)
        self.update_status("Panel refreshed")

        logger.debug("action_refresh_panel: END")
        logger.debug("=" * 60)

    def action_quick_search(self) -> None:
        """Show quick search dialog."""
        logger.debug("=" * 60)
        logger.debug("action_quick_search: START")

        if not self.active_panel or not self.active_panel.file_list:
            logger.debug("action_quick_search: No active panel")
            return

        file_list = self.active_panel.file_list

        async def handle_search(search_term: Optional[str]) -> None:
            """Handle search input."""
            if not search_term:
                logger.debug("action_quick_search: Empty search")
                return

            logger.debug(f"action_quick_search: Searching for '{search_term}'")

            # Search through entries (case-insensitive)
            search_lower = search_term.lower()
            offset = 1 if file_list.current_path else 0

            for i, entry in enumerate(file_list.entries):
                if entry.name.lower().startswith(search_lower):
                    target_row = i + offset
                    file_list.move_cursor(row=target_row)
                    logger.debug(f"action_quick_search: Found '{entry.name}' at row {target_row}")
                    self.update_status(f"Found: {entry.name}")
                    return

            # If no match found
            self.update_status(f"Not found: {search_term}")
            logger.debug("action_quick_search: No match found")

        self.push_screen(QuickSearchModal(), handle_search)
        logger.debug("action_quick_search: END")
        logger.debug("=" * 60)

    def action_show_dir_size(self) -> None:
        """Show size information for the selected directory."""
        logger.debug("=" * 60)
        logger.debug("action_show_dir_size: START")

        if not self.active_panel or not self.active_panel.file_list:
            logger.debug("action_show_dir_size: No active panel")
            return

        file_list = self.active_panel.file_list
        entries = file_list.get_selected_entries()

        if not entries:
            logger.debug("action_show_dir_size: No entries selected")
            self.update_status("No file or directory selected")
            return

        # For now, only handle single directory
        entry = entries[0]
        if not entry.is_dir:
            logger.debug("action_show_dir_size: Not a directory")
            self.update_status(f"{entry.name} is a file, not a directory")
            return

        # Build the full path
        dir_path = build_path(self.active_panel.remote, file_list.current_path, entry.name)
        logger.debug(f"action_show_dir_size: Getting size for '{dir_path}'")

        # Show a temporary status while calculating
        self.update_status(f"Calculating size of {entry.name}...")

        # Get size information
        size_info = rclone_wrapper.get_directory_size(self.rclone_path, self.config_path, dir_path, self.app_config.extra_rclone_flags)

        if size_info:
            file_count = size_info.get('count', 0)
            total_size = size_info.get('bytes', 0)
            logger.debug(f"action_show_dir_size: count={file_count}, bytes={total_size}")

            # Show the modal with the results
            self.push_screen(DirectorySizeModal(entry.name, file_count, total_size))
        else:
            logger.debug("action_show_dir_size: Failed to get size")
            self.update_status(f"Failed to calculate size of {entry.name}")

        logger.debug("action_show_dir_size: END")
        logger.debug("=" * 60)

    def update_status(self, message: str) -> None:
        """Update the status bar message (deprecated - status bar removed)."""
        # Status bar has been removed, this method is kept for compatibility
        pass


# Helper functions
def refresh_panel(panel: Optional[FilePanel], rclone_path: str, config_path: str, extra_flags: str = "") -> None:
    """Refresh the file list in a panel."""
    if not panel or not panel.file_list:
        return

    current_path = panel.file_list.current_path
    try:
        entries = rclone_wrapper.list_directory(rclone_path, config_path, panel.remote, current_path, extra_flags)
        panel.file_list.set_entries(entries)

        # Update border title to show current location
        if entries or current_path == "":
            # Successfully loaded
            panel.file_list.border_title = f"{panel.remote}:{current_path}" if current_path else f"{panel.remote}:/"
        else:
            # Empty directory or error
            panel.file_list.border_title = f"{panel.remote}:{current_path} [dim](empty or error)[/dim]"
    except Exception as e:
        # Handle any errors during listing
        panel.file_list.set_entries([])
        panel.file_list.border_title = f"{panel.remote} [red](error)[/red]"


def navigate_up(current_path: str) -> str:
    """Navigate up one directory level."""
    parts = current_path.rstrip('/').split('/')
    return '/'.join(parts[:-1]) if len(parts) > 1 else ""


def build_path(remote: str, current_path: str, filename: str) -> str:
    """Build a full rclone path."""
    if filename:
        return f"{remote}:{os.path.join(current_path, filename)}"
    return f"{remote}:{current_path}"


def main():
    """Run the application."""
    app = RcloneCommander()
    app.run()


if __name__ == "__main__":
    main()
