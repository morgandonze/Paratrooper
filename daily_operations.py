#!/usr/bin/env python3
"""
Daily section operations for the Paratrooper system.

This module handles all operations related to daily sections,
recurring tasks, and synchronization between daily and main sections.
"""

import re
from datetime import datetime, timedelta

from models import Task, TaskFile, TODAY, TASK_ID_PATTERN, RECURRING_PATTERN
from file_operations import FileOperations


class DailyOperations:
    """Handles all operations related to daily sections and recurring tasks."""
    
    def __init__(self, file_ops: FileOperations, config=None):
        self.file_ops = file_ops
        self.config = config
        self.today = TODAY
    
    def _get_most_recent_daily_date(self, content=None):
        """Get the most recent daily section date"""
        if content is None:
            content = self.file_ops.read_file()
        
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
    
    def should_recur_today(self, recur_pattern, last_date_str):
        """Check if a recurring task should appear today"""
        if not recur_pattern:
            return False
        
        try:
            last_date = datetime.strptime(last_date_str, "%d-%m-%Y")
        except ValueError:
            return False
        
        today = datetime.now()
        
        # Handle different recurrence patterns
        if recur_pattern == "daily":
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
                else:
                    day_num = int(day_part)
                    return today.day == day_num
        elif recur_pattern.startswith("recur:"):
            # Custom recurrence: recur:3d, recur:2w, etc.
            interval_part = recur_pattern.split(":", 1)[1]
            
            # Parse interval
            if interval_part.endswith('d'):
                days = int(interval_part[:-1])
                days_since = (today - last_date).days
                return days_since >= days
            elif interval_part.endswith('w'):
                weeks = int(interval_part[:-1])
                days_since = (today - last_date).days
                return days_since >= (weeks * 7)
            elif interval_part.endswith('m'):
                months = int(interval_part[:-1])
                # Simple month calculation
                months_since = (today.year - last_date.year) * 12 + (today.month - last_date.month)
                return months_since >= months
            elif interval_part.endswith('y'):
                years = int(interval_part[:-1])
                years_since = today.year - last_date.year
                return years_since >= years
        
        return False
    
    def get_recurring_tasks(self):
        """Get all recurring tasks that should appear today"""
        task_file = self.file_ops.parse_file()
        recurring_tasks = []
        
        for section_name, section in task_file.main_sections.items():
            for task in section.tasks:
                if task.recurring and self.should_recur_today(task.recurring.strip('()'), task.date or self.today):
                    recurring_tasks.append({
                        'id': task.id,
                        'text': task.text,
                        'section': section_name,
                        'recurring': task.recurring
                    })
            
            # Check subsections
            for subsection_name, subsection in section.subsections.items():
                for task in subsection.tasks:
                    if task.recurring and self.should_recur_today(task.recurring.strip('()'), task.date or self.today):
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
        task_file = self.file_ops.parse_file()
        
        # Check if today's section already exists
        if self.today in task_file.daily_sections:
            # Instead of just printing an error, show the daily list
            return "show_daily_list"
        
        # Get recurring tasks for today
        recurring_tasks = self.get_recurring_tasks()
        
        # Get unfinished tasks from previous day (if carry-over is enabled)
        unfinished_tasks = []
        if self.config and self.config.carry_over_enabled:
            most_recent_result = self.get_most_recent_daily_section(task_file)
            if most_recent_result:
                most_recent_date, most_recent_tasks = most_recent_result
                if most_recent_date and most_recent_date != self.today:
                    unfinished_tasks = self.get_unfinished_tasks_from_daily(most_recent_tasks)
        
        # Create today's daily section
        today_tasks = []
        
        # Get IDs of unfinished tasks to avoid duplication
        unfinished_task_ids = {task.id for task in unfinished_tasks}
        
        # Add recurring tasks (skip if already being carried over)
        for recurring_task in recurring_tasks:
            if recurring_task['id'] not in unfinished_task_ids:
                task_text = recurring_task['text']  # No need for "from" text anymore
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
                today_tasks.append(task)
        
        # Add unfinished tasks from previous day
        for unfinished_task in unfinished_tasks:
            # Reset status to incomplete for carry-over
            task = Task(
                id=unfinished_task.id,
                text=unfinished_task.text,
                status=" ",
                date=self.today,
                recurring=unfinished_task.recurring,
                # Snooze and due functionality removed - use future dates instead
                section=unfinished_task.section,
                subsection=unfinished_task.subsection,
                is_daily=True,
                from_section=unfinished_task.from_section
            )
            today_tasks.append(task)
        
        # Add tasks to today's section
        task_file.daily_sections[self.today] = today_tasks
        
        # Write back to file
        self.file_ops.write_file_from_objects(task_file)
        
        # Reorganize daily sections (move old ones to archive) AFTER carry-over is complete
        task_file.reorganize_daily_sections()
        self.file_ops.write_file_from_objects(task_file)
        
        if recurring_tasks:
            print(f"Daily section for {self.today} updated with {len(recurring_tasks)} new recurring tasks")
        else:
            print(f"Daily section for {self.today} is empty")
        
        if unfinished_tasks:
            print(f"Carried over {len(unfinished_tasks)} unfinished tasks from previous day")
    
    def add_task_to_daily(self, task_text):
        """Add a task directly to today's daily section"""
        task_file = self.file_ops.parse_file()
        
        # Ensure today's section exists
        if self.today not in task_file.daily_sections:
            task_file.daily_sections[self.today] = []
        
        # Get next ID
        content = self.file_ops.read_file()
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
        self.file_ops.write_file_from_objects(task_file)
        
        print(f"Added task #{task_id} to today's section: {task_text}")
    
    def add_task_to_daily_by_id(self, task_id):
        """Pull a task from main list into today's daily section"""
        # Find the task in main section
        content = self.file_ops.read_file()
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
            
            if in_main and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                task_line = line
                task_section = current_section.upper() if current_section else None
                break
        
        if not task_line:
            print(f"Task #{task_id} not found in main section")
            return
        
        # Parse the task
        task_data = self.file_ops._parse_task_line(task_line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Create task for daily section (no need for "from" text anymore)
        task_text = task_data['text']
        task = Task(
            id=task_id,
            text=task_text,
            status=" ",
            date=self.today,
            recurring=task_data['metadata'].get('recurring'),
            # Snooze and due functionality removed
            section=task_section,
            is_daily=True,
            from_section=task_section
        )
        
        # Add to today's daily section
        task_file = self.file_ops.parse_file()
        
        # Ensure today's section exists
        if self.today not in task_file.daily_sections:
            task_file.daily_sections[self.today] = []
        
        # Add to top of today's section
        task_file.daily_sections[self.today].insert(0, task)
        
        # Write back to file
        self.file_ops.write_file_from_objects(task_file)
        
        print(f"Pulled task #{task_id} to today's section: {task_data['text']}")
    
    def progress_task_in_daily(self, task_id):
        """Mark a task as progressed in today's daily section"""
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        in_daily = False
        current_daily_date = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line == '# DAILY':
                in_daily = True
                continue
            elif line.startswith('# ') and line != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and line.startswith('## '):
                current_daily_date = line[3:].strip()
                continue
            
            if in_daily and current_daily_date and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                # Mark as progressed
                updated_line = self.file_ops._mark_task_progress(line)
                lines[i] = updated_line
                self.file_ops.write_file('\n'.join(lines))
                print(f"Marked progress on task #{task_id} in today's daily section")
                return
        
        print(f"Task #{task_id} not found in today's daily section")
    
    def delete_task_from_daily(self, task_id):
        """Remove a task from today's daily section"""
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        in_daily = False
        current_daily_date = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if line == '# DAILY':
                in_daily = True
                continue
            elif line.startswith('# ') and line != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and line.startswith('## '):
                current_daily_date = line[3:].strip()
                continue
            
            if in_daily and current_daily_date and f"#{task_id}" in line and self.file_ops._is_task_line(line):
                # Remove the line
                lines.pop(i)
                self.file_ops.write_file('\n'.join(lines))
                print(f"Removed task #{task_id} from today's daily section")
                return
        
        print(f"Task #{task_id} not found in today's daily section")
    
    def sync_daily_sections(self, days_back=3):
        """Sync daily sections back to main list"""
        task_file = self.file_ops.parse_file()
        
        if not task_file.daily_sections:
            print("No daily sections to sync")
            return
        
        # Get the most recent daily section
        most_recent_date, most_recent_tasks = self.get_most_recent_daily_section(task_file)
        if not most_recent_tasks:
            print("No tasks in daily section to sync")
            return
        
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        completed_count = 0
        progressed_count = 0
        
        # Process each task in the daily section
        for task in most_recent_tasks:
            if task.status == 'x':  # Completed
                # Find the corresponding task in main section
                for i, line in enumerate(lines):
                    if f"#{task.id}" in line and self.file_ops._is_task_line(line):
                        # Check if it's a recurring task
                        if task.recurring:
                            # For recurring tasks, just update the date
                            updated_line = self.file_ops._update_task_date(line)
                        else:
                            # For non-recurring tasks, mark as complete
                            updated_line = self.file_ops._mark_task_complete(line)
                            updated_line = self.file_ops._update_task_date(updated_line)
                        
                        lines[i] = updated_line
                        completed_count += 1
                        break
            
            elif task.status == '~':  # Progress
                # Find the corresponding task in main section
                for i, line in enumerate(lines):
                    if f"#{task.id}" in line and self.file_ops._is_task_line(line):
                        # Update the date to show recent engagement
                        updated_line = self.file_ops._update_task_date(line)
                        lines[i] = updated_line
                        progressed_count += 1
                        break
        
        # Write back to file
        self.file_ops.write_file('\n'.join(lines))
        
        if completed_count > 0 or progressed_count > 0:
            print(f"Synced {completed_count} completed and {progressed_count} progressed tasks from daily section")
        else:
            print("No changes needed")
