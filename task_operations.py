#!/usr/bin/env python3
"""
Task CRUD operations for the Paratrooper system.

This module handles all Create, Read, Update, Delete operations
for tasks in the main sections.
"""

import re
from datetime import datetime, timedelta

from models import Task, TODAY, TASK_ID_PATTERN, FORBIDDEN_TASK_CHARS
from file_operations import FileOperations


class TaskOperations:
    """Handles all CRUD operations for tasks in main sections."""
    
    def __init__(self, file_ops: FileOperations):
        self.file_ops = file_ops
        self.today = TODAY
    
    def get_next_id(self):
        """Get the next available task ID"""
        content = self.file_ops.read_file()
        id_matches = re.findall(TASK_ID_PATTERN, content)
        if not id_matches:
            return "001"
        
        # Find the highest ID and increment
        max_id = max(int(id) for id in id_matches)
        next_id = max_id + 1
        return f"{next_id:03d}"
    
    def find_task_by_id(self, task_id):
        """Find a task by ID anywhere in the file"""
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and self.file_ops._is_task_line(line):
                return i + 1, line
        
        return None, None
    
    def find_task_by_id_in_main(self, task_id):
        """Find a task by ID in the main section only"""
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        in_main = False
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                return i + 1, line
        
        return None, None
    
    def add_task_to_main(self, task_text, section=None):
        """Add a task to the main list"""
        if section is None:
            raise ValueError("Section name is required. Please specify a section (e.g., 'WORK', 'HEALTH', 'PROJECTS')")
        # Normalize section name to uppercase
        section = section.upper()
        
        # Validate task text
        is_valid, error_msg = self.file_ops._validate_task_text(task_text)
        if not is_valid:
            print(f"Error: {error_msg}")
            return
        
        # Check for recurring pattern in text
        recurring_pattern = self.file_ops._extract_recurrence_pattern(task_text)
        if recurring_pattern:
            recurring = f"({recurring_pattern})"
            # Remove the pattern from the task text
            task_text = re.sub(r'\s*\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)', '', task_text).strip()
        else:
            recurring = None
        
        task_id = self.get_next_id()
        
        # Build the task line using new format
        task = Task(
            id=task_id,
            text=task_text,
            status=" ",
            date=self.today,
            recurring=recurring,
            section=section
        )
        task_line = task.to_markdown()
        
        # Parse the file to get current structure
        task_file = self.file_ops.parse_file()
        
        # Add task to the appropriate section
        if ':' in section:
            # This is a subsection
            main_section_name, subsection_name = section.split(':', 1)
            main_section = task_file.get_main_section(main_section_name)
            subsection = main_section.add_subsection(subsection_name)
            subsection.add_task(Task.from_markdown(task_line, main_section_name, subsection_name))
        else:
            # This is a main section
            main_section = task_file.get_main_section(section)
            main_section.add_task(Task.from_markdown(task_line, section))
        
        # Write back to file
        self.file_ops.write_file_from_objects(task_file)
        
        print(f"Added task #{task_id} to {section}: {task_text}")
    
    def complete_task(self, task_id):
        """Mark a task as complete"""
        # First check if task is already in daily section
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        in_daily = False
        current_daily_date = None
        task_found_in_daily = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if line_stripped == '# DAILY':
                in_daily = True
                continue
            elif line_stripped.startswith('# ') and line_stripped != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and line_stripped.startswith('## '):
                current_daily_date = line_stripped[3:].strip()
                continue
            
            if in_daily and current_daily_date and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                # Task found in daily section - mark as complete
                updated_line = self.file_ops._mark_task_complete(line)
                lines[i] = updated_line
                self.file_ops.write_file('\n'.join(lines))
                task_found_in_daily = True
                break
        
        if not task_found_in_daily:
            # Task not in daily section - check if it exists in main section
            line_number, line_content = self.find_task_by_id(task_id)
            
            if not line_content:
                print(f"Task #{task_id} not found")
                return
            
            # Add task to daily section first
            from daily_operations import DailyOperations
            daily_ops = DailyOperations(self.file_ops)
            daily_ops.add_task_to_daily_by_id(task_id)
            
            # Now find and complete the task in daily section
            content = self.file_ops.read_file()
            lines = content.split('\n')
            
            in_daily = False
            current_daily_date = None
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                
                if line_stripped == '# DAILY':
                    in_daily = True
                    continue
                elif line_stripped.startswith('# ') and line_stripped != '# DAILY':
                    in_daily = False
                    continue
                
                if in_daily and line_stripped.startswith('## '):
                    current_daily_date = line_stripped[3:].strip()
                    continue
                
                if in_daily and current_daily_date and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                    # Mark as complete
                    updated_line = self.file_ops._mark_task_complete(line)
                    lines[i] = updated_line
                    self.file_ops.write_file('\n'.join(lines))
                    break
        
        print(f"Completed task #{task_id}")
    
    def reopen_task(self, task_id):
        """Reopen a completed task (mark as incomplete)"""
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Update the task
        updated_line = re.sub(r'- \[x\]', '- [ ]', line_content)
        updated_line = self.file_ops._update_task_date(updated_line)
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.file_ops.write_file('\n'.join(lines))
        
        print(f"Reopened task #{task_id}")
    
    def snooze_task(self, task_id, days_or_date):
        """Snooze a task by setting its date to a future date"""
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Parse the snooze parameter
        if days_or_date.isdigit():
            # It's a number of days
            days = int(days_or_date)
            snooze_date = (datetime.now() + timedelta(days=days)).strftime("%d-%m-%Y")
        else:
            # It's a date
            snooze_date = days_or_date
        
        # Parse the task to get its components
        task = Task.from_markdown(line_content)
        if not task:
            print(f"Could not parse task #{task_id}")
            return
        
        # Update the task with new date
        task.date = snooze_date
        updated_line = task.to_markdown()
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.file_ops.write_file('\n'.join(lines))
        
        print(f"Snoozed task #{task_id} until {snooze_date}")
    
    def edit_task(self, task_id, new_text):
        """Edit the text of a task"""
        # Validate new task text
        is_valid, error_msg = self.file_ops._validate_task_text(new_text)
        if not is_valid:
            print(f"Error: {error_msg}")
            return
        
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Parse the current task line
        task_data = self.file_ops._parse_task_line(line_content)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Build new task line with updated text using new format
        task = Task(
            id=task_data['metadata'].get('id'),
            text=new_text,
            status=task_data['status'],
            date=task_data['metadata'].get('date'),
            recurring=task_data['metadata'].get('recurring')
        )
        updated_line = task.to_markdown()
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.file_ops.write_file('\n'.join(lines))
        
        print(f"Edited task #{task_id}: {new_text}")
    
    def move_task(self, task_id, new_section):
        """Move a task to a new section"""
        # Normalize section name to uppercase
        new_section = new_section.upper()
        
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Parse the current task
        task_data = self.file_ops._parse_task_line(line_content)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Remove the task from its current location
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines.pop(line_number - 1)
        
        # Parse the file to get current structure
        task_file = self.file_ops.parse_file()
        
        # Add task to the new section
        if ':' in new_section:
            # This is a subsection
            main_section_name, subsection_name = new_section.split(':', 1)
            main_section = task_file.get_main_section(main_section_name)
            subsection = main_section.add_subsection(subsection_name)
            subsection.add_task(Task.from_markdown(line_content, main_section_name, subsection_name))
        else:
            # This is a main section
            main_section = task_file.get_main_section(new_section)
            main_section.add_task(Task.from_markdown(line_content, new_section))
        
        # Write back to file
        self.file_ops.write_file_from_objects(task_file)
        
        print(f"Moved task #{task_id} to {new_section}")
    
    def modify_task_recurrence(self, task_id, new_recurrence):
        """Modify the recurrence pattern of a task"""
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Parse the current task using Task.from_markdown to get all fields including section
        original_task = Task.from_markdown(line_content)
        if not original_task:
            print(f"Could not parse task #{task_id}")
            return
        
        # Create new task with updated recurrence but preserving all other fields
        updated_task = Task(
            id=original_task.id,
            text=original_task.text,
            status=original_task.status,
            date=original_task.date,
            recurring=f"({new_recurrence})",
            section=original_task.section,
            subsection=original_task.subsection,
            is_daily=original_task.is_daily,
            from_section=original_task.from_section
        )
        updated_line = updated_task.to_markdown()
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.file_ops.write_file('\n'.join(lines))
        
        print(f"Modified recurrence for task #{task_id}: {new_recurrence}")
    
    def delete_task_from_main(self, task_id):
        """Delete a task from the main list only"""
        line_number, line_content = self.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found in main section")
            return
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines.pop(line_number - 1)
        self.file_ops.write_file('\n'.join(lines))
        
        print(f"Deleted task #{task_id} from main list")
    
    def purge_task(self, task_id):
        """Delete a task from everywhere"""
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        # Remove all instances of the task
        updated_lines = []
        for line in lines:
            if f"#{task_id}" not in line or not self.file_ops._is_task_line(line):
                updated_lines.append(line)
        
        self.file_ops.write_file('\n'.join(updated_lines))
        print(f"Purged task #{task_id} from everywhere")
    
    def _is_task_in_daily_section(self, task_id, content=None):
        """Check if a task is in the daily section"""
        if content is None:
            content = self.file_ops.read_file()
        
        lines = content.split('\n')
        in_daily = False
        
        for line in lines:
            line = line.strip()
            
            if line == '# DAILY':
                in_daily = True
                continue
            elif line.startswith('# ') and line != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                return True
        
        return False
    
    def _add_task_to_daily_section(self, task_id, status="complete"):
        """Add a task to the daily section with specified status"""
        # This method would be implemented in daily_operations.py
        # For now, we'll just mark it as complete in the main section
        line_number, line_content = self.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found in main section")
            return
        
        if status == "complete":
            updated_line = self.file_ops._mark_task_complete(line_content)
        elif status == "progress":
            updated_line = self.file_ops._mark_task_progress(line_content)
        else:
            updated_line = line_content
        
        updated_line = self.file_ops._update_task_date(updated_line)
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.file_ops.write_file('\n'.join(lines))
