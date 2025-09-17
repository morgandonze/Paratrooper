"""
Utility functions for the PARA + Daily Task Management System.
"""

import re
from typing import Optional, Tuple
from datetime import datetime, timedelta


def extract_task_id(text: str) -> Optional[str]:
    """Extract task ID from text."""
    match = re.search(r'#(\d{3})', text)
    return match.group(1) if match else None


def extract_date(text: str) -> Optional[str]:
    """Extract date from text."""
    match = re.search(r'@(\d{2}-\d{2}-\d{4})', text)
    return match.group(1) if match else None


def is_task_line(line: str) -> bool:
    """Check if a line is a task line."""
    return line.strip().startswith('- [') and ']' in line


def is_recurring_task(text: str) -> bool:
    """Check if a task is recurring."""
    return bool(re.search(r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)', text))


def should_recur_today(recurrence: str, last_date: str, today: str) -> bool:
    """Check if a recurring task should appear today."""
    if not recurrence or not last_date:
        return False
    
    try:
        last_dt = datetime.strptime(last_date, "%d-%m-%Y")
        today_dt = datetime.strptime(today, "%d-%m-%Y")
        
        if 'daily' in recurrence:
            return True
        elif 'weekly' in recurrence:
            return (today_dt - last_dt).days >= 7
        elif 'monthly' in recurrence:
            return (today_dt - last_dt).days >= 30
        elif 'recur:' in recurrence:
            # Extract custom recurrence pattern
            match = re.search(r'recur:(\d+)', recurrence)
            if match:
                days = int(match.group(1))
                return (today_dt - last_dt).days >= days
        
        return False
    except ValueError:
        return False


def extract_recurrence_pattern(text: str) -> Tuple[str, Optional[str]]:
    """Extract recurrence pattern from task text."""
    # Look for recurrence pattern in parentheses
    match = re.search(r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)', text)
    if match:
        recurrence = match.group(0)
        clean_text = text.replace(recurrence, '').strip()
        return clean_text, recurrence
    
    return text, None


def validate_task_text(text: str) -> Tuple[bool, Optional[str]]:
    """Validate task text according to format rules."""
    if not text or text.strip() != text:
        return False, "Task text cannot be empty or have leading/trailing spaces"
    
    # Check for forbidden characters (excluding parentheses for recurrence)
    for char in ['@', '#', '|', '(', ')', '[', ']', '{', '}', '<', '\\', '~', '`']:
        if char in text and char != '(' and char != ')':
            return False, f"Task text cannot contain '{char}' character"
    
    # Check that parentheses are only used for recurrence patterns
    if '(' in text or ')' in text:
        try:
            clean_text, recurrence = extract_recurrence_pattern(text)
            if not recurrence:
                return False, "Parentheses can only be used for recurrence patterns like (daily), (weekly), etc."
        except ValueError as e:
            return False, str(e)
    
    return True, None


def parse_task_line(line: str) -> Optional[dict]:
    """Parse a task line using new format with | separator."""
    if not is_task_line(line):
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
    is_valid, error = validate_task_text(task_text)
    if not is_valid:
        return None
    
    # Parse metadata
    id_match = re.search(r'#(\d{3})', metadata_part)
    date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', metadata_part)
    snooze_match = re.search(r'snooze:(\d{2}-\d{2}-\d{4})', metadata_part)
    recur_match = re.search(r'\(([^)]*(?:daily|weekly|monthly|recur:)[^)]*)\)', metadata_part)
    
    return {
        'status': status,
        'text': task_text,
        'id': id_match.group(1) if id_match else None,
        'date': date_match.group(1) if date_match else None,
        'snooze': snooze_match.group(1) if snooze_match else None,
        'recurring': recur_match.group(0) if recur_match else None,
        'raw_line': line
    }


def build_task_line(status: str, text: str, date: Optional[str] = None, 
                   recurring: Optional[str] = None, snooze: Optional[str] = None, 
                   task_id: Optional[str] = None) -> str:
    """Build a task line using new format with | separator."""
    # Validate task text
    is_valid, error = validate_task_text(text)
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
    
    if metadata_parts:
        metadata_part = " ".join(metadata_parts)
        return f"{status_part} | {metadata_part}"
    else:
        return status_part


def get_next_id(tasks: list) -> str:
    """Get the next available task ID."""
    if not tasks:
        return "001"
    
    # Extract all existing IDs
    existing_ids = set()
    for task in tasks:
        if hasattr(task, 'id') and task.id:
            try:
                existing_ids.add(int(task.id))
            except ValueError:
                continue
    
    # Find the next available ID
    next_id = 1
    while next_id in existing_ids:
        next_id += 1
    
    return f"{next_id:03d}"


def format_date(date_str: str) -> str:
    """Format date string consistently."""
    try:
        # Try to parse and reformat the date
        dt = datetime.strptime(date_str, "%d-%m-%Y")
        return dt.strftime("%d-%m-%Y")
    except ValueError:
        return date_str


def is_stale_task(task, today: str, stale_days: int = 7) -> bool:
    """Check if a task is stale (not updated for N days)."""
    if not task.date:
        return True
    
    try:
        task_date = datetime.strptime(task.date, "%d-%m-%Y")
        today_date = datetime.strptime(today, "%d-%m-%Y")
        days_old = (today_date - task_date).days
        return days_old >= stale_days
    except ValueError:
        return True
