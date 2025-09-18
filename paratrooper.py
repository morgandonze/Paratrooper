#!/usr/bin/env python3
"""
Task management scripts for PARA + Daily system with hierarchical sections
Usage: python paratrooper.py [command] [args]

This file now serves as a backward-compatible entry point to the modular
Paratrooper system. All functionality has been refactored into separate modules:
- models.py: Data models (Config, Task, Section, TaskFile)
- task_manager.py: Business logic (TaskManager class)
- cli.py: Command-line interface (main function)
"""

# Import all classes for backward compatibility
from models import Config, Task, Section, TaskFile
from task_manager import TaskManager
from cli import main

# Make classes available at module level for backward compatibility
__all__ = ['Config', 'Task', 'Section', 'TaskFile', 'TaskManager', 'main']

if __name__ == "__main__":
    main()
