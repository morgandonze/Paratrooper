#!/usr/bin/env python3
"""
Consolidated Paratrooper task management system.

This module contains all business logic consolidated from the specialized modules:
- File operations and parsing
- Task CRUD operations  
- Daily section operations
- Display operations
- Task formatting

All functionality is now in a single Paratrooper class for simplicity.
"""

import re
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List

from models import (
    Config, Task, Section, TaskFile, TODAY,
    TASK_STATUS_PATTERN, TASK_ID_PATTERN, DATE_PATTERN, RECURRING_PATTERN,
    FORBIDDEN_TASK_CHARS
)

class Paratrooper:
    """Consolidated task management system with all business logic."""
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config.load()
        
        self.config = config
        self.task_file = config.task_file
        self.today = TODAY
        self.editor = config.editor
    
    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================
    
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
                    if " from " in task.text:
                        parts = task.text.split(" from ")
                        if len(parts) == 2:
                            task.text = parts[0]
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
    
    def _normalize_task_id(self, task_id):
        """Normalize task ID by removing leading zeros"""
        return str(int(task_id)) if task_id.isdigit() else task_id
    
    def _task_id_matches_line(self, task_id, line):
        """Check if a task ID matches a line, handling both normalized and padded formats"""
        normalized_id = self._normalize_task_id(task_id)
        # Use word boundary matching to avoid partial matches (e.g., #1 matching #11)
        import re
        pattern1 = rf'#{re.escape(normalized_id)}\b'
        pattern2 = rf'#{re.escape(normalized_id.zfill(3))}\b'
        return bool(re.search(pattern1, line) or re.search(pattern2, line))
    
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
    
    def _update_task_date_to_specific_date(self, line, target_date):
        """Update the date in a task line to a specific date"""
        if ' | ' in line:
            # Handle pipe-separated format: - [x] | task | section | date | recurring
            parts = line.split(' | ')
            
            # Find the date field (usually at index 3, but could be at 2 if no section)
            date_field_index = None
            for i, part in enumerate(parts):
                if re.match(r'@?\d{2}-\d{2}-\d{4}', part.strip()):
                    date_field_index = i
                    break
            
            if date_field_index is not None:
                # Replace existing date (without @ prefix in new format)
                parts[date_field_index] = target_date
            else:
                # Add date field - determine where to insert it
                if len(parts) >= 3:
                    # Insert date after section (index 2)
                    parts.insert(3, target_date)
                else:
                    # Fallback: add at end
                    parts.append(target_date)
            
            return ' | '.join(parts)
        else:
            # Handle old format without pipes
            return f"{line} | @{target_date}"
    
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
            if self._task_id_matches_line(task_id, line) and self._is_task_line(line):
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
            
            if in_main and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                return i + 1, line
        
        return None, None
    
    # ============================================================================
    # TASK OPERATIONS
    # ============================================================================
    
    def get_next_id(self):
        """Get the next available task ID"""
        content = self.read_file()
        id_matches = re.findall(TASK_ID_PATTERN, content)
        if not id_matches:
            return "001"
        
        # Find the highest ID and increment
        max_id = max(int(id) for id in id_matches)
        next_id = max_id + 1
        
        # Format with appropriate padding: 3 digits for 1-999, no padding for 1000+
        if next_id <= 999:
            return f"{next_id:03d}"
        else:
            return str(next_id)
    
    def add_task_to_main(self, task_text, section=None):
        """Add a task to the main list"""
        if section is None:
            raise ValueError("Section name is required. Please specify a section (e.g., 'WORK', 'HEALTH', 'PROJECTS')")
        # Normalize section name to uppercase
        section = section.upper()
        
        # Validate task text
        is_valid, error_msg = self._validate_task_text(task_text)
        if not is_valid:
            print(f"Error: {error_msg}")
            return
        
        # Check for recurring pattern in text
        recurring_pattern = self._extract_recurrence_pattern(task_text)
        if recurring_pattern:
            recurring = recurring_pattern  # No parentheses in new format
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
        task_file = self.parse_file()
        
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
        self.write_file_from_objects(task_file)
        
        print(f"Added task #{task_id} to {section}: {task_text}")
    
    def complete_task(self, task_id):
        """Mark a task as complete"""
        # First check if task is already in daily section
        content = self.read_file()
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
            
            if in_daily and current_daily_date and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                # Task found in daily section - mark as complete
                updated_line = self._mark_task_complete(line)
                lines[i] = updated_line
                self.write_file('\n'.join(lines))
                task_found_in_daily = True
                break
        
        if not task_found_in_daily:
            # Task not in daily section - check if it exists in main section
            line_number, line_content = self.find_task_by_id(task_id)
            
            if not line_content:
                print(f"Task #{task_id} not found")
                return
            
            # Add task to daily section first
            self.add_task_to_daily_by_id(task_id)
            
            # Now find and complete the task in daily section
            content = self.read_file()
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
                
                if in_daily and current_daily_date and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                    # Mark as complete
                    updated_line = self._mark_task_complete(line)
                    lines[i] = updated_line
                    self.write_file('\n'.join(lines))
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
        updated_line = self._update_task_date(updated_line)
        
        content = self.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.write_file('\n'.join(lines))
        
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
        
        content = self.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.write_file('\n'.join(lines))
        
        print(f"Snoozed task #{task_id} until {snooze_date}")
    
    def edit_task(self, task_id, new_text):
        """Edit the text of a task"""
        # Validate new task text
        is_valid, error_msg = self._validate_task_text(new_text)
        if not is_valid:
            print(f"Error: {error_msg}")
            return
        
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Parse the current task line
        task_data = self._parse_task_line(line_content)
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
        
        content = self.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.write_file('\n'.join(lines))
        
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
        task_data = self._parse_task_line(line_content)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Remove the task from its current location
        content = self.read_file()
        lines = content.split('\n')
        lines.pop(line_number - 1)
        
        # Parse the file to get current structure
        task_file = self.parse_file()
        
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
        self.write_file_from_objects(task_file)
        
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
        
        content = self.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_line
        self.write_file('\n'.join(lines))
        
        print(f"Modified recurrence for task #{task_id}: {new_recurrence}")
    
    def delete_task_from_main(self, task_id):
        """Delete a task from the main list only"""
        line_number, line_content = self.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found in main section")
            return
        
        content = self.read_file()
        lines = content.split('\n')
        lines.pop(line_number - 1)
        self.write_file('\n'.join(lines))
        
        print(f"Deleted task #{task_id} from main list")
    
    def purge_task(self, task_id):
        """Delete a task from everywhere"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Remove all instances of the task
        updated_lines = []
        for line in lines:
            if not self._task_id_matches_line(task_id, line) or not self._is_task_line(line):
                updated_lines.append(line)
        
        self.write_file('\n'.join(updated_lines))
        print(f"Purged task #{task_id} from everywhere")
    
    # ============================================================================
    # DAILY OPERATIONS
    # ============================================================================
    
    def _get_most_recent_daily_date(self, content=None):
        """Get the most recent daily section date"""
        if content is None:
            content = self.read_file()
        
        lines = content.split('\n')
        in_daily = False
        dates = []
        
        for line in lines:
            line = line.strip()
            
            if line == '# DAILY':
                in_daily = True
                continue
            elif line.startswith('# ') and line != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and line.startswith('## '):
                date_str = line[3:].strip()
                try:
                    # Validate date format
                    datetime.strptime(date_str, "%d-%m-%Y")
                    dates.append(date_str)
                except ValueError:
                    continue
        
        if not dates:
            return None
        
        # Return the most recent date
        return max(dates, key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
    
    def _is_task_in_daily_section(self, task_id, content=None):
        """Check if a task is in the daily section"""
        if content is None:
            content = self.read_file()
        
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
            
            if in_daily and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                return True
        
        return False
    
    def should_recur_today(self, recur_pattern, last_date_str):
        """Check if a recurring task should appear today"""
        if not recur_pattern:
            return False
        
        today = datetime.now()
        
        # Handle different recurrence patterns
        if recur_pattern == "daily":
            # Daily tasks should always appear, regardless of when they were last completed
            return True
        elif recur_pattern == "weekdays":
            return today.weekday() < 5  # Monday=0, Friday=4
        elif recur_pattern.startswith("weekly"):
            if recur_pattern == "weekly":
                # Default to Sunday
                return today.weekday() == 6
            else:
                # Parse specific days: weekly:mon,wed,fri
                day_part = recur_pattern.split(":", 1)[1]
                day_map = {
                    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
                    'fri': 4, 'sat': 5, 'sun': 6
                }
                
                if ',' in day_part:
                    # Multiple days
                    days = [day_map.get(day.strip()) for day in day_part.split(',')]
                    return today.weekday() in days
                else:
                    # Single day
                    target_day = day_map.get(day_part.strip())
                    return today.weekday() == target_day
        elif recur_pattern.startswith("monthly"):
            if recur_pattern == "monthly":
                # Default to 1st of month
                return today.day == 1
            else:
                # Parse specific day: monthly:15th
                day_part = recur_pattern.split(":", 1)[1]
                if day_part.endswith('th'):
                    day_num = int(day_part[:-2])
                    return today.day == day_num
                elif day_part.endswith('st'):
                    day_num = int(day_part[:-2])
                    return today.day == day_num
                elif day_part.endswith('nd'):
                    day_num = int(day_part[:-2])
                    return today.day == day_num
                elif day_part.endswith('rd'):
                    day_num = int(day_part[:-2])
                    return today.day == day_num
                else:
                    day_num = int(day_part)
                    return today.day == day_num
        elif recur_pattern.startswith("recur:"):
            # Custom recurrence: recur:3d, recur:2w, etc.
            # For custom recurrence, we need to check the last date
            if not last_date_str:
                # If no date provided (new task), assume it should recur immediately
                return True
            
            try:
                last_date = datetime.strptime(last_date_str, "%d-%m-%Y")
            except (ValueError, TypeError):
                # If we can't parse the date, assume it should recur
                return True
            
            interval_part = recur_pattern.split(":", 1)[1]
            
            # Handle combination patterns (comma-separated intervals)
            intervals = [interval.strip() for interval in interval_part.split(',')]
            
            # Convert all intervals to days and sum them up
            total_days = 0
            for interval in intervals:
                if interval.endswith('d'):
                    days = int(interval[:-1])
                    total_days += days
                elif interval.endswith('w'):
                    weeks = int(interval[:-1])
                    total_days += weeks * 7
                elif interval.endswith('m'):
                    months = int(interval[:-1])
                    # Approximate months as 30 days for simplicity
                    total_days += months * 30
                elif interval.endswith('y'):
                    years = int(interval[:-1])
                    # Approximate years as 365 days for simplicity
                    total_days += years * 365
            
            # Check if the total interval has been met
            days_since = (today - last_date).days
            # For existing tasks, check if the total interval has passed
            # Only allow immediate recurrence for daily tasks
            return days_since >= total_days
        
        return False
    
    def _get_main_task_by_id(self, task_id):
        """Get a main task by its ID"""
        task_file = self.parse_file()
        
        for section_name, section in task_file.main_sections.items():
            for task in section.tasks:
                if task.id == task_id:
                    return task
            
            # Check subsections
            for subsection_name, subsection in section.subsections.items():
                for task in subsection.tasks:
                    if task.id == task_id:
                        return task
        
        return None
    
    def get_recurring_tasks(self):
        """Get all recurring tasks that should appear today"""
        task_file = self.parse_file()
        recurring_tasks = []
        
        for section_name, section in task_file.main_sections.items():
            for task in section.tasks:
                if task.recurring:
                    # For new tasks (created today), allow immediate recurrence
                    # For existing tasks, check if they should recur based on their last appearance date
                    should_recur = False
                    if task.date == self.today and task.status in [' ', '~']:
                        # New task created today - should appear immediately
                        should_recur = True
                    else:
                        # Existing task - check if it should recur based on interval
                        should_recur = self.should_recur_today(task.recurring.strip('()'), task.date or self.today)
                    
                    if should_recur:
                        recurring_tasks.append({
                            'id': task.id,
                            'text': task.text,
                            'section': section_name,
                            'recurring': task.recurring
                        })
            
            # Check subsections
            for subsection_name, subsection in section.subsections.items():
                for task in subsection.tasks:
                    if task.recurring:
                        # For new tasks (created today), allow immediate recurrence
                        # For existing tasks, check if they should recur based on their last appearance date
                        should_recur = False
                        if task.date == self.today and task.status in [' ', '~']:
                            # New task created today - should appear immediately
                            should_recur = True
                        else:
                            # Existing task - check if it should recur based on interval
                            should_recur = self.should_recur_today(task.recurring.strip('()'), task.date or self.today)
                        
                        if should_recur:
                            recurring_tasks.append({
                                'id': task.id,
                                'text': task.text,
                                'section': f"{section_name}:{subsection_name}",
                                'recurring': task.recurring
                            })
        
        return recurring_tasks
    
    def get_most_recent_daily_section(self, task_file):
        """Get the most recent daily section from a TaskFile object"""
        if not task_file.daily_sections:
            return None
        
        most_recent_date = max(task_file.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
        return most_recent_date, task_file.daily_sections[most_recent_date]
    
    def get_unfinished_tasks_from_daily(self, daily_tasks):
        """Get unfinished tasks from daily section (for carry-over)"""
        unfinished = []
        for task in daily_tasks:
            if task.status in [' ', '~']:  # Incomplete or progress
                unfinished.append(task)
        return unfinished
    
    def add_daily_section(self):
        """Add today's daily section with recurring tasks and carry-over"""
        task_file = self.parse_file()
        
        # Check if today's section already exists
        section_already_exists = self.today in task_file.daily_sections
        
        # Get recurring tasks for today
        recurring_tasks = self.get_recurring_tasks()
        
        # Clean up incomplete recurring tasks from old daily sections
        # Only clean up tasks that have new instances being added today
        new_recurring_task_ids = {task['id'] for task in recurring_tasks}
        cleaned_tasks = self._cleanup_incomplete_recurring_tasks(task_file, new_recurring_task_ids)
        
        # Get unfinished tasks from previous day (if carry-over is enabled)
        # Only carry over tasks that should actually recur today
        unfinished_tasks = []
        if self.config and self.config.carry_over_enabled:
            most_recent_result = self.get_most_recent_daily_section(task_file)
            if most_recent_result:
                most_recent_date, most_recent_tasks = most_recent_result
                if most_recent_date and most_recent_date != self.today:
                    all_unfinished = self.get_unfinished_tasks_from_daily(most_recent_tasks)
                    
                    # Filter to only carry over tasks that should recur today
                    for task in all_unfinished:
                        if task.recurring:
                            # For recurring tasks, only carry over if they should recur today
                            if self.should_recur_today(task.recurring.strip('()'), task.date or self.today):
                                unfinished_tasks.append(task)
                        else:
                            # For non-recurring tasks, always carry over
                            unfinished_tasks.append(task)
        
        if section_already_exists:
            # If section already exists, just add missing recurring tasks
            existing_tasks = task_file.daily_sections[self.today]
            existing_task_ids = {task.id for task in existing_tasks}
            
            # Get IDs of unfinished tasks to avoid duplication
            unfinished_task_ids = {task.id for task in unfinished_tasks}
            
            # Add recurring tasks that aren't already in the daily section
            new_recurring_tasks = []
            for recurring_task in recurring_tasks:
                if (recurring_task['id'] not in existing_task_ids and 
                    recurring_task['id'] not in unfinished_task_ids):
                    task_text = recurring_task['text']
                    task = Task(
                        id=recurring_task['id'],
                        text=task_text,
                        status=" ",
                        date=self.today,
                        recurring=recurring_task['recurring'],
                        section=recurring_task['section'],
                        is_daily=True,
                        from_section=recurring_task['section']
                    )
                    # Add to the beginning of the existing tasks
                    existing_tasks.insert(0, task)
                    new_recurring_tasks.append(task)
            
            # Write back to file
            self.write_file_from_objects(task_file)
            
            if new_recurring_tasks:
                print(f"Added {len(new_recurring_tasks)} new recurring tasks to today's daily section")
            
            return "show_daily_list"
        
        # Create today's daily section (original logic for new sections)
        today_tasks = []
        
        # Get IDs of unfinished tasks to avoid duplication
        unfinished_task_ids = {task.id for task in unfinished_tasks}
        
        # Add recurring tasks (skip if already being carried over)
        for recurring_task in recurring_tasks:
            if recurring_task['id'] not in unfinished_task_ids:
                task_text = recurring_task['text']  # No need for "from" text anymore
                # Get the main task to preserve its activity date
                main_task = self._get_main_task_by_id(recurring_task['id'])
                activity_date = main_task.date if main_task else self.today
                task = Task(
                    id=recurring_task['id'],
                    text=task_text,
                    status=" ",
                    date=activity_date,  # Preserve main task's activity date
                    recurring=recurring_task['recurring'],
                    section=recurring_task['section'],
                    is_daily=True,
                    from_section=recurring_task['section']
                )
                today_tasks.append(task)
        
        # Add unfinished tasks from previous day
        for unfinished_task in unfinished_tasks:
            # Reset status to incomplete for carry-over, but preserve activity date
            task = Task(
                id=unfinished_task.id,
                text=unfinished_task.text,
                status=" ",
                date=unfinished_task.date,  # Preserve the activity date
                recurring=unfinished_task.recurring,
                section=unfinished_task.section,
                subsection=unfinished_task.subsection,
                is_daily=True,
                from_section=unfinished_task.from_section
            )
            today_tasks.append(task)
        
        # Add tasks to today's section
        task_file.daily_sections[self.today] = today_tasks
        
        # Write back to file
        self.write_file_from_objects(task_file)
        
        # Reorganize daily sections (move old ones to archive) AFTER adding today's section
        # Only move sections that don't contain recurring tasks that should persist
        self._reorganize_daily_sections_smart(task_file, new_recurring_task_ids)
        self.write_file_from_objects(task_file)
        
        if recurring_tasks:
            print(f"Daily section for {self.today} updated with {len(recurring_tasks)} new recurring tasks")
        else:
            print(f"Daily section for {self.today} is empty")
        
        if unfinished_tasks:
            print(f"Carried over {len(unfinished_tasks)} unfinished tasks from previous day")
        
        if cleaned_tasks:
            print(f"Cleaned up {len(cleaned_tasks)} incomplete recurring tasks from previous days")
    
    def _cleanup_incomplete_recurring_tasks(self, task_file, new_recurring_task_ids=None):
        """Remove incomplete recurring tasks from old daily sections only if new instances are being added"""
        cleaned_tasks = []
        
        if not task_file.daily_sections:
            return cleaned_tasks
        
        # Get today's date for comparison
        today_obj = datetime.strptime(self.today, "%d-%m-%Y")
        
        # Only clean up tasks that have new instances being added today
        if new_recurring_task_ids is None:
            new_recurring_task_ids = set()
        
        # Find incomplete recurring tasks in old daily sections
        tasks_to_remove = []
        for date_str, tasks in task_file.daily_sections.items():
            if date_str == self.today:
                continue  # Skip today's section
            
            try:
                section_date = datetime.strptime(date_str, "%d-%m-%Y")
                if section_date >= today_obj:
                    continue  # Skip future dates
            except ValueError:
                continue  # Skip invalid dates
            
            for task in tasks:
                if (task.recurring and 
                    task.status in [' ', '~'] and  # Incomplete or progress
                    task.id in new_recurring_task_ids):  # Only remove if new instance is being added
                    tasks_to_remove.append({
                        'id': task.id,
                        'date': date_str,
                        'task': task
                    })
        
        # Remove the tasks from their sections
        for task_info in tasks_to_remove:
            date_str = task_info['date']
            task_to_remove = task_info['task']
            
            if date_str in task_file.daily_sections:
                tasks = task_file.daily_sections[date_str]
                for i, task in enumerate(tasks):
                    if task.id == task_to_remove.id:
                        tasks.pop(i)
                        cleaned_tasks.append(task_info)
                        break
        
        return cleaned_tasks
    
    def _reorganize_daily_sections_smart(self, task_file, new_recurring_task_ids=None):
        """Move non-recent daily sections to archive, but preserve recurring tasks that should persist"""
        if not task_file.daily_sections or len(task_file.daily_sections) <= 1:
            return
        
        # Get the most recent date
        most_recent_date = max(task_file.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
        
        # Get IDs of tasks that are in today's section (carried over or new)
        today_task_ids = set()
        if self.today in task_file.daily_sections:
            today_task_ids = {task.id for task in task_file.daily_sections[self.today]}
        
        # Only move sections that don't contain recurring tasks that should persist
        dates_to_move = []
        for date in task_file.daily_sections.keys():
            if date == most_recent_date:
                continue  # Keep the most recent section
            
            # Check if this section contains recurring tasks that should persist
            should_persist = False
            for task in task_file.daily_sections[date]:
                if task.recurring and task.id not in (new_recurring_task_ids or set()):
                    # This is a recurring task that's not getting a new instance today
                    # Check if it should persist based on its recurrence pattern
                    if self._should_persist_recurring_task(task, date):
                        should_persist = True
                        break  # If any task should persist, keep the entire section
            
            if not should_persist:
                dates_to_move.append(date)
        
        # Move non-persistent sections to archive, but remove tasks that are in today's section
        for date in dates_to_move:
            # Filter out tasks that are already in today's section (carried over)
            tasks_to_archive = []
            for task in task_file.daily_sections[date]:
                if task.id not in today_task_ids:
                    tasks_to_archive.append(task)
            
            # Only archive if there are tasks to archive
            if tasks_to_archive:
                if date not in task_file.archive_sections:
                    task_file.archive_sections[date] = []
                task_file.archive_sections[date].extend(tasks_to_archive)
            
            # Remove the entire section from daily sections
            del task_file.daily_sections[date]
    
    def _should_persist_recurring_task(self, task, section_date):
        """Check if a recurring task should persist in its appearance date section"""
        if not task.recurring:
            return False
        
        # For recurring tasks, they should persist until a new instance is created
        # This means they should persist if they haven't met their recurrence interval yet
        try:
            section_date_obj = datetime.strptime(section_date, "%d-%m-%Y")
            today_obj = datetime.strptime(self.today, "%d-%m-%Y")
            
            # Check if this task should recur today based on its pattern
            # If it should recur today, it will get a new instance, so don't persist the old one
            # If it shouldn't recur today, persist the old instance
            should_recur_today = self.should_recur_today(task.recurring.strip('()'), task.date or self.today)
            
            # Persist if the task should NOT recur today (meaning it hasn't met its interval yet)
            return not should_recur_today
            
        except ValueError:
            return False
    
    def add_task_to_daily(self, task_text):
        """Add a task directly to today's daily section"""
        task_file = self.parse_file()
        
        # Ensure today's section exists
        if self.today not in task_file.daily_sections:
            task_file.daily_sections[self.today] = []
        
        # Get next ID
        content = self.read_file()
        id_matches = re.findall(TASK_ID_PATTERN, content)
        if not id_matches:
            task_id = "001"
        else:
            max_id = max(int(id) for id in id_matches)
            task_id = f"{max_id + 1:03d}"
        
        # Create task
        task = Task(
            id=task_id,
            text=task_text,
            status=" ",
            date=self.today,
            section="DAILY",
            is_daily=True
        )
        
        # Add to today's section
        task_file.daily_sections[self.today].insert(0, task)  # Add to top
        
        # Write back to file
        self.write_file_from_objects(task_file)
        
        print(f"Added task #{task_id} to today's section: {task_text}")
    
    def add_task_to_daily_by_id(self, task_id):
        """Pull a task from main list into today's daily section"""
        # Find the task in main section
        content = self.read_file()
        lines = content.split('\n')
        
        task_line = None
        task_section = None
        in_main = False
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                current_section = line[3:].strip()
                continue
            
            if in_main and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                task_line = line
                task_section = current_section.upper() if current_section else None
                break
        
        if not task_line:
            print(f"Task #{task_id} not found in main section")
            return
        
        # Parse the task
        task_data = self._parse_task_line(task_line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Create task for daily section (no need for "from" text anymore)
        task_text = task_data['text']
        # Preserve the main task's activity date
        activity_date = task_data['metadata'].get('date', self.today)
        task = Task(
            id=task_id,
            text=task_text,
            status=" ",
            date=activity_date,  # Preserve main task's activity date
            recurring=task_data['metadata'].get('recurring'),
            section=task_section,
            is_daily=True,
            from_section=task_section
        )
        
        # Add to today's daily section
        task_file = self.parse_file()
        
        # Ensure today's section exists
        if self.today not in task_file.daily_sections:
            task_file.daily_sections[self.today] = []
        
        # Add to top of today's section
        task_file.daily_sections[self.today].insert(0, task)
        
        # Write back to file
        self.write_file_from_objects(task_file)
        
        print(f"Pulled task #{task_id} to today's section: {task_data['text']}")
    
    def progress_task_in_daily(self, task_id):
        """Mark a task as progressed in today's daily section"""
        content = self.read_file()
        lines = content.split('\n')
        
        in_daily = False
        current_daily_date = None
        task_found_in_daily = False
        
        # First check if task is already in daily section
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
            
            if in_daily and current_daily_date and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                # Mark as progressed
                updated_line = self._mark_task_progress(line)
                lines[i] = updated_line
                self.write_file('\n'.join(lines))
                print(f"Marked progress on task #{task_id} in today's daily section")
                task_found_in_daily = True
                break
        
        if not task_found_in_daily:
            # Task not in daily section - add it first, then mark progress
            self.add_task_to_daily_by_id(task_id)
            
            # Now find and mark progress on the task in daily section
            content = self.read_file()
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
                
                if in_daily and current_daily_date and self._task_id_matches_line(task_id, line) and self._is_task_line(line):
                    # Mark as progressed
                    updated_line = self._mark_task_progress(line)
                    lines[i] = updated_line
                    self.write_file('\n'.join(lines))
                    print(f"Marked progress on task #{task_id} in today's daily section")
                    break
    
    def create_pass_entry(self, task_id, days_ago):
        """Create a pass entry M-N days ago in the archive section and update main task date"""
        # Find the task in main section
        line_number, line_content = self.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found in main section")
            return
        
        # Parse the task
        task_data = self._parse_task_line(line_content)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Calculate task age (M days)
        current_task_date = datetime.strptime(task_data['metadata']['date'], "%d-%m-%Y")
        today = datetime.now()
        task_age_days = (today - current_task_date).days
        
        # Validate N is between 1 and M
        if days_ago < 1 or days_ago > task_age_days:
            print(f"Error: N must be between 1 and {task_age_days} for this task")
            return
        
        # Calculate target date: N days ago from today
        target_date = today - timedelta(days=days_ago)
        target_date_str = target_date.strftime("%d-%m-%Y")
        
        # Create a pass entry task (marked as progressed)
        pass_task = Task(
            id=task_id,
            text=task_data['text'],
            status="~",  # Progress status
            date=target_date_str,
            recurring=task_data['metadata'].get('recurring'),
            section='ARCHIVE',  # Pass entries go to archive
            is_daily=True,
            from_section=task_data.get('section', 'ARCHIVE')
        )
        
        # Parse the file to get current structure
        task_file = self.parse_file()
        
        # Add the pass entry to the archive section for the target date
        if target_date_str not in task_file.archive_sections:
            task_file.archive_sections[target_date_str] = []
        
        # Check if a pass entry already exists for this task on this date
        existing_entries = task_file.archive_sections[target_date_str]
        duplicate_exists = False
        for existing_entry in existing_entries:
            if existing_entry.id == task_id:
                duplicate_exists = True
                print(f"Pass entry for task #{task_id} on {target_date_str} already exists (skipping duplicate)")
                break
        
        # Add the pass entry to the archive only if it's not a duplicate
        if not duplicate_exists:
            task_file.archive_sections[target_date_str].append(pass_task)
            # Write back to file
            self.write_file_from_objects(task_file)
            print(f"Created pass entry for task #{task_id} on {target_date_str}")
        else:
            print(f"Pass entry for task #{task_id} on {target_date_str} already exists (skipping duplicate)")
        
        # Update the main task's date to the target date
        self._update_main_task_date_from_pass_entry(task_id, target_date_str)
    
    def _update_main_task_date_from_pass_entry(self, task_id, pass_entry_date):
        """Update the main task's date to the pass entry date only if moving forward"""
        # Find the task in main section
        line_number, line_content = self.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Warning: Could not find task #{task_id} in main section to update date")
            return
        
        # Parse the current task
        task_data = self._parse_task_line(line_content)
        if not task_data:
            print(f"Warning: Could not parse task #{task_id} to update date")
            return
        
        # Get current task date
        current_task_date = datetime.strptime(task_data['metadata']['date'], "%d-%m-%Y")
        pass_entry_datetime = datetime.strptime(pass_entry_date, "%d-%m-%Y")
        
        # Only update if the pass entry date is different from current date
        # Pass entries represent historical activity, so we update regardless of direction
        if pass_entry_datetime != current_task_date:
            new_date = pass_entry_date
            
            # Create updated task with new date
            updated_task = Task(
                id=task_id,
                text=task_data['text'],
                status=task_data['status'],
                date=new_date,
                recurring=task_data['metadata'].get('recurring'),
                section=task_data.get('section', 'MAIN')
            )
            
            # Update the file
            content = self.read_file()
            lines = content.split('\n')
            lines[line_number - 1] = updated_task.to_markdown()
            self.write_file('\n'.join(lines))
    
    def delete_task_from_daily(self, task_id):
        """Remove a task from today's daily section"""
        # Parse the file into model objects
        task_file = self.parse_file()
        
        # Check if today's daily section exists
        if self.today not in task_file.daily_sections:
            print(f"No daily section for {self.today}")
            return
        
        # Find and remove the task with the given ID
        tasks = task_file.daily_sections[self.today]
        task_found = False
        
        for i, task in enumerate(tasks):
            if task.id == task_id:
                tasks.pop(i)
                task_found = True
                break
        
        if not task_found:
            print(f"Task #{task_id} not found in today's daily section")
            return
        
        # Regenerate the file from the updated model data
        self.write_file_from_objects(task_file)
        print(f"Removed task #{task_id} from today's daily section")
    
    def sync_daily_sections(self, days_back=3):
        """Sync daily sections back to main list"""
        task_file = self.parse_file()
        
        if not task_file.daily_sections:
            print("No daily sections to sync")
            return
        
        # Get the most recent daily section
        most_recent_date, most_recent_tasks = self.get_most_recent_daily_section(task_file)
        if not most_recent_tasks:
            print("No tasks in daily section to sync")
            return
        
        content = self.read_file()
        lines = content.split('\n')
        
        completed_count = 0
        progressed_count = 0
        
        # Process each task in the daily section
        for task in most_recent_tasks:
            if task.status == 'x':  # Completed
                # Find the corresponding task in main section only
                task_found = False
                in_main_section = False
                for i, line in enumerate(lines):
                    # Check if we're in the main section
                    if line.strip() == '# MAIN':
                        in_main_section = True
                        continue
                    elif line.strip() == '# DAILY' or line.strip() == '# ARCHIVE':
                        in_main_section = False
                        continue
                    
                    # Only process tasks in the main section
                    if in_main_section and f"#{task.id}" in line and self._is_task_line(line):
                        # Check if it's a recurring task
                        if task.recurring:
                            # For recurring tasks, update the date to today (activity date) but keep incomplete
                            updated_line = self._update_task_date_to_specific_date(line, most_recent_date)
                        else:
                            # For non-recurring tasks, mark as complete
                            updated_line = self._mark_task_complete(line)
                            updated_line = self._update_task_date(updated_line)
                        
                        lines[i] = updated_line
                        completed_count += 1
                        task_found = True
                        break
                
                if not task_found:
                    print(f"Warning: Could not find task #{task.id} in main sections to sync")
            
            elif task.status == '~':  # Progress
                # Find the corresponding task in main section only
                task_found = False
                in_main_section = False
                for i, line in enumerate(lines):
                    # Check if we're in the main section
                    if line.strip() == '# MAIN':
                        in_main_section = True
                        continue
                    elif line.strip() == '# DAILY' or line.strip() == '# ARCHIVE':
                        in_main_section = False
                        continue
                    
                    # Only process tasks in the main section
                    if in_main_section and f"#{task.id}" in line and self._is_task_line(line):
                        # Update the date to show recent engagement (use today as activity date)
                        updated_line = self._update_task_date_to_specific_date(line, most_recent_date)
                        lines[i] = updated_line
                        progressed_count += 1
                        task_found = True
                        break
                
                if not task_found:
                    print(f"Warning: Could not find task #{task.id} in main sections to sync")
        
        # Write back to file
        self.write_file('\n'.join(lines))
        
        if completed_count > 0 or progressed_count > 0:
            print(f"Synced {completed_count} completed and {progressed_count} progressed tasks from daily section")
        else:
            print("No changes needed")
    
    # ============================================================================
    # DISPLAY OPERATIONS
    # ============================================================================
    
    def find_section(self, section_name, level=1):
        """Find a section by name and level"""
        content = self.read_file()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line == '#' * level + ' ' + section_name:
                return i + 1
        
        return None
    
    def _get_task_status_info(self, task_data):
        """Get status information for a task"""
        if not task_data:
            return "unknown", 0, "unknown"
        
        status = task_data.get('status', ' ')
        text = task_data.get('text', '')
        date_str = task_data.get('metadata', {}).get('date')
        recurring = task_data.get('metadata', {}).get('recurring')
        
        # Check if task is snoozed (date is in the future)
        if date_str:
            try:
                task_date = datetime.strptime(date_str, "%d-%m-%Y")
                today = datetime.now()
                if task_date > today:
                    return "snoozed", 0, date_str
            except ValueError:
                pass
        
        # Calculate staleness
        if date_str:
            try:
                task_date = datetime.strptime(date_str, "%d-%m-%Y")
                today = datetime.now()
                
                # For recurring tasks, calculate days based on expected next occurrence
                if recurring:  # Any recurring task, regardless of status
                    # Check if there's an incomplete instance in daily section
                    incomplete_daily_date = self._get_incomplete_daily_instance_date(task_data.get('metadata', {}).get('id'))
                    
                    if incomplete_daily_date:
                        # Use the incomplete daily instance date
                        try:
                            incomplete_date_obj = datetime.strptime(incomplete_daily_date, "%d-%m-%Y")
                            days_old = (today - incomplete_date_obj).days
                        except ValueError:
                            # Fall back to normal calculation if date parsing fails
                            days_old = (today - task_date).days
                    else:
                        # Calculate based on expected next occurrence
                        expected_date = self._calculate_next_recurrence_date(recurring.strip('()'), date_str)
                        if expected_date:
                            days_old = (today - expected_date).days
                            # If we're before the expected date, don't count as stale
                            if days_old < 0:
                                days_old = 0
                        else:
                            days_old = (today - task_date).days
                else:
                    # For non-recurring tasks, check for pass entries first
                    pass_entry_date = self._get_incomplete_daily_instance_date(task_data.get('metadata', {}).get('id'))
                    if pass_entry_date:
                        # Use the pass entry date (it represents the most recent activity)
                        try:
                            pass_date_obj = datetime.strptime(pass_entry_date, "%d-%m-%Y")
                            days_old = (today - pass_date_obj).days
                        except ValueError:
                            # Fall back to normal calculation if date parsing fails
                            days_old = (today - task_date).days
                    else:
                        # For non-recurring tasks, use normal calculation
                        days_old = (today - task_date).days
                
                if status == 'x':
                    return "complete", days_old, date_str
                elif status == '~':
                    return "progress", days_old, date_str
                else:
                    return "incomplete", days_old, date_str
            except ValueError:
                return "invalid_date", 0, date_str
        
        return "no_date", 0, "no_date"
    
    def _calculate_task_age(self, task_data):
        """Calculate the age of a task in days (from creation/appearance)"""
        if not task_data:
            return None
        
        date_str = task_data.get('metadata', {}).get('date')
        if not date_str:
            return None
        
        try:
            task_date = datetime.strptime(date_str, "%d-%m-%Y")
            today = datetime.now()
            return (today - task_date).days
        except ValueError:
            return None
    
    def _calculate_next_recurrence_date(self, recur_pattern, last_date):
        """Calculate the expected next occurrence date for a recurring task"""
        if not recur_pattern or not last_date:
            return None
        
        try:
            last_date_obj = datetime.strptime(last_date, "%d-%m-%Y")
        except ValueError:
            return None
        
        today = datetime.now()
        
        # Handle different recurrence patterns
        if recur_pattern == "daily":
            # Next occurrence is tomorrow after completion
            return last_date_obj + timedelta(days=1)
        elif recur_pattern == "weekdays":
            # Next occurrence is next weekday after completion
            next_date = last_date_obj + timedelta(days=1)
            while next_date.weekday() >= 5:  # Skip weekends
                next_date += timedelta(days=1)
            return next_date
        elif recur_pattern.startswith("weekly"):
            if recur_pattern == "weekly":
                # Default to Sunday
                target_weekday = 6
            else:
                # Parse specific days: weekly:mon,wed,fri
                day_part = recur_pattern.split(":", 1)[1]
                day_map = {
                    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
                    'fri': 4, 'sat': 5, 'sun': 6
                }
                
                if ',' in day_part:
                    # Multiple days - find next occurrence
                    days = [day_map.get(day.strip()) for day in day_part.split(',')]
                    days = [d for d in days if d is not None]
                    if not days:
                        return None
                    # Find the next weekday that matches
                    next_date = last_date_obj + timedelta(days=1)
                    while next_date.weekday() not in days:
                        next_date += timedelta(days=1)
                    return next_date
                else:
                    # Single day
                    target_weekday = day_map.get(day_part.strip())
                    if target_weekday is None:
                        return None
            
            # Calculate next occurrence of target weekday
            days_ahead = target_weekday - last_date_obj.weekday()
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7
            return last_date_obj + timedelta(days=days_ahead)
            
        elif recur_pattern.startswith("monthly"):
            if recur_pattern == "monthly":
                # Default to 1st of month
                target_day = 1
            else:
                # Parse specific day: monthly:15th
                day_part = recur_pattern.split(":", 1)[1]
                if day_part.endswith('th'):
                    target_day = int(day_part[:-2])
                elif day_part.endswith('st'):
                    target_day = int(day_part[:-2])
                elif day_part.endswith('nd'):
                    target_day = int(day_part[:-2])
                elif day_part.endswith('rd'):
                    target_day = int(day_part[:-2])
                else:
                    target_day = int(day_part)
            
            # Calculate next occurrence - always move to next month from completion date
            if last_date_obj.month == 12:
                next_year = last_date_obj.year + 1
                next_month = 1
            else:
                next_year = last_date_obj.year
                next_month = last_date_obj.month + 1
            
            # Handle month-end edge cases
            try:
                return datetime(next_year, next_month, target_day)
            except ValueError:
                # Target day doesn't exist in that month (e.g., Feb 30)
                # Use the last day of the month
                if next_month == 12:
                    next_month = 1
                    next_year += 1
                else:
                    next_month += 1
                return datetime(next_year, next_month, 1) - timedelta(days=1)
                
        elif recur_pattern.startswith("recur:"):
            # Custom recurrence: recur:3d, recur:2w, etc.
            interval_part = recur_pattern.split(":", 1)[1]
            
            # Parse interval
            if interval_part.endswith('d'):
                days = int(interval_part[:-1])
                return last_date_obj + timedelta(days=days)
            elif interval_part.endswith('w'):
                weeks = int(interval_part[:-1])
                return last_date_obj + timedelta(weeks=weeks)
            elif interval_part.endswith('m'):
                months = int(interval_part[:-1])
                # Simple month calculation
                if last_date_obj.month + months > 12:
                    next_year = last_date_obj.year + ((last_date_obj.month + months - 1) // 12)
                    next_month = ((last_date_obj.month + months - 1) % 12) + 1
                else:
                    next_year = last_date_obj.year
                    next_month = last_date_obj.month + months
                
                # Handle month-end edge cases
                try:
                    return datetime(next_year, next_month, last_date_obj.day)
                except ValueError:
                    # Use last day of month
                    return datetime(next_year, next_month, 1) - timedelta(days=1)
            elif interval_part.endswith('y'):
                years = int(interval_part[:-1])
                return last_date_obj.replace(year=last_date_obj.year + years)
        
        return None
    
    def _get_incomplete_daily_instance_date(self, task_id):
        """Check if there's an incomplete instance of a recurring task in daily sections or pass entries in archive"""
        if not task_id:
            return None
        
        content = self.read_file()
        lines = content.split('\n')
        
        in_daily = False
        in_archive = False
        current_daily_date = None
        current_archive_date = None
        
        # Track the most recent activity date from both daily and archive sections
        most_recent_activity_date = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped == '# DAILY':
                in_daily = True
                in_archive = False
                continue
            elif line_stripped == '# ARCHIVE':
                in_daily = False
                in_archive = True
                continue
            elif line_stripped.startswith('# ') and line_stripped not in ['# DAILY', '# ARCHIVE']:
                in_daily = False
                in_archive = False
                continue
            
            if in_daily and line_stripped.startswith('## '):
                current_daily_date = line_stripped[3:].strip()
                continue
            elif in_archive and line_stripped.startswith('## '):
                current_archive_date = line_stripped[3:].strip()
                continue
            
            # Check daily section for incomplete tasks
            if (in_daily and current_daily_date and 
                self._task_id_matches_line(task_id, line) and self._is_task_line(line)):
                task_data = self._parse_task_line(line)
                if task_data and task_data.get('status') in [' ', '~']:  # Incomplete or progress
                    most_recent_activity_date = current_daily_date
            
            # Check archive section for pass entries (progress status)
            elif (in_archive and current_archive_date and 
                  self._task_id_matches_line(task_id, line) and self._is_task_line(line)):
                task_data = self._parse_task_line(line)
                if task_data and task_data.get('status') == '~':  # Pass entries are marked as progress
                    most_recent_activity_date = current_archive_date
        
        return most_recent_activity_date
    
    def show_stale_tasks(self, scope=None, limit=5):
        """Show stale tasks (excluding recurring) with optional scope filtering and limit"""
        content = self.read_file()
        lines = content.split('\n')
        
        tasks_by_status = []
        in_main = False
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                current_section = line[3:].strip()
                continue
            
            if in_main and self._is_task_line(line):
                # Apply scope filtering
                if scope:
                    if ':' in scope:
                        # Subsection scope
                        main_sec, sub_sec = scope.split(':', 1)
                        if current_section != main_sec:
                            continue
                        # Check if this is in the right subsection
                        # This is a simplified check - in reality we'd need to track subsection
                        continue
                    else:
                        # Section scope
                        if current_section != scope.upper():
                            continue
                
                task_data = self._parse_task_line(line)
                if task_data:
                    # Exclude recurring tasks
                    recurring = task_data.get('metadata', {}).get('recurring')
                    if recurring:
                        continue
                    
                    status_type, days_old, date_str = self._get_task_status_info(task_data)
                    
                    if status_type not in ['complete', 'snoozed']:
                        tasks_by_status.append({
                            'line': line,
                            'status_type': status_type,
                            'days_old': days_old,
                            'date_str': date_str,
                            'section': current_section,
                            'task_data': task_data
                        })
        
        # Sort by staleness (oldest first)
        tasks_by_status.sort(key=lambda x: x['days_old'], reverse=True)
        
        # Apply limit
        limited_tasks = tasks_by_status[:limit]
        
        print(f"=== Stale tasks (oldest first, showing {len(limited_tasks)} of {len(tasks_by_status)}) ===")
        
        for task_info in limited_tasks:
            days_old = task_info['days_old']
            status_type = task_info['status_type']
            section = task_info['section']
            task_data = task_info['task_data']
            
            # Color coding based on staleness
            if days_old >= 7:
                color = "🔴"  # Red for very stale
            elif days_old >= 3:
                color = "🟡"  # Yellow for stale
            else:
                color = "🟢"  # Green for recent
            
            # Create a Task object for consistent formatting
            task = Task(
                id=task_data['metadata'].get('id', '???'),
                text=task_data['text'],
                status=task_data['status'],
                date=task_data['metadata'].get('date'),
                recurring=task_data['metadata'].get('recurring')
            )
            
            print(self._format_for_status_display(task, days_old, section))
    
    def show_age_tasks(self, scope=None, limit=5):
        """Show tasks by age (excluding recurring) with optional scope filtering and limit"""
        content = self.read_file()
        lines = content.split('\n')
        
        tasks_by_age = []
        in_main = False
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                current_section = line[3:].strip()
                continue
            
            if in_main and self._is_task_line(line):
                # Apply scope filtering
                if scope:
                    if ':' in scope:
                        # Subsection scope
                        main_sec, sub_sec = scope.split(':', 1)
                        if current_section != main_sec:
                            continue
                        # Check if this is in the right subsection
                        # This is a simplified check - in reality we'd need to track subsection
                        continue
                    else:
                        # Section scope
                        if current_section != scope.upper():
                            continue
                
                task_data = self._parse_task_line(line)
                if task_data:
                    # Exclude recurring tasks
                    recurring = task_data.get('metadata', {}).get('recurring')
                    if recurring:
                        continue
                    
                    # Calculate age based on task creation/appearance date
                    days_old = self._calculate_task_age(task_data)
                    
                    if days_old is not None:
                        tasks_by_age.append({
                            'line': line,
                            'days_old': days_old,
                            'section': current_section,
                            'task_data': task_data
                        })
        
        # Sort by age (oldest first)
        tasks_by_age.sort(key=lambda x: x['days_old'], reverse=True)
        
        # Apply limit
        limited_tasks = tasks_by_age[:limit]
        
        print(f"=== Tasks by age (oldest first, showing {len(limited_tasks)} of {len(tasks_by_age)}) ===")
        
        for task_info in limited_tasks:
            days_old = task_info['days_old']
            section = task_info['section']
            task_data = task_info['task_data']
            
            # Color coding based on age
            if days_old >= 30:
                color = "🔴"  # Red for very old
            elif days_old >= 14:
                color = "🟡"  # Yellow for old
            else:
                color = "🟢"  # Green for recent
            
            # Create a Task object for consistent formatting
            task = Task(
                id=task_data['metadata'].get('id', '???'),
                text=task_data['text'],
                status=task_data['status'],
                date=task_data['metadata'].get('date'),
                recurring=task_data['metadata'].get('recurring')
            )
            
            print(self._format_for_status_display(task, days_old, section))
    
    def show_task(self, task_id):
        """Show details of a specific task"""
        line_number, line_content = self.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        # Parse the task line to create a Task object for consistent formatting
        task = Task.from_markdown(line_content)
        if task:
            print(self._format_for_task_details(task, line_number))
        else:
            print(f"Task #{task_id}:")
            print(f"  {line_content}")
            print(f"  Line: {line_number}")
    
    def show_task_from_main(self, task_id):
        """Show details of a specific task from main section only"""
        line_number, line_content = self.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found in main section")
            return
        
        # Parse the task line to create a Task object for consistent formatting
        task = Task.from_markdown(line_content)
        if task:
            print(self._format_for_task_details(task, line_number))
        else:
            print(f"Task #{task_id}:")
            print(f"  {line_content}")
            print(f"  Line: {line_number}")
    
    def list_sections(self):
        """List all available sections"""
        content = self.read_file()
        lines = content.split('\n')
        
        sections = []
        in_main = False
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                section_name = line[3:].strip()
                sections.append(section_name)
        
        if sections:
            for section in sections:
                print(f"  {section}")
        else:
            print("No sections found")
    
    def show_config(self):
        """Show current configuration"""
        print("Current Configuration:")
        print(f"  Task file: {self.config.task_file}")
        print(f"  Editor: {self.config.editor}")
        print(f"  Config file: ~/.ptconfig")
    
    def show_help(self):
        """Show help information"""
        help_text = """Daily Task Management System

USAGE:
  tasks [command] [args]

COMMANDS:
  help                   Show this help message
  config                 Show current configuration
  init                   Initialize the task file with default structure
  daily                  Add today's daily section with recurring tasks and carry over all incomplete tasks from previous day
                         Daily entries preserve main task activity dates, section headers show appearance dates
  day                    Alias for daily
  stale [SCOPE] [N]      Show stale tasks (oldest first, excludes recurring tasks)
                         SCOPE can be section (e.g., 'projects') or section:subsection (e.g., 'areas:work')
                         N is number of tasks to show (default: 5)
  age [SCOPE] [N]        Show tasks by age (oldest first, excludes recurring tasks)
                         SCOPE can be section (e.g., 'projects') or section:subsection (e.g., 'areas:work')
                         N is number of tasks to show (default: 5)
  status [SCOPE] [N]     Alias for stale (backward compatibility)                                                     
  
  done ID                Mark task with ID as complete
  undone ID              Reopen completed task (mark as incomplete)
  pass ID                Mark task as progressed [~] in today's daily section
  pass ID N              Create pass entry N days ago in archive section (reduces days since activity)
  sync                   Update main list from completed daily items
                         [x] in daily = complete main task (recurring tasks stay incomplete)
                         [~] in daily = update date but keep incomplete
                         Both daily and main entries get current date when activity occurs
  
  add TEXT [SEC]         Add task to main list section (default: TASKS)
                         Use SEC:SUBSEC for subsections (e.g., WORK:OFFICE)
  up ID                  Pull task from main list into today's daily section
                         Preserves main task's activity date in daily entry
  
  snooze ID DAYS         Hide task for N days (e.g., snooze 042 5)
  snooze ID DATE         Hide task until date (e.g., snooze 042 25-12-2025)
  recur ID PATTERN       Modify task recurrence pattern (e.g., recur 042 daily)
  
  list                   List all tasks from main sections
  list SECTION[:SUBSEC]   List tasks in a specific section (e.g., list PROJECTS:HOME)                                                                           
  show ID                Show details of specific task from main section
  show SECTION[:SUBSEC]   Show tasks in a specific section (e.g., show PROJECTS:HOME)                                                                           
  show *:SUBSEC          Show tasks from all sections with matching subsection (e.g., show *:justculture)                                                       
  sections               List all available sections
  
  edit ID TEXT           Edit task text by ID
  move ID SECTION        Move task to new section (e.g., move 001 PROJECTS:HOME)
  open [EDITOR]          Open tasks file with editor (default: from config)
  
  delete ID              Delete task from main list only
  down ID                 Remove task from today's daily section (return to main)                                                                               
  purge ID               Delete task from main list and all daily sections

EXAMPLES:
  tasks init                              # Initialize task file (first time setup)                                                                             
  tasks daily                              # Start your day (creates or shows daily section)                                                                    
  tasks add "write blog post" WORK         # Add task to specific section
  tasks add "fix faucet" HOME:MAINTENANCE  # Add to subsection
  tasks up 042                            # Pull task #042 to today's daily section                                                                             
  tasks done 042                           # Mark task done
  tasks show *:justculture                # Show all tasks from subsections named 'justculture'
  tasks undone 042                         # Reopen completed task
  tasks list                               # List all tasks from main sections
  tasks list PROJECTS:CLIENT               # List tasks in PROJECTS > CLIENT subsection                                                                           
  tasks show 001                           # Show details of task #001
  tasks pass 042                           # Mark progress on task in daily section
  tasks pass 001 4                         # Create pass entry 4 days ago (reduces urgency)                                                                             
  tasks snooze 023 7                       # Hide task for a week
  tasks recur 042 daily                    # Set task to recur daily
  tasks stale                             # See what needs attention (shows 5 stale tasks)
  tasks stale 10                          # See 10 most stale tasks
  tasks stale projects                    # See stale tasks in PROJECTS section (5 tasks)
  tasks stale projects 3                   # See 3 most stale tasks in PROJECTS section
  tasks stale areas:health                # See stale tasks in AREAS > HEALTH subsection
  tasks age                               # See oldest tasks (shows 5 tasks)
  tasks age 10                            # See 10 oldest tasks
  tasks age projects                      # See oldest tasks in PROJECTS section
  tasks status                            # Alias for stale (backward compatibility)                                                                         
  tasks sync                               # Update main list from daily work
  tasks edit 042 "new task text"           # Edit task text
  tasks move 042 PROJECTS:CLIENT           # Move task to subsection
  tasks open                               # Open tasks file with configured editor                                                                             
  tasks open vim                           # Open tasks file with vim (override config)                                                                         
  tasks open code                          # Open tasks file with VS Code (override config)                                                                     
  tasks delete 042                         # Remove task from main list
  tasks down 042                           # Remove task from today's daily section                                                                             
  tasks purge 042                          # Remove task from everywhere

WORKFLOW:
  1. Morning:   tasks daily
  2. Work:      Check daily section, mark tasks:
                [x] = completed, [~] = made progress but not done
  3. Evening:   tasks sync (updates main list)
  4. Planning:  tasks stale (see neglected tasks)

TASK SYNTAX:
  - [ ] incomplete task | @15-01-2025 #001
  - [x] completed task | @15-01-2025 #002
  - [ ] recurring task | @15-01-2025 (daily) #003
  - [ ] snoozed task | @15-01-2025 snooze:20-01-2025 #004

DAILY SECTION PROGRESS:
  [x] = Task completed (will mark main task complete when synced)
  [~] = Made progress (will update main task date but keep incomplete)

DATE BEHAVIOR:
  - Task dates represent last activity date (or creation date if no activity)
  - Daily section headers show appearance date (when task first appeared)
  - Daily task entries preserve main task's activity date
  - When activity occurs (done/pass), both daily and main entries update to current date
  - Tasks remain in same appearance date section until archived

RECURRING PATTERNS:
  (daily)              Every day
  (weekdays)           Monday-Friday
  (weekly)             Every Sunday (default)
  (weekly:tue)         Every Tuesday
  (weekly:mon,wed,fri) Multiple days per week
  (monthly)            1st of month (default)
  (monthly:15th)       15th of every month
  (recur:3d)           Every 3 days
  (recur:2w)           Every 2 weeks
  (recur:6m)           Every 6 months
  (recur:1y)           Every year
  (recur:1y,3m)        Every 1 year and 3 months

DAY ABBREVIATIONS:
  mon=Monday, tue=Tuesday, wed=Wednesday, thu=Thursday,
  fri=Friday, sat=Saturday, sun=Sunday

CONFIGURATION:
  Configuration file: ~/.ptconfig (or set PTCONFIG env var)
  
  Settings:
  [general]
  task_file = ~/home/0-inbox/tasks.md
  editor = nvim
  
  Editor options:
  - nvim, vim, nano, code, subl, atom, or any command-line editor
  - Use 'tasks config' to see current settings

FILE STRUCTURE:
  # DAILY
  ## 15-01-2025
  
  # MAIN
  
  # ARCHIVE

"""
        
        print(help_text)
    
    def show_daily_list(self):
        """Show today's daily tasks"""
        task_file = self.parse_file()
        
        if self.today not in task_file.daily_sections:
            print(f"No daily section for {self.today}")
            return
        
        tasks = task_file.daily_sections[self.today]
        
        print(f"=== Daily Tasks for {self.today} ===")
        
        if not tasks:
            print("No tasks for today")
            return
        
        for task in tasks:
            print(task.to_markdown())
    
    def show_section(self, section_name):
        """Show tasks in a specific section"""
        content = self.read_file()
        lines = content.split('\n')
        
        if section_name == "*":
            # Show all sections
            self.show_all_main()
            return
        
        if ':' in section_name:
            # Subsection
            main_section, subsection = section_name.split(':', 1)
            self._show_subsection(main_section.upper(), subsection, lines)
        elif section_name == "*":
            # Wildcard - show all sections
            self.show_all_main()
        else:
            # Main section - convert to uppercase for case-insensitive matching
            self._show_main_section(section_name.upper(), lines)
    
    def _show_main_section(self, section_name, lines):
        """Show tasks in a main section"""
        in_main = False
        current_section = None
        tasks_found = False
        
        print(f"=== {section_name} ===")
        print()
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                current_section = line[3:].strip()
                continue
            
            if in_main and current_section == section_name and self._is_task_line(line):
                # Parse the task line to create a Task object for consistent formatting
                task = Task.from_markdown(line)
                if task:
                    print(f"  {task.to_markdown()}")
                    tasks_found = True
        
        if not tasks_found:
            print("No tasks found in this section")
    
    def _show_subsection(self, main_section, subsection, lines):
        """Show tasks in a subsection"""
        in_main = False
        current_section = None
        current_subsection = None
        tasks_found = False
        
        print(f"=== {main_section} > {subsection} ===")
        print()
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                current_section = line[3:].strip()
                current_subsection = None
                continue
            elif in_main and line.startswith('### '):
                current_subsection = line[4:].strip()
                continue
            
            if (in_main and current_section == main_section and 
                current_subsection and current_subsection.lower() == subsection.lower() and self._is_task_line(line)):
                # Parse the task line to create a Task object for consistent formatting
                task = Task.from_markdown(line)
                if task:
                    print(f"  {task.to_markdown()}")
                    tasks_found = True
        
        if not tasks_found:
            print("No tasks found in this subsection")
    
    def show_all_main(self):
        """Show all tasks from main sections"""
        content = self.read_file()
        lines = content.split('\n')
        
        in_main = False
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line == '# MAIN':
                in_main = True
                continue
            elif line.startswith('# ') and line != '# MAIN':
                in_main = False
                continue
            
            if in_main and line.startswith('## '):
                current_section = line[3:].strip()
                print(f"\n=== {current_section} ===")
                continue
            elif in_main and line.startswith('### '):
                subsection = line[4:].strip()
                print(f"\n--- {subsection} ---")
                continue
            
            if in_main and self._is_task_line(line):
                # Parse the task line to create a Task object for consistent formatting
                task = Task.from_markdown(line)
                if task:
                    print(f"  {task.to_markdown()}")
    
    # ============================================================================
    # TASK FORMATTING METHODS
    # ============================================================================
    
    def _format_for_status_display(self, task, days_old, section):
        """Format task for status/staleness display"""
        # Color coding based on staleness
        if days_old >= 7:
            color = "🔴"  # Red for very stale
        elif days_old >= 3:
            color = "🟡"  # Yellow for stale
        else:
            color = "🟢"  # Green for recent
        
        task_id = task.id or "???"
        return f"{color} {days_old:2d} days | #{task_id} | {task.text} | {section}"
    
    def _format_for_task_details(self, task, line_number=None):
        """Format task for detailed display (multi-line format)"""
        lines = []
        lines.append(f"Task #{task.id}:")
        lines.append(f"  {task.to_markdown()}")
        
        if line_number is not None:
            lines.append(f"  Line: {line_number}")
        
        lines.append(f"  Status: {task.status}")
        lines.append(f"  Text: {task.text}")
        
        if task.date:
            lines.append(f"  Date: {task.date}")
        
        # Always show recurring field for clarity
        if task.recurring:
            lines.append(f"  Recurring: {task.recurring}")
        else:
            lines.append(f"  Recurring: None")
        # Snoozing is now handled by setting date to future
        if task.date:
            try:
                task_date = datetime.strptime(task.date, "%d-%m-%Y")
                today = datetime.now()
                if task_date > today:
                    lines.append(f"  Snoozed until: {task.date}")
            except ValueError:
                pass
        
        return "\n".join(lines)
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def init(self):
        """Initialize the task file with default structure if it doesn't exist."""
        if not self.task_file.exists():
            default_content = "# DAILY\n\n# MAIN\n\n# ARCHIVE\n\n"
            self.task_file.write_text(default_content)
            print(f"Created new task file at {self.task_file}")
        else:
            print(f"Task file already exists at {self.task_file}")
    
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


# Backward compatibility alias
TaskManager = Paratrooper
