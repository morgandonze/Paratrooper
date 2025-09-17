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
from paratrooper import TaskManager

class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_tasks.md"
        
        # Create a mock config with our test file
        from paratrooper import Config
        mock_config = Config(
            task_file=self.test_file,
            icon_set="default",
            editor="nvim"
        )
        
        # Create TaskManager instance with test file
        self.tm = TaskManager(mock_config)
    
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
        # Add to default section (TASKS)
        self.tm.add_task_to_main("Test task")
        content = self.tm.read_file()
        self.assertIn("Test task", content)
        self.assertIn("## TASKS", content)
        
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
            self.tm.show_status_tasks()
            
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
            ("task with (parentheses)", "Parentheses can only be used for recurrence patterns like (daily), (weekly), etc."),
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
        # Add a task to TASKS
        self.tm.add_task_to_main("test task", "TASKS")
        
        # Move to WORK
        self.tm.move_task("001", "WORK")
        
        # Check task is in WORK
        result = self.tm.find_task_by_id("001")
        self.assertIsNotNone(result)
        
        # Check task is not in TASKS
        tasks_section = self.tm.find_section("TASKS", level=2)
        self.assertIsNotNone(tasks_section)
        tasks_content = '\n'.join(tasks_section)
        self.assertNotIn("test task", tasks_content)
    
    def test_get_most_recent_daily_section(self):
        """Test finding the most recent daily section"""
        # Create a task file with multiple daily sections
        self.tm.write_file("""# DAILY
## 01-01-2025
- [ ] old task | @01-01-2025 #001

## 02-01-2025
- [ ] recent task | @02-01-2025 #002
- [x] completed task | @02-01-2025 #003

## 03-01-2025
- [ ] newest task | @03-01-2025 #004

# MAIN
## INBOX
""")
        
        # Mock today as 04-01-2025
        with patch.object(self.tm, 'today', '04-01-2025'):
            task_file = self.tm.parse_file()
            most_recent_date, most_recent_tasks = self.tm.get_most_recent_daily_section(task_file)
            
            # Should find 03-01-2025 as most recent (excluding today)
            self.assertEqual(most_recent_date, "03-01-2025")
            self.assertEqual(len(most_recent_tasks), 1)
            self.assertEqual(most_recent_tasks[0].id, "004")
    
    def test_get_unfinished_tasks_from_daily(self):
        """Test extracting unfinished and progressed tasks from daily section"""
        # Create tasks with different statuses
        self.tm.write_file("""# DAILY
## 01-01-2025
- [ ] unfinished task 1 | @01-01-2025 #001
- [x] completed task | @01-01-2025 #002
- [~] progress task | @01-01-2025 #003
- [ ] unfinished task 2 | @01-01-2025 #004

# MAIN
## INBOX
""")
        
        task_file = self.tm.parse_file()
        daily_tasks = task_file.get_daily_section("01-01-2025")
        unfinished_tasks = self.tm.get_unfinished_tasks_from_daily(daily_tasks)
        
        # Should return tasks with status ' ' (incomplete) and '~' (progress)
        self.assertEqual(len(unfinished_tasks), 3)
        self.assertEqual(unfinished_tasks[0].id, "001")
        self.assertEqual(unfinished_tasks[1].id, "003")
        self.assertEqual(unfinished_tasks[2].id, "004")
    
    def test_daily_carry_over_unfinished_tasks(self):
        """Test that daily command carries over unfinished and progressed tasks from previous day"""
        # Create a task file with yesterday's daily section containing unfinished and progressed tasks
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        self.tm.write_file(f"""# DAILY
## {yesterday}
- [ ] unfinished task 1 | @{yesterday} #001
- [x] completed task | @{yesterday} #002
- [~] progress task | @{yesterday} #003
- [ ] unfinished task 2 | @{yesterday} #004

# MAIN
## INBOX
- [ ] recurring task | @01-01-2025 (daily) #005
""")
        
        # Mock today's date
        with patch.object(self.tm, 'today', today):
            # Run daily command
            with patch('builtins.print') as mock_print:
                self.tm.add_daily_section()
                
                # Check that unfinished and progressed tasks were carried over
                content = self.tm.read_file()
                
                # Should have today's daily section
                self.assertIn(f"## {today}", content)
                
                # Should have recurring task
                self.assertIn("recurring task from INBOX", content)
                
                # Should have carried over unfinished and progressed tasks in today's section
                today_section_start = content.find(f"## {today}")
                # Find the end of the daily section (next ## or end of DAILY section)
                next_section_start = content.find("\n## ", today_section_start + 1)
                if next_section_start == -1:
                    next_section_start = content.find("\n# ", today_section_start + 1)
                if next_section_start == -1:
                    today_section = content[today_section_start:]
                else:
                    today_section = content[today_section_start:next_section_start]
                
                self.assertIn("unfinished task 1", today_section)
                self.assertIn("unfinished task 2", today_section)
                self.assertIn("progress task", today_section)
                
                # Should not have completed tasks in today's section
                self.assertNotIn("completed task", today_section)
                
                # Check status message mentions carry-over
                output = str(mock_print.call_args_list)
                self.assertIn("tasks from", output)
    
    def test_daily_no_carry_over_when_no_previous_daily(self):
        """Test that daily command works normally when no previous daily section exists"""
        today = datetime.now().strftime("%d-%m-%Y")
        
        self.tm.write_file("""# DAILY

# MAIN
## INBOX
- [ ] recurring task | @01-01-2025 (daily) #001
""")
        
        # Mock today's date
        with patch.object(self.tm, 'today', today):
            # Run daily command
            with patch('builtins.print') as mock_print:
                self.tm.add_daily_section()
                
                # Check that only recurring tasks were added
                content = self.tm.read_file()
                self.assertIn(f"## {today}", content)
                self.assertIn("recurring task from INBOX", content)
                
                # Check status message doesn't mention carry-over
                output = str(mock_print.call_args_list)
                self.assertNotIn("unfinished tasks from", output)
    
    def test_daily_no_carry_over_duplicates(self):
        """Test that daily command doesn't carry over tasks that are already recurring"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        self.tm.write_file(f"""# DAILY
## {yesterday}
- [ ] recurring task from INBOX | @{yesterday} #001
- [ ] regular task | @{yesterday} #002

# MAIN
## INBOX
- [ ] recurring task | @01-01-2025 (daily) #001
""")
        
        # Mock today's date
        with patch.object(self.tm, 'today', today):
            # Run daily command
            self.tm.add_daily_section()
            
            # Check that recurring task wasn't duplicated in daily section
            content = self.tm.read_file()
            today_section_start = content.find(f"## {today}")
            # Find the end of the daily section (next ## or end of DAILY section)
            next_section_start = content.find("\n## ", today_section_start + 1)
            if next_section_start == -1:
                next_section_start = content.find("\n# ", today_section_start + 1)
            if next_section_start == -1:
                today_section = content[today_section_start:]
            else:
                today_section = content[today_section_start:next_section_start]
            
            recurring_count_in_daily = today_section.count("recurring task")
            self.assertEqual(recurring_count_in_daily, 1)  # Only once in daily section
            
            # Check that regular task was carried over
            self.assertIn("regular task", content)
    
    def test_daily_no_carry_over_progressed_recurring_tasks(self):
        """Test that progressed recurring tasks are NOT carried over (recurrence controls when they appear)"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        self.tm.write_file(f"""# DAILY
## {yesterday}
- [~] workout from AREAS > FITNESS | @{yesterday} #001

# MAIN
## AREAS
### FITNESS
- [ ] workout | @01-01-2025 (daily) #001
""")
        
        # Mock today's date
        with patch.object(self.tm, 'today', today):
            # Run daily command
            self.tm.add_daily_section()
            
            # Check that the progressed recurring task was NOT carried over
            content = self.tm.read_file()
            today_section_start = content.find(f"## {today}")
            # Find the end of the daily section (next ## or end of DAILY section)
            next_section_start = content.find("\n## ", today_section_start + 1)
            if next_section_start == -1:
                next_section_start = content.find("\n# ", today_section_start + 1)
            if next_section_start == -1:
                today_section = content[today_section_start:]
            else:
                today_section = content[today_section_start:next_section_start]
            
            # Should have the recurring task from recurring logic, not from carry-over
            self.assertIn("workout from AREAS > FITNESS", today_section)
            
            # Should only appear once in today's section (not duplicated)
            workout_count = today_section.count("workout")
            self.assertEqual(workout_count, 1)
    
    def test_daily_no_carry_over_incomplete_recurring_tasks(self):
        """Test that incomplete recurring tasks are NOT carried over if they have from_section"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        self.tm.write_file(f"""# DAILY
## {yesterday}
- [ ] workout from AREAS > FITNESS | @{yesterday} #001
- [ ] regular task | @{yesterday} #002

# MAIN
## AREAS
### FITNESS
- [ ] workout | @01-01-2025 (daily) #001
""")
        
        # Mock today's date
        with patch.object(self.tm, 'today', today):
            # Run daily command
            self.tm.add_daily_section()
            
            # Check that the incomplete recurring task was NOT carried over
            content = self.tm.read_file()
            today_section_start = content.find(f"## {today}")
            # Find the end of the daily section (next ## or end of DAILY section)
            next_section_start = content.find("\n## ", today_section_start + 1)
            if next_section_start == -1:
                next_section_start = content.find("\n# ", today_section_start + 1)
            if next_section_start == -1:
                today_section = content[today_section_start:]
            else:
                today_section = content[today_section_start:next_section_start]
            
            # Should have the regular task carried over
            self.assertIn("regular task", today_section)
            
            # Should have the recurring task from the recurring logic, not from carry-over
            self.assertIn("workout from AREAS > FITNESS", today_section)
            
            # Should only appear once in today's section
            workout_count = today_section.count("workout")
            self.assertEqual(workout_count, 1)
    
    def test_daily_carry_over_progressed_non_recurring_tasks(self):
        """Test that progressed non-recurring tasks ARE carried over"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        self.tm.write_file(f"""# DAILY
## {yesterday}
- [~] write blog post | @{yesterday} #001
- [ ] workout from AREAS > FITNESS | @01-01-2025 (daily) #002

# MAIN
## INBOX
- [ ] write blog post | @01-01-2025 #001
## AREAS
### FITNESS
- [ ] workout | @01-01-2025 (daily) #002
""")
        
        # Mock today's date
        with patch.object(self.tm, 'today', today):
            # Run daily command
            self.tm.add_daily_section()
            
            # Check that the progressed non-recurring task was carried over
            content = self.tm.read_file()
            today_section_start = content.find(f"## {today}")
            # Find the end of the daily section (next ## or end of DAILY section)
            next_section_start = content.find("\n## ", today_section_start + 1)
            if next_section_start == -1:
                next_section_start = content.find("\n# ", today_section_start + 1)
            if next_section_start == -1:
                today_section = content[today_section_start:]
            else:
                today_section = content[today_section_start:next_section_start]
            
            # Should have the recurring task from recurring logic
            self.assertIn("workout from AREAS > FITNESS", today_section)
            
            # Should have the progressed non-recurring task carried over
            self.assertIn("write blog post", today_section)
            
            # Should have both tasks
            workout_count = today_section.count("workout")
            blog_count = today_section.count("write blog post")
            self.assertEqual(workout_count, 1)
            self.assertEqual(blog_count, 1)

if __name__ == '__main__':
    unittest.main()
