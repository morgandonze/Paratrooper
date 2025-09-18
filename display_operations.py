#!/usr/bin/env python3
"""
Display and formatting operations for the Paratrooper system.

This module handles all display operations, help text, status reporting,
and formatting for the task management system.
"""

import re
from datetime import datetime, timedelta

from models import Config, Task, TaskFile, TODAY, TASK_ID_PATTERN, DATE_PATTERN
from file_operations import FileOperations


class DisplayOperations:
    """Handles all display operations and formatting for the task management system."""
    
    def __init__(self, file_ops: FileOperations, config: Config):
        self.file_ops = file_ops
        self.config = config
        self.today = TODAY
        
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
    
    def find_section(self, section_name, level=1):
        """Find a section by name and level"""
        content = self.file_ops.read_file()
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
        snooze_str = task_data.get('metadata', {}).get('snooze')
        
        # Check if task is snoozed
        if snooze_str:
            try:
                snooze_date = datetime.strptime(snooze_str, "%d-%m-%Y")
                today = datetime.now()
                if snooze_date > today:
                    return "snoozed", 0, snooze_str
            except ValueError:
                pass
        
        # Calculate staleness
        if date_str:
            try:
                task_date = datetime.strptime(date_str, "%d-%m-%Y")
                today = datetime.now()
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
    
    def show_status_tasks(self, scope=None):
        """Show task status (staleness) with optional scope filtering"""
        content = self.file_ops.read_file()
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
            
            if in_main and self.file_ops._is_task_line(line):
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
                
                task_data = self.file_ops._parse_task_line(line)
                if task_data:
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
        
        print("=== Tasks by status (oldest first) ===")
        
        for task_info in tasks_by_status:
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
            
            # Extract task ID and text
            task_id = task_data['metadata'].get('id', '???')
            text = task_data['text']
            
            print(f"{color} {days_old:2d} days | #{task_id} | {text} | {section}")
    
    def show_task(self, task_id):
        """Show details of a specific task"""
        line_number, line_content = self.file_ops.find_task_by_id(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found")
            return
        
        print(f"Task #{task_id}:")
        print(f"  {line_content}")
        print(f"  Line: {line_number}")
        
        # Parse and show details
        task_data = self.file_ops._parse_task_line(line_content)
        if task_data:
            print(f"  Status: {task_data['status']}")
            print(f"  Text: {task_data['text']}")
            if task_data['metadata'].get('date'):
                print(f"  Date: {task_data['metadata']['date']}")
            if task_data['metadata'].get('recurring'):
                print(f"  Recurring: {task_data['metadata']['recurring']}")
            if task_data['metadata'].get('snooze'):
                print(f"  Snoozed until: {task_data['metadata']['snooze']}")
    
    def show_task_from_main(self, task_id):
        """Show details of a specific task from main section only"""
        line_number, line_content = self.file_ops.find_task_by_id_in_main(task_id)
        
        if not line_content:
            print(f"Task #{task_id} not found in main section")
            return
        
        print(f"Task #{task_id}:")
        print(f"  {line_content}")
        print(f"  Line: {line_number}")
        
        # Parse and show details
        task_data = self.file_ops._parse_task_line(line_content)
        if task_data:
            print(f"  Status: {task_data['status']}")
            print(f"  Text: {task_data['text']}")
            if task_data['metadata'].get('date'):
                print(f"  Date: {task_data['metadata']['date']}")
            if task_data['metadata'].get('recurring'):
                print(f"  Recurring: {task_data['metadata']['recurring']}")
            if task_data['metadata'].get('snooze'):
                print(f"  Snoozed until: {task_data['metadata']['snooze']}")
    
    def list_sections(self):
        """List all available sections"""
        content = self.file_ops.read_file()
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
        print(f"  Icon set: {self.config.icon_set}")
        print(f"  Editor: {self.config.editor}")
        print(f"  Config file: ~/.ptconfig")
        print(f"  Available icon sets: basic, default, nest")
    
    def show_help(self):
        """Show help information"""
        help_text = """PARA + Daily Task Management System

USAGE:
  tasks [command] [args]

COMMANDS:
  help                   Show this help message
  config                 Show current configuration
  init                   Initialize the task file with default structure
  daily                  Add today's daily section with recurring tasks and carry over all incomplete tasks from previous day                                   
  status [SCOPE]         Show task status (oldest first, ignores snoozed)
                         SCOPE can be section (e.g., 'projects') or section:subsection (e.g., 'areas:work')                                                     
  
  complete ID            Mark task with ID as complete
  done ID                Alias for complete
  reopen ID              Reopen completed task (mark as incomplete)
  undone ID              Alias for reopen
  pass ID                Mark task as progressed [~] in today's daily section
  sync                   Update main list from completed daily items
                         [x] in daily = complete main task  
                         [~] in daily = update date but keep incomplete
  
  add TEXT [SEC]         Add task to main list (alias for add-main)
  add-main TEXT [SEC]    Add task to main list section (default: TASKS)
                         Use SEC:SUBSEC for subsections (e.g., WORK:HOME)
  add-daily TEXT         Add task directly to today's daily section
  up ID                  Pull task from main list into today's daily section
  
  snooze ID DAYS         Hide task for N days (e.g., snooze 042 5)
  snooze ID DATE         Hide task until date (e.g., snooze 042 25-12-2025)
  recur ID PATTERN       Modify task recurrence pattern (e.g., recur 042 daily)
  
  list                   List all tasks from main sections
  list SECTION[:SUBSEC]   List tasks in a specific section (e.g., list PROJECTS:HOME)                                                                           
  show ID                Show details of specific task from main section
  show SECTION[:SUBSEC]   Show tasks in a specific section (e.g., show PROJECTS:HOME)                                                                           
  show *:SUBSEC          Show tasks from all sections with matching subsection (e.g., show *:justculture)                                                       
  sections               List all available sections
  archive [DAYS]         Clean up old daily sections and completed tasks (default: 7 days)                                                                      
  
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
  tasks add "fix faucet" WORK:HOME         # Add to subsection
  tasks add-daily "urgent client call"     # Add to today only
  tasks up 042                            # Pull task #042 to today's daily section                                                                             
  tasks complete 042                       # Mark task done
  tasks show *:justculture                # Show all tasks from subsections named 'justculture'                                                                 
  tasks done 042                           # Alias for complete
  tasks reopen 042                         # Reopen completed task
  tasks undone 042                         # Alias for reopen
  tasks list                               # List all tasks from main sections
  tasks list PROJECTS:HOME                 # List tasks in PROJECTS > HOME subsection                                                                           
  tasks show 001                           # Show details of task #001
  tasks pass 042                           # Mark progress on task in daily section                                                                             
  tasks snooze 023 7                       # Hide task for a week
  tasks recur 042 daily                    # Set task to recur daily
  tasks status                             # See what needs attention
  tasks status projects                    # See task status in PROJECTS section
  tasks status areas:work                  # See task status in AREAS > WORK subsection                                                                         
  tasks sync                               # Update main list from daily work
  tasks edit 042 "new task text"           # Edit task text
  tasks move 042 PROJECTS:HOME             # Move task to subsection
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
  4. Planning:  tasks status (see neglected tasks)

TASK SYNTAX:
  - [ ] incomplete task | @15-01-2025 #001
  - [x] completed task | @15-01-2025 #002
  - [ ] recurring task | @15-01-2025 (daily) #003
  - [ ] snoozed task | @15-01-2025 snooze:20-01-2025 #004

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

CONFIGURATION:
  Configuration file: ~/.ptconfig (or set PTCONFIG env var)
  
  Settings:
  [general]
  task_file = ~/home/0-inbox/tasks.md
  icon_set = default
  editor = nvim
  
  Available icon sets:
  - default: [ ] [~] [x] (text-based)
  - basic: ⏳ 🔄 ✅ (emoji)
  - nest: 🪹 🔜 🪺 (nest theme)
  
  Editor options:
  - nvim, vim, nano, code, subl, atom, or any command-line editor
  - Use 'tasks config' to see current settings

FILE STRUCTURE:
  # DAILY
  ## 15-01-2025
  
  # MAIN
  
  # ARCHIVE

For more info: https://fortelabs.com/blog/para/"""
        
        print(help_text)
    
    def show_daily_list(self):
        """Show today's daily tasks"""
        task_file = self.file_ops.parse_file()
        
        if self.today not in task_file.daily_sections:
            print(f"No daily section for {self.today}")
            return
        
        tasks = task_file.daily_sections[self.today]
        
        print(f"=== Daily Tasks for {self.today} ===")
        print()
        
        if not tasks:
            print("No tasks for today")
            return
        
        for task in tasks:
            status_icon = self.icon_sets[self.icon_set]["incomplete"]
            if task.status == 'x':
                status_icon = self.icon_sets[self.icon_set]["complete"]
            elif task.status == '~':
                status_icon = self.icon_sets[self.icon_set]["progress"]
            
            task_line = f"{status_icon} {task.text}"
            if task.from_section:
                task_line += f" from {task.from_section}"
            if task.id:
                task_line += f" #{task.id}"
            
            print(task_line)
    
    def show_section(self, section_name):
        """Show tasks in a specific section"""
        content = self.file_ops.read_file()
        lines = content.split('\n')
        
        if section_name == "*":
            # Show all sections
            self.show_all_main()
            return
        
        if ':' in section_name:
            # Subsection
            main_section, subsection = section_name.split(':', 1)
            self._show_subsection(main_section, subsection, lines)
        elif section_name == "*":
            # Wildcard - show all sections
            self.show_all_main()
        else:
            # Main section
            self._show_main_section(section_name, lines)
    
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
            
            if in_main and current_section == section_name and self.file_ops._is_task_line(line):
                print(f"  {line}")
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
                current_subsection == subsection and self.file_ops._is_task_line(line)):
                print(f"  {line}")
                tasks_found = True
        
        if not tasks_found:
            print("No tasks found in this subsection")
    
    def show_all_main(self):
        """Show all tasks from main sections"""
        content = self.file_ops.read_file()
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
            
            if in_main and self.file_ops._is_task_line(line):
                print(f"  {line}")
