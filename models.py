"""
Core data models for the PARA + Daily Task Management System.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

# Constants
TASK_ID_PATTERN = r'#(\d{3})'
DATE_PATTERN = r'@(\d{2}-\d{2}-\d{4})'
SNOOZE_PATTERN = r'snooze:(\d{2}-\d{2}-\d{4})'
RECURRING_PATTERN = r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)'
FORBIDDEN_TASK_CHARS = ['@', '#', '|', '(', ')', '[', ']', '{', '}', '<', '\\', '~', '`']


@dataclass
class Task:
    """Represents a single task with all its metadata."""
    id: str
    text: str
    status: str = ' '  # ' ' = not started, '~' = in progress, 'x' = complete
    date: Optional[str] = None
    recurring: Optional[str] = None
    snooze: Optional[str] = None
    due: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    from_section: Optional[str] = None

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
                metadata['recurring'] = recur_match.group(0)
            
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
            section=section,
            subsection=subsection,
            **{k: v for k, v in metadata.items() if k != 'id'}
        )


@dataclass
class Section:
    """Represents a section containing tasks."""
    name: str
    level: int
    tasks: List[Task] = field(default_factory=list)
    subsections: Dict[str, 'Section'] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the section after creation."""
        if not self.tasks:
            self.tasks = []
        if not self.subsections:
            self.subsections = {}

    def add_task(self, task: Task):
        """Add a task to this section."""
        self.tasks.append(task)

    def add_subsection(self, name: str) -> 'Section':
        """Add a new subsection to this section."""
        subsection = Section(name, self.level + 1)
        self.subsections[name] = subsection
        return subsection

    def get_subsection(self, name: str) -> Optional['Section']:
        """Get a subsection by name."""
        return self.subsections.get(name)

    def to_markdown(self) -> str:
        """Convert section to markdown format."""
        lines = [f"{'#' * self.level} {self.name}", ""]
        
        # Add tasks
        for task in self.tasks:
            lines.append(task.to_markdown())
        
        # Add subsections
        for subsection in self.subsections.values():
            lines.append(subsection.to_markdown())
        
        return "\n".join(lines)


@dataclass
class TaskFile:
    """Represents the entire task file structure."""
    main_sections: Dict[str, Section] = field(default_factory=dict)
    daily_sections: Dict[str, List[Task]] = field(default_factory=dict)
    archive_sections: Dict[str, List[Task]] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the task file after creation."""
        if not self.main_sections:
            self.main_sections = {}
        if not self.daily_sections:
            self.daily_sections = {}
        if not self.archive_sections:
            self.archive_sections = {}

    def get_main_section(self, name: str) -> Section:
        """Get or create a main section."""
        if name not in self.main_sections:
            self.main_sections[name] = Section(name, 2)
        return self.main_sections[name]

    def get_daily_section(self, date: str) -> List[Task]:
        """Get or create a daily section."""
        if date not in self.daily_sections:
            self.daily_sections[date] = []
        return self.daily_sections[date]

    def to_markdown(self) -> str:
        """Convert the entire task file to markdown format."""
        lines = []
        
        # Daily sections - only show the most recent day
        if self.daily_sections:
            lines.append('# DAILY')
            lines.append('')
            # Get the most recent date
            most_recent_date = max(self.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
            lines.append(f'## {most_recent_date}')
            lines.append('')
            for task in self.daily_sections[most_recent_date]:
                lines.append(task.to_markdown())
            lines.append('')
        
        # Main sections
        if self.main_sections:
            lines.append('# MAIN')
            lines.append('')
            for section in self.main_sections.values():
                lines.append(section.to_markdown())
            lines.append('')
        
        # Archive sections - include all non-recent daily sections
        if self.archive_sections or (self.daily_sections and len(self.daily_sections) > 1):
            lines.append('# ARCHIVE')
            lines.append('')
            
            # Add all non-recent daily sections to archive
            if self.daily_sections and len(self.daily_sections) > 1:
                most_recent_date = max(self.daily_sections.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
                for date, tasks in self.daily_sections.items():
                    if date != most_recent_date and tasks:
                        lines.append(f'## {date}')
                        lines.append('')
                        for task in tasks:
                            lines.append(task.to_markdown())
                        lines.append('')
            
            # Add archive sections
            for section_name, tasks in self.archive_sections.items():
                if tasks:
                    lines.append(f'## {section_name}')
                    lines.append('')
                    for task in tasks:
                        lines.append(task.to_markdown())
                    lines.append('')
        
        return '\n'.join(lines)
