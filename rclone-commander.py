#!/usr/bin/env python3
"""
rclone-commander - A dual-pane TUI file manager for rclone

Author: Miklos Mukka Szel
Email: contact@miklos-szel.com
"""

import sys
from src.rclone_commander.main import RcloneCommander

if __name__ == "__main__":
    app = RcloneCommander()
    app.run()
