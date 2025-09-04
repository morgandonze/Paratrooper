#!/usr/bin/env python3
"""
Task management scripts for PARA + Daily system with hierarchical sections
Usage: python tasks.py [command] [args]
"""

import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
TASK_FILE = Path.home() / "home" / "tasks.txt"
TODAY = datetime.now().strftime("%d-%m-%Y")

class TaskManager:
    def __init__(self):
        self.task_file = TASK_FILE
        self.today = TODAY
        
    def read_file(self):
        """Read the task file, create if doesn't exist"""
        if not self.task_file.exists():
            self.task_file.touch()
            default_content = """# DAILY

# MAIN

## INBOX

## PROJECTS

## AREAS

## RESOURCES

## ZETTELKASTEN

# ARCHIVE

"""
            self.task_file.write_text(default_content)
        return self.task_file.read_text()
    
    def write_file(self, content):
        """Write content back to task file"""
        self.task_file.write_text(content)
    
    def find_section(self, section_name, level=1):
        """Find a section by name and return its content until next section of same level"""
        content = self.read_file()
        lines = content.split('\n')
        
        section_pattern = f"{'#' * level} {section_name.upper()}"
        next_section_pattern = f"{'#' * level} "
        
        section_lines = []
        in_section = False
        
        for line in lines:
            if line.strip() == section_pattern:
                in_section = True
                section_lines.append(line)
                continue
            
            if in_section:
                # Stop if we hit another section of the same level
                if line.startswith(next_section_pattern) and line.strip() != section_pattern:
                    break
                section_lines.append(line)
        
        return section_lines if in_section else None
    
    def get_next_id(self):
        """Get the next available ID by finding the highest existing ID"""
        content = self.read_file()
        
        # Find all existing IDs
        id_matches = re.findall(r'#(\d{3})', content)
        if not id_matches:
            return "001"
        
        highest_id = max(int(id_str) for id_str in id_matches)
        return f"{highest_id + 1:03d}"
    
    def find_task_by_id(self, task_id):
        """Find a task by its ID, return (line_number, line_content) or None"""
        content = self.read_file()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and re.match(r'- \[.\] ', line):
                return (i, line)
        return None
    
    def should_recur_today(self, recur_pattern, last_date_str):
        """Check if a recurring task should appear today"""
        today_obj = datetime.strptime(self.today, "%d-%m-%Y")
        
        if recur_pattern == "daily":
            return True
        elif recur_pattern == "weekdays":
            return today_obj.weekday() < 5  # Monday=0, Friday=4
        elif recur_pattern.startswith("weekly"):
            if ":" in recur_pattern:
                days_part = recur_pattern.split(":")[1]
                day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
                
                # Handle multiple days: weekly:mon,wed,fri
                if "," in days_part:
                    target_days = []
                    for day_abbr in days_part.split(","):
                        target_day = day_map.get(day_abbr.strip().lower())
                        if target_day is not None:
                            target_days.append(target_day)
                    return today_obj.weekday() in target_days
                else:
                    # Single day: weekly:tue
                    target_day = day_map.get(days_part.lower())
                    return today_obj.weekday() == target_day if target_day is not None else False
            else:
                # Default weekly to Sunday
                return today_obj.weekday() == 6
        elif recur_pattern.startswith("monthly"):
            if ":" in recur_pattern:
                day_part = recur_pattern.split(":")[1]
                if day_part.endswith("st") or day_part.endswith("nd") or day_part.endswith("rd") or day_part.endswith("th"):
                    target_day = int(day_part[:-2])
                else:
                    target_day = int(day_part)
                return today_obj.day == target_day
            else:
                # Default monthly to 1st
                return today_obj.day == 1
        elif recur_pattern.startswith("recur:"):
            # Handle general recurrence patterns like recur:2d, recur:1w, recur:1y,3m
            try:
                last_date = datetime.strptime(last_date_str, "%d-%m-%Y")
                intervals_part = recur_pattern[6:]  # Remove "recur:"
                
                # Handle multiple intervals: 1y,3m
                intervals = intervals_part.split(",")
                total_days = 0
                
                for interval in intervals:
                    interval = interval.strip()
                    if interval.endswith('d'):
                        total_days += int(interval[:-1])
                    elif interval.endswith('w'):
                        total_days += int(interval[:-1]) * 7
                    elif interval.endswith('m'):
                        total_days += int(interval[:-1]) * 30  # Approximate
                    elif interval.endswith('y'):
                        total_days += int(interval[:-1]) * 365  # Approximate
                
                days_since = (today_obj - last_date).days
                return days_since >= total_days
            except (ValueError, IndexError):
                return False
        
        return False
    
    def get_recurring_tasks(self):
        """Find all recurring tasks from MAIN section"""
        main_lines = self.find_section("MAIN", level=1)
        if not main_lines:
            return []
        
        recurring_tasks = []
        current_subsection = None
        current_project = None
        
        for line in main_lines:
            if line.startswith("## "):
                current_subsection = line[3:].strip()  # Remove "## "
                current_project = None
            elif line.startswith("### "):
                current_project = line[4:].strip()  # Remove "### "
            elif re.match(r'- \[ \] .* \([^)]*\)', line):
                # Check for recurring pattern
                recur_match = re.search(r'\(([^)]+)\)', line)
                if recur_match:
                    recur_pattern = recur_match.group(1)
                    if recur_pattern not in ["snooze"] and (
                        any(keyword in recur_pattern for keyword in ["daily", "weekly", "monthly"]) or 
                        recur_pattern.startswith("recur:")
                    ):
                        # Extract task info
                        task_match = re.match(r'- \[ \] ([^@#]+)', line)
                        id_match = re.search(r'#(\d{3})', line)
                        
                        if task_match and id_match and current_subsection:
                            task_text = task_match.group(1).strip()
                            task_id = id_match.group(1)
                            date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', line)
                            last_date = date_match.group(1) if date_match else self.today
                            
                            # Build section reference
                            if current_project:
                                section_ref = f"{current_subsection} > {current_project}"
                            else:
                                section_ref = current_subsection
                            
                            if self.should_recur_today(recur_pattern, last_date):
                                recurring_tasks.append({
                                    'text': task_text,
                                    'section': section_ref,
                                    'id': task_id
                                })
        
        return recurring_tasks
    
    def add_daily_section(self):
        """Add today's daily section with recurring tasks"""
        content = self.read_file()
        
        if f"## {self.today}" in content:
            print(f"Daily section for {self.today} already exists")
            return
        
        # Find recurring tasks
        recurring_tasks = self.get_recurring_tasks()
        
        # Build today's section
        daily_section = f"\n## {self.today}\n"
        for task in recurring_tasks:
            daily_section += f"- [ ] {task['text']} (from: {task['section']}) #{task['id']}\n"
        daily_section += "\n"
        
        # Insert into DAILY section
        daily_pattern = r"(# DAILY\n)"
        replacement = f"\\1{daily_section}"
        
        new_content = re.sub(daily_pattern, replacement, content)
        self.write_file(new_content)
        print(f"Added daily section for {self.today} with {len(recurring_tasks)} recurring tasks")
    
    def show_stale_tasks(self):
        """Show tasks ordered by staleness, excluding future-snoozed tasks"""
        content = self.read_file()
        today_obj = datetime.strptime(self.today, "%d-%m-%Y")
        
        # Only look in MAIN section for stale tasks
        main_lines = self.find_section("MAIN", level=1)
        if not main_lines:
            print("No MAIN section found")
            return
        
        task_pattern = r"^(- \[ \] .*)(@\d{2}-\d{2}-\d{4}).*#(\d{3})"
        tasks = []
        
        for line_num, line in enumerate(main_lines):
            match = re.search(task_pattern, line)
            if match:
                task_text = match.group(1)
                date_str = match.group(2)[1:]  # Remove @
                task_id = match.group(3)
                
                # Check if task is snoozed in the future
                snooze_match = re.search(r'snooze:(\d{2}-\d{2}-\d{4})', line)
                if snooze_match:
                    snooze_date = datetime.strptime(snooze_match.group(1), "%d-%m-%Y")
                    if snooze_date > today_obj:
                        continue  # Skip future-snoozed tasks
                
                try:
                    task_date = datetime.strptime(date_str, "%d-%m-%Y")
                    days_ago = (datetime.now() - task_date).days
                    clean_text = task_text.replace("- [ ] ", "").strip()
                    tasks.append((days_ago, date_str, clean_text, task_id))
                except ValueError:
                    continue
        
        # Sort by days ago (descending = oldest first)
        tasks.sort(key=lambda x: x[0], reverse=True)
        
        print("=== Tasks by staleness (oldest first) ===")
        for days_ago, date_str, task_text, task_id in tasks[:15]:
            status = "🔴" if days_ago > 7 else "🟡" if days_ago > 3 else "🟢"
            print(f"{status} {days_ago:2d} days | #{task_id} | {task_text}")
    
    def complete_task(self, task_id):
        """Mark a task as complete by ID and update its date"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Check if it's recurring
        if re.search(r'\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)', line):
            # Recurring task - just update date, keep [ ]
            new_line = re.sub(r'@\d{2}-\d{2}-\d{4}', f'@{self.today}', line)
        else:
            # Non-recurring task - mark complete and update date
            new_line = line.replace('- [ ]', '- [x]')
            new_line = re.sub(r'@\d{2}-\d{2}-\d{4}', f'@{self.today}', new_line)
        
        lines[line_num] = new_line
        self.write_file('\n'.join(lines))
        print(f"Completed task #{task_id}")
    
    def sync_daily_sections(self, days_back=3):
        """Sync completed items from recent daily sections to master list"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Find completed daily tasks with IDs (only in DAILY section)
        daily_lines = self.find_section("DAILY", level=1)
        if not daily_lines:
            print("No DAILY section found")
            return
        
        completed_daily_ids = []
        progressed_daily_ids = []
        
        for line in daily_lines:
            if re.match(r'- \[x\] .*#(\d{3})', line):
                id_match = re.search(r'#(\d{3})', line)
                if id_match:
                    completed_daily_ids.append(id_match.group(1))
            elif re.match(r'- \[~\] .*#(\d{3})', line):
                id_match = re.search(r'#(\d{3})', line)
                if id_match:
                    progressed_daily_ids.append(id_match.group(1))
        
        # Update corresponding master list tasks by ID
        updates_made = 0
        
        # Handle completed tasks
        for task_id in completed_daily_ids:
            result = self.find_task_by_id(task_id)
            if result:
                line_num, line = result
                if re.match(r'- \[ \] ', line):  # Only update if not already complete
                    # Check if recurring - if so, just update date
                    if re.search(r'\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)', line):
                        lines[line_num] = re.sub(r'@\d{2}-\d{2}-\d{4}', f'@{self.today}', line)
                    else:
                        # Non-recurring - mark complete
                        lines[line_num] = line.replace('- [ ]', '- [x]')
                        lines[line_num] = re.sub(r'@\d{2}-\d{2}-\d{4}', f'@{self.today}', lines[line_num])
                    
                    updates_made += 1
        
        # Handle progressed tasks (just update date, don't complete)
        for task_id in progressed_daily_ids:
            result = self.find_task_by_id(task_id)
            if result:
                line_num, line = result
                if re.match(r'- \[ \] ', line):  # Only update incomplete tasks
                    # Just update date, keep as incomplete
                    lines[line_num] = re.sub(r'@\d{2}-\d{2}-\d{4}', f'@{self.today}', line)
                    updates_made += 1
        
        if updates_made > 0:
            self.write_file('\n'.join(lines))
            completed_count = len([id for id in completed_daily_ids if self.find_task_by_id(id)])
            progressed_count = len([id for id in progressed_daily_ids if self.find_task_by_id(id)])
            print(f"Synced {completed_count} completed and {progressed_count} progressed tasks from daily sections")
        else:
            print("No completed or progressed daily tasks found to sync")
    
    def add_task_to_main(self, task_text, section="INBOX"):
        """Add a new task to main list section or subsection"""
        content = self.read_file()
        task_id = self.get_next_id()
        
        # Parse section:subsection format
        if ":" in section:
            main_section, subsection = section.split(":", 1)
            main_section = main_section.upper()
            subsection = subsection.upper()
        else:
            main_section = section.upper()
            subsection = None
        
        new_task = f"- [ ] {task_text} @{self.today} #{task_id}\n"
        
        if subsection:
            # Add to specific subsection under main section
            lines = content.split('\n')
            updated = False
            in_main_section = False
            subsection_found = False
            
            for i, line in enumerate(lines):
                # Check if we're entering the target main section
                if line.strip() == f"## {main_section}":
                    in_main_section = True
                    continue
                
                # If we're in the main section
                if in_main_section:
                    # Stop if we hit another main section or higher level
                    if line.startswith("## ") or line.startswith("# "):
                        # If we never found the subsection, create it here
                        if not subsection_found:
                            lines.insert(i, f"### {subsection}")
                            lines.insert(i + 1, new_task)
                            lines.insert(i + 2, "")
                            updated = True
                        break
                    
                    # Check for the target subsection
                    if line.strip() == f"### {subsection}":
                        subsection_found = True
                        # Find the next line after the subsection header to insert
                        for j in range(i + 1, len(lines)):
                            # Insert before next subsection, main section, or end
                            if (lines[j].startswith("### ") or 
                                lines[j].startswith("## ") or 
                                lines[j].startswith("# ") or
                                j == len(lines) - 1):
                                lines.insert(j, new_task)
                                updated = True
                                break
                        break
            
            # Handle case where we reached end of file while in main section
            if in_main_section and not updated:
                if not subsection_found:
                    lines.append(f"### {subsection}")
                    lines.append(new_task)
                    lines.append("")
                    updated = True
            
            if not in_main_section:
                print(f"Main section '{main_section}' not found. Available sections:")
                main_lines = self.find_section("MAIN", level=1)
                if main_lines:
                    for line in main_lines:
                        if line.startswith("## "):
                            print(f"  - {line[3:]}")
                return
            
            if updated:
                self.write_file('\n'.join(lines))
                print(f"Added task #{task_id} to {main_section}:{subsection}: {task_text}")
            else:
                print(f"Failed to add task to {main_section}:{subsection}")
        else:
            # Add to main section (original behavior)
            section_pattern = f"(## {main_section}\\n)"
            replacement = f"\\1{new_task}"
            
            new_content = re.sub(section_pattern, replacement, content)
            
            # Check if the replacement worked
            if new_content == content:
                print(f"Section '{main_section}' not found. Available sections:")
                main_lines = self.find_section("MAIN", level=1)
                if main_lines:
                    for line in main_lines:
                        if line.startswith("## "):
                            print(f"  - {line[3:]}")
                return
            
            self.write_file(new_content)
            print(f"Added task #{task_id} to {main_section}: {task_text}")
    
    def add_task_to_daily(self, task_text):
        """Add a new task to today's daily section"""
        content = self.read_file()
        task_id = self.get_next_id()
        
        # Check if today's section exists
        if f"## {self.today}" not in content:
            print(f"No daily section for {self.today} found. Creating it first...")
            self.add_daily_section()
            content = self.read_file()
        
        # Add task to today's section
        today_pattern = f"(## {re.escape(self.today)}\\n)"
        new_task = f"- [ ] {task_text} #{task_id}\n"
        replacement = f"\\1{new_task}"
        
        new_content = re.sub(today_pattern, replacement, content)
        self.write_file(new_content)
        print(f"Added task #{task_id} to today's section: {task_text}")
    
    def progress_task_in_daily(self, task_id):
        """Mark a task as progressed ([~]) in today's daily section"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Find today's daily section
        today_section_found = False
        task_found = False
        
        for i, line in enumerate(lines):
            if line.strip() == f"## {self.today}":
                today_section_found = True
                continue
            
            if today_section_found:
                # Stop if we hit another section
                if line.startswith("##") or line.startswith("#"):
                    break
                
                # Look for the task ID in this daily section
                if f"#{task_id}" in line and re.match(r'- \[.\] ', line):
                    # Change to progress marker
                    new_line = re.sub(r'- \[.\] ', '- [~] ', line)
                    lines[i] = new_line
                    task_found = True
                    break
        
        if not today_section_found:
            print(f"No daily section found for {self.today}. Run 'tasks daily' first.")
            return
        
        if not task_found:
            print(f"Task #{task_id} not found in today's daily section.")
            print("Note: You can only mark progress on tasks that are in today's daily section.")
            return
        
        self.write_file('\n'.join(lines))
        print(f"Marked progress on task #{task_id} in today's daily section")
    
    def snooze_task(self, task_id, days_or_date):
        """Snooze a task by ID for X days or until specific date"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        # Calculate snooze date
        if days_or_date.isdigit():
            days = int(days_or_date)
            snooze_date = (datetime.strptime(self.today, "%d-%m-%Y") + timedelta(days=days)).strftime("%d-%m-%Y")
        else:
            try:
                datetime.strptime(days_or_date, "%d-%m-%Y")
                snooze_date = days_or_date
            except ValueError:
                print(f"Invalid date format: {days_or_date}. Use DD-MM-YYYY or number of days.")
                return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Remove existing snooze if present and add new snooze date
        new_line = re.sub(r' snooze:\d{2}-\d{2}-\d{4}', '', line)
        new_line = new_line.rstrip() + f" snooze:{snooze_date}"
        
        lines[line_num] = new_line
        self.write_file('\n'.join(lines))
        print(f"Snoozed task #{task_id} until {snooze_date}")
    
    def show_task(self, task_id):
        """Show details of a specific task by ID"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        line_num, line = result
        print(f"Task #{task_id}:")
        print(f"  {line.strip()}")
        print(f"  Line: {line_num + 1}")
    
    def list_sections(self):
        """List all available sections"""
        content = self.read_file()
        lines = content.split('\n')
        
        print("Available sections:")
        for line in lines:
            if line.startswith("# "):
                print(f"  {line}")
            elif line.startswith("## "):
                print(f"    {line}")
            elif line.startswith("### "):
                print(f"      {line}")
    
    def archive_old_content(self, days_to_keep=7):
        """Archive old daily sections and completed tasks"""
        content = self.read_file()
        lines = content.split('\n')
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        archived_daily_sections = []
        archived_completed_tasks = []
        new_lines = []
        current_section = []
        in_daily_section = False
        
        # Process daily sections
        for line in lines:
            if line.startswith("## ") and re.match(r"## \d{2}-\d{2}-\d{4}", line):
                # This is a daily section header
                if current_section:
                    # Process previous section
                    section_date_str = current_section[0].replace("## ", "")
                    try:
                        section_date = datetime.strptime(section_date_str, "%d-%m-%Y")
                        if section_date < cutoff_date:
                            archived_daily_sections.extend(current_section)
                        else:
                            new_lines.extend(current_section)
                    except ValueError:
                        new_lines.extend(current_section)
                
                current_section = [line]
                in_daily_section = True
            elif line.startswith("# ") and in_daily_section:
                # End of daily sections
                if current_section:
                    section_date_str = current_section[0].replace("## ", "")
                    try:
                        section_date = datetime.strptime(section_date_str, "%d-%m-%Y")
                        if section_date < cutoff_date:
                            archived_daily_sections.extend(current_section)
                        else:
                            new_lines.extend(current_section)
                    except ValueError:
                        new_lines.extend(current_section)
                
                new_lines.append(line)
                in_daily_section = False
                current_section = []
            elif in_daily_section:
                current_section.append(line)
            else:
                # Check for completed tasks in main sections to archive
                if (re.match(r'- \[x\] .*@\d{2}-\d{2}-\d{4}.*#\d{3}', line) and
                    not re.search(r'\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)', line)):
                    date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', line)
                    if date_match:
                        task_date = datetime.strptime(date_match.group(1), "%d-%m-%Y")
                        if task_date < cutoff_date:
                            archived_completed_tasks.append(line)
                            continue
                
                new_lines.append(line)
        
        # Handle last section if we ended in daily
        if current_section and in_daily_section:
            section_date_str = current_section[0].replace("## ", "")
            try:
                section_date = datetime.strptime(section_date_str, "%d-%m-%Y")
                if section_date < cutoff_date:
                    archived_daily_sections.extend(current_section)
                else:
                    new_lines.extend(current_section)
            except ValueError:
                new_lines.extend(current_section)
        
        # Add archived content to ARCHIVE section
        archive_additions = []
        if archived_completed_tasks:
            archive_additions.extend(["", "## ARCHIVED COMPLETED TASKS", ""])
            archive_additions.extend(archived_completed_tasks)
        
        if archived_daily_sections:
            archive_additions.extend(["", "## ARCHIVED DAILY SECTIONS", ""])
            archive_additions.extend(archived_daily_sections)
        
        if archive_additions:
            # Find ARCHIVE section and add content
            for i, line in enumerate(new_lines):
                if line == "# ARCHIVE":
                    new_lines[i+1:i+1] = archive_additions
                    break
        
        new_content = '\n'.join(new_lines)
        self.write_file(new_content)
        
        total_archived = len(archived_daily_sections) + len(archived_completed_tasks)
        print(f"Archived {total_archived} old items")
    
    def show_help(self):
        """Show detailed help information"""
        help_text = """
PARA + Daily Task Management System

USAGE:
  tasks [command] [args]

COMMANDS:
  help                   Show this help message
  daily                  Add today's daily section with recurring tasks
  stale                  Show stale tasks (oldest first, ignores snoozed)
  
  complete ID            Mark task with ID as complete
  pass ID                Mark task as progressed [~] in today's daily section
  sync                   Update main list from completed daily items
                         [x] in daily = complete main task  
                         [~] in daily = update date but keep incomplete
  
  add TEXT [SEC]         Add task to main list (alias for add-main)
  add-main TEXT [SEC]    Add task to main list section (default: INBOX)
                         Use SEC:SUBSEC for subsections (e.g., PROJECTS:HOME)
  add-daily TEXT         Add task directly to today's daily section
  
  snooze ID DAYS         Hide task for N days (e.g., snooze 042 5)
  snooze ID DATE         Hide task until date (e.g., snooze 042 25-12-2025)
  
  show ID                Show details of specific task
  sections               List all available sections
  archive                Clean up old daily sections and completed tasks

EXAMPLES:
  tasks daily                              # Start your day
  tasks add "write blog post" PROJECTS      # Add task to specific section
  tasks add "fix faucet" PROJECTS:HOME      # Add to subsection
  tasks add-daily "urgent client call"     # Add to today only
  tasks complete 042                       # Mark task done
  tasks pass 042                           # Mark progress on task in daily section
  tasks snooze 023 7                       # Hide task for a week
  tasks stale                              # See what needs attention
  tasks sync                               # Update main list from daily work

WORKFLOW:
  1. Morning:   tasks daily
  2. Work:      Check daily section, mark tasks:
                [x] = completed, [~] = made progress but not done
  3. Evening:   tasks sync (updates main list)
  4. Planning:  tasks stale (see neglected tasks)

TASK SYNTAX:
  - [ ] incomplete task @15-01-2025 #001
  - [x] completed task @15-01-2025 #002
  - [ ] recurring task @15-01-2025 (daily) #003
  - [ ] snoozed task @15-01-2025 snooze:20-01-2025 #004

DAILY SECTION PROGRESS:
  [x] = Task completed (will mark main task complete when synced)
  [~] = Made progress (will update main task date but keep incomplete)

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

FILE STRUCTURE:
  # DAILY
  ## 15-01-2025
  
  # MAIN
  ## INBOX
  ## PROJECTS
  ### Project Name
  ## AREAS
  ### Area Name
  ## RESOURCES
  ## ZETTELKASTEN
  
  # ARCHIVE

For more info: https://fortelabs.com/blog/para/
"""
        print(help_text)

def main():
    tm = TaskManager()
    
    if len(sys.argv) < 2:
        tm.show_help()
        return
    
    command = sys.argv[1]
    
    if command == "help":
        tm.show_help()
    elif command == "daily":
        tm.add_daily_section()
    elif command == "stale":
        tm.show_stale_tasks()
    elif command == "complete" and len(sys.argv) > 2:
        tm.complete_task(sys.argv[2])
    elif command == "pass" and len(sys.argv) > 2:
        tm.progress_task_in_daily(sys.argv[2])
    elif command == "sync":
        tm.sync_daily_sections()
    elif command == "add-main" and len(sys.argv) > 2:
        # Parse section argument properly
        valid_sections = ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]
        
        if len(sys.argv) == 3:
            # Just task text, no section
            task_text = sys.argv[2]
            section = "INBOX"
        else:
            # Check if last argument is a section
            last_arg = sys.argv[-1]
            main_part = last_arg.split(":")[0].upper()
            
            if main_part in valid_sections:
                # Last argument is a section/subsection
                section = last_arg
                task_text = " ".join(sys.argv[2:-1])
            else:
                # All arguments are task text
                task_text = " ".join(sys.argv[2:])
                section = "INBOX"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-daily" and len(sys.argv) > 2:
        tm.add_task_to_daily(" ".join(sys.argv[2:]))
    elif command == "snooze" and len(sys.argv) > 3:
        tm.snooze_task(sys.argv[2], sys.argv[3])
    elif command == "show" and len(sys.argv) > 2:
        tm.show_task(sys.argv[2])
    elif command == "sections":
        tm.list_sections()
    elif command == "archive":
        tm.archive_old_content()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()