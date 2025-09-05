#!/usr/bin/env python3
"""
Task management scripts for PARA + Daily system with hierarchical sections
Usage: python tasks.py [command] [args]
"""

import re
import os
import sys
import configparser
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Configuration
TODAY = datetime.now().strftime("%d-%m-%Y")

@dataclass
class Config:
    """Configuration settings for the task manager"""
    task_file: Path
    icon_set: str
    editor: str
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file or create default"""
        if config_path is None:
            config_path = Path(os.environ.get('PTCONFIG', '~/.ptconfig')).expanduser()
        
        # Default configuration
        default_config = cls(
            task_file=Path.home() / "home" / "tasks.md",
            icon_set="default",
            editor="nvim"
        )
        
        if not config_path.exists():
            # Create default config file
            cls.create_default_config(config_path, default_config)
            return default_config
        
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            # Load task file location
            task_file = default_config.task_file
            if 'general' in config and 'task_file' in config['general']:
                task_file = Path(config['general']['task_file']).expanduser()
            
            # Load icon set
            icon_set = default_config.icon_set
            if 'general' in config and 'icon_set' in config['general']:
                icon_set = config['general']['icon_set']
            
            # Load editor
            editor = default_config.editor
            if 'general' in config and 'editor' in config['general']:
                editor = config['general']['editor']
            
            return cls(task_file=task_file, icon_set=icon_set, editor=editor)
            
        except Exception as e:
            print(f"Warning: Error loading config from {config_path}: {e}")
            print("Using default configuration")
            return default_config
    
    @classmethod
    def create_default_config(cls, config_path: Path, config: 'Config'):
        """Create a default configuration file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(f"""# Paratrooper Configuration File
# Location: {config_path}

[general]
# Task file location (supports ~ for home directory)
task_file = {config.task_file}

# Icon set: default, basic, nest
icon_set = {config.icon_set}

# Default editor for 'open' command
editor = {config.editor}
""")
        print(f"Created default configuration file at {config_path}")

# Regex patterns for new format with | separator
TASK_STATUS_PATTERN = r'- \[.\] '
TASK_INCOMPLETE_PATTERN = r'- \[ \] '
TASK_COMPLETE_PATTERN = r'- \[x\] '
TASK_PROGRESS_PATTERN = r'- \[~\] '
TASK_ID_PATTERN = r'#(\d{3})'
DATE_PATTERN = r'@(\d{2}-\d{2}-\d{4})'
SNOOZE_PATTERN = r'snooze:(\d{2}-\d{2}-\d{4})'
RECURRING_PATTERN = r'\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)'

# Character restrictions for task text
ALLOWED_TASK_CHARS = r'[a-zA-Z0-9\s.,!?:;-_"\''
FORBIDDEN_TASK_CHARS = ['@', '#', '|', '(', ')', '[', ']', '{', '}', '<', '\\', '/', '~', '`']

# Task status constants
TASK_STATUS = {
    'INCOMPLETE': '- [ ]',
    'COMPLETE': '- [x]',
    'PROGRESS': '- [~]'
}

@dataclass
class Task:
    """Represents a single task"""
    id: str
    text: str
    status: str  # ' ', 'x', '~'
    date: Optional[str] = None
    recurring: Optional[str] = None
    snooze: Optional[str] = None
    due: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    is_daily: bool = False
    from_section: Optional[str] = None  # For daily tasks, shows where it came from
    
    def to_markdown(self) -> str:
        """Convert task to markdown format"""
        status_part = f"- [{self.status}] {self.text}"
        
        metadata_parts = []
        if self.date:
            metadata_parts.append(f"@{self.date}")
        if self.recurring:
            metadata_parts.append(self.recurring)
        if self.snooze:
            metadata_parts.append(f"snooze:{self.snooze}")
        if self.due:
            metadata_parts.append(f"due:{self.due}")
        if self.id:
            metadata_parts.append(f"#{self.id}")
        
        if metadata_parts:
            metadata_part = " ".join(metadata_parts)
            return f"{status_part} | {metadata_part}"
        else:
            return status_part
    
    @classmethod
    def from_markdown(cls, line: str, section: str = None, subsection: str = None) -> Optional['Task']:
        """Parse a markdown line into a Task object"""
        if not line.strip().startswith('- ['):
            return None
        
        # Extract status
        status_match = re.match(r'- \[(.)\]', line)
        if not status_match:
            return None
        status = status_match.group(1)
        
        # Extract text (everything after status until | or end)
        text_part = line[5:]  # Remove '- [x] '
        if ' | ' in text_part:
            text = text_part.split(' | ')[0].strip()
        else:
            text = text_part.strip()
        
        # Extract metadata
        metadata = {}
        if ' | ' in line:
            metadata_str = line.split(' | ')[1]
            # Parse date
            date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', metadata_str)
            if date_match:
                metadata['date'] = date_match.group(1)
            
            # Parse recurring
            recur_match = re.search(r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)', metadata_str)
            if recur_match:
                metadata['recurring'] = f"({recur_match.group(1)})"
            
            # Parse snooze
            snooze_match = re.search(r'snooze:(\d{2}-\d{2}-\d{4})', metadata_str)
            if snooze_match:
                metadata['snooze'] = snooze_match.group(1)
            
            # Parse due
            due_match = re.search(r'due:(\d{2}-\d{2}-\d{4})', metadata_str)
            if due_match:
                metadata['due'] = due_match.group(1)
            
            # Parse ID
            id_match = re.search(r'#(\d{3})', metadata_str)
            if id_match:
                metadata['id'] = id_match.group(1)
        
        return cls(
            id=metadata.get('id', ''),
            text=text,
            status=status,
            date=metadata.get('date'),
            recurring=metadata.get('recurring'),
            snooze=metadata.get('snooze'),
            due=metadata.get('due'),
            section=section,
            subsection=subsection
        )

@dataclass
class Section:
    """Represents a section in the task file"""
    name: str
    level: int  # 1 for #, 2 for ##, 3 for ###
    tasks: List[Task] = None
    subsections: Dict[str, 'Section'] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
        if self.subsections is None:
            self.subsections = {}
    
    def add_task(self, task: Task):
        """Add a task to this section"""
        self.tasks.append(task)
    
    def add_subsection(self, name: str) -> 'Section':
        """Add a subsection to this section"""
        if name not in self.subsections:
            self.subsections[name] = Section(name=name, level=self.level + 1)
        return self.subsections[name]
    
    def get_subsection(self, name: str) -> Optional['Section']:
        """Get a subsection by name"""
        return self.subsections.get(name)
    
    def to_markdown(self) -> str:
        """Convert section to markdown format"""
        lines = []
        lines.append('#' * self.level + ' ' + self.name)
        
        for task in self.tasks:
            lines.append(task.to_markdown())
        
        for subsection in self.subsections.values():
            lines.append('')
            lines.append(subsection.to_markdown())
        
        return '\n'.join(lines)

@dataclass
class TaskFile:
    """Represents the entire task file"""
    daily_sections: Dict[str, List[Task]] = None  # date -> tasks
    main_sections: Dict[str, Section] = None  # section_name -> Section
    archive_sections: Dict[str, List[Task]] = None  # section_name -> tasks
    
    def __post_init__(self):
        if self.daily_sections is None:
            self.daily_sections = {}
        if self.main_sections is None:
            self.main_sections = {}
        if self.archive_sections is None:
            self.archive_sections = {}
    
    def get_main_section(self, name: str) -> Section:
        """Get or create a main section"""
        if name not in self.main_sections:
            self.main_sections[name] = Section(name=name, level=2)
        return self.main_sections[name]
    
    def get_daily_section(self, date: str) -> List[Task]:
        """Get or create a daily section"""
        if date not in self.daily_sections:
            self.daily_sections[date] = []
        return self.daily_sections[date]
    
    def to_markdown(self) -> str:
        """Convert entire file to markdown format"""
        lines = []
        
        # Daily sections
        if self.daily_sections:
            lines.append('# DAILY')
            lines.append('')
            for date in sorted(self.daily_sections.keys()):
                lines.append(f'## {date}')
                for task in self.daily_sections[date]:
                    lines.append(task.to_markdown())
                lines.append('')
        
        # Main sections
        if self.main_sections:
            lines.append('# MAIN')
            lines.append('')
            for section in self.main_sections.values():
                lines.append(section.to_markdown())
                lines.append('')
        
        # Archive sections
        if self.archive_sections:
            lines.append('# ARCHIVE')
            lines.append('')
            for section_name, tasks in self.archive_sections.items():
                lines.append(f'## {section_name}')
                for task in tasks:
                    lines.append(task.to_markdown())
                lines.append('')
        
        return '\n'.join(lines)

class TaskManager:
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

## INBOX

## PROJECTS

## AREAS

## RESOURCES

## ZETTELKASTEN

# ARCHIVE

"""
            self.task_file.write_text(default_content)
            print(f"Created new task file at {self.task_file}")
        else:
            print(f"Task file already exists at {self.task_file}")
    
    def parse_file(self) -> TaskFile:
        """Parse the task file into Python objects"""
        if self._task_file_obj is not None:
            return self._task_file_obj
        
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
                        # Extract the section name from the text
                        parts = task.text.split(" from ")
                        if len(parts) == 2:
                            task.text = parts[0]  # Remove " from SECTION" part
                            task.from_section = parts[1]
                    task_file.get_daily_section(current_daily_date).append(task)
                continue
            
            # Main sections
            elif in_main and line.startswith('## '):
                current_section = line[3:].strip()
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
                current_section = line[3:].strip()
                continue
            elif in_archive and line.startswith('- ['):
                task = Task.from_markdown(line)
                if task:
                    if current_section not in task_file.archive_sections:
                        task_file.archive_sections[current_section] = []
                    task_file.archive_sections[current_section].append(task)
                continue
        
        # Ensure all main sections exist
        main_sections = ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]
        for section_name in main_sections:
            if section_name not in task_file.main_sections:
                task_file.main_sections[section_name] = Section(section_name, 2)
        
        self._task_file_obj = task_file
        return task_file
    
    def write_file_from_objects(self, task_file: TaskFile):
        """Write the task file from Python objects"""
        content = task_file.to_markdown()
        self.write_file(content)
        self._task_file_obj = task_file
        
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
    
    def _is_incomplete_task(self, line):
        """Check if a line is an incomplete task"""
        return bool(re.match(TASK_INCOMPLETE_PATTERN, line))
    
    def _is_complete_task(self, line):
        """Check if a line is a complete task"""
        return bool(re.match(TASK_COMPLETE_PATTERN, line))
    
    def _is_progress_task(self, line):
        """Check if a line is a progress task"""
        return bool(re.match(TASK_PROGRESS_PATTERN, line))
    
    def _extract_task_id(self, line):
        """Extract task ID from a line"""
        match = re.search(TASK_ID_PATTERN, line)
        return match.group(1) if match else None
    
    def _extract_date(self, line):
        """Extract date from a line"""
        match = re.search(DATE_PATTERN, line)
        return match.group(1) if match else None
    
    def _is_recurring_task(self, line):
        """Check if a task is recurring"""
        return bool(re.search(RECURRING_PATTERN, line))
    
    def _extract_recurrence_pattern(self, text):
        """Extract recurrence pattern from task text and return (clean_text, recurrence_pattern)"""
        # Pattern to match recurrence patterns in parentheses
        recur_pattern = r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)'
        
        # Find all recurrence patterns
        matches = re.findall(recur_pattern, text)
        
        if not matches:
            return text, None
        
        if len(matches) > 1:
            raise ValueError("Task text can only contain one recurrence pattern")
        
        # Extract the recurrence pattern
        recurrence = f"({matches[0]})"
        
        # Remove the recurrence pattern from the text
        clean_text = re.sub(recur_pattern, '', text).strip()
        
        # Clean up extra spaces
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text, recurrence
    
    def _validate_task_text(self, text):
        """Validate task text according to new format rules"""
        if not text or text.strip() != text:
            return False, "Task text cannot be empty or have leading/trailing spaces"
        
        # Check for forbidden characters (excluding parentheses for recurrence)
        for char in FORBIDDEN_TASK_CHARS:
            if char in text and char != '(' and char != ')':
                return False, f"Task text cannot contain '{char}' character"
        
        # Check that parentheses are only used for recurrence patterns
        if '(' in text or ')' in text:
            try:
                clean_text, recurrence = self._extract_recurrence_pattern(text)
                if not recurrence:
                    return False, "Parentheses can only be used for recurrence patterns like (daily), (weekly), etc."
            except ValueError as e:
                return False, str(e)
        
        return True, None
    
    def _parse_task_line(self, line):
        """Parse a task line using new format with | separator"""
        if not self._is_task_line(line):
            return None
        
        # Check for separator
        if ' | ' not in line:
            return None
        
        # Split on separator
        text_part, metadata_part = line.split(' | ', 1)
        
        # Extract status
        status_match = re.match(r'- \[(.)\] ', text_part)
        if not status_match:
            return None
        
        status = status_match.group(1)
        task_text = text_part[6:]  # Remove '- [X] '
        
        # Validate task text
        is_valid, error = self._validate_task_text(task_text)
        if not is_valid:
            return None
        
        # Parse metadata
        id_match = re.search(TASK_ID_PATTERN, metadata_part)
        date_match = re.search(DATE_PATTERN, metadata_part)
        snooze_match = re.search(SNOOZE_PATTERN, metadata_part)
        recur_match = re.search(RECURRING_PATTERN, metadata_part)
        
        return {
            'status': status,
            'text': task_text,
            'id': id_match.group(1) if id_match else None,
            'date': date_match.group(1) if date_match else None,
            'snooze': snooze_match.group(1) if snooze_match else None,
            'recurring': recur_match.group(0) if recur_match else None,
            'raw_line': line
        }
    
    def _build_task_line(self, status, text, date=None, recurring=None, snooze=None, task_id=None):
        """Build a task line using new format with | separator"""
        # Validate task text
        is_valid, error = self._validate_task_text(text)
        if not is_valid:
            raise ValueError(error)
        
        # Build status part
        status_part = f"- [{status}] {text}"
        
        # Build metadata part
        metadata_parts = []
        if date:
            metadata_parts.append(f"@{date}")
        if recurring:
            metadata_parts.append(recurring)
        if snooze:
            metadata_parts.append(f"snooze:{snooze}")
        if task_id:
            metadata_parts.append(f"#{task_id}")
        
        metadata_part = " ".join(metadata_parts)
        
        # Combine with separator
        return f"{status_part} | {metadata_part}"
    
    def _update_task_date(self, line):
        """Update task date to today"""
        return re.sub(DATE_PATTERN, f'@{self.today}', line)
    
    def _mark_task_complete(self, line):
        """Mark a task as complete"""
        # Handle both incomplete and progress tasks
        if self._is_progress_task(line):
            return line.replace(TASK_STATUS['PROGRESS'], TASK_STATUS['COMPLETE'])
        else:
            return line.replace(TASK_STATUS['INCOMPLETE'], TASK_STATUS['COMPLETE'])
    
    def _mark_task_progress(self, line):
        """Mark a task as in progress"""
        return line.replace(TASK_STATUS['INCOMPLETE'], TASK_STATUS['PROGRESS'])
    
    def _is_task_in_daily_section(self, task_id, content=None):
        """Check if a task with given ID is already in today's daily section"""
        if content is None:
            content = self.read_file()
        lines = content.split('\n')
        in_today_section = False
        
        for line in lines:
            # Check if we're entering today's daily section
            if line.strip() == f"## {self.today}":
                in_today_section = True
                continue
            
            # Check if we're leaving today's daily section
            if in_today_section and line.startswith("##") and line.strip() != f"## {self.today}":
                break
            
            # If we're in today's section, check for the task ID
            if in_today_section and self._is_task_line(line):
                if f"#{task_id}" in line:
                    return True
        
        return False
    
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
        id_matches = re.findall(TASK_ID_PATTERN, content)
        if not id_matches:
            return "001"
        
        highest_id = max(int(id_str) for id_str in id_matches)
        return f"{highest_id + 1:03d}"
    
    def find_task_by_id(self, task_id):
        """Find a task by its ID, return (line_number, line_content) or None"""
        content = self.read_file()
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and self._is_task_line(line):
                return (i, line)
        return None
    
    def find_task_by_id_in_main(self, task_id):
        """Find a task by its ID in MAIN section only, return (line_number, line_content) or None"""
        content = self.read_file()
        lines = content.split('\n')
        
        in_main_section = False
        
        for i, line in enumerate(lines):
            # Check if we're entering the MAIN section
            if line.strip() == "# MAIN":
                in_main_section = True
                continue
            
            # Check if we're leaving the MAIN section
            if in_main_section and line.startswith("# ") and line.strip() != "# MAIN":
                break
            
            # Look for the task in MAIN section
            if in_main_section and f"#{task_id}" in line and self._is_task_line(line):
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
        task_file = self.parse_file()
        recurring_tasks = []
        
        # Check all main sections
        for section_name, section in task_file.main_sections.items():
            # Check tasks in the main section
            for task in section.tasks:
                if task.recurring and task.status == ' ':
                    # Remove parentheses from recurrence pattern
                    recur_pattern = task.recurring[1:-1] if task.recurring.startswith('(') and task.recurring.endswith(')') else task.recurring
                    if self.should_recur_today(recur_pattern, task.date):
                        recurring_tasks.append({
                            'text': task.text,
                            'section': section_name,
                            'id': task.id
                        })
            
            # Check tasks in subsections
            for subsection_name, subsection in section.subsections.items():
                for task in subsection.tasks:
                    if task.recurring and task.status == ' ':
                        # Remove parentheses from recurrence pattern
                        recur_pattern = task.recurring[1:-1] if task.recurring.startswith('(') and task.recurring.endswith(')') else task.recurring
                        if self.should_recur_today(recur_pattern, task.date):
                            recurring_tasks.append({
                                'text': task.text,
                                'section': f"{section_name} > {subsection_name}",
                                'id': task.id
                            })
        
        return recurring_tasks
    
    def get_most_recent_daily_section(self, task_file):
        """Get the most recent daily section (excluding today)"""
        if not task_file.daily_sections:
            return None, []
        
        # Get all daily section dates and sort them
        daily_dates = [date for date in task_file.daily_sections.keys() if date != self.today]
        if not daily_dates:
            return None, []
        
        # Sort dates in descending order (most recent first)
        daily_dates.sort(key=lambda x: datetime.strptime(x, "%d-%m-%Y"), reverse=True)
        most_recent_date = daily_dates[0]
        most_recent_tasks = task_file.daily_sections[most_recent_date]
        
        return most_recent_date, most_recent_tasks
    
    def get_unfinished_tasks_from_daily(self, daily_tasks):
        """Get unfinished and progressed tasks from a daily section (status ' ' and '~')"""
        unfinished_tasks = []
        for task in daily_tasks:
            if task.status in [' ', '~']:  # Incomplete and progressed tasks
                unfinished_tasks.append(task)
        return unfinished_tasks
    
    def add_daily_section(self):
        """Add today's daily section with recurring tasks and carry over unfinished tasks"""
        task_file = self.parse_file()
        
        # Check if today's section already exists
        existing_tasks = task_file.get_daily_section(self.today)
        
        # Find recurring tasks that should appear today
        recurring_tasks = self.get_recurring_tasks()
        
        # Filter out tasks that are already in today's section
        existing_task_ids = {task.id for task in existing_tasks}
        new_recurring_tasks = [task for task in recurring_tasks if task['id'] not in existing_task_ids]
        
        # Get unfinished tasks from the most recent daily section
        most_recent_date, most_recent_tasks = self.get_most_recent_daily_section(task_file)
        unfinished_tasks = self.get_unfinished_tasks_from_daily(most_recent_tasks)
        
        # Filter out unfinished tasks that are already in today's section or are recurring
        recurring_task_ids = {task['id'] for task in recurring_tasks}
        new_unfinished_tasks = []
        for task in unfinished_tasks:
            # Don't carry over if already in today's section
            if task.id in existing_task_ids:
                continue
                
            # For progressed tasks: carry over if they are NOT recurring
            # (if they are recurring, recurrence pattern controls when they appear)
            if task.status == '~':
                if task.id not in recurring_task_ids:
                    new_unfinished_tasks.append(task)
            else:  # Incomplete tasks
                # Carry over if not recurring and not from a recurring task
                if (task.id not in recurring_task_ids and 
                    not task.from_section):
                    new_unfinished_tasks.append(task)
        
        if not new_recurring_tasks and not new_unfinished_tasks and existing_tasks:
            # Display the existing daily section
            self.show_daily_list()
            return
        
        # Add new recurring tasks to today's section at the TOP
        for task_data in new_recurring_tasks:
            daily_task = Task(
                id=task_data['id'],
                text=f"{task_data['text']} from {task_data['section']}",
                status=' ',
                is_daily=True,
                from_section=task_data['section']
            )
            existing_tasks.insert(0, daily_task)
        
        # Add unfinished tasks from previous day (after recurring tasks)
        for task in new_unfinished_tasks:
            # Create a copy of the task for today's section
            carried_task = Task(
                id=task.id,
                text=task.text,
                status=' ',
                is_daily=True,
                from_section=task.from_section
            )
            existing_tasks.append(carried_task)
        
        # Write the file back
        self.write_file_from_objects(task_file)
        
        # Generate status message
        status_parts = []
        if new_recurring_tasks:
            status_parts.append(f"{len(new_recurring_tasks)} new recurring tasks")
        if new_unfinished_tasks:
            # Count unfinished vs progressed tasks
            incomplete_count = sum(1 for task in new_unfinished_tasks if task.status == ' ')
            progress_count = sum(1 for task in new_unfinished_tasks if task.status == '~')
            
            task_parts = []
            if incomplete_count > 0:
                task_parts.append(f"{incomplete_count} unfinished")
            if progress_count > 0:
                task_parts.append(f"{progress_count} progressed")
            
            status_parts.append(f"{len(new_unfinished_tasks)} tasks from {most_recent_date} ({', '.join(task_parts)})")
        
        if existing_tasks:
            if status_parts:
                print(f"Daily section for {self.today} updated with {', '.join(status_parts)}")
            else:
                print(f"Daily section for {self.today} updated")
        else:
            if status_parts:
                print(f"Added daily section for {self.today} with {', '.join(status_parts)}")
            else:
                print(f"Added daily section for {self.today}")
        
        # Display the current daily section
        self.show_daily_list()
    
    def _get_task_status_info(self, task_data):
        """Get status symbol and days since activity for a task"""
        if not task_data or not task_data.get('date'):
            return "⚪", "?"
        
        try:
            task_date = datetime.strptime(task_data['date'], "%d-%m-%Y")
            days_ago = (datetime.now() - task_date).days
            
            # Status symbols: red (>7 days), yellow (>3 days), green (≤3 days)
            if days_ago > 7:
                status_symbol = "🔴"
            elif days_ago > 3:
                status_symbol = "🟡"
            else:
                status_symbol = "🟢"
            
            return status_symbol, days_ago
        except ValueError:
            return "⚪", "?"
    
    def show_status_tasks(self, scope=None):
        """Show tasks ordered by status (staleness), excluding future-snoozed tasks
        
        Args:
            scope: Optional section filter (e.g., 'projects', 'areas:work')
        """
        content = self.read_file()
        today_obj = datetime.strptime(self.today, "%d-%m-%Y")
        
        # Only look in MAIN section for status tasks
        main_lines = self.find_section("MAIN", level=1)
        if not main_lines:
            print("No MAIN section found")
            return
        
        # Parse scope if provided
        target_main_section = None
        target_subsection = None
        if scope:
            if ":" in scope:
                target_main_section, target_subsection = scope.split(":", 1)
                target_main_section = target_main_section.upper()
                target_subsection = target_subsection.upper()
            else:
                target_main_section = scope.upper()
                target_subsection = None
        
        tasks = []
        current_main_section = None
        current_subsection = None
        
        for line_num, line in enumerate(main_lines):
            # Track current section
            if line.startswith("## ") and not line.startswith("### "):
                current_main_section = line[3:].strip()
                current_subsection = None
            elif line.startswith("### "):
                current_subsection = line[4:].strip()
            
            # Parse task using new format
            task_data = self._parse_task_line(line)
            if not task_data or task_data['status'] != ' ' or not task_data['id'] or not task_data['date']:
                continue
            
            # Apply scope filtering
            if scope:
                if target_subsection:
                    # Looking for specific subsection
                    if (current_main_section != target_main_section or 
                        current_subsection != target_subsection):
                        continue
                else:
                    # Looking for main section only
                    if current_main_section != target_main_section:
                        continue
            
            # Check if task is snoozed in the future
            if task_data['snooze']:
                try:
                    snooze_date = datetime.strptime(task_data['snooze'], "%d-%m-%Y")
                    if snooze_date > today_obj:
                        continue  # Skip future-snoozed tasks
                except ValueError:
                    pass
            
            try:
                task_date = datetime.strptime(task_data['date'], "%d-%m-%Y")
                days_ago = (datetime.now() - task_date).days
                tasks.append((days_ago, task_data['date'], task_data['text'], task_data['id'], current_main_section, current_subsection))
            except ValueError:
                continue
        
        # Sort by days ago (descending = oldest first)
        tasks.sort(key=lambda x: x[0], reverse=True)
        
        # Display header
        if scope:
            if target_subsection:
                print(f"=== Task status in {target_main_section} > {target_subsection} (oldest first) ===")
            else:
                print(f"=== Task status in {target_main_section} (oldest first) ===")
        else:
            print("=== Tasks by status (oldest first) ===")
        
        if not tasks:
            if scope:
                if target_subsection:
                    print(f"No tasks found in {target_main_section} > {target_subsection}")
                else:
                    print(f"No tasks found in {target_main_section}")
            else:
                print("No tasks found")
            return
        
        for days_ago, date_str, task_text, task_id, main_section, subsection in tasks[:15]:
            status = "🔴" if days_ago > 7 else "🟡" if days_ago > 3 else "🟢"
            if subsection:
                section_info = f"{main_section} > {subsection}"
            else:
                section_info = main_section
            print(f"{status} {days_ago:2d} days | #{task_id} | {task_text} | {section_info}")
    
    def reopen_task(self, task_id):
        """Reopen a completed task by ID (mark as incomplete)"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task
        task_data = self._parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Check if task is already incomplete
        if task_data['status'] == ' ':
            print(f"Task #{task_id} is already incomplete")
            return
        
        # Check if this task is in today's daily section
        in_daily_section = False
        for i in range(line_num, -1, -1):
            if lines[i].strip() == f"## {self.today}":
                in_daily_section = True
                break
            elif lines[i].startswith("## ") and lines[i].strip() != f"## {self.today}":
                break
        
        if in_daily_section:
            # Task is in daily section - mark as incomplete there
            new_line = self._build_task_line(' ', task_data['text'], 
                                           date=task_data['date'], 
                                           recurring=task_data['recurring'],
                                           snooze=task_data['snooze'],
                                           task_id=task_data['id'])
            lines[line_num] = new_line
            self.write_file('\n'.join(lines))
            print(f"Reopened task #{task_id} in daily section")
        else:
            # Task is in main list - mark as incomplete
            new_line = self._build_task_line(' ', task_data['text'], 
                                           date=self.today, 
                                           recurring=task_data['recurring'],
                                           snooze=task_data['snooze'],
                                           task_id=task_data['id'])
            lines[line_num] = new_line
            self.write_file('\n'.join(lines))
            print(f"Reopened task #{task_id}")
    
    def complete_task(self, task_id):
        """Mark a task as complete by ID and update its date"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task
        task_data = self._parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Check if this task is in today's daily section
        in_daily_section = False
        for i in range(line_num, -1, -1):
            if lines[i].strip() == f"## {self.today}":
                in_daily_section = True
                break
            elif lines[i].startswith("## ") and lines[i].strip() != f"## {self.today}":
                break
        
        if in_daily_section:
            # Task is in daily section - mark as complete there
            if task_data['status'] == '~':
                # Change from progress to complete
                new_line = self._build_task_line('x', task_data['text'], 
                                               date=task_data['date'], 
                                               recurring=task_data['recurring'],
                                               snooze=task_data['snooze'],
                                               task_id=task_data['id'])
            elif task_data['status'] == ' ':
                # Change from incomplete to complete
                new_line = self._build_task_line('x', task_data['text'], 
                                               date=task_data['date'], 
                                               recurring=task_data['recurring'],
                                               snooze=task_data['snooze'],
                                               task_id=task_data['id'])
            else:
                # Already complete, just return
                print(f"Task #{task_id} is already complete")
                return
            
            lines[line_num] = new_line
            self.write_file('\n'.join(lines))
            print(f"Completed task #{task_id} in daily section")
        else:
            # Task is in main list - handle as before
            if task_data['recurring']:
                # Recurring task - just update date, keep [ ]
                new_line = self._build_task_line(' ', task_data['text'], 
                                               date=self.today, 
                                               recurring=task_data['recurring'],
                                               snooze=task_data['snooze'],
                                               task_id=task_data['id'])
            else:
                # Non-recurring task - mark complete and update date
                new_line = self._build_task_line('x', task_data['text'], 
                                               date=self.today, 
                                               recurring=task_data['recurring'],
                                               snooze=task_data['snooze'],
                                               task_id=task_data['id'])
            
            lines[line_num] = new_line
            self.write_file('\n'.join(lines))
            print(f"Completed task #{task_id}")
            
            # If task was completed in main list and not in daily section, add it to daily section
            if not self._is_task_in_daily_section(task_id):
                if self._add_task_to_daily_section(task_id, "complete"):
                    print(f"Added task #{task_id} to daily section")
    
    
    def _add_task_to_daily_section(self, task_id, status="complete"):
        """Add a task from main list to today's daily section with specified status"""
        # Find the task in main list
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            return False
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task using new format
        task_data = self._parse_task_line(line)
        if not task_data:
            return False
        
        task_text = task_data['text']
        
        # Find the section this task belongs to
        current_subsection = None
        current_project = None
        
        # Search backwards from the task line to find its section
        for i in range(line_num - 1, -1, -1):
            if i >= len(lines):
                continue
                
            current_line = lines[i]
            
            # Check for main section (##)
            if current_line.startswith("## ") and not current_line.startswith("### "):
                section_name = current_line[3:].strip()
                if section_name in ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]:
                    current_subsection = section_name
                    break
                elif re.match(r"## \d{2}-\d{2}-\d{4}", current_line):
                    continue
                else:
                    current_subsection = section_name
                    break
            
            # Check for project subsection (###)
            elif current_line.startswith("### "):
                if current_project is None:
                    current_project = current_line[4:].strip()
        
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
            new_task = self._build_task_line('x', f"{task_text} from {section_ref}", task_id=task_id) + "\n"
        else:  # progress
            new_task = self._build_task_line('~', f"{task_text} from {section_ref}", task_id=task_id) + "\n"
        
        # Find today's daily section and add the task at the TOP
        today_section_found = False
        for i, line in enumerate(lines):
            if line.strip() == f"## {self.today}":
                today_section_found = True
                # Add right after the daily section header
                lines.insert(i + 1, new_task)
                self.write_file('\n'.join(lines))
                return True
        
        return False
    
    def sync_daily_sections(self, days_back=3):
        """Sync completed items from today's daily section to master list and vice versa"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Find today's daily section specifically
        today_section_found = False
        completed_daily_ids = []
        progressed_daily_ids = []
        
        for line in lines:
            # Check if we're entering today's daily section
            if line.strip() == f"## {self.today}":
                today_section_found = True
                continue
            
            # If we're in today's section, process tasks
            if today_section_found:
                # Stop if we hit another daily section or leave the DAILY section
                if line.startswith("## ") and line.strip() != f"## {self.today}":
                    break
                
                # Look for completed and progressed tasks
                if self._is_complete_task(line):
                    task_id = self._extract_task_id(line)
                    if task_id:
                        completed_daily_ids.append(task_id)
                elif self._is_progress_task(line):
                    task_id = self._extract_task_id(line)
                    if task_id:
                        progressed_daily_ids.append(task_id)
        
        if not today_section_found:
            print(f"No daily section found for {self.today}")
            return
        
        # Update corresponding master list tasks by ID
        updates_made = 0
        daily_additions = 0
        
        # Handle completed tasks from daily section
        for task_id in completed_daily_ids:
            result = self.find_task_by_id_in_main(task_id)
            if result:
                line_num, line = result
                if self._is_incomplete_task(line):  # Only update if not already complete
                    # Check if recurring - if so, just update date
                    if self._is_recurring_task(line):
                        lines[line_num] = self._update_task_date(line)
                    else:
                        # Non-recurring - mark complete
                        lines[line_num] = self._mark_task_complete(line)
                        lines[line_num] = self._update_task_date(lines[line_num])
                    
                    updates_made += 1
        
        # Handle progressed tasks from daily section
        for task_id in progressed_daily_ids:
            # Skip if this task was already processed as completed
            if task_id in completed_daily_ids:
                continue
                
            result = self.find_task_by_id_in_main(task_id)
            if result:
                line_num, line = result
                if self._is_incomplete_task(line):  # Only update incomplete tasks
                    # Just update date, keep as incomplete
                    lines[line_num] = self._update_task_date(line)
                    updates_made += 1
        
        # Now check for tasks completed/progressed in main list that aren't in daily section
        main_completed_ids = []
        main_progressed_ids = []
        
        for line in lines:
            if self._is_task_line(line):
                task_id = self._extract_task_id(line)
                if task_id:
                    # Check if task is in main list and has today's date
                    if self._extract_date(line) == self.today:
                        if self._is_complete_task(line) and not self._is_recurring_task(line):
                            main_completed_ids.append(task_id)
                        elif self._is_progress_task(line):
                            main_progressed_ids.append(task_id)
        
        # Add missing tasks to daily section
        for task_id in main_completed_ids:
            if not self._is_task_in_daily_section(task_id):
                if self._add_task_to_daily_section(task_id, "complete"):
                    daily_additions += 1
        
        for task_id in main_progressed_ids:
            if not self._is_task_in_daily_section(task_id):
                if self._add_task_to_daily_section(task_id, "progress"):
                    daily_additions += 1
        
        if updates_made > 0 or daily_additions > 0:
            # Only write file if we made changes to main list (not daily additions)
            if updates_made > 0:
                self.write_file('\n'.join(lines))
            completed_count = len([id for id in completed_daily_ids if self.find_task_by_id_in_main(id)])
            progressed_count = len([id for id in progressed_daily_ids if self.find_task_by_id_in_main(id)])
            print(f"Synced {completed_count} completed and {progressed_count} progressed tasks from daily section")
            if daily_additions > 0:
                print(f"Added {daily_additions} tasks to daily section from main list")
        else:
            print("No changes needed")
    
    def add_task_to_main(self, task_text, section="INBOX"):
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
        clean_text, recurrence = self._extract_recurrence_pattern(task_text)
        
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
            section_obj = task_file.get_main_section(main_section)
            subsection_obj = section_obj.add_subsection(subsection)
            subsection_obj.add_task(new_task)
        else:
            section_obj = task_file.get_main_section(main_section)
            section_obj.add_task(new_task)
        
        # Write the file back
        self.write_file_from_objects(task_file)
        print(f"Added task #{task_id} to {main_section}:{subsection if subsection else ''}: {clean_text}")
    
    def add_task_to_daily(self, task_text):
        """Add a new task to today's daily section"""
        task_file = self.parse_file()
        task_id = self.get_next_id()
        
        # Extract recurrence pattern from task text
        clean_text, recurrence = self._extract_recurrence_pattern(task_text)
        
        # Create new task
        new_task = Task(
            id=task_id,
            text=clean_text,
            status=' ',
            recurring=recurrence,
            is_daily=True
        )
        
        # Add to today's daily section at the TOP
        task_file.get_daily_section(self.today).insert(0, new_task)
        
        # Write the file back
        self.write_file_from_objects(task_file)
        print(f"Added task #{task_id} to today's section: {clean_text}")
    
    def add_task_to_daily_by_id(self, task_id):
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
        task_data = self._parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        task_text = task_data['text']
        
        # Find the section this task belongs to
        current_subsection = None
        current_project = None
        
        # Search backwards from the task line to find its section
        for i in range(line_num - 1, -1, -1):
            if i >= len(lines):
                continue
                
            current_line = lines[i]
            
            # Check for main section (##)
            if current_line.startswith("## ") and not current_line.startswith("### "):
                section_name = current_line[3:].strip()
                if section_name in ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]:
                    current_subsection = section_name
                    break
                elif re.match(r"## \d{2}-\d{2}-\d{4}", current_line):
                    # This is a daily section, skip it
                    continue
                else:
                    # This might be a subsection under MAIN
                    current_subsection = section_name
                    break
            
            # Check for project subsection (###)
            elif current_line.startswith("### "):
                # Only set if we haven't found one yet (first one encountered when searching backwards)
                if current_project is None:
                    current_project = current_line[4:].strip()
                # Continue searching for the main section
        
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
        new_task = self._build_task_line(' ', f"{task_text} from {section_ref}", task_id=task_id) + "\n"
        replacement = f"\\1{new_task}"
        
        new_content = re.sub(today_pattern, replacement, content)
        self.write_file(new_content)
        print(f"Pulled task #{task_id} to today's section: {task_text}")
    
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
                if f"#{task_id}" in line and self._is_task_line(line):
                    # Parse and update task
                    task_data = self._parse_task_line(line)
                    if task_data and task_data['status'] == ' ':
                        new_line = self._build_task_line('~', task_data['text'], 
                                                       date=task_data['date'], 
                                                       recurring=task_data['recurring'],
                                                       snooze=task_data['snooze'],
                                                       task_id=task_data['id'])
                        lines[i] = new_line
                        task_found = True
                        break
        
        if not today_section_found:
            print(f"No daily section found for {self.today}. Run 'tasks daily' first.")
            return
        
        if not task_found:
            # Task not in daily section, check if it's in main list and add it
            result = self.find_task_by_id_in_main(task_id)
            if result:
                line_num, line = result
                if self._is_incomplete_task(line):
                    # Mark as progress in main list
                    new_line = self._mark_task_progress(line)
                    new_line = self._update_task_date(new_line)
                    lines[line_num] = new_line
                    self.write_file('\n'.join(lines))
                    
                    # Add to daily section
                    if self._add_task_to_daily_section(task_id, "progress"):
                        print(f"Marked progress on task #{task_id} and added to daily section")
                    else:
                        print(f"Marked progress on task #{task_id}")
                else:
                    print(f"Task #{task_id} is already completed or in progress")
            else:
                print(f"Task #{task_id} not found in main list or daily section")
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
        
        # Parse the task
        task_data = self._parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Build new line with snooze date
        new_line = self._build_task_line(task_data['status'], task_data['text'], 
                                       date=task_data['date'], 
                                       recurring=task_data['recurring'],
                                       snooze=snooze_date,
                                       task_id=task_data['id'])
        
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
        task_data = self._parse_task_line(line)
        
        print(f"Task #{task_id}:")
        print(f"  {line.strip()}")
        print(f"  Line: {line_num + 1}")
        
        if task_data:
            print(f"  Status: {task_data['status']}")
            print(f"  Text: {task_data['text']}")
            if task_data['date']:
                print(f"  Date: {task_data['date']}")
            if task_data['recurring']:
                print(f"  Recurring: {task_data['recurring']}")
            if task_data['snooze']:
                print(f"  Snoozed until: {task_data['snooze']}")
    
    def show_task_from_main(self, task_id):
        """Show details of a specific task by ID from main section only"""
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            print(f"No task found with ID #{task_id} in MAIN section")
            return
        
        line_num, line = result
        task_data = self._parse_task_line(line)
        
        # Find the section this task belongs to
        content = self.read_file()
        lines = content.split('\n')
        
        current_subsection = None
        current_project = None
        
        # Search backwards from the task line to find its section
        for i in range(line_num - 1, -1, -1):
            if i >= len(lines):
                continue
                
            current_line = lines[i]
            
            # Check for main section (##)
            if current_line.startswith("## ") and not current_line.startswith("### "):
                section_name = current_line[3:].strip()
                if section_name in ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]:
                    current_subsection = section_name
                    break
                elif re.match(r"## \d{2}-\d{2}-\d{4}", current_line):
                    # This is a daily section, skip it
                    continue
                else:
                    # This might be a subsection under MAIN
                    current_subsection = section_name
                    break
            
            # Check for project subsection (###)
            elif current_line.startswith("### "):
                # Only set if we haven't found one yet (first one encountered when searching backwards)
                if current_project is None:
                    current_project = current_line[4:].strip()
                # Continue searching for the main section
        
        # Build section reference
        if current_project and current_subsection:
            section_ref = f"{current_subsection} > {current_project}"
        elif current_subsection:
            section_ref = current_subsection
        else:
            section_ref = "UNKNOWN"
        
        print(f"Task #{task_id} from {section_ref}:")
        print(f"  {line.strip()}")
        print(f"  Line: {line_num + 1}")
        
        if task_data:
            print(f"  Status: {task_data['status']}")
            print(f"  Text: {task_data['text']}")
            if task_data['date']:
                print(f"  Date: {task_data['date']}")
            if task_data['recurring']:
                print(f"  Recurring: {task_data['recurring']}")
            if task_data['snooze']:
                print(f"  Snoozed until: {task_data['snooze']}")
    
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
        """Archive old daily sections to ARCHIVE section"""
        content = self.read_file()
        lines = content.split('\n')
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        archived_daily_sections = []
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
        
        # Add archived content to ARCHIVE section - only daily subsections
        archive_additions = []
        if archived_daily_sections:
            archive_additions.extend(archived_daily_sections)
        
        if archive_additions:
            # Find ARCHIVE section and add content
            for i, line in enumerate(new_lines):
                if line == "# ARCHIVE":
                    new_lines[i+1:i+1] = archive_additions
                    break
        
        new_content = '\n'.join(new_lines)
        self.write_file(new_content)
        
        total_archived = len(archived_daily_sections)
        print(f"Archived {total_archived} old daily sections")
    
    def delete_task_from_main(self, task_id):
        """Delete a task from the main list by ID"""
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            print(f"No task found with ID #{task_id} in MAIN section")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Remove the task line
        lines.pop(line_num)
        
        self.write_file('\n'.join(lines))
        print(f"Deleted task #{task_id} from main list")
    
    def delete_task_from_daily(self, task_id):
        """Delete a task from today's daily section by ID"""
        content = self.read_file()
        lines = content.split('\n')
        
        today_section_found = False
        task_found = False
        
        for i, line in enumerate(lines):
            # Check if we're entering today's daily section
            if line.strip() == f"## {self.today}":
                today_section_found = True
                continue
            
            # If we're in today's section, look for the task
            if today_section_found:
                # Stop if we hit another daily section or leave the DAILY section
                if line.startswith("## ") and line.strip() != f"## {self.today}":
                    break
                
                # Look for the task ID in this daily section
                if f"#{task_id}" in line and self._is_task_line(line):
                    # Remove the task line
                    lines.pop(i)
                    task_found = True
                    break
        
        if not today_section_found:
            print(f"No daily section found for {self.today}")
            return
        
        if not task_found:
            print(f"Task #{task_id} not found in today's daily section")
            return
        

        
        self.write_file('\n'.join(lines))
        print(f"Deleted task #{task_id} from today's daily section")
    
    def purge_task(self, task_id):
        """Delete a task from both main list and all daily sections by ID"""
        deleted_from_main = False
        deleted_from_daily = False
        
        # Read the file once
        content = self.read_file()
        lines = content.split('\n')
        
        # Delete from main list
        result = self.find_task_by_id_in_main(task_id)
        if result:
            line_num, line = result
            lines.pop(line_num)
            deleted_from_main = True
        
        # Find all instances of the task in daily sections
        indices_to_remove = []
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and self._is_task_line(line):
                # Check if this is in a daily section (not in MAIN or ARCHIVE)
                in_daily_section = False
                in_main_section = False
                in_archive_section = False
                
                # Look backwards to determine which section we're in
                for j in range(i, -1, -1):
                    if lines[j].strip() == "# MAIN":
                        in_main_section = True
                        break
                    elif lines[j].strip() == "# ARCHIVE":
                        in_archive_section = True
                        break
                    elif lines[j].startswith("## ") and re.match(r"## \d{2}-\d{2}-\d{4}", lines[j]):
                        in_daily_section = True
                        break
                
                # Only delete if it's in a daily section
                if in_daily_section and not in_main_section and not in_archive_section:
                    indices_to_remove.append(i)
        
        # Remove tasks in reverse order to maintain correct indices
        for i in sorted(indices_to_remove, reverse=True):
            lines.pop(i)
            deleted_from_daily = True
        
        # Write the file once with all changes
        if deleted_from_main or deleted_from_daily:
            self.write_file('\n'.join(lines))
        
        if deleted_from_main and deleted_from_daily:
            print(f"Purged task #{task_id} from main list and all daily sections")
        elif deleted_from_main:
            print(f"Purged task #{task_id} from main list (not found in daily sections)")
        elif deleted_from_daily:
            print(f"Purged task #{task_id} from daily sections (not found in main list)")
        else:
            print(f"No task found with ID #{task_id} in main list or daily sections")
    
    def show_config(self):
        """Show current configuration"""
        print("Current Configuration:")
        print(f"  Task file: {self.task_file}")
        print(f"  Icon set: {self.icon_set}")
        print(f"  Editor: {self.editor}")
        print(f"  Config file: {os.environ.get('PTCONFIG', '~/.ptconfig')}")
        print(f"  Available icon sets: {', '.join(sorted(self.icon_sets.keys()))}")

    def show_help(self):
        """Show detailed help information"""
        help_text = """
PARA + Daily Task Management System

USAGE:
  tasks [command] [args]

COMMANDS:
  help                   Show this help message
  config                 Show current configuration
  init                   Initialize the task file with default structure
  daily                  Add today's daily section with recurring tasks and carry over unfinished/progressed tasks from previous day
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
  add-main TEXT [SEC]    Add task to main list section (default: INBOX)
                         Use SEC:SUBSEC for subsections (e.g., PROJECTS:HOME)
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
  tasks add "write blog post" PROJECTS     # Add task to specific section
  tasks add "fix faucet" PROJECTS:HOME     # Add to subsection
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

    def show_daily_list(self):
        """Show today's daily section"""
        content = self.read_file()
        lines = content.split('\n')
        
        today_section_found = False
        daily_tasks = []
        
        for line in lines:
            if line.strip() == f"## {self.today}":
                today_section_found = True
                continue
            
            if today_section_found:
                # Stop if we hit another daily section or leave the DAILY section
                if line.startswith("## ") and line.strip() != f"## {self.today}":
                    break
                
                # Collect tasks from today's section
                if self._is_task_line(line):
                    daily_tasks.append(line)
        
        if not today_section_found:
            print(f"No daily section found for {self.today}")
            print("Run 'tasks daily' to create today's section")
            return
        
        if not daily_tasks:
            print(f"Daily section for {self.today} is empty")
            return
        
        print(f"=== Daily Tasks for {self.today} ===")
        print()
        for task in daily_tasks:
            # Parse task using new format
            task_data = self._parse_task_line(task)
            if not task_data:
                continue
            
            # Extract status and ID using current icon set
            icons = self.icon_sets[self.icon_set]
            if task_data['status'] == 'x':
                status = icons['complete']
            elif task_data['status'] == '~':
                status = icons['progress']
            else:
                status = icons['incomplete']
            
            task_id = task_data['id']
            id_display = f"#{task_id}" if task_id else ""
            
            print(f"{status} {task_data['text']} {id_display}")
    
    def edit_task(self, task_id, new_text):
        """Edit task text by ID"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task
        task_data = self._parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Validate new text
        is_valid, error = self._validate_task_text(new_text)
        if not is_valid:
            print(f"Invalid task text: {error}")
            return
        
        # Extract recurrence pattern from new text (like add command does)
        clean_text, recurrence = self._extract_recurrence_pattern(new_text)
        
        # Build new line with updated text and parsed recurrence
        new_line = self._build_task_line(task_data['status'], clean_text, 
                                       date=task_data['date'], 
                                       recurring=recurrence,
                                       snooze=task_data['snooze'],
                                       task_id=task_data['id'])
        
        lines[line_num] = new_line
        self.write_file('\n'.join(lines))
        print(f"Updated task #{task_id}: {clean_text}")
    
    def move_task(self, task_id, new_section):
        """Move task to a new section"""
        result = self.find_task_by_id(task_id)
        if not result:
            print(f"No task found with ID #{task_id}")
            return
        
        line_num, line = result
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse the task
        task_data = self._parse_task_line(line)
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
        new_task = self._build_task_line(task_data['status'], task_data['text'], 
                                       date=task_data['date'], 
                                       recurring=task_data['recurring'],
                                       snooze=task_data['snooze'],
                                       task_id=task_data['id']) + "\n"
        
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
                print(f"Main section '{main_section}' not found. Available sections:")
                main_lines = self.find_section("MAIN", level=1)
                if main_lines:
                    for line in main_lines:
                        if line.startswith("## "):
                            print(f"  - {line[3:]}")
                return
            
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
                print(f"Section '{main_section}' not found. Available sections:")
                # Look for sections in the current content
                for line in lines:
                    if line.startswith("## "):
                        print(f"  - {line[3:]}")
                return
            
            self.write_file(new_content)
            print(f"Moved task #{task_id} to {main_section}: {task_data['text']}")

    def modify_task_recurrence(self, task_id, new_recurrence):
        """Modify the recurrence pattern of a task"""
        # Find the task in main list
        result = self.find_task_by_id_in_main(task_id)
        if not result:
            print(f"Task #{task_id} not found in main list")
            return
        
        line_num, line = result
        
        # Parse the task
        task_data = self._parse_task_line(line)
        if not task_data:
            print(f"Could not parse task #{task_id}")
            return
        
        # Validate the new recurrence pattern
        if new_recurrence and not new_recurrence.startswith('(') and not new_recurrence.endswith(')'):
            # Add parentheses if not present
            new_recurrence = f"({new_recurrence})"
        
        # Validate recurrence pattern format
        if new_recurrence and not re.search(RECURRING_PATTERN, new_recurrence):
            print(f"Invalid recurrence pattern: {new_recurrence}")
            print("Valid patterns: (daily), (weekly), (monthly), (recur:2d), etc.")
            return
        
        # Update the task data
        task_data['recurring'] = new_recurrence if new_recurrence else None
        
        # Rebuild the task line
        new_line = self._build_task_line(
            task_data['status'],
            task_data['text'],
            date=task_data['date'],
            recurring=task_data['recurring'],
            snooze=task_data['snooze'],
            task_id=task_data['id']
        )
        
        # Read the file and update the line
        content = self.read_file()
        lines = content.split('\n')
        lines[line_num] = new_line
        
        # Write the file back
        new_content = '\n'.join(lines)
        self.write_file(new_content)
        
        # Show the updated task
        if new_recurrence:
            print(f"Updated task #{task_id} recurrence to {new_recurrence}")
        else:
            print(f"Removed recurrence from task #{task_id}")
        
        print(f"Task: {task_data['text']}")
        print(f"New line: {new_line}")

    def show_section(self, section_name):
        """Show a specific section from main list, supports wildcards (*) for section names"""
        content = self.read_file()
        lines = content.split('\n')
        
        # Parse section:subsection format
        if ":" in section_name:
            main_section, subsection = section_name.split(":", 1)
            main_section = main_section.upper()
            subsection = subsection.upper()
        else:
            main_section = section_name.upper()
            subsection = None
        
        # Check if we're using wildcard for main section
        use_wildcard = main_section == "*"
        
        section_found = False
        subsection_found = False
        section_tasks = []
        current_subsection = None
        matched_sections = []  # Track which sections matched for wildcard
        found_any_subsection = False  # Track if we found any matching subsections
        current_section = None  # Track current section for context
        
        in_main_section = False
        
        for line in lines:
            # Check if we're entering the MAIN section
            if line.strip() == "# MAIN":
                in_main_section = True
                continue
            
            # Check if we're leaving the MAIN section
            if in_main_section and line.startswith("# ") and line.strip() != "# MAIN":
                break
            
            if in_main_section:
                # Check for main section headers (##)
                if line.startswith("## ") and not line.startswith("### "):
                    current_section = line[3:].strip()
                    if use_wildcard:
                        # For wildcard, we're always in a "found" state
                        section_found = True
                        current_subsection = None
                        subsection_found = False  # Reset subsection_found when entering new main section
                        matched_sections.append(current_section)
                    elif current_section == main_section:
                        section_found = True
                        current_subsection = None
                        subsection_found = False  # Reset subsection_found when entering new main section
                    else:
                        # We've moved past our target section (only for non-wildcard)
                        if section_found and not use_wildcard:
                            break
                
                # Check for subsection headers (###)
                elif line.startswith("### "):
                    current_subsection = line[4:].strip()
                    if subsection and current_subsection == subsection:
                        subsection_found = True
                        found_any_subsection = True
                    elif subsection:
                        # Reset subsection_found when we find a different subsection
                        subsection_found = False
                
                # Collect tasks
                elif self._is_task_line(line):
                    # If we're looking for a specific subsection
                    if subsection:
                        if subsection_found and section_found:
                            if use_wildcard:
                                section_tasks.append((line, current_section, current_subsection))
                            else:
                                section_tasks.append(line)
                    # If we're looking for just the main section (no subsection specified)
                    elif section_found and not subsection:
                        if use_wildcard:
                            # For wildcard without subsection, collect all tasks
                            section_tasks.append((line, current_section, current_subsection))
                        else:
                            # Regular non-wildcard without subsection
                            section_tasks.append(line)
        
        if not section_found:
            if use_wildcard:
                print("No sections found in MAIN")
            else:
                print(f"Section '{main_section}' not found in MAIN")
            print("Available sections:")
            main_lines = self.find_section("MAIN", level=1)
            if main_lines:
                for line in main_lines:
                    if line.startswith("## "):
                        print(f"  - {line[3:]}")
            return
        
        if subsection and not found_any_subsection:
            if use_wildcard:
                print(f"Subsection '{subsection}' not found in any section")
            else:
                print(f"Subsection '{subsection}' not found in '{main_section}'")
            return
        
        # Display the section
        if not use_wildcard:
            if subsection:
                print(f"=== {main_section} > {subsection} ===")
            else:
                print(f"=== {main_section} ===")
        
        if not section_tasks:
            print("(No tasks)")
            return
        
        # Group tasks by section for wildcard display
        if use_wildcard and section_tasks:
            # Group tasks by section
            tasks_by_section = {}
            for task_info in section_tasks:
                if isinstance(task_info, tuple):
                    task_line, section, subsection = task_info
                    if subsection:
                        section_key = f"{section} > {subsection}"
                    else:
                        section_key = section
                    if section_key not in tasks_by_section:
                        tasks_by_section[section_key] = []
                    tasks_by_section[section_key].append(task_line)
                else:
                    # Fallback for non-wildcard (shouldn't happen)
                    if "No section" not in tasks_by_section:
                        tasks_by_section["No section"] = []
                    tasks_by_section["No section"].append(task_info)
            
            # Display grouped tasks
            for section_key, tasks in tasks_by_section.items():
                print(f"\n--- {section_key} ---")
                for task in tasks:
                    # Parse task using new format
                    task_data = self._parse_task_line(task)
                    if not task_data:
                        continue
                    
                    # Extract status and ID using current icon set
                    icons = self.icon_sets[self.icon_set]
                    if task_data['status'] == 'x':
                        status = icons['complete']
                    elif task_data['status'] == '~':
                        status = icons['progress']
                    else:
                        status = icons['incomplete']
                    
                    # Get status symbol and days for wildcard display
                    status_symbol, days_ago = self._get_task_status_info(task_data)
                    days_display = f"{days_ago}d" if isinstance(days_ago, int) else f"{days_ago}"
                    status_info = f"{status_symbol} {days_display}"
                    
                    task_id = task_data['id']
                    id_display = f"#{task_id}" if task_id else ""
                    
                    print(f"{status} {status_info} {task_data['text']} {id_display}")
        else:
            # Regular display for non-wildcard
            for task in section_tasks:
                # Parse task using new format
                task_data = self._parse_task_line(task)
                if not task_data:
                    continue
                
                # Extract status and ID using current icon set
                icons = self.icon_sets[self.icon_set]
                if task_data['status'] == 'x':
                    status = icons['complete']
                elif task_data['status'] == '~':
                    status = icons['progress']
                else:
                    status = icons['incomplete']
                
                task_id = task_data['id']
                id_display = f"#{task_id}" if task_id else ""
                
                print(f"{status} {task_data['text']} {id_display}")

    def show_all_main(self):
        """Show all sections from the main list, organized by full header (main:subsection)"""
        content = self.read_file()
        lines = content.split('\n')
        
        in_main_section = False
        current_section = None
        current_subsection = None
        section_tasks = {}  # Dictionary to store tasks by full header
        
        for line in lines:
            # Check if we're entering the MAIN section
            if line.strip() == "# MAIN":
                in_main_section = True
                continue
            
            # Check if we're leaving the MAIN section
            if in_main_section and line.startswith("# ") and line.strip() != "# MAIN":
                break
            
            if in_main_section:
                # Check for main section headers (##)
                if line.startswith("## ") and not line.startswith("### "):
                    current_section = line[3:].strip()
                    current_subsection = None
                
                # Check for subsection headers (###)
                elif line.startswith("### "):
                    current_subsection = line[4:].strip()
                
                # Collect tasks
                elif self._is_task_line(line):
                    # Create full header key
                    if current_subsection:
                        full_header = f"{current_section}:{current_subsection}"
                    else:
                        full_header = current_section
                    
                    # Initialize list for this header if it doesn't exist
                    if full_header not in section_tasks:
                        section_tasks[full_header] = []
                    
                    section_tasks[full_header].append(line)
        
        # Print all sections with their tasks, organized by full header
        if section_tasks:
            for full_header, tasks in section_tasks.items():
                print(f"\n=== {full_header} ===")
                for task in tasks:
                    task_data = self._parse_task_line(task)
                    if not task_data:
                        continue
                    
                    # Extract status and ID using current icon set
                    icons = self.icon_sets[self.icon_set]
                    if task_data['status'] == 'x':
                        status = icons['complete']
                    elif task_data['status'] == '~':
                        status = icons['progress']
                    else:
                        status = icons['incomplete']
                    
                    task_id = task_data['id']
                    id_display = f"#{task_id}" if task_id else ""
                    
                    print(f"{status} {task_data['text']} {id_display}")
        else:
            if not in_main_section:
                print("No MAIN section found in the task file.")
            else:
                print("No tasks found in the MAIN section.")

    def open_file(self, editor=None):
        """Open the tasks file with the user's selected editor (default from config)"""
        import subprocess
        import shutil
        
        # Determine which editor to use
        if editor:
            editor_cmd = editor
        else:
            # Use configured editor first, then fall back to common editors
            editors = [self.editor, 'nvim', 'vim', 'nano', 'code', 'subl', 'atom']
            editor_cmd = None
            
            for ed in editors:
                if shutil.which(ed):
                    editor_cmd = ed
                    break
            
            if not editor_cmd:
                print("No suitable editor found. Please specify an editor:")
                print("  tasks open vim")
                print("  tasks open nano")
                print("  tasks open code")
                print(f"Or configure your preferred editor in ~/.ptconfig:")
                print(f"  editor = your_preferred_editor")
                return
        
        # Ensure the task file exists
        if not self.task_file.exists():
            print(f"Task file doesn't exist at {self.task_file}")
            print("Run 'tasks init' to create it first.")
            return
        
        try:
            # Open the file with the selected editor
            subprocess.run([editor_cmd, str(self.task_file)], check=True)
            print(f"Opened {self.task_file} with {editor_cmd}")
        except subprocess.CalledProcessError as e:
            print(f"Error opening file with {editor_cmd}: {e}")
        except FileNotFoundError:
            print(f"Editor '{editor_cmd}' not found. Please install it or specify a different editor.")

def main():
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Load configuration
    config = Config.load()
    tm = TaskManager(config)
    
    if len(args) < 1:
        tm.show_help()
        return
    
    command = args[0]
    
    if command == "help":
        tm.show_help()
    elif command == "config":
        tm.show_config()
    elif command == "init":
        tm.init()
    elif command == "daily":
        # Always check for new recurring tasks and add them
        tm.add_daily_section()
    elif command == "status":
        scope = args[1] if len(args) > 1 else None
        tm.show_status_tasks(scope)
    elif command == "complete" and len(args) > 1:
        tm.complete_task(args[1])
    elif command == "done" and len(args) > 1:
        tm.complete_task(args[1])
    elif command == "reopen" and len(args) > 1:
        tm.reopen_task(args[1])
    elif command == "undone" and len(args) > 1:
        tm.reopen_task(args[1])
    elif command == "pass" and len(args) > 1:
        tm.progress_task_in_daily(args[1])
    elif command == "sync":
        tm.sync_daily_sections()
    elif command == "add" and len(args) > 1:
        # Parse section argument properly
        valid_sections = ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]
        
        # Check if last argument is a section
        last_arg = args[-1]
        main_part = last_arg.split(":")[0].upper()
        
        if main_part in valid_sections:
            # Last argument is a section/subsection
            section = last_arg
            task_text = " ".join(args[1:-1])
        else:
            # All arguments are task text
            task_text = " ".join(args[1:])
            section = "INBOX"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-main" and len(args) > 2:
        # Parse section argument properly
        valid_sections = ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]
        
        if len(args) == 3:
            # Just task text, no section
            task_text = args[2]
            section = "INBOX"
        else:
            # Check if last argument is a section
            last_arg = args[-1]
            main_part = last_arg.split(":")[0].upper()
            
            if main_part in valid_sections:
                # Last argument is a section/subsection
                section = last_arg
                task_text = " ".join(args[2:-1])
            else:
                # All arguments are task text
                task_text = " ".join(args[2:])
                section = "INBOX"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-daily" and len(args) > 1:
        tm.add_task_to_daily(" ".join(args[1:]))
    elif command == "up" and len(args) > 1:
        tm.add_task_to_daily_by_id(args[1])
    elif command == "snooze" and len(args) > 2:
        tm.snooze_task(args[1], args[2])
    elif command == "recur" and len(args) > 2:
        task_id = args[1]
        new_recurrence = " ".join(args[2:])
        tm.modify_task_recurrence(task_id, new_recurrence)

    elif command == "sections":
        tm.list_sections()
    elif command == "archive":
        if len(args) > 2:
            try:
                days = int(args[2])
                tm.archive_old_content(days)
            except ValueError:
                print("Invalid number of days. Use: tasks archive [days]")
        else:
            tm.archive_old_content()
    elif command == "delete" and len(args) > 1:
        tm.delete_task_from_main(args[1])
    elif command == "down" and len(args) > 1:
        tm.delete_task_from_daily(args[1])
    elif command == "purge" and len(args) > 1:
        tm.purge_task(args[1])
    elif command == "list":
        if len(args) > 1:
            # Check if it's a section:subsection format or a known section name
            if ":" in args[1] or args[1].upper() in ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]:
                tm.show_section(args[1])
            elif not args[1].isdigit():
                # Try as section name if it's not a number
                tm.show_section(args[1])
            else:
                # Original show task by ID functionality
                tm.show_task(args[1])
        else:
            # List all main sections when no arguments provided
            tm.show_all_main()
    elif command == "show" and len(args) > 1:
        # Check if it's a section:subsection format or wildcard
        if ":" in args[1] or args[1] == "*" or args[1].upper() in ["INBOX", "PROJECTS", "AREAS", "RESOURCES", "ZETTELKASTEN"]:
            tm.show_section(args[1])
        elif not args[1].isdigit():
            # Try as section name if it's not a number
            tm.show_section(args[1])
        else:
            # Show details of a specific task by ID from main section
            tm.show_task_from_main(args[1])
    elif command == "edit" and len(args) > 2:
        task_id = args[1]
        new_text = " ".join(args[2:])
        tm.edit_task(task_id, new_text)
    elif command == "move" and len(args) > 2:
        task_id = args[1]
        new_section = args[2]
        tm.move_task(task_id, new_section)
    elif command == "open":
        editor = args[1] if len(args) > 1 else None
        tm.open_file(editor)
    else:
        print(f"Unknown command: {command}")
        print("Run 'tasks help' to see available commands.")

if __name__ == "__main__":
    main()
