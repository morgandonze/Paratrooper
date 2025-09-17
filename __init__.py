"""
PARA + Daily Task Management System

A simple, powerful task management system that combines the PARA methodology
with daily progress tracking in a plain text markdown file.
"""

from .config import Config
from .models import Task, Section, TaskFile
from .task_manager import TaskManager
from .cli import main

__version__ = "2.0.0"
__author__ = "Paratrooper Team"

__all__ = ["Config", "Task", "Section", "TaskFile", "TaskManager", "main"]
