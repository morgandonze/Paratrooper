#!/usr/bin/env python3
"""
Centralized task formatting for consistent display across all contexts.

This module provides a single source of truth for how tasks are displayed
in different contexts, ensuring consistency while allowing for context-specific
deviations where warranted.
"""

from typing import Optional
from models import Task


class TaskFormatter:
    """Centralized task formatting with context-specific variations."""
    
    def __init__(self):
        """Initialize formatter."""
        pass
    
    def format_for_file(self, task: Task) -> str:
        """
        Format task for file storage (explicit pipe-separated format).
        
        Format: - [x] | task description | section > subsection | @date | #id | (recurring)
        This is the canonical format used in the task file.
        """
        # Clean task text (remove any existing "from" info since we have explicit section fields)
        task_text = task.text
        if task.from_section and f" from {task.from_section}" in task_text:
            task_text = task_text.replace(f" from {task.from_section}", "")
        
        # Build section field (combine section and subsection)
        section_field = ""
        if task.section:
            if task.subsection:
                section_field = f"{task.section} > {task.subsection}"
            else:
                section_field = task.section
        
        # Build explicit format
        parts = [
            f"- [{task.status}] #{task.id}" if task.id else f"- [{task.status}]",
            task_text,
            section_field,
            task.date or "",
            task.recurring.replace("(", "").replace(")", "") if task.recurring else ""
        ]
        
        return " | ".join(parts)
    
    def format_for_daily_list(self, task: Task) -> str:
        """
        Format task for daily list display.
        
        Standard format: - [x] task text from WORK | @date #001
        Uses same format as file for consistency, but could use icons if preferred.
        """
        return self.format_for_file(task)
    
    def format_for_section_display(self, task: Task, indent: str = "  ") -> str:
        """
        Format task for section display (with indentation).
        
        Standard format:   - [x] task text | @date #001
        Same as file format but with indentation for visual hierarchy.
        """
        return f"{indent}{self.format_for_file(task)}"
    
    def format_for_status_display(self, task: Task, days_old: int, section: str) -> str:
        """
        Format task for status/staleness display.
        
        Special format: 🔴 7 days | #001 | task text | WORK
        This format is warranted because it needs to show staleness information.
        """
        # Color coding based on staleness
        if days_old >= 7:
            color = "🔴"  # Red for very stale
        elif days_old >= 3:
            color = "🟡"  # Yellow for stale
        else:
            color = "🟢"  # Green for recent
        
        task_id = task.id or "???"
        return f"{color} {days_old:2d} days | #{task_id} | {task.text} | {section}"
    
    def format_for_task_details(self, task: Task, line_number: Optional[int] = None) -> str:
        """
        Format task for detailed display (multi-line format).
        
        Multi-line format for detailed inspection:
        Task #001:
          - [x] task text | @date #001
          Line: 7
          Status: x
          Text: task text
          Date: 18-09-2025
        """
        lines = []
        lines.append(f"Task #{task.id}:")
        lines.append(f"  {self.format_for_file(task)}")
        
        if line_number is not None:
            lines.append(f"  Line: {line_number}")
        
        lines.append(f"  Status: {task.status}")
        lines.append(f"  Text: {task.text}")
        
        if task.date:
            lines.append(f"  Date: {task.date}")
        if task.recurring:
            lines.append(f"  Recurring: {task.recurring}")
        # Snoozing is now handled by setting date to future
        if task.date:
            from datetime import datetime
            try:
                task_date = datetime.strptime(task.date, "%d-%m-%Y")
                today = datetime.now()
                if task_date > today:
                    lines.append(f"  Snoozed until: {task.date}")
            except ValueError:
                pass
        
        return "\n".join(lines)
    
