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
# SNOOZE_PATTERN removed - snoozing now handled by future dates
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
    editor: str
    carry_over_enabled: bool = True
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> 'Config':
        """Load configuration from file or create default"""
        if config_path is None:
            # Check for local .ptconfig first, then global config
            local_config = Path('.ptconfig')
            if local_config.exists():
                config_path = local_config
            else:
                config_path = Path(os.environ.get('PTCONFIG', '~/.ptconfig')).expanduser()
        
        # Default configuration
        default_config = cls(
            task_file=Path.home() / "home" / "tasks.md",
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
            
            # Load editor
            editor = default_config.editor
            if 'general' in config and 'editor' in config['general']:
                editor = config['general']['editor']
            
            # Load carry over setting
            carry_over_enabled = default_config.carry_over_enabled
            if 'general' in config and 'carry_over_enabled' in config['general']:
                carry_over_enabled = config['general'].getboolean('carry_over_enabled')
            
            return cls(task_file=task_file, editor=editor, carry_over_enabled=carry_over_enabled)
            
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
    section: Optional[str] = None
    subsection: Optional[str] = None
    is_daily: bool = False
    from_section: Optional[str] = None  # For daily tasks, shows where it came from
    
    def to_markdown(self) -> str:
        """Convert task to markdown format using centralized formatter"""
        from task_formatter import TaskFormatter
        formatter = TaskFormatter()
        return formatter.format_for_file(self)
    
    @classmethod
    def from_markdown(cls, line: str, section: str = None, subsection: str = None) -> Optional['Task']:
        """Parse a markdown line into a Task object using explicit pipe-separated format"""
        if not line.strip().startswith('- ['):
            return None
        
        # Extract status and ID
        status_match = re.match(r'- \[(.)\]\s*(?:#(\d{3}))?', line)
        if not status_match:
            return None
        status = status_match.group(1)
        task_id = status_match.group(2) or ''
        
        # Split by pipes to get explicit fields
        parts = line.split(' | ')
        if len(parts) < 2:
            return None
        
        # Remove the status+ID part from the first element
        remaining_first = parts[0]
        if task_id:
            remaining_first = remaining_first.replace(f'- [{status}] #{task_id}', '').strip()
        else:
            remaining_first = remaining_first.replace(f'- [{status}]', '').strip()
        
        # Reconstruct parts array with cleaned first element
        if remaining_first:
            parts[0] = remaining_first
        else:
            parts = parts[1:]  # Remove empty first element
        
        # Filter out empty parts to handle extra pipes
        parts = [part.strip() for part in parts if part.strip()]
        
        # Parse fields based on position
        task_text = parts[0] if len(parts) > 0 else ''
        section_field = parts[1] if len(parts) > 1 else ''
        date_field = parts[2] if len(parts) > 2 else ''
        recurring_field = parts[3] if len(parts) > 3 else ''
        
        # Parse section field (may contain "SECTION > SUBSECTION")
        parsed_section = section.upper() if section else None
        parsed_subsection = subsection
        if section_field:
            if ' > ' in section_field:
                parsed_section, parsed_subsection = section_field.split(' > ', 1)
                parsed_section = parsed_section.upper()
            else:
                parsed_section = section_field.upper()
                parsed_subsection = None
        
        # Parse date field (no @ prefix needed)
        parsed_date = date_field if date_field else None
        
        # Parse recurring field (no () wrapper needed)
        parsed_recurring = f"({recurring_field})" if recurring_field else None
        
        return cls(
            id=task_id,
            text=task_text,
            status=status,
            date=parsed_date,
            recurring=parsed_recurring,
            section=parsed_section,
            subsection=parsed_subsection
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
        
        # Always include DAILY section
        lines.append('# DAILY')
        lines.append('')
        
        # Daily sections - only show the most recent day
        if self.daily_sections:
            # Get the most recent date
            most_recent_date = max(self.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
            lines.append(f'## {most_recent_date}')
            for task in self.daily_sections[most_recent_date]:
                lines.append(task.to_markdown())
            lines.append('')
        
        # Always include MAIN section
        lines.append('# MAIN')
        lines.append('')
        
        # Main sections
        if self.main_sections:
            section_list = list(self.main_sections.values())
            for i, section in enumerate(section_list):
                lines.append(section.to_markdown())
                # Only add blank line if this is not the last section
                if i < len(section_list) - 1:
                    lines.append('')
        
        # Always include ARCHIVE section
        lines.append('# ARCHIVE')
        lines.append('')
        
        # Archive sections - show all archived sections and move non-recent daily sections
        if self.archive_sections or (self.daily_sections and len(self.daily_sections) > 1):
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
