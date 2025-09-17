#!/usr/bin/env python3
"""
PARA + Daily Task Management System - Refactored Entry Point

This is the new modular version of the task management system.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from cli import main

if __name__ == "__main__":
    main()
