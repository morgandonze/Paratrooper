#!/usr/bin/env python3
"""
File operations and parsing for the Paratrooper system.

This module handles all file I/O operations, parsing, and formatting
for the task management system.
"""

import re
from datetime import datetime
from pathlib import Path

from models import (
    Task, TaskFile, TODAY,
    TASK_STATUS_PATTERN, TASK_INCOMPLETE_PATTERN, TASK_COMPLETE_PATTERN, TASK_PROGRESS_PATTERN,
    TASK_ID_PATTERN, DATE_PATTERN, RECURRING_PATTERN,
    FORBIDDEN_TASK_CHARS
)


class FileOperations:
    """Handles all file I/O operations and parsing for the task management system."""
    
    def __init__(self, task_file: Path):
        self.task_file = task_file
        self.today = TODAY
    
    def parse_file(self) -> TaskFile:
        """Parse the task file into Python objects"""
        content = self.read_file()
        task_file = TaskFile()
        
        lines = content.split('\n')
        current_section = None
        current_subsection = None
        current_daily_date = None
        in_daily = False
        in_main = False
        in_archive = False
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for main sections
            if line == '# DAILY':
                in_daily = True
                in_main = False
                in_archive = False
                continue
            elif line == '# MAIN':
                in_daily = False
                in_main = True
                in_archive = False
                continue
            elif line == '# ARCHIVE':
                in_daily = False
                in_main = False
                in_archive = True
                continue
            
            # Daily sections
            if in_daily and line.startswith('## '):
                current_daily_date = line[3:].strip()
                continue
            elif in_daily and current_daily_date and line.startswith('- ['):
                task = Task.from_markdown(line)
                if task:
                    task.is_daily = True
                    # Check if this task came from a main section (indicated by " from " in text)
                    # This is for backward compatibility with existing tasks that might have "from" text
                    if " from " in task.text:
                        # Extract the section name from the text
                        parts = task.text.split(" from ")
                        if len(parts) == 2:
                            task.text = parts[0]  # Remove " from SECTION" part
                            task.from_section = parts[1]
                    task_file.get_daily_section(current_daily_date).append(task)
                continue
            
            # Main sections
            elif in_main and line.startswith('## '):
                current_section = line[3:].strip().upper()
                current_subsection = None
                continue
            elif in_main and line.startswith('### '):
                current_subsection = line[4:].strip()
                continue
            elif in_main and line.startswith('- ['):
                task = Task.from_markdown(line, current_section, current_subsection)
                if task:
                    if current_subsection:
                        section = task_file.get_main_section(current_section)
                        subsection = section.add_subsection(current_subsection)
                        subsection.add_task(task)
                    else:
                        task_file.get_main_section(current_section).add_task(task)
                continue
            
            # Archive sections
            elif in_archive and line.startswith('## '):
                current_section = line[3:].strip().upper()
                continue
            elif in_archive and line.startswith('- ['):
                task = Task.from_markdown(line)
                if task:
                    if current_section not in task_file.archive_sections:
                        task_file.archive_sections[current_section] = []
                    task_file.archive_sections[current_section].append(task)
                continue
        
        return task_file
    
    def write_file_from_objects(self, task_file: TaskFile):
        """Write the task file from Python objects"""
        content = task_file.to_markdown()
        self.write_file(content)
    
    def read_file(self):
        """Read the task file, create if doesn't exist."""
        if not self.task_file.exists():
            default_content = "# DAILY\n\n# MAIN\n\n# ARCHIVE\n\n"
            self.task_file.write_text(default_content)
        return self.task_file.read_text()
    
    def write_file(self, content):
        """Write content back to task file"""
        self.task_file.write_text(content)
        self.format_file()
    
    def format_file(self):
        """Format the file to ensure proper spacing between sections and tasks"""
        content = self.read_file()
        lines = content.split('\n')
        formatted_lines = []
        
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()
            
            # Skip empty lines at the beginning
            if not current_line and not formatted_lines:
                i += 1
                continue
            
            # Check if this is a section header
            if current_line.startswith('## '):
                # Look ahead to see if this section has any tasks
                section_has_tasks = False
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line.startswith('## ') or next_line.startswith('# '):
                        # Hit another section, stop looking
                        break
                    elif self._is_task_line(lines[j]):
                        section_has_tasks = True
                        break
                    j += 1
                
                # Add the section header
                formatted_lines.append(lines[i])
                
                # Add blank line after section header if it has tasks
                if section_has_tasks and i + 1 < len(lines) and lines[i + 1].strip() != '':
                    formatted_lines.append('')
                elif not section_has_tasks:
                    # Skip any blank lines after empty section headers
                    while i + 1 < len(lines) and lines[i + 1].strip() == '':
                        i += 1
                    
                    # Add blank line after empty section header if there's another section coming
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('## ') or next_line.startswith('# '):
                            formatted_lines.append('')
            else:
                # Add the current line
                formatted_lines.append(lines[i])
                
                # Add empty line after headers (but not at the end of file)
                if (lines[i].startswith('#') and i < len(lines) - 1 and 
                    not lines[i + 1].strip() == ''):
                    formatted_lines.append('')
                
                # Add empty line after tasks (but not at the end of file)
                elif (self._is_task_line(lines[i]) and i < len(lines) - 1 and 
                      not lines[i + 1].strip() == ''):
                    formatted_lines.append('')
            
            i += 1
        
        # Remove trailing empty lines
        while formatted_lines and formatted_lines[-1].strip() == '':
            formatted_lines.pop()
        
        # Add final newline
        formatted_lines.append('')
        
        self.task_file.write_text('\n'.join(formatted_lines))
    
    def _is_task_line(self, line):
        """Check if a line is a task line"""
        return bool(re.match(TASK_STATUS_PATTERN, line))
    
    def _extract_task_id(self, line):
        """Extract task ID from a line"""
        match = re.search(TASK_ID_PATTERN, line)
        return match.group(1) if match else None
    
    def _extract_date(self, line):
        """Extract date from a line"""
        match = re.search(DATE_PATTERN, line)
        return match.group(1) if match else None
    
    def _is_recurring_task(self, line):
        """Check if a line contains a recurring task"""
        return bool(re.search(RECURRING_PATTERN, line))
    
    def _extract_recurrence_pattern(self, text):
        """Extract recurrence pattern from task text"""
        match = re.search(r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)', text)
        return match.group(1) if match else None
    
    def _validate_task_text(self, text):
        """Validate task text for forbidden characters"""
        # Check for recurring pattern first
        recurring_pattern = self._extract_recurrence_pattern(text)
        if recurring_pattern:
            # Remove the recurring pattern from text for validation
            text_without_recurring = re.sub(r'\s*\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)', '', text).strip()
        else:
            text_without_recurring = text
        
        for char in FORBIDDEN_TASK_CHARS:
            if char in text_without_recurring:
                return False, f"Task text cannot contain '{char}'"
        return True, None
    
    def _parse_task_line(self, line):
        """Parse a task line into components using the new explicit format"""
        if not self._is_task_line(line):
            return None
        
        # Use the Task.from_markdown method for consistent parsing
        task = Task.from_markdown(line)
        if not task:
            return None
        
        return {
            'status': task.status,
            'text': task.text,
            'metadata': {
                'id': task.id,
                'date': task.date,
                'recurring': task.recurring
            }
        }
    
    def _build_task_line(self, status, text, date=None, recurring=None, task_id=None):
        """Build a task line from components"""
        status_part = f"- [{status}] {text}"
        
        metadata_parts = []
        if date:
            metadata_parts.append(f"@{date}")
        if recurring:
            metadata_parts.append(recurring)
        # Snooze functionality removed
        if task_id:
            metadata_parts.append(f"#{task_id}")
        
        if metadata_parts:
            metadata_part = " ".join(metadata_parts)
            return f"{status_part} | {metadata_part}"
        else:
            return status_part
    
    def _update_task_date(self, line):
        """Update the date in a task line to today"""
        if ' | ' in line:
            # Handle pipe-separated format: - [x] | task | section | date | recurring
            parts = line.split(' | ')
            
            # Find the date field (usually at index 3, but could be at 2 if no section)
            # Look for date patterns with or without @ prefix
            date_field_index = None
            for i, part in enumerate(parts):
                if re.match(r'@?\d{2}-\d{2}-\d{4}', part.strip()):
                    date_field_index = i
                    break
            
            if date_field_index is not None:
                # Replace existing date (without @ prefix in new format)
                parts[date_field_index] = self.today
            else:
                # Add date field - determine where to insert it
                # Format: - [x] | task | section | date | recurring
                if len(parts) >= 3:
                    # Insert date after section (index 2)
                    parts.insert(3, self.today)
                else:
                    # Add date at the end
                    parts.append(self.today)
            
            return ' | '.join(parts)
        else:
            # Handle old format without pipes
            return f"{line} | @{self.today}"
    
    def _mark_task_complete(self, line):
        """Mark a task as complete"""
        return re.sub(r'- \[.\]', '- [x]', line)
    
    def _mark_task_progress(self, line):
        """Mark a task as progressed"""
        return re.sub(r'- \[.\]', '- [~]', line)
    
    def find_task_by_id(self, task_id):
        """Find a task by ID anywhere in the file"""
        content = self.read_file()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and self._is_task_line(line):
                return i + 1, line
        
        return None, None
    
    def find_task_by_id_in_main(self, task_id):
        """Find a task by ID in the main section only"""
        content = self.read_file()
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
            
            if in_main and f"#{task_id}" in line and self._is_task_line(line):
                return i + 1, line
        
        return None, None
