#!/usr/bin/env python3
"""
Paratrooper - Daily Task Management System

A powerful, flexible task management system that combines the PARA methodology 
with daily progress tracking. Built as a modular Python package that manages 
a plain text file, making it portable, future-proof, and tool-agnostic.

The paratrooper is ready to drop into your daily tasks!
"""

# Import all public classes for easy access
from models import Config, Task, Section, TaskFile
from task_manager import TaskManager

# Make classes available at package level for backward compatibility
__all__ = ['Config', 'Task', 'Section', 'TaskFile', 'TaskManager']

# Version information
__version__ = "1.0.0"
__author__ = "Paratrooper Development Team"
__description__ = "Daily Task Management System"