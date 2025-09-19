#!/usr/bin/env python3
"""
Data models for the Paratrooper task management system.

This module contains the core data structures: Config, Task, Section, and TaskFile.
"""

import re
import os
import configparser
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict

# Configuration
TODAY = datetime.now().strftime("%d-%m-%Y")

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
FORBIDDEN_TASK_CHARS = ['@', '#', '|', '(', ')', '[', ']', '{', '}', '<', '\\', '~', '`']

# Task status constants
TASK_STATUS = {
    'INCOMPLETE': '- [ ]',
    'COMPLETE': '- [x]',
    'PROGRESS': '- [~]'
}


@dataclass
class Config:
    """Configuration settings for the task manager"""
    task_file: Path
    icon_set: str
    editor: str
    carry_over_enabled: bool = True
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file or create default"""
        if config_path is None:
            config_path = Path(os.environ.get('PTCONFIG', '~/.ptconfig')).expanduser()
        
        # Default configuration
        default_config = cls(
            task_file=Path.home() / "home" / "tasks.md",
            icon_set="default",
            editor="nvim",
            carry_over_enabled=True
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
            
            # Load carry over setting
            carry_over_enabled = default_config.carry_over_enabled
            if 'general' in config and 'carry_over_enabled' in config['general']:
                carry_over_enabled = config['general'].getboolean('carry_over_enabled')
            
            return cls(task_file=task_file, icon_set=icon_set, editor=editor, carry_over_enabled=carry_over_enabled)
            
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

# Carry over incomplete tasks from previous day (true/false)
carry_over_enabled = {str(config.carry_over_enabled).lower()}
""")
        print(f"Created default configuration file at {config_path}")


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
        # Include "from" information in the task text if it exists and isn't already there
        task_text = self.text
        if self.from_section and f" from {self.from_section}" not in self.text:
            task_text = f"{self.text} from {self.from_section}"
        
        status_part = f"- [{self.status}] {task_text}"
        
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
        
        # Daily sections - only show the most recent day
        if self.daily_sections:
            lines.append('# DAILY')
            lines.append('')
            # Get the most recent date
            most_recent_date = max(self.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
            lines.append(f'## {most_recent_date}')
            for task in self.daily_sections[most_recent_date]:
                lines.append(task.to_markdown())
            lines.append('')
        
        # Main sections
        if self.main_sections:
            lines.append('# MAIN')
            lines.append('')
            section_list = list(self.main_sections.values())
            for i, section in enumerate(section_list):
                lines.append(section.to_markdown())
                # Only add blank line if this is not the last section
                if i < len(section_list) - 1:
                    lines.append('')
        
        # Archive sections - include all non-recent daily sections
        if self.archive_sections or (self.daily_sections and len(self.daily_sections) > 1):
            lines.append('# ARCHIVE')
            lines.append('')
            
            # Add all non-recent daily sections to archive
            if self.daily_sections and len(self.daily_sections) > 1:
                most_recent_date = max(self.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
                for date in sorted(self.daily_sections.keys(), reverse=True):
                    if date != most_recent_date:
                        lines.append(f'## {date}')
                        for task in self.daily_sections[date]:
                            lines.append(task.to_markdown())
                        lines.append('')
            
            # Add existing archive sections
            for section_name, tasks in self.archive_sections.items():
                lines.append(f'## {section_name}')
                for task in tasks:
                    lines.append(task.to_markdown())
                lines.append('')
        
        return '\n'.join(lines)
    
    def reorganize_daily_sections(self):
        """Move non-recent daily sections to archive"""
        if not self.daily_sections or len(self.daily_sections) <= 1:
            return
        
        # Get the most recent date
        most_recent_date = max(self.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
        
        # Move non-recent daily sections to archive
        dates_to_move = [date for date in self.daily_sections.keys() if date != most_recent_date]
        for date in dates_to_move:
            # Move tasks to archive
            if date not in self.archive_sections:
                self.archive_sections[date] = []
            self.archive_sections[date].extend(self.daily_sections[date])
            # Remove from daily sections
            del self.daily_sections[date]
