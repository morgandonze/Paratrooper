#!/usr/bin/env python3
"""
Refactored TaskManager class that coordinates specialized modules.

This module contains a much smaller TaskManager class that delegates
to specialized modules for different functional areas.
"""

import subprocess
from datetime import datetime, timedelta
from typing import Optional

from models import Config
from file_operations import FileOperations
from task_operations import TaskOperations
from daily_operations import DailyOperations
from display_operations import DisplayOperations


class TaskManager:
    """Coordinator class that delegates to specialized modules."""
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config.load()
        
        self.config = config
        self.task_file = config.task_file
        self.today = config.today if hasattr(config, 'today') else None
        self._task_file_obj = None
        self.editor = config.editor
        
        # Initialize specialized modules
        self.file_ops = FileOperations(self.task_file)
        self.task_ops = TaskOperations(self.file_ops)
        self.daily_ops = DailyOperations(self.file_ops)
        self.display_ops = DisplayOperations(self.file_ops, config)
    
    def init(self):
        """Initialize the task file with default structure if it doesn't exist"""
        if not self.task_file.exists():
            self.task_file.touch()
            default_content = """# DAILY

# MAIN

# ARCHIVE

"""
            self.task_file.write_text(default_content)
            print(f"Created new task file at {self.task_file}")
        else:
            print(f"Task file already exists at {self.task_file}")
    
    def parse_file(self):
        """Parse the task file into Python objects"""
        return self.file_ops.parse_file()
    
    def write_file_from_objects(self, task_file):
        """Write the task file from Python objects"""
        self.file_ops.write_file_from_objects(task_file)
    
    def read_file(self):
        """Read the task file"""
        return self.file_ops.read_file()
    
    def write_file(self, content):
        """Write content back to task file"""
        self.file_ops.write_file(content)
    
    # Task Operations - delegate to TaskOperations
    def get_next_id(self):
        return self.task_ops.get_next_id()
    
    def find_task_by_id(self, task_id):
        return self.task_ops.find_task_by_id(task_id)
    
    def find_task_by_id_in_main(self, task_id):
        return self.task_ops.find_task_by_id_in_main(task_id)
    
    def add_task_to_main(self, task_text, section="TASKS"):
        return self.task_ops.add_task_to_main(task_text, section)
    
    def complete_task(self, task_id):
        return self.task_ops.complete_task(task_id)
    
    def reopen_task(self, task_id):
        return self.task_ops.reopen_task(task_id)
    
    def snooze_task(self, task_id, days_or_date):
        return self.task_ops.snooze_task(task_id, days_or_date)
    
    def edit_task(self, task_id, new_text):
        return self.task_ops.edit_task(task_id, new_text)
    
    def move_task(self, task_id, new_section):
        return self.task_ops.move_task(task_id, new_section)
    
    def modify_task_recurrence(self, task_id, new_recurrence):
        return self.task_ops.modify_task_recurrence(task_id, new_recurrence)
    
    def delete_task_from_main(self, task_id):
        return self.task_ops.delete_task_from_main(task_id)
    
    def purge_task(self, task_id):
        return self.task_ops.purge_task(task_id)
    
    # Daily Operations - delegate to DailyOperations
    def add_daily_section(self):
        return self.daily_ops.add_daily_section()
    
    def add_task_to_daily(self, task_text):
        return self.daily_ops.add_task_to_daily(task_text)
    
    def add_task_to_daily_by_id(self, task_id):
        return self.daily_ops.add_task_to_daily_by_id(task_id)
    
    def progress_task_in_daily(self, task_id):
        return self.daily_ops.progress_task_in_daily(task_id)
    
    def delete_task_from_daily(self, task_id):
        return self.daily_ops.delete_task_from_daily(task_id)
    
    def sync_daily_sections(self, days_back=3):
        return self.daily_ops.sync_daily_sections(days_back)
    
    def get_recurring_tasks(self):
        return self.daily_ops.get_recurring_tasks()
    
    def should_recur_today(self, recur_pattern, last_date_str):
        return self.daily_ops.should_recur_today(recur_pattern, last_date_str)
    
    def get_most_recent_daily_section(self, task_file):
        return self.daily_ops.get_most_recent_daily_section(task_file)
    
    def get_unfinished_tasks_from_daily(self, daily_tasks):
        return self.daily_ops.get_unfinished_tasks_from_daily(daily_tasks)
    
    # Display Operations - delegate to DisplayOperations
    def show_status_tasks(self, scope=None):
        return self.display_ops.show_status_tasks(scope)
    
    def show_task(self, task_id):
        return self.display_ops.show_task(task_id)
    
    def show_task_from_main(self, task_id):
        return self.display_ops.show_task_from_main(task_id)
    
    def list_sections(self):
        return self.display_ops.list_sections()
    
    def show_config(self):
        return self.display_ops.show_config()
    
    def show_help(self):
        return self.display_ops.show_help()
    
    def show_daily_list(self):
        return self.display_ops.show_daily_list()
    
    def show_section(self, section_name):
        return self.display_ops.show_section(section_name)
    
    def show_all_main(self):
        return self.display_ops.show_all_main()
    
    def find_section(self, section_name, level=1):
        return self.display_ops.find_section(section_name, level)
    
    # Archive Operations - keep in TaskManager for now
    def archive_old_content(self, days_to_keep=7):
        """Clean up old daily sections and completed tasks"""
        task_file = self.parse_file()
        
        if not task_file.daily_sections:
            print("No daily sections to archive")
            return
        
        # Get cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Find sections to archive
        sections_to_archive = []
        for date_str in list(task_file.daily_sections.keys()):
            try:
                section_date = datetime.strptime(date_str, "%d-%m-%Y")
                if section_date < cutoff_date:
                    sections_to_archive.append(date_str)
            except ValueError:
                continue
        
        if not sections_to_archive:
            print("No old content to archive")
            return
        
        # Move sections to archive
        for date_str in sections_to_archive:
            if date_str not in task_file.archive_sections:
                task_file.archive_sections[date_str] = []
            task_file.archive_sections[date_str].extend(task_file.daily_sections[date_str])
            del task_file.daily_sections[date_str]
        
        # Write back to file
        self.write_file_from_objects(task_file)
        
        print(f"Archived {len(sections_to_archive)} old daily sections")
    
    def open_file(self, editor=None):
        """Open the task file with an editor"""
        if editor is None:
            editor = self.editor
        
        try:
            subprocess.run([editor, str(self.task_file)], check=True)
        except subprocess.CalledProcessError:
            print(f"Error opening file with {editor}")
        except FileNotFoundError:
            print(f"Editor '{editor}' not found")
    
    # Helper methods that need access to multiple modules
    def _is_task_in_daily_section(self, task_id, content=None):
        """Check if a task is in the daily section"""
        return self.daily_ops._is_task_in_daily_section(task_id, content)
    
    def _add_task_to_daily_section(self, task_id, status="complete"):
        """Add a task to the daily section with specified status"""
        return self.task_ops._add_task_to_daily_section(task_id, status)
    
    def _get_task_status_info(self, task_data):
        """Get status information for a task"""
        return self.display_ops._get_task_status_info(task_data)
    
    def _get_most_recent_daily_date(self, content=None):
        """Get the most recent daily section date"""
        return self.daily_ops._get_most_recent_daily_date(content)
