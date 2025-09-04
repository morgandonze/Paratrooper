#!/usr/bin/env python3
"""
Unit tests for PARA + Daily Task Management System
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the TaskManager class
from tasks import TaskManager

class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_tasks.md"
        
        # Create TaskManager instance with test file
        with patch('tasks.TASK_FILE', self.test_file):
            self.tm = TaskManager()
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove test directory and files
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_read_file_creates_default_structure(self):
        """Test that read_file creates default structure when file doesn't exist"""
        content = self.tm.read_file()
        
        expected_sections = [
            "# DAILY",
            "# MAIN",
            "## INBOX",
            "## PROJECTS", 
            "## AREAS",
            "## RESOURCES",
            "## ZETTELKASTEN",
            "# ARCHIVE"
        ]
        
        for section in expected_sections:
            self.assertIn(section, content)
    
    def test_is_task_line(self):
        """Test task line detection"""
        # Valid task lines
        self.assertTrue(self.tm._is_task_line("- [ ] Test task"))
        self.assertTrue(self.tm._is_task_line("- [x] Completed task"))
        self.assertTrue(self.tm._is_task_line("- [~] Progress task"))
        
        # Invalid task lines
        self.assertFalse(self.tm._is_task_line("# Header"))
        self.assertFalse(self.tm._is_task_line("## Subheader"))
        self.assertFalse(self.tm._is_task_line("Just text"))
        self.assertFalse(self.tm._is_task_line(""))
    
    def test_task_status_detection(self):
        """Test different task status detection"""
        # Incomplete tasks
        self.assertTrue(self.tm._is_incomplete_task("- [ ] Test task"))
        self.assertFalse(self.tm._is_incomplete_task("- [x] Test task"))
        self.assertFalse(self.tm._is_incomplete_task("- [~] Test task"))
        
        # Complete tasks
        self.assertTrue(self.tm._is_complete_task("- [x] Test task"))
        self.assertFalse(self.tm._is_complete_task("- [ ] Test task"))
        self.assertFalse(self.tm._is_complete_task("- [~] Test task"))
        
        # Progress tasks
        self.assertTrue(self.tm._is_progress_task("- [~] Test task"))
        self.assertFalse(self.tm._is_progress_task("- [ ] Test task"))
        self.assertFalse(self.tm._is_progress_task("- [x] Test task"))
    
    def test_extract_task_id(self):
        """Test task ID extraction"""
        # Valid IDs with new format
        self.assertEqual(self.tm._extract_task_id("- [ ] Task | @15-01-2025 #001"), "001")
        self.assertEqual(self.tm._extract_task_id("- [x] Task | @15-01-2025 #042"), "042")
        self.assertEqual(self.tm._extract_task_id("- [~] Task | @15-01-2025 #123"), "123")
        
        # Invalid or missing IDs
        self.assertIsNone(self.tm._extract_task_id("- [ ] Task | @15-01-2025"))  # No ID
        self.assertIsNone(self.tm._extract_task_id("- [ ] Task | @15-01-2025 #abc"))  # Non-numeric
        self.assertIsNone(self.tm._extract_task_id("# Header"))
    
    def test_extract_date(self):
        """Test date extraction"""
        # Valid dates with new format
        self.assertEqual(self.tm._extract_date("- [ ] Task | @15-01-2025 #001"), "15-01-2025")
        self.assertEqual(self.tm._extract_date("- [x] Task | @04-09-2025 #002"), "04-09-2025")
        
        # Invalid or missing dates
        self.assertIsNone(self.tm._extract_date("- [ ] Task | #001"))  # No date
        self.assertIsNone(self.tm._extract_date("- [ ] Task | @invalid-date #001"))
    
    def test_is_recurring_task(self):
        """Test recurring task detection"""
        # Valid recurring patterns with new format
        self.assertTrue(self.tm._is_recurring_task("- [ ] Task | @15-01-2025 (daily) #001"))
        self.assertTrue(self.tm._is_recurring_task("- [ ] Task | @15-01-2025 (weekly) #002"))
        self.assertTrue(self.tm._is_recurring_task("- [ ] Task | @15-01-2025 (monthly) #003"))
        self.assertTrue(self.tm._is_recurring_task("- [ ] Task | @15-01-2025 (recur:3d) #004"))
        self.assertTrue(self.tm._is_recurring_task("- [ ] Task | @15-01-2025 (weekly:tue) #005"))
        
        # Non-recurring tasks
        self.assertFalse(self.tm._is_recurring_task("- [ ] Regular task | @15-01-2025 #001"))
        self.assertFalse(self.tm._is_recurring_task("- [ ] Task | @15-01-2025 snooze:20-01-2025 #002"))
    
    def test_get_next_id(self):
        """Test ID generation"""
        # Empty file should start with 001
        self.assertEqual(self.tm.get_next_id(), "001")
        
        # Add a task and check next ID
        self.tm.write_file("""# MAIN
## INBOX
- [ ] Task | @15-01-2025 #001
""")
        self.assertEqual(self.tm.get_next_id(), "002")
        
        # Add more tasks and check
        self.tm.write_file("""# MAIN
## INBOX
- [ ] Task | @15-01-2025 #001
- [ ] Task | @15-01-2025 #005
- [ ] Task | @15-01-2025 #003
""")
        self.assertEqual(self.tm.get_next_id(), "006")  # Should find highest and increment
    
    def test_find_task_by_id(self):
        """Test finding tasks by ID"""
        self.tm.write_file("""# MAIN
## INBOX
- [ ] First task | @15-01-2025 #001
- [ ] Second task | @15-01-2025 #002
""")
        
        # Find existing task
        result = self.tm.find_task_by_id("001")
        self.assertIsNotNone(result)
        line_num, line = result
        self.assertIn("First task", line)
        
        # Find non-existent task
        result = self.tm.find_task_by_id("999")
        self.assertIsNone(result)
    
    def test_find_task_by_id_in_main(self):
        """Test finding tasks by ID in MAIN section only"""
        self.tm.write_file("""# DAILY
## 04-09-2025
- [ ] Daily task | @15-01-2025 #001

# MAIN
## INBOX
- [ ] Main task | @15-01-2025 #002

# ARCHIVE
- [ ] Archived task | @15-01-2025 #003
""")
        
        # Should find task in MAIN section
        result = self.tm.find_task_by_id_in_main("002")
        self.assertIsNotNone(result)
        line_num, line = result
        self.assertIn("Main task", line)
        
        # Should not find task in DAILY section
        result = self.tm.find_task_by_id_in_main("001")
        self.assertIsNone(result)
        
        # Should not find task in ARCHIVE section
        result = self.tm.find_task_by_id_in_main("003")
        self.assertIsNone(result)
    
    def test_should_recur_today(self):
        """Test recurring task logic"""
        today = datetime.now()
        
        # Daily tasks should always recur
        self.assertTrue(self.tm.should_recur_today("daily", "01-01-2025"))
        
        # Weekdays logic
        if today.weekday() < 5:  # Monday-Friday
            self.assertTrue(self.tm.should_recur_today("weekdays", "01-01-2025"))
        else:  # Weekend
            self.assertFalse(self.tm.should_recur_today("weekdays", "01-01-2025"))
        
        # Weekly logic (default Sunday)
        if today.weekday() == 6:  # Sunday
            self.assertTrue(self.tm.should_recur_today("weekly", "01-01-2025"))
        else:
            self.assertFalse(self.tm.should_recur_today("weekly", "01-01-2025"))
        
        # Monthly logic (default 1st)
        if today.day == 1:
            self.assertTrue(self.tm.should_recur_today("monthly", "01-01-2025"))
        else:
            self.assertFalse(self.tm.should_recur_today("monthly", "01-01-2025"))
    
    def test_format_file(self):
        """Test file formatting"""
        # Create file with inconsistent spacing
        self.tm.write_file("""# DAILY
## 04-09-2025
- [ ] Task 1 #001
- [ ] Task 2 #002
# MAIN
## INBOX
- [ ] Task 3 #003
## PROJECTS
- [ ] Task 4 #004
""")
        
        # Format should add proper spacing
        self.tm.format_file()
        content = self.tm.read_file()
        
        # Should have empty lines between sections and tasks
        lines = content.split('\n')
        
        # Check for proper spacing
        self.assertIn("# DAILY", lines)
        self.assertIn("", lines)  # Empty line
        self.assertIn("## 04-09-2025", lines)
        self.assertIn("", lines)  # Empty line
        self.assertIn("- [ ] Task 1 #001", lines)
        self.assertIn("", lines)  # Empty line
        self.assertIn("- [ ] Task 2 #002", lines)
        self.assertIn("", lines)  # Empty line
        self.assertIn("# MAIN", lines)
    
    def test_add_task_to_main(self):
        """Test adding tasks to main list"""
        # Add to default section (INBOX)
        self.tm.add_task_to_main("Test task")
        content = self.tm.read_file()
        self.assertIn("Test task", content)
        self.assertIn("## INBOX", content)
        
        # Add to specific section
        self.tm.add_task_to_main("Project task", "PROJECTS")
        content = self.tm.read_file()
        self.assertIn("Project task", content)
        self.assertIn("## PROJECTS", content)
        
        # Add to subsection
        self.tm.add_task_to_main("Home task", "PROJECTS:HOME")
        content = self.tm.read_file()
        self.assertIn("Home task", content)
        self.assertIn("### HOME", content)
    
    def test_complete_task(self):
        """Test completing tasks"""
        self.tm.write_file("""# MAIN
## INBOX
- [ ] Test task | @04-09-2025 #001
- [ ] Recurring task | @04-09-2025 (daily) #002
""")
        
        # Complete non-recurring task
        self.tm.complete_task("001")
        content = self.tm.read_file()
        self.assertIn("- [x] Test task", content)
        
        # Complete recurring task (should just update date)
        self.tm.complete_task("002")
        content = self.tm.read_file()
        self.assertIn("- [ ] Recurring task", content)  # Should stay incomplete
        # Date should be updated to today
    
    def test_snooze_task(self):
        """Test snoozing tasks"""
        self.tm.write_file("""# MAIN
## INBOX
- [ ] Test task | @04-09-2025 #001
""")
        
        # Snooze for 3 days
        self.tm.snooze_task("001", "3")
        content = self.tm.read_file()
        self.assertIn("snooze:", content)
        
        # Snooze until specific date
        self.tm.snooze_task("001", "10-09-2025")
        content = self.tm.read_file()
        self.assertIn("snooze:10-09-2025", content)
    
    def test_show_stale_tasks(self):
        """Test stale task detection"""
        # Create tasks with different dates
        old_date = (datetime.now() - timedelta(days=10)).strftime("%d-%m-%Y")
        recent_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        
        self.tm.write_file(f"""# MAIN
## INBOX
- [ ] Old task | @{old_date} #001
- [ ] Recent task | @{recent_date} #002
- [ ] Snoozed task | @{old_date} snooze:20-09-2025 #003
""")
        
        # Capture output
        with patch('builtins.print') as mock_print:
            self.tm.show_stale_tasks()
            
            # Should show old task but not snoozed task
            output = mock_print.call_args_list
            output_str = str(output)
            self.assertIn("Old task", output_str)
            self.assertNotIn("Snoozed task", output_str)
    
    def test_parse_task_line(self):
        """Test new task line parsing"""
        # Valid task line
        task_line = "- [ ] test task | @15-01-2025 (daily) snooze:20-01-2025 #001"
        task_data = self.tm._parse_task_line(task_line)
        
        self.assertIsNotNone(task_data)
        self.assertEqual(task_data['status'], ' ')
        self.assertEqual(task_data['text'], 'test task')
        self.assertEqual(task_data['id'], '001')
        self.assertEqual(task_data['date'], '15-01-2025')
        self.assertEqual(task_data['recurring'], '(daily)')
        self.assertEqual(task_data['snooze'], '20-01-2025')
        
        # Invalid task line (no separator)
        invalid_line = "- [ ] test task @15-01-2025 #001"
        task_data = self.tm._parse_task_line(invalid_line)
        self.assertIsNone(task_data)
    
    def test_validate_task_text(self):
        """Test task text validation"""
        # Valid texts
        valid_texts = [
            "simple task",
            "task with numbers 123",
            "task with punctuation: . , ! ? : ; - _",
            'task with "quotes"',
            "UPPERCASE and lowercase",
        ]
        
        for text in valid_texts:
            with self.subTest(text=text):
                is_valid, error = self.tm._validate_task_text(text)
                self.assertTrue(is_valid, f"Text should be valid: {text}")
                self.assertIsNone(error)
        
        # Invalid texts
        invalid_texts = [
            ("", "Task text cannot be empty or have leading/trailing spaces"),
            (" ", "Task text cannot be empty or have leading/trailing spaces"),
            (" task", "Task text cannot be empty or have leading/trailing spaces"),
            ("task ", "Task text cannot be empty or have leading/trailing spaces"),
            ("task with @ symbol", "Task text cannot contain '@' character"),
            ("task with # symbol", "Task text cannot contain '#' character"),
            ("task with | pipe", "Task text cannot contain '|' character"),
            ("task with (parentheses)", "Task text cannot contain '(' character"),
            ("task with [brackets]", "Task text cannot contain '[' character"),
        ]
        
        for text, expected_error in invalid_texts:
            with self.subTest(text=text):
                is_valid, error = self.tm._validate_task_text(text)
                self.assertFalse(is_valid, f"Text should be invalid: {text}")
                self.assertEqual(error, expected_error)
    
    def test_build_task_line(self):
        """Test task line building"""
        # Simple task
        task_line = self.tm._build_task_line(' ', 'test task', date='15-01-2025', task_id='001')
        expected = "- [ ] test task | @15-01-2025 #001"
        self.assertEqual(task_line, expected)
        
        # Complex task
        task_line = self.tm._build_task_line('x', 'complex task', date='15-01-2025', 
                                           recurring='(daily)', snooze='20-01-2025', task_id='002')
        expected = "- [x] complex task | @15-01-2025 (daily) snooze:20-01-2025 #002"
        self.assertEqual(task_line, expected)
        
        # Invalid text should raise error
        with self.assertRaises(ValueError):
            self.tm._build_task_line(' ', 'task with @ symbol', task_id='001')
    
    def test_edit_task(self):
        """Test edit task command"""
        # Add a task
        self.tm.add_task_to_main("original task", "INBOX")
        
        # Edit the task
        self.tm.edit_task("001", "updated task")
        
        # Check the task was updated
        result = self.tm.find_task_by_id("001")
        self.assertIsNotNone(result)
        line_num, line = result
        self.assertIn("updated task", line)
        
        # Test invalid text
        with patch('builtins.print') as mock_print:
            self.tm.edit_task("001", "task with @ symbol")
            mock_print.assert_called_with("Invalid task text: Task text cannot contain '@' character")
    
    def test_move_task(self):
        """Test move task command"""
        # Add a task to INBOX
        self.tm.add_task_to_main("test task", "INBOX")
        
        # Move to PROJECTS
        self.tm.move_task("001", "PROJECTS")
        
        # Check task is in PROJECTS
        result = self.tm.find_task_by_id("001")
        self.assertIsNotNone(result)
        
        # Check task is not in INBOX
        inbox_section = self.tm.find_section("INBOX", level=2)
        self.assertIsNotNone(inbox_section)
        inbox_content = '\n'.join(inbox_section)
        self.assertNotIn("test task", inbox_content)

if __name__ == '__main__':
    unittest.main()
