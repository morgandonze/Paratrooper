"""
Core task management functionality for the PARA + Daily Task Management System.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timedelta

from models import Task, Section, TaskFile
from config import Config
from utils import (
    extract_task_id, extract_date, is_task_line, is_recurring_task,
    should_recur_today, extract_recurrence_pattern, validate_task_text,
    parse_task_line, build_task_line, get_next_id, format_date, is_stale_task
)

# Constants
TODAY = datetime.now().strftime("%d-%m-%Y")


class TaskManager:
    """Main task management class."""
    
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config.load()
        
        self.config = config
        self.task_file = config.task_file
        self.today = TODAY
        self._task_file_obj = None
        self.editor = config.editor
        
        # Define icon sets
        self.icon_sets = {
            "default": {
                "incomplete": "[ ]",
                "progress": "[~]",
                "complete": "[x]"
            },
            "basic": {
                "incomplete": "⏳",
                "progress": "🔄", 
                "complete": "✅"
            },
            "nest": {
                "incomplete": "🪹",
                "progress": "🔜",
                "complete": "🪺"
            }
        }
        
        # Set current icon set
        self.icon_set = config.icon_set
        if self.icon_set not in self.icon_sets:
            print(f"Warning: Unknown icon set '{self.icon_set}', using default")
            self.icon_set = "default"
    
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
    
    def parse_file(self) -> TaskFile:
        """Parse the task file and return a TaskFile object."""
        content = self.read_file()
        lines = content.split('\n')
        
        task_file = TaskFile()
        current_section = None
        current_subsection = None
        current_project = None
        in_daily = False
        in_main = False
        in_archive = False
        
        for line in lines:
            line = line.rstrip()
            
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
            
            # Check for daily section dates
            if in_daily and line.startswith('## ') and re.match(r'## \d{2}-\d{2}-\d{4}', line):
                current_section = line[3:].strip()
                continue
            
            # Check for main section (##)
            if in_main and line.startswith('## ') and not line.startswith('### '):
                current_section = line[3:].strip()
                current_subsection = None
                current_project = None
                continue
            
            # Check for subsection (###)
            if in_main and line.startswith('### '):
                current_subsection = line[4:].strip()
                current_project = None
                continue
            
            # Check for project (####)
            if in_main and line.startswith('#### '):
                current_project = line[5:].strip()
                continue
            
            # Parse task lines
            if is_task_line(line):
                task_data = parse_task_line(line)
                if task_data:
                    task = Task(
                        id=task_data['id'] or '',
                        text=task_data['text'],
                        status=task_data['status'],
                        date=task_data['date'],
                        recurring=task_data['recurring'],
                        snooze=task_data['snooze'],
                        section=current_section,
                        subsection=current_subsection
                    )
                    
                    if in_daily and current_section:
                        task_file.daily_sections[current_section] = task_file.daily_sections.get(current_section, [])
                        task_file.daily_sections[current_section].append(task)
                    elif in_main and current_section:
                        section = task_file.get_main_section(current_section)
                        if current_subsection:
                            subsection = section.get_subsection(current_subsection)
                            if not subsection:
                                subsection = section.add_subsection(current_subsection)
                            subsection.add_task(task)
                        else:
                            section.add_task(task)
                    elif in_archive:
                        if current_section:
                            if current_section not in task_file.archive_sections:
                                task_file.archive_sections[current_section] = []
                            task_file.archive_sections[current_section].append(task)
        
        self._task_file_obj = task_file
        return task_file
    
    def write_file_from_objects(self, task_file: TaskFile):
        """Write TaskFile object back to the file."""
        content = task_file.to_markdown()
        self.write_file(content)
        self._task_file_obj = task_file
        
    def read_file(self):
        """Read the task file, create if doesn't exist"""
        if not self.task_file.exists():
            self.task_file.touch()
            default_content = """# DAILY

# MAIN

# ARCHIVE

"""
            self.task_file.write_text(default_content)
        return self.task_file.read_text()
    
    def write_file(self, content):
        """Write content back to task file"""
        self.task_file.write_text(content)
    
    def get_next_id(self):
        """Get the next available task ID"""
        task_file = self.parse_file()
        all_tasks = []
        
        # Collect all tasks from all sections
        for section in task_file.main_sections.values():
            all_tasks.extend(section.tasks)
            for subsection in section.subsections.values():
                all_tasks.extend(subsection.tasks)
        
        for tasks in task_file.daily_sections.values():
            all_tasks.extend(tasks)
        
        for tasks in task_file.archive_sections.values():
            all_tasks.extend(tasks)
        
        return get_next_id(all_tasks)
    
    def find_task_by_id(self, task_id: str) -> Optional[Tuple[int, str]]:
        """Find a task by ID and return (line_number, line_content)"""
        content = self.read_file()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and is_task_line(line):
                return i, line
        
        return None
    
    def find_task_by_id_in_main(self, task_id: str) -> Optional[Tuple[int, str]]:
        """Find a task by ID in main sections only"""
        content = self.read_file()
        lines = content.split('\n')
        
        in_main = False
        for i, line in enumerate(lines):
            if line.strip() == "# MAIN":
                in_main = True
                continue
            elif in_main and line.startswith("# ") and line.strip() != "# MAIN":
                break
            
            if in_main and f"#{task_id}" in line and is_task_line(line):
                return i, line
        
        return None
    
    def add_task_to_main(self, task_text: str, section: str = "TASKS"):
        """Add a new task to main list section or subsection"""
        task_file = self.parse_file()
        task_id = self.get_next_id()
        
        # Parse section:subsection format
        if ":" in section:
            main_section, subsection = section.split(":", 1)
            main_section = main_section.upper()
            subsection = subsection.upper()
        else:
            main_section = section.upper()
            subsection = None
        
        # Extract recurrence pattern from task text
        clean_text, recurrence = extract_recurrence_pattern(task_text)
        
        # Create new task
        new_task = Task(
            id=task_id,
            text=clean_text,
            status=' ',
            date=self.today,
            recurring=recurrence,
            section=main_section,
            subsection=subsection
        )
        
        # Add task to the appropriate section
        if subsection:
            main_section_obj = task_file.get_main_section(main_section)
            subsection_obj = main_section_obj.get_subsection(subsection)
            if not subsection_obj:
                subsection_obj = main_section_obj.add_subsection(subsection)
            subsection_obj.add_task(new_task)
        else:
            section_obj = task_file.get_main_section(main_section)
            section_obj.add_task(new_task)
        
        # Write back to file
        self.write_file_from_objects(task_file)
        print(f"Added task #{task_id} to {section}: {clean_text}")
    
    def add_task_to_daily(self, task_text: str):
        """Add a task directly to today's daily section"""
        task_file = self.parse_file()
        task_id = self.get_next_id()
        
        # Extract recurrence pattern from task text
        clean_text, recurrence = extract_recurrence_pattern(task_text)
        
        # Create new task
        new_task = Task(
            id=task_id,
            text=clean_text,
            status=' ',
            date=self.today,
            recurring=recurrence
        )
        
        # Add to today's daily section
        daily_tasks = task_file.get_daily_section(self.today)
        daily_tasks.append(new_task)
        
        # Write back to file
        self.write_file_from_objects(task_file)
        print(f"Added task #{task_id} to today's daily section: {clean_text}")
    
    def add_daily_section(self):
        """Add or show today's daily section"""
        task_file = self.parse_file()
        
        if self.today in task_file.daily_sections:
            print(f"Daily section for {self.today} already exists")
            self.show_daily_list()
        else:
            task_file.daily_sections[self.today] = []
            self.write_file_from_objects(task_file)
            print(f"Added daily section for {self.today}")
            print(f"Daily section for {self.today} is empty")
    
    def show_daily_list(self):
        """Show today's daily tasks"""
        task_file = self.parse_file()
        
        if self.today not in task_file.daily_sections or not task_file.daily_sections[self.today]:
            print(f"Daily section for {self.today} is empty")
            return
        
        print(f"=== Daily Tasks for {self.today} ===")
        for task in task_file.daily_sections[self.today]:
            print(f"[{task.status}] {task.text}")
    
    def show_help(self):
        """Show help information"""
        help_text = """
PARA + Daily Task Management System
====================================

COMMANDS:
  init                   Initialize task file (first time setup)
  daily                  Start your day (creates or shows daily section)
  
  add TEXT [SEC]         Add task to main list (alias for add-main)
  add-main TEXT [SEC]    Add task to main list section (default: TASKS)
                         Use SEC:SUBSEC for subsections (e.g., WORK:HOME)
  add-daily TEXT         Add task directly to today's daily section
  up ID                  Pull task from main list into today's daily section
  
  snooze ID DAYS         Hide task for N days (e.g., snooze 042 5)
  snooze ID DATE         Hide task until date (e.g., snooze 042 25-12-2025)
  show ID                Show details of specific task from main section
  show SECTION[:SUBSEC]   Show tasks in a specific section (e.g., show WORK:HOME)
  show *:SUBSEC          Show tasks from all sections with matching subsection (e.g., show *:justculture)
  sections               List all available sections
  
  complete ID            Mark task as complete in daily section
  done ID                Alias for complete
  pass ID                Mark task as in progress in daily section
  reopen ID              Reopen completed task
  undone ID              Alias for reopen
  
  edit ID TEXT           Edit task text by ID
  move ID SECTION        Move task to new section (e.g., move 001 WORK:HOME)
  open [EDITOR]          Open tasks file with editor (default: from config)
  
  delete ID              Delete task from main list
  purge ID               Delete task from main list and all daily sections
  
  sync                   Update main list from completed daily items
                         [x] in daily = complete main task  
                         [~] in daily = update date but keep incomplete
  
  status [SECTION]       Show stale tasks that need attention
  recur ID PATTERN       Set task recurrence (e.g., recur 042 daily)
  
  list                   List all tasks from main sections
  list SECTION[:SUBSEC]   List tasks in a specific section (e.g., list WORK:HOME)
  show ID                Show details of specific task from main section
  show SECTION[:SUBSEC]   Show tasks in a specific section (e.g., show WORK:HOME)
  show *:SUBSEC          Show tasks from all sections with matching subsection (e.g., show *:justculture)
  sections               List all available sections
  
  config                 Show current configuration
  help                   Show this help message

EXAMPLES:
  tasks init                              # Initialize task file (first time setup)
  tasks daily                              # Start your day (creates or shows daily section)
  tasks add "write blog post" WORK         # Add task to specific section
  tasks add "fix faucet" WORK:HOME         # Add to subsection
  tasks add-daily "urgent client call"     # Add to today only
  tasks up 042                            # Pull task #042 to today's daily section
  tasks complete 042                       # Mark task done
  tasks show *:justculture                # Show all tasks from subsections named 'justculture'
  tasks done 042                           # Alias for complete
  tasks pass 042                           # Mark progress on task in daily section
  tasks reopen 042                         # Reopen completed task
  tasks undone 042                         # Alias for reopen
  tasks snooze 042 5                       # Hide task for 5 days
  tasks snooze 042 25-12-2025              # Hide task until specific date
  tasks status                             # See what needs attention
  tasks status work                        # See task status in WORK section
  tasks status health:work                 # See task status in HEALTH > WORK subsection
  tasks sync                               # Update main list from daily work
  tasks edit 042 "new task text"           # Edit task text
  tasks move 042 WORK:HOME                 # Move task to subsection
  tasks open                               # Open tasks file with configured editor
  tasks open vim                           # Open tasks file with vim (override config)
  tasks delete 042                         # Delete task from main list
  tasks purge 042                          # Delete task from main list and all daily sections
  tasks recur 042 daily                    # Set task to recur daily
  tasks list                               # List all tasks from main sections
  tasks list WORK:HOME                     # List tasks in WORK > HOME subsection
  tasks show 001                           # Show details of task #001
  tasks sections                           # List all available sections
  tasks config                             # Show current configuration

FILE STRUCTURE:
  # DAILY
  ## 15-01-2025
  
  # MAIN
  
  # ARCHIVE

For more info: https://fortelabs.com/blog/para/
"""
        print(help_text)
    
    def show_config(self):
        """Show current configuration"""
        print(f"Task file: {self.task_file}")
        print(f"Editor: {self.editor}")
        print(f"Icon set: {self.icon_set}")
    
    def open_file(self, editor: Optional[str] = None):
        """Open the task file with the specified editor"""
        editor_cmd = editor or self.editor
        try:
            subprocess.run([editor_cmd, str(self.task_file)], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to open editor: {editor_cmd}")
        except FileNotFoundError:
            print(f"Editor not found: {editor_cmd}")
    
    def add_task_to_daily_by_id(self, task_id: str):
        """Pull a task from main list into today's daily section by ID"""
        # Find the task in the main list only
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            print(f"No task found with ID #{task_id} in MAIN section")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Extract task text using new format parsing
        task_data = parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        task_text = task_data['text']
        
        # Find the section this task belongs to
        current_subsection = None
        current_project = None
        section_name = None
        
        # Search backwards from the task line to find its section
        for i in range(line_num - 1, -1, -1):
            if i >= len(lines):
                continue
                
            current_line = lines[i]
            
            # Check for main section (##)
            if current_line.startswith("## ") and not current_line.startswith("### "):
                section_name = current_line[3:].strip()
                # Any section name is valid now
                current_subsection = section_name
                break
            elif re.match(r"## \d{2}-\d{2}-\d{4}", current_line):
                # This is a daily section, skip it
                continue
            elif current_line.startswith("### "):
                # Only set if we haven't found one yet (first one encountered when searching backwards)
                if current_project is None:
                    current_project = current_line[4:].strip()
                # Continue searching for the main section
            else:
                # Continue searching for section
                continue
        
        # Build section reference
        if current_project and current_subsection:
            section_ref = f"{current_subsection} > {current_project}"
        elif current_subsection:
            section_ref = current_subsection
        else:
            section_ref = "UNKNOWN"
        
        # Check if today's section exists
        if f"## {self.today}" not in content:
            print(f"No daily section for {self.today} found. Creating it first...")
            self.add_daily_section()
            content = self.read_file()
            lines = content.split('\n')
        
        # Check if task is already in today's daily section
        if self._is_task_in_daily_section(task_id, content):
            print(f"Task #{task_id} is already in today's daily section")
            return
        
        # Add task to today's section with section information at the TOP
        today_pattern = f"(## {re.escape(self.today)}\\n)"
        new_task = build_task_line(' ', f"{task_text} from {section_ref}", task_id=task_id) + "\n"
        replacement = f"\\1{new_task}"
        
        new_content = re.sub(today_pattern, replacement, content)
        self.write_file(new_content)
        print(f"Pulled task #{task_id} to today's section: {task_text}")
    
    def _is_task_in_daily_section(self, task_id: str, content: str) -> bool:
        """Check if a task is already in today's daily section"""
        lines = content.split('\n')
        in_daily_section = False
        
        for line in lines:
            # Check if we're entering the DAILY section
            if line.strip() == "# DAILY":
                in_daily_section = True
                continue
            
            # Check if we're leaving the DAILY section
            if in_daily_section and line.startswith("# ") and line.strip() != "# DAILY":
                break
            
            # Check if this is a daily section date
            if in_daily_section and line.startswith("## ") and re.match(r"## \d{2}-\d{2}-\d{4}", line):
                if line.strip() == f"## {self.today}":
                    # We're in today's section, check for the task
                    continue
                else:
                    # This is a different day's section, skip it
                    continue
            
            # If we're in today's daily section, check for the task
            if in_daily_section and f"#{task_id}" in line and is_task_line(line):
                return True
        
        return False
    
    def _get_most_recent_daily_date(self, content: str) -> Optional[str]:
        """Get the most recent daily section date"""
        lines = content.split('\n')
        daily_dates = []
        
        for line in lines:
            if re.match(r"## \d{2}-\d{2}-\d{4}", line):
                date_str = line[3:].strip()
                daily_dates.append(date_str)
        
        if not daily_dates:
            return None
        
        # Sort dates and return the most recent
        daily_dates.sort(key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
        return daily_dates[-1]
    
    def complete_task(self, task_id: str):
        """Mark a task as complete"""
        # First try to complete in daily section
        if self._complete_task_in_daily(task_id):
            return
        
        # If not in daily section, add to daily section and complete
        if self._add_task_to_daily_section(task_id, "complete"):
            return
        
        print(f"Task #{task_id} not found")
    
    def _complete_task_in_daily(self, task_id: str) -> bool:
        """Mark a task as complete in the most recent daily section"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Find the most recent daily section
        most_recent_date = self._get_most_recent_daily_date(content)
        if not most_recent_date:
            return False
            
        daily_section_found = False
        task_found = False
        
        for i, line in enumerate(lines):
            if line.strip() == f"## {most_recent_date}":
                daily_section_found = True
                continue
            
            if daily_section_found and line.startswith("# ") and line.strip() != f"## {most_recent_date}":
                break
            
            if daily_section_found and f"#{task_id}" in line and is_task_line(line):
                # Update the task status to complete
                lines[i] = re.sub(r'- \[[^]]*\]', '- [x]', line)
                task_found = True
                break
        
        if task_found:
            self.write_file('\n'.join(lines))
            print(f"Completed task #{task_id} in daily section")
            return True
        
        return False
    
    def _add_task_to_daily_section(self, task_id: str, status: str = "complete") -> bool:
        """Add a task to today's daily section from main list"""
        # Find the task in main list
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            return False
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task using new format
        task_data = parse_task_line(line)
        if not task_data:
            return False
        
        task_text = task_data['text']
        
        # Find the section this task belongs to
        current_subsection = None
        current_project = None
        section_name = None
        
        # Search backwards from the task line to find its section
        for i in range(line_num - 1, -1, -1):
            if i >= len(lines):
                continue
                
            current_line = lines[i]
            
            # Check for main section (##)
            if current_line.startswith("## ") and not current_line.startswith("### "):
                section_name = current_line[3:].strip()
                # Any section name is valid now
                current_subsection = section_name
                break
            elif re.match(r"## \d{2}-\d{2}-\d{4}", current_line):
                # This is a daily section, skip it
                continue
            elif current_line.startswith("### "):
                if current_project is None:
                    current_project = current_line[4:].strip()
                # Continue searching for the main section
            else:
                # Continue searching for section
                continue
        
        # Build section reference
        if current_project and current_subsection:
            section_ref = f"{current_subsection} > {current_project}"
        elif current_subsection:
            section_ref = current_subsection
        else:
            section_ref = "UNKNOWN"
        
        # Create the new task line with appropriate status
        # Use simple format to avoid forbidden characters
        if status == "complete":
            new_task_line = f"- [x] {task_text} from {section_ref} | #{task_id}\n"
        else:  # progress
            new_task_line = f"- [~] {task_text} from {section_ref} | #{task_id}\n"
        
        # Check if today's section exists
        if f"## {self.today}" not in content:
            print(f"No daily section for {self.today} found. Creating it first...")
            self.add_daily_section()
            content = self.read_file()
            lines = content.split('\n')
        
        # Add task to today's section
        today_pattern = f"(## {re.escape(self.today)}\\n)"
        replacement = f"\\1{new_task_line}"
        
        new_content = re.sub(today_pattern, replacement, content)
        self.write_file(new_content)
        print(f"Added task #{task_id} to daily section")
        return True
    
    def progress_task_in_daily(self, task_id: str):
        """Mark a task as progressed ([~]) in the most recent daily section"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Find the most recent daily section
        most_recent_date = self._get_most_recent_daily_date(content)
        if not most_recent_date:
            print("No daily section found. Run 'tasks daily' first.")
            return
            
        daily_section_found = False
        task_found = False
        
        for i, line in enumerate(lines):
            if line.strip() == f"## {most_recent_date}":
                daily_section_found = True
                continue
            
            if daily_section_found and line.startswith("# ") and line.strip() != f"## {most_recent_date}":
                break
            
            if daily_section_found and f"#{task_id}" in line and is_task_line(line):
                # Update the task status to progress
                lines[i] = re.sub(r'- \[[^]]*\]', '- [~]', line)
                task_found = True
                break
        
        if task_found:
            self.write_file('\n'.join(lines))
            print(f"Marked progress on task #{task_id} in today's daily section")
        else:
            print(f"Task #{task_id} not found in daily section")
    
    def sync_daily_sections(self):
        """Sync completed tasks from daily sections back to main list"""
        task_file = self.parse_file()
        daily_additions = 0
        
        # Process all daily sections
        for date, tasks in task_file.daily_sections.items():
            for task in tasks:
                if task.status == 'x':  # Completed
                    # Find the corresponding task in main list and mark as complete
                    main_task = self._find_main_task_by_id(task.id)
                    if main_task:
                        main_task.status = 'x'
                        main_task.date = date
                        daily_additions += 1
                elif task.status == '~':  # Progressed
                    # Update the date but keep incomplete
                    main_task = self._find_main_task_by_id(task.id)
                    if main_task:
                        main_task.date = date
                        daily_additions += 1
        
        if daily_additions > 0:
            self.write_file_from_objects(task_file)
            print(f"Synced {daily_additions} completed and progressed tasks from daily section")
        else:
            print("No changes needed")
    
    def _find_main_task_by_id(self, task_id: str) -> Optional[Task]:
        """Find a task in main sections by ID"""
        task_file = self.parse_file()
        
        for section in task_file.main_sections.values():
            for task in section.tasks:
                if task.id == task_id:
                    return task
            for subsection in section.subsections.values():
                for task in subsection.tasks:
                    if task.id == task_id:
                        return task
        
        return None
    
    def snooze_task(self, task_id: str, days_or_date: str):
        """Snooze a task for specified days or until a date"""
        # Parse the snooze parameter
        if days_or_date.isdigit():
            # It's a number of days
            days = int(days_or_date)
            snooze_date = (datetime.now() + timedelta(days=days)).strftime("%d-%m-%Y")
        else:
            # It's a date
            snooze_date = days_or_date
        
        # Find and update the task
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"Task #{task_id} not found")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Update the task line to add snooze
        if 'snooze:' in line:
            # Replace existing snooze
            lines[line_num] = re.sub(r'snooze:\d{2}-\d{2}-\d{4}', f'snooze:{snooze_date}', line)
        else:
            # Add snooze to the end
            if ' | ' in line:
                lines[line_num] = line + f' snooze:{snooze_date}'
            else:
                lines[line_num] = line + f' | snooze:{snooze_date}'
        
        self.write_file('\n'.join(lines))
        print(f"Snoozed task #{task_id} until {snooze_date}")
    
    def show_task(self, task_id: str):
        """Show details of a specific task"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"Task #{task_id} not found")
            return
        
        line_num, line = result
        task_data = parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        print(f"Task #{task_id}: {task_data['text']}")
        print(f"Status: {task_data['status']}")
        if task_data['date']:
            print(f"Date: {task_data['date']}")
        if task_data['recurring']:
            print(f"Recurring: {task_data['recurring']}")
        if task_data['snooze']:
            print(f"Snoozed until: {task_data['snooze']}")
    
    def show_stale_tasks(self, section_name: Optional[str] = None):
        """Show stale tasks that need attention"""
        task_file = self.parse_file()
        stale_tasks = []
        
        # Check main sections
        for section in task_file.main_sections.values():
            if section_name and section.name.upper() != section_name.upper():
                continue
            
            for task in section.tasks:
                if is_stale_task(task, self.today):
                    stale_tasks.append((section.name, task))
            
            for subsection in section.subsections.values():
                for task in subsection.tasks:
                    if is_stale_task(task, self.today):
                        stale_tasks.append((f"{section.name} > {subsection.name}", task))
        
        if stale_tasks:
            print(f"Stale tasks (not updated for 7+ days):")
            for section_ref, task in stale_tasks:
                print(f"  #{task.id} in {section_ref}: {task.text}")
        else:
            print("No stale tasks found")
    
    def edit_task(self, task_id: str, new_text: str):
        """Edit a task's text"""
        # Validate new text
        is_valid, error = validate_task_text(new_text)
        if not is_valid:
            print(f"Invalid task text: {error}")
            return
        
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"Task #{task_id} not found")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Update the task text
        task_data = parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Build new task line with updated text
        new_task_line = build_task_line(
            task_data['status'],
            new_text,
            date=task_data['date'],
            recurring=task_data['recurring'],
            snooze=task_data['snooze'],
            task_id=task_data['id']
        )
        
        lines[line_num] = new_task_line
        self.write_file('\n'.join(lines))
        print(f"Updated task #{task_id}: {new_text}")
    
    def move_task(self, task_id: str, new_section: str):
        """Move task to a new section"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"Task #{task_id} not found")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task
        task_data = parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Parse section:subsection format
        if ":" in new_section:
            main_section, subsection = new_section.split(":", 1)
            main_section = main_section.upper()
            subsection = subsection.upper()
        else:
            main_section = new_section.upper()
            subsection = None
        
        # Remove task from current location
        del lines[line_num]
        
        # Build new task line
        new_task = build_task_line(
            task_data['status'],
            task_data['text'],
            date=task_data['date'],
            recurring=task_data['recurring'],
            snooze=task_data['snooze'],
            task_id=task_data['id']
        ) + "\n"
        
        # Add to new section
        if subsection:
            # Add to specific subsection under main section
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
                    updated = True
            
            if not in_main_section:
                # Create the section if it doesn't exist
                # Find the MAIN section and add the new section after it
                for i, line in enumerate(lines):
                    if line.strip() == "# MAIN":
                        # Insert the new section after MAIN
                        lines.insert(i + 1, f"## {main_section}")
                        lines.insert(i + 2, "")
                        lines.insert(i + 3, f"### {subsection}")
                        lines.insert(i + 4, new_task)
                        updated = True
                        break
            
            if updated:
                self.write_file('\n'.join(lines))
                print(f"Moved task #{task_id} to {main_section}:{subsection}: {task_data['text']}")
            else:
                print(f"Failed to move task to {main_section}:{subsection}")
        else:
            # Add to main section (original behavior)
            section_pattern = f"(## {main_section}\\n)"
            new_task_with_spacing = f"\\1{new_task}"
            
            new_content = re.sub(section_pattern, new_task_with_spacing, '\n'.join(lines))
            
            # Check if the replacement worked
            if new_content == '\n'.join(lines):
                # Create the section if it doesn't exist
                # Find the MAIN section and add the new section after it
                for i, line in enumerate(lines):
                    if line.strip() == "# MAIN":
                        # Insert the new section after MAIN
                        lines.insert(i + 1, f"## {main_section}")
                        lines.insert(i + 2, "")
                        lines.insert(i + 3, new_task)
                        new_content = '\n'.join(lines)
                        break
            
            self.write_file(new_content)
            print(f"Moved task #{task_id} to {main_section}: {task_data['text']}")
    
    def delete_task_from_main(self, task_id: str):
        """Delete a task from main list"""
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            print(f"Task #{task_id} not found in main list")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Remove the task line
        del lines[line_num]
        
        self.write_file('\n'.join(lines))
        print(f"Deleted task #{task_id} from main list")
    
    def delete_task_from_daily(self, task_id: str):
        """Delete a task from daily section"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Find and remove the task
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and is_task_line(line):
                del lines[i]
                self.write_file('\n'.join(lines))
                print(f"Deleted task #{task_id} from today's daily section")
                return
        
        print(f"Task #{task_id} not found in daily section")
    
    def purge_task(self, task_id: str):
        """Delete task from main list and all daily sections"""
        # Delete from main list
        self.delete_task_from_main(task_id)
        
        # Delete from all daily sections
        content = self.read_file()
        lines = content.split('\n')
        
        # Find and remove all instances
        new_lines = []
        for line in lines:
            if f"#{task_id}" in line and is_task_line(line):
                continue  # Skip this line
            new_lines.append(line)
        
        self.write_file('\n'.join(new_lines))
        print(f"Purged task #{task_id} from main list and all daily sections")
    
    def list_sections(self):
        """List all available sections"""
        task_file = self.parse_file()
        
        print("Available sections:")
        for section_name in task_file.main_sections.keys():
            print(f"  - {section_name}")
    
    def show_section(self, section_name: str):
        """Show tasks in a specific section"""
        if section_name == "*":
            # Show all sections
            self.show_all_main()
            return
        
        task_file = self.parse_file()
        
        if ":" in section_name:
            # Subsection specified
            main_section, subsection = section_name.split(":", 1)
            main_section = main_section.upper()
            subsection = subsection.upper()
            
            if main_section in task_file.main_sections:
                section = task_file.main_sections[main_section]
                if subsection in section.subsections:
                    print(f"=== {main_section} > {subsection} ===")
                    for task in section.subsections[subsection].tasks:
                        print(f"[{task.status}] {task.text} | #{task.id}")
                else:
                    print(f"Subsection '{subsection}' not found in '{main_section}'")
            else:
                print(f"Section '{main_section}' not found")
        else:
            # Main section
            section_name = section_name.upper()
            if section_name in task_file.main_sections:
                section = task_file.main_sections[section_name]
                print(f"=== {section_name} ===")
                for task in section.tasks:
                    print(f"[{task.status}] {task.text} | #{task.id}")
                
                # Show subsections
                for subsection_name, subsection in section.subsections.items():
                    print(f"\n### {subsection_name}")
                    for task in subsection.tasks:
                        print(f"[{task.status}] {task.text} | #{task.id}")
            else:
                print(f"Section '{section_name}' not found")
    
    def show_all_main(self):
        """Show all main sections"""
        task_file = self.parse_file()
        
        if not task_file.main_sections:
            print("No main sections found")
            return
        
        for section_name, section in task_file.main_sections.items():
            print(f"=== {section_name} ===")
            for task in section.tasks:
                print(f"[{task.status}] {task.text} | #{task.id}")
            
            # Show subsections
            for subsection_name, subsection in section.subsections.items():
                print(f"\n### {subsection_name}")
                for task in subsection.tasks:
                    print(f"[{task.status}] {task.text} | #{task.id}")
            print()
