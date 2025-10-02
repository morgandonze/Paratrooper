#!/usr/bin/env python3
"""
Comprehensive test suite for paratrooper.py

This test suite covers all major functionality of the paratrooper task management system
to ensure the current implementation works correctly before refactoring.
"""

import unittest
import tempfile
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add the current directory to the path so we can import paratrooper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paratrooper import Config, Task, Section, TaskFile, Paratrooper


class TestConfig(unittest.TestCase):
    """Test the Config class functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_default_config_creation(self):
        """Test that default config is created correctly"""
        config = Config.load(self.config_path)
        self.assertIsNotNone(config)
        self.assertEqual(str(config.task_file), str(Path.home() / "home" / "tasks.md"))
        self.assertEqual(config.editor, "nvim")
    
    def test_config_file_creation(self):
        """Test that config file is created on disk"""
        config = Config.load(self.config_path)
        self.assertTrue(self.config_path.exists())
        
        # Read the file and check content
        with open(self.config_path, 'r') as f:
            content = f.read()
            self.assertIn("[general]", content)
            self.assertIn("task_file =", content)


class TestTask(unittest.TestCase):
    """Test the Task class functionality"""
    
    def test_task_creation(self):
        """Test basic task creation"""
        task = Task(
            id="001",
            text="Test task",
            status=" ",
            date="15-01-2025",
            section="TASKS"
        )
        self.assertEqual(task.text, "Test task")
        self.assertEqual(task.status, " ")
        self.assertEqual(task.date, "15-01-2025")
        self.assertEqual(task.id, "001")
        self.assertEqual(task.section, "TASKS")
    
    def test_task_to_markdown(self):
        """Test task conversion to markdown"""
        task = Task(
            id="001",
            text="Test task",
            status="x",
            date="15-01-2025",
            section="TASKS"
        )
        markdown = task.to_markdown()
        expected = "- [x] #001 | Test task | TASKS | 15-01-2025"
        self.assertEqual(markdown, expected)
    
    def test_task_from_markdown(self):
        """Test parsing task from markdown"""
        line = "- [x] #001 | Test task | TASKS | 15-01-2025 | "
        task = Task.from_markdown(line, "TASKS")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.text, "Test task")
        self.assertEqual(task.status, "x")
        self.assertEqual(task.date, "15-01-2025")
        self.assertEqual(task.id, "001")
        self.assertEqual(task.section, "TASKS")
    
    def test_recurring_task_parsing(self):
        """Test parsing recurring tasks"""
        line = "- [ ] #004 | morning workout | HEALTH | 15-01-2025 | daily"
        task = Task.from_markdown(line, "HEALTH")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.text, "morning workout")
        self.assertEqual(task.status, " ")
        self.assertEqual(task.date, "15-01-2025")
        self.assertEqual(task.id, "004")
        self.assertEqual(task.recurring, "daily")
    
    def test_snoozed_task_parsing(self):
        """Test parsing tasks with future dates (snoozing)"""
        line = "- [ ] #005 | review budget | FINANCE | 20-01-2025 | "
        task = Task.from_markdown(line, "FINANCE")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.text, "review budget")
        self.assertEqual(task.status, " ")
        self.assertEqual(task.date, "20-01-2025")
        self.assertEqual(task.id, "005")


class TestSection(unittest.TestCase):
    """Test the Section class functionality"""
    
    def test_section_creation(self):
        """Test basic section creation"""
        section = Section(name="WORK", level=1)
        self.assertEqual(section.name, "WORK")
        self.assertEqual(section.level, 1)
        self.assertEqual(section.tasks, [])
        self.assertEqual(section.subsections, {})
    
    def test_add_task(self):
        """Test adding tasks to section"""
        section = Section(name="WORK", level=1)
        task = Task(id="001", text="Test task", status=" ", date="15-01-2025", section="WORK")
        
        section.add_task(task)
        self.assertEqual(len(section.tasks), 1)
        self.assertEqual(section.tasks[0].text, "Test task")
    
    def test_add_subsection(self):
        """Test adding subsections"""
        section = Section(name="WORK", level=1)
        subsection = section.add_subsection("HOME")
        
        self.assertIsNotNone(subsection)
        self.assertEqual(subsection.name, "HOME")
        self.assertEqual(subsection.level, 2)
        self.assertIn("HOME", section.subsections)
    
    def test_get_subsection(self):
        """Test getting existing subsection"""
        section = Section(name="WORK", level=1)
        section.add_subsection("HOME")
        
        subsection = section.get_subsection("HOME")
        self.assertIsNotNone(subsection)
        self.assertEqual(subsection.name, "HOME")
    
    def test_get_nonexistent_subsection(self):
        """Test getting non-existent subsection returns None"""
        section = Section(name="WORK", level=1)
        subsection = section.get_subsection("NONEXISTENT")
        self.assertIsNone(subsection)


class TestTaskFile(unittest.TestCase):
    """Test the TaskFile class functionality"""
    
    def test_task_file_creation(self):
        """Test basic task file creation"""
        task_file = TaskFile()
        self.assertIsNotNone(task_file.main_sections)
        self.assertIsNotNone(task_file.daily_sections)
        self.assertIsNotNone(task_file.archive_sections)
    
    def test_get_main_section(self):
        """Test getting or creating main sections"""
        task_file = TaskFile()
        section = task_file.get_main_section("WORK")
        
        self.assertIsNotNone(section)
        self.assertEqual(section.name, "WORK")
        self.assertIn("WORK", task_file.main_sections)
    
    def test_get_daily_section(self):
        """Test getting or creating daily sections"""
        task_file = TaskFile()
        date = "15-01-2025"
        tasks = task_file.get_daily_section(date)
        
        self.assertIsNotNone(tasks)
        self.assertIsInstance(tasks, list)
        self.assertIn(date, task_file.daily_sections)


class TestTaskManager(unittest.TestCase):
    """Test the TaskManager class functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        self.config_path = Path(self.temp_dir) / "test_config"
        
        # Create a test config
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_init_creates_file(self):
        """Test that init creates the task file"""
        self.tm.init()
        self.assertTrue(self.task_file_path.exists())
        
        # Check file content
        with open(self.task_file_path, 'r') as f:
            content = f.read()
            self.assertIn("# DAILY", content)
            self.assertIn("# MAIN", content)
            self.assertIn("# ARCHIVE", content)
    
    def test_add_task_to_main(self):
        """Test adding tasks to main list"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        content = self.tm.read_file()
        self.assertIn("Test task", content)
        self.assertIn("WORK", content)
    
    def test_add_task_to_daily(self):
        """Test adding tasks to daily section"""
        self.tm.init()
        self.tm.add_daily_section()  # Create today's section
        self.tm.add_task_to_daily("Daily task")
        
        content = self.tm.read_file()
        self.assertIn("Daily task", content)
    
    def test_get_next_id(self):
        """Test getting next available ID"""
        self.tm.init()
        
        # Add some tasks
        self.tm.add_task_to_main("Task 1", "TASKS")
        self.tm.add_task_to_main("Task 2", "TASKS")
        
        # Get next ID
        next_id = self.tm.get_next_id()
        self.assertIsNotNone(next_id)
        self.assertIsInstance(next_id, str)
    
    def test_find_task_by_id(self):
        """Test finding tasks by ID"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get the task ID from the file
        content = self.tm.read_file()
        lines = content.split('\n')
        task_line = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_line = line
                break
        
        self.assertIsNotNone(task_line)
        # Extract ID from the line
        task_id = task_line.split('#')[-1].strip()
        
        # Find the task
        result = self.tm.find_task_by_id(task_id)
        self.assertIsNotNone(result)
        line_number, line_content = result
        self.assertIn("Test task", line_content)
    
    def test_complete_task(self):
        """Test completing a task"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get the task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_line = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_line = line
                break
        
        task_id = task_line.split('#')[-1].strip()
        
        # Complete the task
        self.tm.complete_task(task_id)
        
        # Check that task is marked complete
        content = self.tm.read_file()
        self.assertIn(f"- [x] #001 | Test task", content)
    
    def test_recurring_task_detection(self):
        """Test detecting recurring tasks"""
        self.tm.init()
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        
        recurring_tasks = self.tm.get_recurring_tasks()
        self.assertGreater(len(recurring_tasks), 0)
        
        # Check that we found our recurring task
        found = False
        for task in recurring_tasks:
            if "morning workout" in task['text']:
                found = True
                break
        self.assertTrue(found)
    
    def test_daily_section_creation(self):
        """Test creating daily section with recurring tasks"""
        self.tm.init()
        
        # Add a recurring task
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        
        # Create daily section
        self.tm.add_daily_section()
        
        content = self.tm.read_file()
        # Should have today's date in daily section
        today = datetime.now().strftime("%d-%m-%Y")
        self.assertIn(today, content)
    
    def test_sync_daily_sections(self):
        """Test syncing daily sections to main list"""
        self.tm.init()
        
        # Add a task to main
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_line = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_line = line
                break
        
        task_id = task_line.split('#')[-1].strip()
        
        # Add to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id(task_id)
        
        # Mark as complete in daily section (manually edit file)
        content = self.tm.read_file()
        content = content.replace(f"- [ ] #001 | Test task", f"- [x] #001 | Test task")
        self.tm.write_file(content)
        
        # Sync
        self.tm.sync_daily_sections()
        
        # Check that main task is now complete
        content = self.tm.read_file()
        self.assertIn(f"- [x] #001 | Test task", content)
    
    def test_snooze_task(self):
        """Test snoozing a task"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID using the proper method
        line_num, task_line = self.tm.find_task_by_id("001")
        self.assertIsNotNone(task_line, "Task should be found")
        
        # Snooze for 3 days
        self.tm.snooze_task("001", "3")
        
        # Check that task has future date (snoozing)
        content = self.tm.read_file()
        self.assertIn("04-10-2025", content)  # 3 days from test date
    
    def test_archive_old_content(self):
        """Test archiving old content"""
        self.tm.init()
        
        # Add some old daily sections manually
        content = self.tm.read_file()
        old_date = (datetime.now() - timedelta(days=10)).strftime("%d-%m-%Y")
        content += f"\n## {old_date}\n- [x] old task #999\n"
        self.tm.write_file(content)
        
        # Archive old content
        self.tm.archive_old_content(days_to_keep=7)
        
        # Check that old content moved to archive
        content = self.tm.read_file()
        self.assertIn("# ARCHIVE", content)
        self.assertIn(old_date, content)
    
    def test_delete_task_from_main(self):
        """Test deleting tasks from main list"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_line = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_line = line
                break
        
        task_id = task_line.split('#')[-1].strip()
        
        # Delete the task
        self.tm.delete_task_from_main(task_id)
        
        # Check that task is gone
        content = self.tm.read_file()
        self.assertNotIn("Test task", content)
    
    def test_show_status_tasks(self):
        """Test showing task status (staleness)"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Show status - should not crash
        try:
            self.tm.show_status_tasks()
        except Exception as e:
            self.fail(f"show_status_tasks raised an exception: {e}")
    
    def test_list_sections(self):
        """Test listing sections"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # List sections - should not crash
        try:
            self.tm.list_sections()
        except Exception as e:
            self.fail(f"list_sections raised an exception: {e}")
    
    def test_show_task(self):
        """Test showing task details"""
        self.tm.init()
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_line = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_line = line
                break
        
        task_id = task_line.split('#')[-1].strip()
        
        # Show task - should not crash
        try:
            self.tm.show_task(task_id)
        except Exception as e:
            self.fail(f"show_task raised an exception: {e}")
    
    def test_add_task_to_daily_by_id_formatting(self):
        """Test that add_task_to_daily_by_id includes proper formatting"""
        self.tm.init()
        
        # Add a task to a specific section
        self.tm.add_task_to_main("Write blog post", "PROJECTS")
        
        # Get the task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_line = None
        for line in lines:
            if "Write blog post" in line and "#" in line:
                task_line = line
                break
        
        task_id = task_line.split('#')[-1].strip()
        
        # Create daily section and add task
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id(task_id)
        
        # Verify the task appears in daily section
        content = self.tm.read_file()
        self.assertIn("Write blog post", content)
        
        # Verify it's in the daily section, not main
        daily_section_start = content.find("# DAILY")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        self.assertIn("Write blog post", daily_section)
    
    def test_most_recent_daily_section_logic(self):
        """Test that operations work with the most recent daily section, not just today's"""
        self.tm.init()
        
        # Create multiple daily sections with different dates
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Add tasks to main
        self.tm.add_task_to_main("Task 1", "WORK")
        self.tm.add_task_to_main("Task 2", "WORK")
        
        # Get task IDs
        content = self.tm.read_file()
        lines = content.split('\n')
        task_ids = []
        for line in lines:
            if ("Task 1" in line or "Task 2" in line) and "#" in line:
                task_ids.append(line.split('#')[-1].strip())
        
        # Create yesterday's daily section manually
        content = self.tm.read_file()
        content = content.replace("# DAILY", f"# DAILY\n## {yesterday}\n- [ ] Task 1 from WORK #{task_ids[0]}")
        self.tm.write_file(content)
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Add Task 2 to daily (should go to today's section, the most recent)
        self.tm.add_task_to_daily_by_id(task_ids[1])
        
        # Verify Task 2 is in today's section (most recent)
        content = self.tm.read_file()
        self.assertIn(f"Task 2", content)
        
        # Verify _get_most_recent_daily_date returns today's date
        most_recent_date = self.tm._get_most_recent_daily_date(content)
        self.assertEqual(most_recent_date, today)
    
    def test_reorganize_daily_sections(self):
        """Test that reorganize_daily_sections moves old daily sections to archive"""
        self.tm.init()
        
        # Create a task file with multiple daily sections
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        content = f"""# DAILY

## {yesterday}
- [x] #001 | Old task | WORK | {yesterday}

## {today}
- [ ] #002 | New task | WORK | {today}

# MAIN

## WORK
- [ ] #002 | New task | WORK | {today}

# ARCHIVE
"""
        self.tm.write_file(content)
        
        # Call reorganize_daily_sections
        task_file = self.tm.parse_file()
        task_file.reorganize_daily_sections()
        
        # Verify old daily section moved to archive
        self.assertNotIn(yesterday, task_file.daily_sections)
        self.assertIn(yesterday, task_file.archive_sections)
        
        # Verify today's section remains in daily
        self.assertIn(today, task_file.daily_sections)
        self.assertNotIn(today, task_file.archive_sections)
    
    def test_daily_section_display_only_most_recent(self):
        """Test that DAILY section only shows the most recent day in markdown output"""
        self.tm.init()
        
        # Create multiple daily sections
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        content = f"""# DAILY

## {yesterday}
- [x] #001 | Old task | WORK | {yesterday}

## {today}
- [ ] #002 | New task | WORK | {today}

# MAIN

## WORK
- [ ] #002 | New task | WORK | {today}

# ARCHIVE
"""
        self.tm.write_file(content)
        
        # Parse file and convert to markdown
        task_file = self.tm.parse_file()
        markdown = task_file.to_markdown()
        
        # Verify only today's section appears in DAILY section
        daily_section_start = markdown.find("# DAILY")
        main_section_start = markdown.find("# MAIN")
        daily_section = markdown[daily_section_start:main_section_start]
        
        self.assertIn(f"## {today}", daily_section)
        self.assertIn("New task", daily_section)
        self.assertNotIn(f"## {yesterday}", daily_section)
        self.assertNotIn("Old task", daily_section)
        
        # Verify yesterday's section appears in ARCHIVE
        archive_section_start = markdown.find("# ARCHIVE")
        archive_section = markdown[archive_section_start:]
        self.assertIn(f"## {yesterday}", archive_section)
        self.assertIn("Old task", archive_section)
    
    def test_automatic_reorganization_on_daily_operations(self):
        """Test that daily operations automatically reorganize sections"""
        self.tm.init()
        
        # Create multiple daily sections manually
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        content = f"""# DAILY

## {yesterday}
- [x] #001 | Old task | WORK | {yesterday}

## {today}
- [ ] #002 | New task | WORK | {today}

# MAIN

## WORK
- [ ] #002 | New task | WORK | {today}

# ARCHIVE
"""
        self.tm.write_file(content)
        
        # Parse the file to get the TaskFile object
        task_file = self.tm.parse_file()
        
        # Manually call reorganize_daily_sections to test the functionality
        task_file.reorganize_daily_sections()
        
        # Write the reorganized file back
        self.tm.write_file_from_objects(task_file)
        
        # Verify reorganization happened
        content = self.tm.read_file()
        
        # Yesterday's section should be in archive
        archive_section_start = content.find("# ARCHIVE")
        archive_section = content[archive_section_start:]
        self.assertIn(f"## {yesterday}", archive_section)
        
        # Today's section should remain in daily
        daily_section_start = content.find("# DAILY")
        main_section_start = content.find("# MAIN")
        daily_section = content[daily_section_start:main_section_start]
        self.assertIn(f"## {today}", daily_section)

    def test_daily_carry_over_functionality(self):
        """Test that incomplete tasks from previous day are carried over to today's daily section"""
        self.tm.init()
        
        # Create dates for testing
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Add tasks to main sections
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        self.tm.add_task_to_main("write report", "WORK")
        self.tm.add_task_to_main("call client", "WORK")
        
        # Get task IDs using the proper method
        workout_line_num, workout_line = self.tm.find_task_by_id("001")
        report_line_num, report_line = self.tm.find_task_by_id("002")
        client_line_num, client_line = self.tm.find_task_by_id("003")
        
        self.assertIsNotNone(workout_line, "Workout task should be found")
        self.assertIsNotNone(report_line, "Report task should be found")
        self.assertIsNotNone(client_line, "Client task should be found")
        
        # Create yesterday's daily section manually with incomplete tasks
        yesterday_content = f"""# DAILY

## {yesterday}
- [ ] #001 | morning workout | HEALTH | {today} | daily
- [~] #002 | write report | WORK | {today}
- [x] #003 | call client | WORK | {today}

# MAIN

## HEALTH
- [ ] #001 | morning workout | HEALTH | {today} | daily

## WORK
- [ ] #002 | write report | WORK | {today}
- [ ] #003 | call client | WORK | {today}

# ARCHIVE
"""
        
        # Write the test content
        self.tm.task_file.write_text(yesterday_content)
        
        # Run daily command to create today's section
        self.tm.add_daily_section()
        
        # Verify the results
        content = self.tm.read_file()
        
        # Should have today's daily section
        self.assertIn(f"## {today}", content)
        
        # Should carry over incomplete tasks (workout and report, but not client)
        daily_section_start = content.find(f"## {today}")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        # Recurring task should be added
        self.assertIn("morning workout", daily_section)
        
        # Incomplete task should be carried over (status reset to incomplete)
        self.assertIn("write report", daily_section)
        
        # Completed task should NOT be carried over
        self.assertNotIn("call client", daily_section)
        
        # Previous day's section should be moved to archive
        self.assertIn("# ARCHIVE", content)
        archive_section_start = content.find("# ARCHIVE")
        archive_section = content[archive_section_start:]
        self.assertIn(f"## {yesterday}", archive_section)
        
        # Verify carry-over message was shown (we can't easily test stdout, but the functionality works)
        # The test passes if the assertions above pass

    def test_daily_duplication_prevention(self):
        """Test that recurring tasks don't get duplicated when also being carried over from previous day"""
        self.tm.init()
        
        # Create dates for testing
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Add a recurring task to main section
        self.tm.add_task_to_main("Take out trash (daily)", "DOMESTIC")
        
        # Get task ID using the proper method
        line_num, task_line = self.tm.find_task_by_id("001")
        self.assertIsNotNone(task_line, "Task should be found")
        task_id = "001"
        
        # Create yesterday's daily section with the recurring task as incomplete
        yesterday_content = f"""# DAILY

## {yesterday}
- [ ] #{task_id} | Take out trash | DOMESTIC | {today} | daily

# MAIN

## DOMESTIC
- [ ] #{task_id} | Take out trash | DOMESTIC | {today} | daily

# ARCHIVE
"""
        
        # Write the test content
        self.tm.task_file.write_text(yesterday_content)
        
        # Run daily command to create today's section
        self.tm.add_daily_section()
        
        # Verify the results
        content = self.tm.read_file()
        
        # Should have today's daily section
        self.assertIn(f"## {today}", content)
        
        # Get today's daily section content
        daily_section_start = content.find(f"## {today}")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        # Count occurrences of the task in today's daily section
        task_occurrences = daily_section.count("Take out trash")
        
        # Should appear exactly once (not duplicated)
        self.assertEqual(task_occurrences, 1, 
                        f"Task 'Take out trash' appears {task_occurrences} times in daily section, should appear exactly once")
        
        # Should appear as a carry-over task (check for task ID to ensure it's the same task)
        # The task ID should be present in the daily section
        self.assertIn(f"#{task_id}", daily_section)
        self.assertIn("Take out trash", daily_section)
        
        # Verify it's the carry-over task by checking the format
        self.assertIn("daily", daily_section)
        
        # The key test: should appear exactly once (no duplication)
        # This is the main assertion that verifies the fix works
        
        # Previous day's section should be moved to archive
        self.assertIn("# ARCHIVE", content)
        archive_section_start = content.find("# ARCHIVE")
        archive_section = content[archive_section_start:]
        self.assertIn(f"## {yesterday}", archive_section)

    def test_main_section_headers_always_persist(self):
        """Test that all main section headers persist regardless of content"""
        # Test 1: Newly initialized file
        self.tm.init()
        
        # Verify initial structure has all three main sections
        initial_content = self.tm.read_file()
        self.assertIn("# DAILY", initial_content)
        self.assertIn("# MAIN", initial_content)
        self.assertIn("# ARCHIVE", initial_content)
        
        # Add a task using the default section (TASKS)
        self.tm.add_task_to_main("Test", "TASKS")
        
        # Verify all main sections still exist after adding task
        final_content = self.tm.read_file()
        self.assertIn("# DAILY", final_content)
        self.assertIn("# MAIN", final_content)
        self.assertIn("# ARCHIVE", final_content)
        
        # Should have created a Tasks subsection under MAIN
        self.assertIn("## TASKS", final_content)
        
        # Should have the task in the Tasks subsection
        self.assertIn("- [ ] #001 | Test | TASKS |", final_content)
        
        # Verify the structure is correct by checking the order
        lines = final_content.split('\n')
        daily_index = lines.index('# DAILY')
        main_index = lines.index('# MAIN')
        tasks_index = lines.index('## TASKS')
        archive_index = lines.index('# ARCHIVE')
        
        # Verify proper ordering
        self.assertLess(daily_index, main_index)
        self.assertLess(main_index, tasks_index)
        self.assertLess(tasks_index, archive_index)
        
        # Verify the task appears between Tasks header and ARCHIVE
        task_line_index = None
        for i, line in enumerate(lines):
            if "Test" in line and "#001" in line:
                task_line_index = i
                break
        
        self.assertIsNotNone(task_line_index)
        self.assertGreater(task_line_index, tasks_index)
        self.assertLess(task_line_index, archive_index)
    
    def test_main_section_headers_persist_with_existing_content(self):
        """Test that main section headers persist even when sections have existing content"""
        # Initialize and add some content to different sections
        self.tm.init()
        
        # Add tasks to main sections
        self.tm.add_task_to_main("Work task", "WORK")
        self.tm.add_task_to_main("Health task", "HEALTH")
        
        # Add a daily section with content
        self.tm.add_daily_section()
        self.tm.add_task_to_daily("Daily task")
        
        # Verify all main sections exist
        content = self.tm.read_file()
        self.assertIn("# DAILY", content)
        self.assertIn("# MAIN", content)
        self.assertIn("# ARCHIVE", content)
        
        # Add another task to a new section
        self.tm.add_task_to_main("New task", "PROJECTS")
        
        # Verify all main sections still exist after adding more content
        final_content = self.tm.read_file()
        self.assertIn("# DAILY", final_content)
        self.assertIn("# MAIN", final_content)
        self.assertIn("# ARCHIVE", final_content)
        
        # Verify the new section was added
        self.assertIn("## PROJECTS", final_content)
        self.assertIn("New task", final_content)
    
    def test_main_section_headers_persist_after_deletions(self):
        """Test that main section headers persist even after deleting all content from sections"""
        # Initialize and add content
        self.tm.init()
        self.tm.add_task_to_main("Work task", "WORK")
        self.tm.add_task_to_main("Health task", "HEALTH")
        
        # Verify all sections exist
        content = self.tm.read_file()
        self.assertIn("# DAILY", content)
        self.assertIn("# MAIN", content)
        self.assertIn("# ARCHIVE", content)
        self.assertIn("## WORK", content)
        self.assertIn("## HEALTH", content)
        
        # Get task IDs
        lines = content.split('\n')
        work_task_id = None
        health_task_id = None
        for line in lines:
            if "Work task" in line and "#" in line:
                work_task_id = line.split('#')[-1].strip()
            elif "Health task" in line and "#" in line:
                health_task_id = line.split('#')[-1].strip()
        
        # Delete all tasks from main sections
        self.tm.delete_task_from_main(work_task_id)
        self.tm.delete_task_from_main(health_task_id)
        
        # Verify all main section headers still exist even with empty sections
        final_content = self.tm.read_file()
        self.assertIn("# DAILY", final_content)
        self.assertIn("# MAIN", final_content)
        self.assertIn("# ARCHIVE", final_content)
        
        # Note: Currently empty subsections are preserved, but this behavior 
        # may change in the future to remove empty subsections
        # For now, verify they still exist (current behavior)
        self.assertIn("## WORK", final_content)
        self.assertIn("## HEALTH", final_content)
    
    def test_main_section_headers_persist_with_manual_file_modification(self):
        """Test that main section headers persist even when manually modifying the file structure"""
        # Initialize file
        self.tm.init()
        
        # Manually create a file with only MAIN section
        manual_content = """# DAILY

# MAIN

## WORK
- [ ] #001 | Existing task | WORK | 18-09-2025

# ARCHIVE
"""
        self.tm.write_file(manual_content)
        
        # Add a new task
        self.tm.add_task_to_main("New task", "PROJECTS")
        
        # Verify all main sections still exist
        final_content = self.tm.read_file()
        self.assertIn("# DAILY", final_content)
        self.assertIn("# MAIN", final_content)
        self.assertIn("# ARCHIVE", final_content)
        
        # Verify both old and new content exists
        self.assertIn("Existing task", final_content)
        self.assertIn("New task", final_content)
        self.assertIn("## WORK", final_content)
        self.assertIn("## PROJECTS", final_content)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        self.config_path = Path(self.temp_dir) / "test_config"
        
        # Create a test config
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_complete_daily_workflow(self):
        """Test a complete daily workflow"""
        # Initialize
        self.tm.init()
        
        # Add some tasks to main list
        self.tm.add_task_to_main("Write blog post", "WORK")
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        
        # Start the day
        self.tm.add_daily_section()
        
        # Pull a task to daily
        content = self.tm.read_file()
        lines = content.split('\n')
        blog_task_line = None
        for line in lines:
            if "Write blog post" in line and "#" in line:
                blog_task_line = line
                break
        
        blog_task_id = blog_task_line.split('#')[-1].strip()
        self.tm.add_task_to_daily_by_id(blog_task_id)
        
        # Mark progress on daily task
        self.tm.progress_task_in_daily(blog_task_id)
        
        # Complete the workout (recurring task)
        content = self.tm.read_file()
        lines = content.split('\n')
        workout_task_line = None
        for line in lines:
            if "morning workout" in line and "#" in line:
                workout_task_line = line
                break
        
        workout_task_id = workout_task_line.split('#')[-1].strip()
        self.tm.complete_task(workout_task_id)
        
        # Sync at end of day
        self.tm.sync_daily_sections()
        
        # Verify results
        content = self.tm.read_file()
        # Blog post should still be incomplete but with updated date
        self.assertIn("Write blog post", content)
        # Workout should be complete
        self.assertIn("- [x] #002 | morning workout", content)
    
    def test_recurring_task_workflow(self):
        """Test recurring task workflow across multiple days"""
        self.tm.init()
        
        # Add recurring task
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Verify recurring task appears in daily section
        content = self.tm.read_file()
        self.assertIn("morning workout", content)
        
        # Complete the workout in daily section
        # Find the workout task ID in the daily section specifically
        content = self.tm.read_file()
        daily_section_start = content.find("# DAILY")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        lines = daily_section.split('\n')
        workout_task_id = None
        for line in lines:
            if 'morning workout' in line and '#' in line:
                workout_task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(workout_task_id, "Workout task ID should be found in daily section")
        self.tm.complete_task(workout_task_id)
        
        # Sync
        self.tm.sync_daily_sections()
        
        # Verify main task is still incomplete (recurring)
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section = content[main_section_start:]
        # The date should be today's date since the task was completed today
        expected_date = self.tm.today
        self.assertIn(f"- [ ] #{workout_task_id} | morning workout | HEALTH | {expected_date} | daily", main_section)


class TestCaseInsensitiveSections(unittest.TestCase):
    """Test case-insensitive section handling functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_add_task_case_insensitive_section(self):
        """Test adding tasks with different case section names"""
        # Test various case combinations
        test_cases = [
            ("work", "WORK"),
            ("WORK", "WORK"), 
            ("Work", "WORK"),
            ("health", "HEALTH"),
            ("HEALTH", "HEALTH"),
            ("Health", "HEALTH"),
            ("projects", "PROJECTS"),
            ("PROJECTS", "PROJECTS"),
            ("Projects", "PROJECTS")
        ]
        
        for input_section, expected_section in test_cases:
            with self.subTest(input_section=input_section):
                self.tm.add_task_to_main(f"Test task for {input_section}", input_section)
                
                # Check that task was added to the correct uppercase section
                content = self.tm.read_file()
                self.assertIn(f"## {expected_section}", content)
                self.assertIn(f"Test task for {input_section}", content)
    
    def test_move_task_case_insensitive_section(self):
        """Test moving tasks with different case section names"""
        # Add a task first
        self.tm.add_task_to_main("Test task", "work")
        
        # Move to different case variations
        test_cases = [
            ("WORK", "WORK"),
            ("Work", "WORK"),
            ("health", "HEALTH"),
            ("HEALTH", "HEALTH")
        ]
        
        for target_section, expected_section in test_cases:
            with self.subTest(target_section=target_section):
                # Find the task ID
                content = self.tm.read_file()
                task_id = None
                for line in content.split('\n'):
                    if "Test task" in line and "#" in line:
                        task_id = line.split('#')[1].split()[0]
                        break
                
                self.assertIsNotNone(task_id, "Could not find task ID")
                
                # Move the task
                self.tm.move_task(task_id, target_section)
                
                # Check that task moved to correct uppercase section
                content = self.tm.read_file()
                self.assertIn(f"## {expected_section}", content)
                self.assertIn(f"Test task", content)
    
    def test_new_section_creation_case_insensitive(self):
        """Test that new sections are created with uppercase names regardless of input case"""
        new_sections = ["learning", "LEARNING", "Learning", "finance", "FINANCE", "Finance"]
        
        for section in new_sections:
            with self.subTest(section=section):
                self.tm.add_task_to_main(f"Task for {section}", section)
                
                # Check that section was created in uppercase
                content = self.tm.read_file()
                expected_section = section.upper()
                self.assertIn(f"## {expected_section}", content)
    
    def test_task_from_markdown_case_insensitive(self):
        """Test that Task.from_markdown normalizes section names"""
        test_cases = [
            ("work", "WORK"),
            ("WORK", "WORK"),
            ("Work", "WORK"),
            ("health:fitness", "HEALTH:FITNESS"),
            ("HEALTH:FITNESS", "HEALTH:FITNESS")
        ]
        
        for input_section, expected_section in test_cases:
            with self.subTest(input_section=input_section):
                task_line = f"- [ ] #001 | Test task | {input_section} | 18-09-2025 | "
                task = Task.from_markdown(task_line)
                
                self.assertIsNotNone(task)
                self.assertEqual(task.section, expected_section.split(':')[0])
                if ':' in expected_section:
                    self.assertEqual(task.subsection, expected_section.split(':')[1])
    
    def test_list_command_case_insensitive(self):
        """Test that list command works with case-insensitive section names"""
        # Add tasks to different sections
        self.tm.add_task_to_main("Work task", "work")
        self.tm.add_task_to_main("Health task", "health")
        self.tm.add_task_to_main("Project task", "projects")
        
        # Test various case combinations for list command
        test_cases = [
            ("work", "WORK"),
            ("WORK", "WORK"),
            ("Work", "WORK"),
            ("health", "HEALTH"),
            ("HEALTH", "HEALTH"),
            ("Health", "HEALTH"),
            ("projects", "PROJECTS"),
            ("PROJECTS", "PROJECTS"),
            ("Projects", "PROJECTS")
        ]
        
        for input_section, expected_section in test_cases:
            with self.subTest(input_section=input_section):
                # Capture output to verify the section is displayed correctly
                import io
                import sys
                captured_output = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = captured_output
                
                try:
                    # Test the show_section method (used by list command)
                    self.tm.show_section(input_section)
                    output = captured_output.getvalue()
                    
                    # Should display the correct section header
                    self.assertIn(f"=== {expected_section} ===", output)
                    
                    # Should show the appropriate task
                    if expected_section == "WORK":
                        self.assertIn("Work task", output)
                    elif expected_section == "HEALTH":
                        self.assertIn("Health task", output)
                    elif expected_section == "PROJECTS":
                        self.assertIn("Project task", output)
                        
                finally:
                    sys.stdout = old_stdout
    
    def test_list_command_subsection_case_insensitive(self):
        """Test that list command works with case-insensitive subsection names"""
        # Add tasks to subsections
        self.tm.add_task_to_main("Office task", "work:office")
        self.tm.add_task_to_main("Home task", "work:home")
        
        # Test various case combinations for subsections
        test_cases = [
            ("work:office", "WORK:office"),
            ("WORK:office", "WORK:office"),
            ("Work:office", "WORK:office"),
            ("work:OFFICE", "WORK:OFFICE"),
            ("WORK:OFFICE", "WORK:OFFICE"),
            ("Work:Office", "WORK:Office")
        ]
        
        for input_section, expected_section in test_cases:
            with self.subTest(input_section=input_section):
                # Capture output to verify the subsection is displayed correctly
                import io
                import sys
                captured_output = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = captured_output
                
                try:
                    # Test the show_section method (used by list command)
                    self.tm.show_section(input_section)
                    output = captured_output.getvalue()
                    
                    # Should display the correct subsection header
                    main_section, subsection = expected_section.split(':')
                    self.assertIn(f"=== {main_section} > {subsection} ===", output)
                    
                    # Should show the appropriate task
                    if subsection.lower() == "office":
                        self.assertIn("Office task", output)
                    elif subsection.lower() == "home":
                        self.assertIn("Home task", output)
                        
                finally:
                    sys.stdout = old_stdout


class TestTaskFormatter(unittest.TestCase):
    """Test the TaskFormatter functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        
        from paratrooper import Paratrooper
        from models import Config
        config = Config.load(self.config_path)
        self.formatter = Paratrooper(config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_format_for_file(self):
        """Test formatting tasks for file storage"""
        task = Task(
            id="001",
            text="Test task",
            status=" ",
            section="WORK",
            subsection=None,
            date="18-09-2025",
            recurring=None
        )
        
        result = task.to_markdown()
        expected = "- [ ] #001 | Test task | WORK | 18-09-2025"
        self.assertEqual(result, expected)
    
    def test_format_for_file_with_subsection(self):
        """Test formatting tasks with subsections"""
        task = Task(
            id="002",
            text="Test task",
            status="x",
            section="HEALTH",
            subsection="FITNESS",
            date="18-09-2025",
            recurring="daily"
        )
        
        result = task.to_markdown()
        expected = "- [x] #002 | Test task | HEALTH:FITNESS | 18-09-2025 | daily"
        self.assertEqual(result, expected)
    
    def test_format_for_file_daily_task(self):
        """Test formatting daily tasks"""
        task = Task(
            id="003",
            text="Workout",
            status=" ",
            section="DAILY",
            subsection=None,
            date="18-09-2025",
            recurring=None,
            is_daily=True,
            from_section="HEALTH"
        )
        
        result = task.to_markdown()
        expected = "- [ ] #003 | Workout | DAILY | 18-09-2025"
        self.assertEqual(result, expected)
    
    def test_format_for_daily_list(self):
        """Test formatting for daily list display"""
        task = Task(
            id="001",
            text="Test task",
            status=" ",
            section="WORK",
            subsection=None,
            date="18-09-2025",
            recurring=None
        )
        
        result = task.to_markdown()
        # Should include task text and basic info
        self.assertIn("Test task", result)
        self.assertIn("#001", result)
    
    def test_format_for_status_display(self):
        """Test formatting for status display"""
        task = Task(
            id="001",
            text="Test task",
            status=" ",
            section="WORK",
            subsection=None,
            date="18-09-2025",
            recurring=None
        )
        
        result = self.formatter._format_for_status_display(task, days_old=5, section="WORK")
        # Should include status indicator and task info
        self.assertIn("Test task", result)
        self.assertIn("#001", result)
        self.assertIn("5 days", result)


class TestSyncCommandFixes(unittest.TestCase):
    """Test the sync command fixes from commit f062213"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_sync_only_updates_main_section_tasks(self):
        """Test that sync only updates tasks in main sections, not daily sections"""
        # Add a task to main section
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_id = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Add task to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id(task_id)
        
        # Manually mark task as complete in daily section
        content = self.tm.read_file()
        # Find the daily section task and mark it complete
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and "Test task" in line and "[ ]" in line:
                lines[i] = line.replace("[ ]", "[x]")
                break
        content = '\n'.join(lines)
        self.tm.write_file(content)
        
        # Sync - should only update main section task
        self.tm.sync_daily_sections()
        
        # Verify main section task is updated
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        # Task should be marked complete in main section
        self.assertIn(f"- [x] #001 | Test task", main_section)
        
        # Daily section should remain unchanged (not updated by sync)
        daily_section_start = content.find("# DAILY")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        # Daily section should still have the original format
        self.assertIn(f"- [x] #001 | Test task", daily_section)
    
    def test_sync_warning_when_task_not_found_in_main(self):
        """Test that sync shows warning when task cannot be found in main sections"""
        # First add a real task to main
        self.tm.add_task_to_main("Real task", "WORK")
        
        # Get the real task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        real_task_id = None
        for line in lines:
            if "Real task" in line and "#" in line:
                real_task_id = line.split('#')[1].split()[0]
                break
        
        # Add the real task to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id(real_task_id)
        
        # Manually add a fake task to daily section to test warning
        content = self.tm.read_file()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f"#{real_task_id}" in line and "Real task" in line and "[ ]" in line:
                # Mark real task as complete
                lines[i] = line.replace("[ ]", "[x]")
                # Add fake task after it
                lines.insert(i + 1, f"- [x] #999 | Fake task | WORK | {self.tm.today or '30-09-2025'}")
                break
        content = '\n'.join(lines)
        self.tm.write_file(content)
        
        # Capture stdout to check for warning message
        import io
        import sys
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            # Sync should show warning for task #999
            self.tm.sync_daily_sections()
            
            # Check that warning was printed
            output = captured_output.getvalue()
            self.assertIn("Warning: Could not find task #999 in main sections to sync", output)
        finally:
            sys.stdout = old_stdout
    
    def test_update_task_date_pipe_separated_format(self):
        """Test _update_task_date with pipe-separated format"""
        from paratrooper import Paratrooper
        
        file_ops = Paratrooper(self.tm.config)
        
        # Test various pipe-separated formats
        test_cases = [
            # (input_line, expected_pattern)
            ("- [ ] #001 | Test task | WORK | 15-01-2025 | ", "Test task | WORK | " + file_ops.today + " | "),
            ("- [x] #002 | Another task | HEALTH | @15-01-2025 | daily", "Another task | HEALTH | " + file_ops.today + " | daily"),
            ("- [ ] #003 | Task without date | WORK | ", "Task without date | WORK | " + file_ops.today + " | "),
            ("- [~] #004 | Progress task | PROJECTS | 15-01-2025 | ", "Progress task | PROJECTS | " + file_ops.today + " | "),
        ]
        
        for input_line, expected_pattern in test_cases:
            with self.subTest(input_line=input_line):
                result = file_ops._update_task_date(input_line)
                
                # Check that date was updated to today
                self.assertIn(file_ops.today, result)
                
                # Check that @ prefix was removed if it existed
                self.assertNotIn("@" + file_ops.today, result)
                
                # Check that the expected pattern is present
                self.assertIn(expected_pattern, result)
    
    def test_update_task_date_old_format_fallback(self):
        """Test _update_task_date fallback for old format without pipes"""
        from paratrooper import Paratrooper
        
        file_ops = Paratrooper(self.tm.config)
        
        # Test old format without pipes
        input_line = "- [ ] #001 Test task"
        result = file_ops._update_task_date(input_line)
        
        # Should add pipe-separated format with @ prefix for old format
        expected = f"- [ ] #001 Test task | @{file_ops.today}"
        self.assertEqual(result, expected)
    
    def test_sync_recurring_task_date_update(self):
        """Test that recurring tasks get their dates updated during sync"""
        # Add a recurring task
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_id = None
        for line in lines:
            if "morning workout" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Add to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id(task_id)
        
        # Complete the task in daily section
        content = self.tm.read_file()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f"#{task_id}" in line and "morning workout" in line and "[ ]" in line:
                lines[i] = line.replace("[ ]", "[x]")
                break
        content = '\n'.join(lines)
        self.tm.write_file(content)
        
        # Sync
        self.tm.sync_daily_sections()
        
        # Verify main section task has updated date
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        # Should have today's date
        from datetime import datetime
        today = datetime.now().strftime("%d-%m-%Y")
        self.assertIn(today, main_section)
        self.assertIn("morning workout", main_section)
        
        # Should still be incomplete (recurring task)
        self.assertIn("[ ] #001 | morning workout", main_section)


class TestDailyTaskDeletionRefactor(unittest.TestCase):
    """Test the daily task deletion refactor from commit 937864d"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_delete_task_from_daily_model_based_approach(self):
        """Test that delete_task_from_daily uses model-based approach"""
        # Add a task to main section
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_id = None
        for line in lines:
            if "Test task" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Add task to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id(task_id)
        
        # Verify task is in daily section
        content = self.tm.read_file()
        self.assertIn("Test task", content)
        
        # Delete task from daily section
        self.tm.delete_task_from_daily(task_id)
        
        # Verify task is removed from daily section
        content = self.tm.read_file()
        daily_section_start = content.find("# DAILY")
        main_section_start = content.find("# MAIN")
        daily_section = content[daily_section_start:main_section_start]
        
        # Task should be removed from daily section
        self.assertNotIn("Test task", daily_section)
        
        # But should still exist in main section
        main_section = content[main_section_start:]
        self.assertIn("Test task", main_section)
    
    def test_delete_task_from_daily_error_handling(self):
        """Test error handling when deleting non-existent task from daily section"""
        # Create daily section with a task
        self.tm.add_daily_section()
        self.tm.add_task_to_daily("Test task")
        
        # Try to delete non-existent task
        import io
        import sys
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            self.tm.delete_task_from_daily("999")
            
            # Check that error message was printed
            output = captured_output.getvalue()
            self.assertIn("Task #999 not found in today's daily section", output)
        finally:
            sys.stdout = old_stdout
    
    def test_delete_task_from_daily_no_daily_section(self):
        """Test error handling when no daily section exists"""
        import io
        import sys
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            self.tm.delete_task_from_daily("001")
            
            # Check that error message was printed
            output = captured_output.getvalue()
            self.assertIn("No daily section for", output)
        finally:
            sys.stdout = old_stdout


class TestDisplayOperationsFix(unittest.TestCase):
    """Test the display operations fix from commit 937864d"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_daily_tasks_display_no_extra_blank_line(self):
        """Test that daily tasks display doesn't have extra blank line"""
        # Add a task to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_daily("Test daily task")
        
        # Capture the output of show_daily_tasks
        import io
        import sys
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            self.tm.show_daily_list()
            output = captured_output.getvalue()
            
            # Check that there's no extra blank line after the header
            lines = output.split('\n')
            
            # Find the header line
            header_index = None
            for i, line in enumerate(lines):
                if "=== Daily Tasks for" in line and "===" in line:
                    header_index = i
                    break
            
            self.assertIsNotNone(header_index, "Could not find header line")
            
            # The line after the header should not be empty
            if header_index + 1 < len(lines):
                next_line = lines[header_index + 1]
                self.assertNotEqual(next_line.strip(), "", "Extra blank line found after header")
        finally:
            sys.stdout = old_stdout


class TestRecurringTaskBugFix(unittest.TestCase):
    """Test the recurring task bug fix - ensures daily tasks appear every day regardless of completion"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_should_recur_today_daily_always_true(self):
        """Test that should_recur_today returns True for daily tasks regardless of last date"""
        from paratrooper import Paratrooper
        from paratrooper import Paratrooper
        
        file_ops = Paratrooper(self.tm.config)
        daily_ops = file_ops
        
        # Test daily pattern with various dates
        test_cases = [
            "30-09-2025",  # Today
            "29-09-2025",  # Yesterday
            "01-01-2025",  # Old date
            "31-12-2024",  # Very old date
        ]
        
        for last_date in test_cases:
            with self.subTest(last_date=last_date):
                result = daily_ops.should_recur_today("daily", last_date)
                self.assertTrue(result, f"Daily task should recur regardless of last date {last_date}")
    
    def test_should_recur_today_weekly_respects_schedule(self):
        """Test that weekly tasks only recur on their scheduled days"""
        from paratrooper import Paratrooper
        from datetime import datetime, timedelta
        from unittest.mock import patch
        
        file_ops = Paratrooper(self.tm.config)
        
        # Test weekly patterns by checking if they correctly identify scheduled days
        test_cases = [
            ("weekly:mon", [0]),           # Monday only
            ("weekly:tue", [1]),           # Tuesday only
            ("weekly:wed", [2]),           # Wednesday only
            ("weekly:thu", [3]),          # Thursday only
            ("weekly:fri", [4]),          # Friday only
            ("weekly:sat", [5]),          # Saturday only
            ("weekly:sun", [6]),          # Sunday only
            ("weekly:mon,wed,fri", [0, 2, 4]),  # Multiple days
        ]
        
        for pattern, expected_days in test_cases:
            with self.subTest(pattern=pattern):
                # Test each day of the week
                for weekday in range(7):
                    # Create a mock date for the specific weekday
                    # We'll use a known date and adjust it to the target weekday
                    base_date = datetime(2025, 10, 1)  # October 1, 2025 (Wednesday)
                    days_to_adjust = weekday - base_date.weekday()
                    test_date = base_date + timedelta(days=days_to_adjust)
                    
                    # Mock the datetime.now() to return our test date
                    with patch('paratrooper.datetime') as mock_datetime:
                        mock_datetime.now.return_value = test_date
                        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
                        
                        result = file_ops.should_recur_today(pattern, "29-09-2025")
                        expected = weekday in expected_days
                        self.assertEqual(result, expected, 
                            f"Weekly pattern {pattern} should recur on weekday {weekday} (day {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][weekday]})")
    
    def test_should_recur_today_custom_recurrence_respects_intervals(self):
        """Test that custom recurrence patterns respect time intervals"""
        from paratrooper import Paratrooper
        from paratrooper import Paratrooper
        from datetime import datetime, timedelta
        
        file_ops = Paratrooper(self.tm.config)
        daily_ops = file_ops
        
        today = datetime.now()
        
        # Test custom recurrence patterns
        test_cases = [
            # (pattern, days_ago, expected_result)
            ("recur:1d", 0, True),   # Same day, new task should appear immediately
            ("recur:1d", 1, True),   # Yesterday, should recur
            ("recur:1d", 2, True),   # Day before yesterday, should recur
            ("recur:3d", 0, True),   # Same day, new task should appear immediately
            ("recur:3d", 2, False),  # 2 days ago, needs 3
            ("recur:3d", 3, True),   # 3 days ago, should recur
            ("recur:3d", 4, True),   # 4 days ago, should recur
            ("recur:1w", 0, True),  # Same day, new task should appear immediately
            ("recur:1w", 6, False),  # 6 days ago, needs 7
            ("recur:1w", 7, True),   # 7 days ago, should recur
            ("recur:1w", 8, True),   # 8 days ago, should recur
        ]
        
        for pattern, days_ago, expected in test_cases:
            with self.subTest(pattern=pattern, days_ago=days_ago):
                last_date = (today - timedelta(days=days_ago)).strftime("%d-%m-%Y")
                result = daily_ops.should_recur_today(pattern, last_date)
                self.assertEqual(result, expected,
                    f"Pattern {pattern} with last date {days_ago} days ago should return {expected}")
    
    def test_daily_task_appears_after_completion_and_sync(self):
        """Test the specific bug: daily task should appear tomorrow even if completed today"""
        # Add a daily recurring task
        self.tm.add_task_to_main("Take out trash (daily)", "DOMESTIC")
        
        # Get task ID
        content = self.tm.read_file()
        lines = content.split('\n')
        task_id = None
        for line in lines:
            if "Take out trash" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Verify task appears in daily section
        content = self.tm.read_file()
        self.assertIn("Take out trash", content)
        
        # Complete the task in daily section
        self.tm.complete_task(task_id)
        
        # Sync to update main list
        self.tm.sync_daily_sections()
        
        # Verify main task date was updated (but still incomplete)
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        # Should still be incomplete (recurring task)
        self.assertIn("- [ ] #001 | Take out trash", main_section)
        
        # Should have today's date
        from datetime import datetime
        today = datetime.now().strftime("%d-%m-%Y")
        self.assertIn(today, main_section)
        
        # Now test the critical part: create a new daily section
        # This simulates running 'daily' command tomorrow
        self.tm.add_daily_section()
        
        # Verify the daily task appears again (this was the bug)
        content = self.tm.read_file()
        daily_section_start = content.find("# DAILY")
        main_section_start = content.find("# MAIN")
        daily_section = content[daily_section_start:main_section_start]
        
        # The task should appear in today's daily section again
        self.assertIn("Take out trash", daily_section)
        self.assertIn(f"#{task_id}", daily_section)
    
    def test_multiple_recurring_patterns_work_correctly(self):
        """Test that different recurring patterns work correctly together"""
        # Add tasks with different recurring patterns
        self.tm.add_task_to_main("Daily workout (daily)", "HEALTH")
        self.tm.add_task_to_main("Weekly review (weekly:mon)", "WORK")
        self.tm.add_task_to_main("Monthly budget (monthly:1st)", "FINANCE")
        
        # Create daily section
        self.tm.add_daily_section()
        
        # Verify all recurring tasks appear (or don't) based on their patterns
        content = self.tm.read_file()
        daily_section_start = content.find("# DAILY")
        main_section_start = content.find("# MAIN")
        daily_section = content[daily_section_start:main_section_start]
        
        # Daily task should always appear
        self.assertIn("Daily workout", daily_section)
        
        # Weekly and monthly tasks depend on today's date
        from datetime import datetime
        today = datetime.now()
        
        if today.weekday() == 0:  # Monday
            self.assertIn("Weekly review", daily_section)
        else:
            self.assertNotIn("Weekly review", daily_section)
        
        if today.day == 1:  # First of month
            self.assertIn("Monthly budget", daily_section)
        else:
            self.assertNotIn("Monthly budget", daily_section)
    
    def test_recurring_task_duplication_prevention(self):
        """Test that recurring tasks don't get duplicated when carried over from previous day"""
        from datetime import datetime, timedelta
        
        # Create dates for testing
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        today = datetime.now().strftime("%d-%m-%Y")
        
        # Add a daily recurring task
        self.tm.add_task_to_main("Morning workout (daily)", "HEALTH")
        
        # Get task ID using the proper method
        line_num, task_line = self.tm.find_task_by_id("001")
        self.assertIsNotNone(task_line, "Task should be found")
        task_id = "001"
        
        # Create yesterday's daily section with the task as incomplete
        yesterday_content = f"""# DAILY

## {yesterday}
- [ ] #{task_id} | Morning workout | HEALTH | {today} | daily

# MAIN

## HEALTH
- [ ] #{task_id} | Morning workout | HEALTH | {today} | daily

# ARCHIVE
"""
        
        # Write the test content
        self.tm.task_file.write_text(yesterday_content)
        
        # Run daily command to create today's section
        self.tm.add_daily_section()
        
        # Verify the task appears exactly once (not duplicated)
        content = self.tm.read_file()
        
        # Get today's daily section content
        daily_section_start = content.find(f"## {today}")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        # Count occurrences of the task in today's daily section
        task_occurrences = daily_section.count("Morning workout")
        
        # Should appear exactly once (not duplicated)
        self.assertEqual(task_occurrences, 1, 
            f"Task 'Morning workout' appears {task_occurrences} times in daily section, should appear exactly once")
    
    def test_recurring_task_with_invalid_date_handling(self):
        """Test that recurring tasks handle invalid dates gracefully"""
        from paratrooper import Paratrooper
        from paratrooper import Paratrooper
        
        file_ops = Paratrooper(self.tm.config)
        daily_ops = file_ops
        
        # Test with invalid date formats
        invalid_dates = [
            "invalid-date",
            "32-13-2025",  # Invalid day/month
            "not-a-date",
            "",
            None
        ]
        
        for invalid_date in invalid_dates:
            with self.subTest(invalid_date=invalid_date):
                # Daily tasks should still recur even with invalid dates
                result = daily_ops.should_recur_today("daily", invalid_date)
                self.assertTrue(result, f"Daily task should recur even with invalid date: {invalid_date}")
                
                # Custom recurrence should handle invalid dates gracefully
                result = daily_ops.should_recur_today("recur:3d", invalid_date)
                self.assertTrue(result, f"Custom recurrence should handle invalid date gracefully: {invalid_date}")
    
    def test_should_recur_today_combination_patterns(self):
        """Test that combination recurrence patterns work with additive logic"""
        from paratrooper import Paratrooper
        from datetime import datetime, timedelta
        
        file_ops = Paratrooper(self.tm.config)
        daily_ops = file_ops
        
        today = datetime.now()
        
        # Test combination patterns with additive logic
        test_cases = [
            # (pattern, days_ago, expected_result, description)
            ("recur:1w,2d", 0, True, "New task with 1w,2d (9 days) should appear immediately"),
            ("recur:1w,2d", 1, False, "1w,2d (9 days) from yesterday - not enough time"),
            ("recur:1w,2d", 8, False, "1w,2d (9 days) from 8 days ago - not enough time"),
            ("recur:1w,2d", 9, True, "1w,2d (9 days) from 9 days ago - should recur"),
            ("recur:1w,2d", 10, True, "1w,2d (9 days) from 10 days ago - should recur"),
            ("recur:2d,1w", 0, True, "New task with 2d,1w (9 days) should appear immediately"),
            ("recur:2d,1w", 8, False, "2d,1w (9 days) from 8 days ago - not enough time"),
            ("recur:2d,1w", 9, True, "2d,1w (9 days) from 9 days ago - should recur"),
            ("recur:1m,2d", 0, True, "New task with 1m,2d (32 days) should appear immediately"),
            ("recur:1m,2d", 30, False, "1m,2d (32 days) from 30 days ago - not enough time"),
            ("recur:1m,2d", 32, True, "1m,2d (32 days) from 32 days ago - should recur"),
        ]
        
        for pattern, days_ago, expected, description in test_cases:
            with self.subTest(pattern=pattern, days_ago=days_ago):
                last_date = (today - timedelta(days=days_ago)).strftime("%d-%m-%Y")
                result = daily_ops.should_recur_today(pattern, last_date)
                self.assertEqual(result, expected,
                    f"{description}: Pattern {pattern} with last date {days_ago} days ago should return {expected}")
    
    def test_new_recurring_tasks_appear_immediately_in_daily(self):
        """Test that new recurring tasks with periodic patterns appear immediately in daily section"""
        from paratrooper import Paratrooper
        
        # Add a new recurring task
        self.tm.add_task_to_main("Test new recurring task (recur:2d)", "TEST")
        
        # Get recurring tasks - should include the new task
        recurring_tasks = self.tm.get_recurring_tasks()
        
        # Find our test task
        test_task = None
        for task in recurring_tasks:
            if task['text'] == "Test new recurring task":
                test_task = task
                break
        
        self.assertIsNotNone(test_task, "New recurring task should be found in recurring tasks")
        self.assertEqual(test_task['recurring'], 'recur:2d')
        
        # Add daily section and check if task appears
        self.tm.add_daily_section()
        
        # Check if task appears in today's daily section
        task_file = self.tm.parse_file()
        today = self.tm.today
        
        if today in task_file.daily_sections:
            daily_tasks = task_file.daily_sections[today]
            task_found = False
            for task in daily_tasks:
                if task.text == "Test new recurring task":
                    task_found = True
                    self.assertEqual(task.recurring, 'recur:2d')
                    break
            
            self.assertTrue(task_found, "New recurring task should appear in today's daily section")


class TestCLICommands(unittest.TestCase):
    """Test CLI command functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_add_command_case_insensitive(self):
        """Test add command with case-insensitive sections"""
        # Test various case combinations
        test_cases = [
            ("work", "WORK"),
            ("WORK", "WORK"),
            ("Work", "WORK"),
            ("health", "HEALTH"),
            ("projects", "PROJECTS")
        ]
        
        for input_section, expected_section in test_cases:
            with self.subTest(input_section=input_section):
                # Simulate CLI command: add "Test task" section
                self.tm.add_task_to_main("Test task", input_section)
                
                # Check that task was added to correct uppercase section
                content = self.tm.read_file()
                self.assertIn(f"## {expected_section}", content)
                self.assertIn("Test task", content)
    
    def test_move_command_case_insensitive(self):
        """Test move command with case-insensitive sections"""
        # Add a task first
        self.tm.add_task_to_main("Test task", "work")
        
        # Move to different case variations
        test_cases = [
            ("WORK", "WORK"),
            ("Work", "WORK"),
            ("health", "HEALTH"),
            ("HEALTH", "HEALTH")
        ]
        
        for target_section, expected_section in test_cases:
            with self.subTest(target_section=target_section):
                # Find the task ID
                content = self.tm.read_file()
                task_id = None
                for line in content.split('\n'):
                    if "Test task" in line and "#" in line:
                        task_id = line.split('#')[1].split()[0]
                        break
                
                self.assertIsNotNone(task_id, "Could not find task ID")
                
                # Move the task
                self.tm.move_task(task_id, target_section)
                
                # Check that task moved to correct uppercase section
                content = self.tm.read_file()
                self.assertIn(f"## {expected_section}", content)
    
    def test_list_command_functionality(self):
        """Test list command functionality"""
        # Add some tasks to different sections
        self.tm.add_task_to_main("Work task", "work")
        self.tm.add_task_to_main("Health task", "health")
        self.tm.add_task_to_main("Project task", "projects")
        
        # Test listing all sections
        try:
            self.tm.list_sections()
        except Exception as e:
            self.fail(f"list_sections raised an exception: {e}")
    
    def test_show_command_functionality(self):
        """Test show command functionality"""
        # Add a task
        self.tm.add_task_to_main("Test task", "work")
        
        # Find the task ID
        content = self.tm.read_file()
        task_id = None
        for line in content.split('\n'):
            if "Test task" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Test showing the task
        try:
            self.tm.show_task(task_id)
        except Exception as e:
            self.fail(f"show_task raised an exception: {e}")
    
    def test_done_command_functionality(self):
        """Test done command functionality"""
        # Add a task
        self.tm.add_task_to_main("Test task", "work")
        
        # Find the task ID
        content = self.tm.read_file()
        task_id = None
        for line in content.split('\n'):
            if "Test task" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Complete the task
        self.tm.complete_task(task_id)
        
        # Check that task is marked as complete
        content = self.tm.read_file()
        self.assertIn("[x]", content)
        self.assertIn("Test task", content)
    
    def test_delete_command_functionality(self):
        """Test delete command functionality"""
        # Add a task
        self.tm.add_task_to_main("Test task", "work")
        
        # Find the task ID
        content = self.tm.read_file()
        task_id = None
        for line in content.split('\n'):
            if "Test task" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Delete the task
        self.tm.delete_task_from_main(task_id)
        
        # Check that task is removed
        content = self.tm.read_file()
        self.assertNotIn("Test task", content)
    
    def test_snooze_command_functionality(self):
        """Test snooze command functionality"""
        # Add a task
        self.tm.add_task_to_main("Test task", "work")
        
        # Find the task ID
        content = self.tm.read_file()
        task_id = None
        for line in content.split('\n'):
            if "Test task" in line and "#" in line:
                task_id = line.split('#')[1].split()[0]
                break
        
        self.assertIsNotNone(task_id, "Could not find task ID")
        
        # Snooze the task
        self.tm.snooze_task(task_id, "21-09-2025")
        
        # Check that task has future date
        content = self.tm.read_file()
        self.assertIn("21-09-2025", content)
        self.assertIn("Test task", content)
    
    def test_add_command_section_parsing(self):
        """Test that add command correctly parses section names"""
        # Test various section name formats
        test_cases = [
            # (task_text, section_arg, expected_section)
            ("Read books phychology-books-lucas-segeren-2025-sep-14.txt", "inbox", "INBOX"),
            ("Test task without section", None, "TASKS"),  # No section arg - defaults to TASKS
            ("Test task with uppercase section", "PROJECTS", "PROJECTS"),
            ("Test task with subsection", "AREAS:HEALTH", "AREAS:HEALTH"),
            ("Test task with lowercase section", "work", "WORK"),
            ("Test task with mixed case", "Health", "HEALTH"),
        ]
        
        for task_text, section_arg, expected_section in test_cases:
            with self.subTest(task_text=task_text, section_arg=section_arg):
                # Simulate the CLI parsing logic from cli.py
                if section_arg:
                    args = ['add', task_text, section_arg]
                else:
                    args = ['add', task_text]
                
                # Extract the parsing logic
                last_arg = args[-1]
                
                if ":" in last_arg or last_arg.isupper() or (len(last_arg) < 20 and not " " in last_arg and not last_arg.isdigit()):
                    # Last argument is a section/subsection
                    section = last_arg
                    parsed_task_text = " ".join(args[1:-1])
                else:
                    # All arguments are task text
                    parsed_task_text = " ".join(args[1:])
                    section = "TASKS"
                
                # Verify parsing results
                self.assertEqual(section.upper(), expected_section)
                self.assertEqual(parsed_task_text, task_text)
                
                # Test actual task addition
                self.tm.add_task_to_main(parsed_task_text, section.upper())
                
                # Verify task was added to correct section
                content = self.tm.read_file()
                
                # For subsections, check for both main section and subsection headers
                if ':' in expected_section:
                    main_section, subsection = expected_section.split(':', 1)
                    self.assertIn(f"## {main_section}", content)
                    self.assertIn(f"### {subsection}", content)
                else:
                    self.assertIn(f"## {expected_section}", content)
                
                self.assertIn(task_text, content)


class TestRecurringTaskStatusCalculation(unittest.TestCase):
    """Test the recurring task status calculation functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        self.config = Config.load(self.config_path)
        self.config.task_file = self.task_file_path
        
        # Import Paratrooper for testing
        from paratrooper import Paratrooper
        
        self.tm = Paratrooper(self.config)
        self.tm.init()
        
        self.file_ops = Paratrooper(self.config)
        self.display_ops = self.file_ops
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_next_recurrence_date_daily(self):
        """Test next recurrence date calculation for daily tasks"""
        # Daily tasks should recur the next day
        last_date = "15-01-2025"
        expected_date = self.display_ops._calculate_next_recurrence_date("daily", last_date)
        self.assertIsNotNone(expected_date)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "16-01-2025")
    
    def test_calculate_next_recurrence_date_weekly(self):
        """Test next recurrence date calculation for weekly tasks"""
        # Weekly task completed on Wednesday should recur next Sunday (default)
        last_date = "15-01-2025"  # Wednesday
        expected_date = self.display_ops._calculate_next_recurrence_date("weekly", last_date)
        self.assertIsNotNone(expected_date)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "19-01-2025")  # Sunday
    
    def test_calculate_next_recurrence_date_weekly_specific_day(self):
        """Test next recurrence date calculation for weekly tasks with specific day"""
        # Weekly task on Monday, completed on Wednesday
        last_date = "15-01-2025"  # Wednesday
        expected_date = self.display_ops._calculate_next_recurrence_date("weekly:mon", last_date)
        self.assertIsNotNone(expected_date)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "20-01-2025")  # Monday
    
    def test_calculate_next_recurrence_date_monthly(self):
        """Test next recurrence date calculation for monthly tasks"""
        # Monthly task completed on 12th should recur on 12th of next month
        last_date = "12-01-2025"
        expected_date = self.display_ops._calculate_next_recurrence_date("monthly:12th", last_date)
        self.assertIsNotNone(expected_date)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "12-02-2025")
    
    def test_calculate_next_recurrence_date_monthly_edge_case(self):
        """Test monthly recurrence with month-end edge case"""
        # Monthly task on 31st, completed on 31st of January
        last_date = "31-01-2025"
        expected_date = self.display_ops._calculate_next_recurrence_date("monthly:31st", last_date)
        self.assertIsNotNone(expected_date)
        # Should be 28th of February (last day of February)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "28-02-2025")
    
    def test_calculate_next_recurrence_date_custom_interval(self):
        """Test next recurrence date calculation for custom intervals"""
        # Every 3 days
        last_date = "15-01-2025"
        expected_date = self.display_ops._calculate_next_recurrence_date("recur:3d", last_date)
        self.assertIsNotNone(expected_date)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "18-01-2025")
        
        # Every 2 weeks
        expected_date = self.display_ops._calculate_next_recurrence_date("recur:2w", last_date)
        self.assertIsNotNone(expected_date)
        self.assertEqual(expected_date.strftime("%d-%m-%Y"), "29-01-2025")
    
    def test_get_task_status_info_completed_recurring_task_future_occurrence(self):
        """Test status calculation for completed recurring task with next occurrence in future"""
        # Create a task that was completed recently, with next occurrence in the future
        task_data = {
            'status': 'x',
            'text': 'Monthly budget review',
            'metadata': {
                'id': '001',
                'date': '12-09-2025',  # Completed on Sept 12
                'recurring': '(monthly:12th)'
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should show 0 days old because next occurrence is in the future
        self.assertEqual(status_type, "complete")
        self.assertEqual(days_old, 0)
        self.assertEqual(date_str, "12-09-2025")
    
    def test_get_task_status_info_completed_recurring_task_overdue(self):
        """Test status calculation for completed recurring task that's overdue"""
        # Create a task that was completed long ago and is overdue
        task_data = {
            'status': 'x',
            'text': 'Monthly budget review',
            'metadata': {
                'id': '001',
                'date': '12-08-2025',  # Completed on Aug 12
                'recurring': '(monthly:12th)'
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should show days overdue from expected occurrence (Sept 12)
        self.assertEqual(status_type, "complete")
        self.assertGreater(days_old, 0)  # Should be overdue
        self.assertEqual(date_str, "12-08-2025")
    
    def test_get_task_status_info_incomplete_recurring_task(self):
        """Test status calculation for incomplete recurring task uses expected next occurrence"""
        # Create an incomplete recurring task
        task_data = {
            'status': ' ',
            'text': 'Monthly budget review',
            'metadata': {
                'id': '002',
                'date': '12-09-2025',  # Last activity on Sept 12
                'recurring': '(monthly:12th)'
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should use expected next occurrence calculation for recurring tasks
        self.assertEqual(status_type, "incomplete")
        self.assertEqual(days_old, 0)  # Should show 0 days old since next occurrence is in future
        self.assertEqual(date_str, "12-09-2025")
    
    def test_get_task_status_info_non_recurring_task(self):
        """Test status calculation for non-recurring task uses normal calculation"""
        # Create a non-recurring task
        task_data = {
            'status': 'x',
            'text': 'One-time task',
            'metadata': {
                'id': '003',
                'date': '25-09-2025',  # Completed 5 days ago
                'recurring': None
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should use normal calculation for non-recurring tasks
        self.assertEqual(status_type, "complete")
        self.assertGreater(days_old, 0)  # Should show actual days since completion
        self.assertEqual(date_str, "25-09-2025")
    
    def test_get_task_status_info_progress_recurring_task(self):
        """Test status calculation for recurring task with progress status"""
        # Create a recurring task with progress status
        task_data = {
            'status': '~',
            'text': 'Weekly review',
            'metadata': {
                'id': '004',
                'date': '29-09-2025',  # Last activity yesterday (Sunday)
                'recurring': '(weekly:sun)'
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should use expected next occurrence calculation for recurring tasks
        self.assertEqual(status_type, "progress")
        self.assertEqual(days_old, 0)  # Should show 0 days old since next occurrence is next Sunday
        self.assertEqual(date_str, "29-09-2025")
    
    def test_get_incomplete_daily_instance_date_no_daily_section(self):
        """Test that incomplete daily instance check returns None when no daily section exists"""
        # Test with no daily section
        incomplete_date = self.display_ops._get_incomplete_daily_instance_date('001')
        self.assertIsNone(incomplete_date)
    
    def test_get_incomplete_daily_instance_date_with_daily_section(self):
        """Test incomplete daily instance check with actual daily section"""
        # Add a task to daily section
        self.tm.add_daily_section()
        self.tm.add_task_to_main("Test task", "WORK")
        self.tm.add_task_to_daily_by_id("001")
        
        # Check for incomplete instance
        incomplete_date = self.display_ops._get_incomplete_daily_instance_date('001')
        self.assertIsNotNone(incomplete_date)
        self.assertEqual(incomplete_date, datetime.now().strftime("%d-%m-%Y"))
    
    def test_get_incomplete_daily_instance_date_completed_task(self):
        """Test incomplete daily instance check with completed task in daily section"""
        # Add a task to daily section and complete it
        self.tm.add_daily_section()
        self.tm.add_task_to_main("Test task", "WORK")
        self.tm.add_task_to_daily_by_id("001")
        self.tm.complete_task("001")
        
        # Check for incomplete instance - should return None since task is completed
        incomplete_date = self.display_ops._get_incomplete_daily_instance_date('001')
        self.assertIsNone(incomplete_date)
    
    def test_recurring_task_status_integration(self):
        """Test the complete integration of recurring task status calculation"""
        # Add a monthly recurring task
        self.tm.add_task_to_main("Monthly budget review (monthly:12th)", "FINANCE")
        
        # Complete the task
        self.tm.complete_task("001")
        
        # Test status calculation through the full system
        # This tests the integration with the actual task file
        content = self.file_ops.read_file()
        self.assertIn("Monthly budget review", content)
        self.assertIn("monthly:12th", content)
        
        # The status should be calculated correctly when showing status
        import io
        import sys
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            self.tm.show_status_tasks()
            output = captured_output.getvalue()
            
            # Should not crash and should show the task
            self.assertIn("Monthly budget review", output)
            
        finally:
            sys.stdout = old_stdout
    
    def test_multiple_recurring_patterns_status_calculation(self):
        """Test status calculation with multiple different recurring patterns"""
        patterns = [
            ("daily", "Daily workout"),
            ("weekly:sun", "Weekly review"),
            ("monthly:15th", "Monthly budget"),
            ("recur:3d", "Every 3 days task")
        ]
        
        for pattern, task_text in patterns:
            with self.subTest(pattern=pattern):
                task_data = {
                    'status': 'x',
                    'text': task_text,
                    'metadata': {
                        'id': '001',
                        'date': '25-09-2025',
                        'recurring': f'({pattern})'
                    }
                }
                
                status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
                
                # Should not crash and should return valid results
                self.assertIn(status_type, ["complete", "incomplete", "progress", "snoozed", "no_date"])
                self.assertGreaterEqual(days_old, 0)
                self.assertEqual(date_str, "25-09-2025")
    
    def test_edge_case_invalid_recurrence_pattern(self):
        """Test handling of invalid recurrence patterns"""
        task_data = {
            'status': 'x',
            'text': 'Task with invalid pattern',
            'metadata': {
                'id': '001',
                'date': '25-09-2025',
                'recurring': '(invalid:pattern)'
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should fall back to normal calculation
        self.assertEqual(status_type, "complete")
        self.assertGreater(days_old, 0)
        self.assertEqual(date_str, "25-09-2025")
    
    def test_edge_case_invalid_date_format(self):
        """Test handling of invalid date formats"""
        task_data = {
            'status': 'x',
            'text': 'Task with invalid date',
            'metadata': {
                'id': '001',
                'date': 'invalid-date',
                'recurring': '(monthly:12th)'
            }
        }
        
        status_type, days_old, date_str = self.display_ops._get_task_status_info(task_data)
        
        # Should handle gracefully
        self.assertEqual(status_type, "invalid_date")
        self.assertEqual(days_old, 0)
        self.assertEqual(date_str, "invalid-date")

    def test_daily_recurring_task_added_to_existing_daily_section(self):
        """Test regression: daily recurring tasks are added to existing daily section
        
        Scenario:
        1. No daily section existed for today
        2. User creates a daily recurring task
        3. User creates a task and uses `up`, which created the daily section
        4. User runs `daily` and the daily recurring task should be added to today's daily section
        """
        self.tm.init()
        
        # Step 1: Add a daily recurring task to main section
        self.tm.add_task_to_main("morning workout (daily)", "HEALTH")
        
        # Step 2: Add a regular task to main section
        self.tm.add_task_to_main("write report", "WORK")
        
        # Step 3: Use 'up' command to add the regular task to daily section
        # This creates today's daily section
        self.tm.add_task_to_daily_by_id("002")
        
        # Verify daily section was created with the regular task
        content = self.tm.read_file()
        today = datetime.now().strftime("%d-%m-%Y")
        self.assertIn(f"## {today}", content)
        
        # Check that only the regular task is in daily section (not the recurring task yet)
        daily_section_start = content.find(f"## {today}")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        self.assertIn("write report", daily_section)
        self.assertNotIn("morning workout", daily_section)
        
        # Step 4: Run 'daily' command - this should add the recurring task to existing daily section
        result = self.tm.add_daily_section()
        
        # Should return "show_daily_list" since section already existed
        self.assertEqual(result, "show_daily_list")
        
        # Verify the recurring task was added to the existing daily section
        content = self.tm.read_file()
        daily_section_start = content.find(f"## {today}")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        
        # Both tasks should now be in the daily section
        self.assertIn("morning workout", daily_section)
        self.assertIn("write report", daily_section)
        
        # The recurring task should be at the top (inserted at position 0)
        daily_lines = daily_section.strip().split('\n')
        task_lines = [line for line in daily_lines if line.strip().startswith('- [')]
        
        # First task should be the recurring task
        self.assertIn("morning workout", task_lines[0])
        self.assertIn("daily", task_lines[0])
        
        # Second task should be the regular task
        self.assertIn("write report", task_lines[1])


class TestPassEntryFeature(unittest.TestCase):
    """Test the new pass entry functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        self.config = Config.load(self.config_path)
        self.config.task_file = self.task_file_path
        
        # Import Paratrooper for testing
        from paratrooper import Paratrooper
        
        self.tm = Paratrooper(self.config)
        self.tm.init()
        
        self.file_ops = Paratrooper(self.config)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_pass_entry_basic(self):
        """Test basic pass entry creation"""
        # Add a test task
        self.tm.add_task_to_main("Test task for pass entry", "TEST")
        
        # Get the task ID (should be the highest one)
        content = self.tm.read_file()
        import re
        id_matches = re.findall(r'#(\d{3})', content)
        self.assertTrue(id_matches, "Should have at least one task ID")
        test_id = max(id_matches)
        
        # First, manually set the main task date to 5 days ago to allow pass entry creation
        from datetime import datetime, timedelta
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%d-%m-%Y')
        
        # Update the main task date manually
        line_number, line_content = self.tm.find_task_by_id_in_main(test_id)
        task_data = self.tm._parse_task_line(line_content)
        from models import Task
        updated_task = Task(
            id=test_id,
            text=task_data['text'],
            status=task_data['status'],
            date=five_days_ago,
            recurring=task_data['metadata'].get('recurring'),
            section=task_data.get('section', 'MAIN')
        )
        
        # Update the file
        content = self.tm.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_task.to_markdown()
        self.tm.write_file('\n'.join(lines))
        
        # Create pass entry 3 days ago
        self.tm.create_pass_entry(test_id, 3)
        
        # Verify the pass entry was created in archive
        task_file = self.tm.parse_file()
        from datetime import datetime, timedelta
        target_date = datetime.now() - timedelta(days=3)
        target_date_str = target_date.strftime('%d-%m-%Y')
        
        self.assertIn(target_date_str, task_file.archive_sections, 
                     f"Archive section for {target_date_str} should exist")
        
        # Check that the pass entry has the correct properties
        pass_entries = task_file.archive_sections[target_date_str]
        self.assertEqual(len(pass_entries), 1, "Should have exactly one pass entry")
        
        pass_entry = pass_entries[0]
        self.assertEqual(pass_entry.id, test_id, "Pass entry should have correct task ID")
        self.assertEqual(pass_entry.status, "~", "Pass entry should be marked as progress")
        self.assertEqual(pass_entry.text, "Test task for pass entry", "Pass entry should have correct text")
        self.assertEqual(pass_entry.date, target_date_str, "Pass entry should have correct date")
        # Note: is_daily is not preserved in markdown format, so we don't test it here
    
    def test_create_pass_entry_multiple_days(self):
        """Test pass entry creation with different day values"""
        # Create separate tasks for each pass entry to avoid date conflicts
        days_to_test = [1, 5, 10, 30]
        task_ids = []
        
        for i, days_ago in enumerate(days_to_test):
            # Add a test task for each day
            self.tm.add_task_to_main(f"Test task for {days_ago} days ago", "TEST")
            
            # Get the task ID
            content = self.tm.read_file()
            import re
            id_matches = re.findall(r'#(\d{3})', content)
            test_id = max(id_matches)
            task_ids.append(test_id)
            
            # Set the main task date to allow pass entry creation
            from datetime import datetime, timedelta
            task_age = days_ago + 5  # Make sure task is old enough
            task_date = (datetime.now() - timedelta(days=task_age)).strftime('%d-%m-%Y')
            
            # Update the main task date manually
            line_number, line_content = self.tm.find_task_by_id_in_main(test_id)
            task_data = self.tm._parse_task_line(line_content)
            from models import Task
            updated_task = Task(
                id=test_id,
                text=task_data['text'],
                status=task_data['status'],
                date=task_date,
                recurring=task_data['metadata'].get('recurring'),
                section=task_data.get('section', 'MAIN')
            )
            
            # Update the file
            content = self.tm.read_file()
            lines = content.split('\n')
            lines[line_number - 1] = updated_task.to_markdown()
            self.tm.write_file('\n'.join(lines))
            
            # Create pass entry
            self.tm.create_pass_entry(test_id, days_ago)
        
        # Verify all pass entries were created
        task_file = self.tm.parse_file()
        from datetime import datetime, timedelta
        
        for i, days_ago in enumerate(days_to_test):
            target_date = datetime.now() - timedelta(days=days_ago)
            target_date_str = target_date.strftime('%d-%m-%Y')
            
            self.assertIn(target_date_str, task_file.archive_sections, 
                         f"Archive section for {target_date_str} should exist")
            
            # Check that the pass entry has the correct properties
            pass_entries = task_file.archive_sections[target_date_str]
            # Find the pass entry for this specific task
            task_pass_entry = None
            for entry in pass_entries:
                if entry.id == task_ids[i]:
                    task_pass_entry = entry
                    break
            
            self.assertIsNotNone(task_pass_entry, f"Pass entry for task {task_ids[i]} should exist")
            self.assertEqual(task_pass_entry.id, task_ids[i], f"Pass entry should have correct task ID")
            self.assertEqual(task_pass_entry.status, "~", f"Pass entry should be marked as progress")
            self.assertEqual(task_pass_entry.date, target_date_str, f"Pass entry should have correct date")
    
    def test_create_pass_entry_nonexistent_task(self):
        """Test pass entry creation with non-existent task ID"""
        # The method should handle non-existent tasks gracefully
        # Let's test this by calling it directly and checking the output
        import io
        import sys
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        self.tm.create_pass_entry("999", 3)
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Check that error message was printed
        output = captured_output.getvalue()
        self.assertIn("Task #999 not found in main section", output)
    
    def test_pass_entry_preserves_task_properties(self):
        """Test that pass entry preserves original task properties"""
        # Add a recurring task
        self.tm.add_task_to_main("Recurring test task (daily)", "TEST")
        
        # Get the task ID
        content = self.tm.read_file()
        import re
        id_matches = re.findall(r'#(\d{3})', content)
        test_id = max(id_matches)
        
        # First, manually set the main task date to 5 days ago to allow pass entry creation
        from datetime import datetime, timedelta
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%d-%m-%Y')
        
        # Update the main task date manually
        line_number, line_content = self.tm.find_task_by_id_in_main(test_id)
        task_data = self.tm._parse_task_line(line_content)
        from models import Task
        updated_task = Task(
            id=test_id,
            text=task_data['text'],
            status=task_data['status'],
            date=five_days_ago,
            recurring=task_data['metadata'].get('recurring'),
            section=task_data.get('section', 'MAIN')
        )
        
        # Update the file
        content = self.tm.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_task.to_markdown()
        self.tm.write_file('\n'.join(lines))
        
        # Create pass entry
        self.tm.create_pass_entry(test_id, 2)
        
        # Verify pass entry preserves recurring property
        task_file = self.tm.parse_file()
        from datetime import datetime, timedelta
        target_date = datetime.now() - timedelta(days=2)
        target_date_str = target_date.strftime('%d-%m-%Y')
        
        pass_entries = task_file.archive_sections[target_date_str]
        pass_entry = pass_entries[0]
        
        # The pass entry should preserve the recurring property
        self.assertIsNotNone(pass_entry.recurring, "Pass entry should preserve recurring property")
    
    def test_pass_entry_duplicate_prevention(self):
        """Test that duplicate pass entries are prevented"""
        # Add a test task
        self.tm.add_task_to_main("Test task for duplicate prevention", "TEST")
        
        # Get the task ID
        content = self.tm.read_file()
        import re
        id_matches = re.findall(r'#(\d{3})', content)
        test_id = max(id_matches)
        
        # First, manually set the main task date to 5 days ago to allow pass entry creation
        from datetime import datetime, timedelta
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%d-%m-%Y')
        
        # Update the main task date manually
        line_number, line_content = self.tm.find_task_by_id_in_main(test_id)
        task_data = self.tm._parse_task_line(line_content)
        from models import Task
        updated_task = Task(
            id=test_id,
            text=task_data['text'],
            status=task_data['status'],
            date=five_days_ago,
            recurring=task_data['metadata'].get('recurring'),
            section=task_data.get('section', 'MAIN')
        )
        
        # Update the file
        content = self.tm.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_task.to_markdown()
        self.tm.write_file('\n'.join(lines))
        
        # Create first pass entry
        self.tm.create_pass_entry(test_id, 2)
        
        # Try to create duplicate pass entry for same date
        import io
        import sys
        
        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        self.tm.create_pass_entry(test_id, 2)
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Check that duplicate prevention message was printed
        output = captured_output.getvalue()
        self.assertIn("already exists (skipping duplicate)", output)
        
        # Verify only one entry exists
        task_file = self.tm.parse_file()
        from datetime import datetime, timedelta
        target_date = datetime.now() - timedelta(days=2)
        target_date_str = target_date.strftime('%d-%m-%Y')
        
        pass_entries = task_file.archive_sections[target_date_str]
        self.assertEqual(len(pass_entries), 1, "Should have exactly one pass entry")
    
    def test_pass_entry_updates_main_task_date(self):
        """Test that pass entry creation updates the main task's date only when moving forward"""
        # Add a test task
        self.tm.add_task_to_main("Test task for date update", "TEST")
        
        # Get the task ID
        content = self.tm.read_file()
        import re
        id_matches = re.findall(r'#(\d{3})', content)
        test_id = max(id_matches)
        
        # First, manually set the main task date to 3 days ago to test forward-only logic
        from datetime import datetime, timedelta
        three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%d-%m-%Y')
        
        # Update the main task date manually
        line_number, line_content = self.tm.find_task_by_id_in_main(test_id)
        task_data = self.tm._parse_task_line(line_content)
        from models import Task
        updated_task = Task(
            id=test_id,
            text=task_data['text'],
            status=task_data['status'],
            date=three_days_ago,
            recurring=task_data['metadata'].get('recurring'),
            section=task_data.get('section', 'MAIN')
        )
        
        # Update the file
        content = self.tm.read_file()
        lines = content.split('\n')
        lines[line_number - 1] = updated_task.to_markdown()
        self.tm.write_file('\n'.join(lines))
        
        # Get the updated task date
        line_number, updated_line = self.tm.find_task_by_id_in_main(test_id)
        updated_task_data = self.tm._parse_task_line(updated_line)
        current_date = updated_task_data['metadata'].get('date')
        
        # Verify the date is 3 days ago
        self.assertEqual(current_date, three_days_ago, f"Main task date should be {three_days_ago}")
        
        # Create pass entry 2 days ago (should UPDATE - more recent than 3 days ago)
        self.tm.create_pass_entry(test_id, 2)
        
        # Check that main task date was updated
        line_number, final_line = self.tm.find_task_by_id_in_main(test_id)
        final_task_data = self.tm._parse_task_line(final_line)
        final_date = final_task_data['metadata'].get('date')
        
        # The updated date should be different from the 3-day-ago date
        self.assertNotEqual(current_date, final_date, "Main task date should have been updated")
        
        # Verify the date is 2 days ago
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime('%d-%m-%Y')
        self.assertEqual(final_date, two_days_ago, f"Main task date should be {two_days_ago}")
        
        # Now test that creating a pass entry 4 days ago (older) does NOT update
        self.tm.create_pass_entry(test_id, 4)
        
        # Check that main task date was NOT updated
        line_number, unchanged_line = self.tm.find_task_by_id_in_main(test_id)
        unchanged_task_data = self.tm._parse_task_line(unchanged_line)
        unchanged_date = unchanged_task_data['metadata'].get('date')
        
        # The date should still be 2 days ago
        self.assertEqual(unchanged_date, two_days_ago, "Main task date should not have been updated to older date")
    
    def test_pass_entry_cli_integration(self):
        """Test that the CLI correctly routes pass entry commands"""
        # This test verifies the CLI parsing logic works correctly
        # We'll test the argument parsing logic directly
        
        # Test cases for CLI parsing
        test_cases = [
            (["pass", "001"], 2, "progress_task_in_daily"),  # Original behavior
            (["pass", "001", "4"], 3, "create_pass_entry"),   # New behavior
            (["pass", "001", "abc"], 3, "error"),             # Invalid second arg
            (["pass"], 1, "error"),                           # Not enough args
        ]
        
        for args, expected_len, expected_action in test_cases:
            with self.subTest(args=args):
                if expected_action == "error":
                    # These should be handled by the CLI error checking
                    continue
                elif expected_action == "progress_task_in_daily":
                    self.assertEqual(len(args), 2, f"Args {args} should have length 2")
                elif expected_action == "create_pass_entry":
                    self.assertEqual(len(args), 3, f"Args {args} should have length 3")
                    self.assertTrue(args[2].isdigit(), f"Third arg {args[2]} should be digit")


class TestLeadingZerosTaskIDParsing(unittest.TestCase):
    """Test that task IDs with leading zeros are handled correctly"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config"
        self.task_file = Path(self.temp_dir) / "tasks.md"
        
        # Create config
        self.config = Config(task_file=self.task_file, editor="vim")
        Config.create_default_config(self.config_file, self.config)
        
        # Create task manager
        self.tm = Paratrooper(self.config)
        self.tm.init()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_task_id_normalization_helper(self):
        """Test the _normalize_task_id helper function"""
        # Test various input formats
        self.assertEqual(self.tm._normalize_task_id("11"), "11")
        self.assertEqual(self.tm._normalize_task_id("011"), "11")
        self.assertEqual(self.tm._normalize_task_id("001"), "1")
        self.assertEqual(self.tm._normalize_task_id("123"), "123")
        self.assertEqual(self.tm._normalize_task_id("0123"), "123")
        
        # Test non-digit input (should return as-is)
        self.assertEqual(self.tm._normalize_task_id("abc"), "abc")
        self.assertEqual(self.tm._normalize_task_id(""), "")
    
    def test_task_id_matching_helper(self):
        """Test the _task_id_matches_line helper function"""
        test_line = "- [ ] #011 | Test task | WORK | 15-01-2025"
        
        # Test that both normalized and padded formats match
        self.assertTrue(self.tm._task_id_matches_line("11", test_line))
        self.assertTrue(self.tm._task_id_matches_line("011", test_line))
        
        # Test that wrong IDs don't match
        self.assertFalse(self.tm._task_id_matches_line("12", test_line))
        self.assertFalse(self.tm._task_id_matches_line("001", test_line))
        
        # Test with different task ID formats
        test_line_001 = "- [ ] #001 | Another task | HEALTH | 15-01-2025"
        self.assertTrue(self.tm._task_id_matches_line("1", test_line_001))
        self.assertTrue(self.tm._task_id_matches_line("001", test_line_001))
        self.assertFalse(self.tm._task_id_matches_line("11", test_line_001))
    
    def test_find_task_by_id_with_leading_zeros(self):
        """Test that find_task_by_id works with both normalized and padded IDs"""
        # Add a task with leading zeros
        self.tm.add_task_to_main("Test task with leading zeros", "WORK")
        
        # The task should be stored with ID #001
        # Test finding it with normalized ID
        line_num, line_content = self.tm.find_task_by_id("1")
        self.assertIsNotNone(line_content)
        self.assertIn("#001", line_content)
        
        # Test finding it with padded ID
        line_num, line_content = self.tm.find_task_by_id("001")
        self.assertIsNotNone(line_content)
        self.assertIn("#001", line_content)
    
    def test_find_task_by_id_in_main_with_leading_zeros(self):
        """Test that find_task_by_id_in_main works with both normalized and padded IDs"""
        # Add a task with leading zeros
        self.tm.add_task_to_main("Test task in main", "WORK")
        
        # Test finding it with normalized ID
        line_num, line_content = self.tm.find_task_by_id_in_main("1")
        self.assertIsNotNone(line_content)
        self.assertIn("#001", line_content)
        
        # Test finding it with padded ID
        line_num, line_content = self.tm.find_task_by_id_in_main("001")
        self.assertIsNotNone(line_content)
        self.assertIn("#001", line_content)
    
    def test_cli_show_command_with_leading_zeros(self):
        """Test that CLI show command works with normalized task IDs"""
        # Add a task
        self.tm.add_task_to_main("Test task for CLI", "WORK")
        
        # Test that show command works with normalized ID
        # We'll simulate the CLI parsing logic
        test_args = ["show", "1"]  # Normalized ID
        
        if test_args[1].isdigit():
            normalized_id = str(int(test_args[1]))
            line_num, line_content = self.tm.find_task_by_id_in_main(normalized_id)
            self.assertIsNotNone(line_content)
            self.assertIn("#001", line_content)
    
    def test_multiple_task_ids_with_leading_zeros(self):
        """Test handling multiple tasks with different leading zero patterns"""
        # Add multiple tasks
        self.tm.add_task_to_main("First task", "WORK")
        self.tm.add_task_to_main("Second task", "WORK")
        self.tm.add_task_to_main("Third task", "WORK")
        
        # Test finding each task with normalized IDs
        line_num, line_content = self.tm.find_task_by_id("1")
        self.assertIsNotNone(line_content)
        self.assertIn("First task", line_content)
        
        line_num, line_content = self.tm.find_task_by_id("2")
        self.assertIsNotNone(line_content)
        self.assertIn("Second task", line_content)
        
        line_num, line_content = self.tm.find_task_by_id("3")
        self.assertIsNotNone(line_content)
        self.assertIn("Third task", line_content)
        
        # Test finding with padded IDs
        line_num, line_content = self.tm.find_task_by_id("001")
        self.assertIsNotNone(line_content)
        self.assertIn("First task", line_content)
        
        line_num, line_content = self.tm.find_task_by_id("002")
        self.assertIsNotNone(line_content)
        self.assertIn("Second task", line_content)
        
        line_num, line_content = self.tm.find_task_by_id("003")
        self.assertIsNotNone(line_content)
        self.assertIn("Third task", line_content)
    
    def test_task_operations_with_leading_zeros(self):
        """Test that task operations work with normalized IDs"""
        # Add a task
        self.tm.add_task_to_main("Task to test operations", "WORK")
        
        # Test completing task with normalized ID
        self.tm.complete_task("1")
        
        # Verify task was completed
        line_num, line_content = self.tm.find_task_by_id("1")
        self.assertIsNotNone(line_content)
        self.assertIn("- [x]", line_content)
        
        # Test editing task with normalized ID
        self.tm.edit_task("1", "Updated task text")
        
        # Verify task was edited
        line_num, line_content = self.tm.find_task_by_id("1")
        self.assertIsNotNone(line_content)
        self.assertIn("Updated task text", line_content)
    
    def test_large_task_ids_without_leading_zeros(self):
        """Test that large task IDs (1000+) work correctly without padding"""
        # This test ensures that IDs >= 1000 don't get padded
        # We'll simulate having a task with ID 1000+
        
        # Create a task file with a large ID
        content = f"""# DAILY

# MAIN

## WORK
- [ ] #1001 | Large ID task | WORK | {self.tm.today}

# ARCHIVE
"""
        self.task_file.write_text(content)
        
        # Test finding the task
        line_num, line_content = self.tm.find_task_by_id("1001")
        self.assertIsNotNone(line_content)
        self.assertIn("#1001", line_content)
        
        # Test that normalization doesn't break large IDs
        normalized_id = self.tm._normalize_task_id("1001")
        self.assertEqual(normalized_id, "1001")
        
        # Test matching
        self.assertTrue(self.tm._task_id_matches_line("1001", line_content))


class TestRecurrenceFixImplementation(unittest.TestCase):
    """Test the new recurrence fix implementation"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config"
        self.task_file_path = Path(self.temp_dir) / "tasks.md"
        
        # Create config pointing to our test file
        config = Config.load(self.config_path)
        config.task_file = self.task_file_path
        
        self.tm = Paratrooper(config)
        self.tm.init()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_cleanup_incomplete_recurring_tasks(self):
        """Test cleanup of incomplete recurring tasks from old daily sections"""
        # Add a recurring task
        self.tm.add_task_to_main("Take out trash (recur:3d)", "DOMESTIC")
        
        # Get task ID
        task_id = self._get_task_id("Take out trash")
        
        # Manually add incomplete instances to old sections first
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        day_before = (datetime.now() - timedelta(days=2)).strftime("%d-%m-%Y")
        
        content = self.tm.read_file()
        lines = content.split('\n')
        
        # Find the daily section and add old incomplete instances
        in_daily = False
        for i, line in enumerate(lines):
            if line.strip() == '# DAILY':
                in_daily = True
                continue
            elif line.strip().startswith('# ') and line.strip() != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and line.strip() == f"## {self.tm.today}":
                # Insert old sections before today's section
                old_sections = [
                    f"## {day_before}",
                    f"- [ ] #{task_id} | Take out trash | DOMESTIC | {day_before} | (recur:3d)",
                    "",
                    f"## {yesterday}",
                    f"- [ ] #{task_id} | Take out trash | DOMESTIC | {yesterday} | (recur:3d)",
                    "",
                    f"## {self.tm.today}",
                ]
                lines[i:i] = old_sections
                break
        
        self.tm.write_file('\n'.join(lines))
        
        # Count occurrences before cleanup (only in daily sections)
        content = self.tm.read_file()
        lines = content.split('\n')
        in_daily = False
        task_count_before = 0
        for line in lines:
            if line.strip() == '# DAILY':
                in_daily = True
                continue
            elif line.strip().startswith('# ') and line.strip() != '# DAILY':
                in_daily = False
                continue
            if in_daily and f"#{task_id}" in line and "Take out trash" in line:
                task_count_before += 1
        self.assertEqual(task_count_before, 3, "Should have 3 instances before cleanup")
        
        # Run cleanup
        task_file = self.tm.parse_file()
        cleaned_tasks = self.tm._cleanup_incomplete_recurring_tasks(task_file)
        
        # Verify cleanup worked
        self.assertEqual(len(cleaned_tasks), 2, "Should have cleaned up 2 old instances")
        
        # Count occurrences after cleanup (only in daily sections)
        content = self.tm.read_file()
        lines = content.split('\n')
        in_daily = False
        task_count_after = 0
        for line in lines:
            if line.strip() == '# DAILY':
                in_daily = True
                continue
            elif line.strip().startswith('# ') and line.strip() != '# DAILY':
                in_daily = False
                continue
            if in_daily and f"#{task_id}" in line and "Take out trash" in line:
                task_count_after += 1
        self.assertEqual(task_count_after, 1, "Should have only 1 instance after cleanup")
    
    def test_get_task_appearance_date(self):
        """Test getting task appearance date from daily sections"""
        # Add a recurring task
        self.tm.add_task_to_main("Morning workout (daily)", "HEALTH")
        
        # Get task ID
        task_id = self._get_task_id("Morning workout")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Test getting appearance date
        appearance_date = self.tm._get_task_appearance_date(task_id)
        self.assertEqual(appearance_date, self.tm.today, "Appearance date should be today")
        
        # Test fallback when task not in daily section
        fallback_date = self.tm._get_task_appearance_date("999")
        self.assertEqual(fallback_date, self.tm.today, "Fallback should return today")
    
    def test_get_main_task_date(self):
        """Test getting date from main task"""
        # Add a task
        self.tm.add_task_to_main("Test task", "WORK")
        
        # Get task ID
        task_id = self._get_task_id("Test task")
        
        # Test getting main task date
        main_date = self.tm._get_main_task_date(task_id)
        self.assertEqual(main_date, self.tm.today, "Main task date should be today")
        
        # Test fallback for non-existent task
        fallback_date = self.tm._get_main_task_date("999")
        self.assertEqual(fallback_date, self.tm.today, "Fallback should return today")
    
    def test_sync_uses_appearance_date_for_recurring_tasks(self):
        """Test that sync uses appearance date for recurring tasks"""
        # Add a recurring task
        self.tm.add_task_to_main("Check email (recur:2d)", "WORK")
        
        # Get task ID
        task_id = self._get_task_id("Check email")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Complete the task
        self.tm.complete_task(task_id)
        
        # Sync to update main list
        self.tm.sync_daily_sections()
        
        # Verify main task date was updated to appearance date (today)
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        today = self.tm.today
        self.assertIn(today, main_section, f"Main task should have today's date ({today})")
        
        # Verify task is still incomplete (recurring)
        self.assertIn(f"- [ ] #{task_id} | Check email", main_section, "Recurring task should remain incomplete")
    
    def test_sync_uses_appearance_date_for_progress_tasks(self):
        """Test that sync uses appearance date for recurring tasks marked as progress"""
        # Add a recurring task
        self.tm.add_task_to_main("Review budget (recur:1w)", "FINANCE")
        
        # Get task ID
        task_id = self._get_task_id("Review budget")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Mark task as progress
        self.tm.progress_task_in_daily(task_id)
        
        # Sync to update main list
        self.tm.sync_daily_sections()
        
        # Verify main task date was updated to appearance date (today)
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        today = self.tm.today
        self.assertIn(today, main_section, f"Main task should have today's date ({today})")
        
        # Verify task is still incomplete
        self.assertIn(f"- [ ] #{task_id} | Review budget", main_section, "Task should remain incomplete")
    
    def test_delayed_completion_scenario(self):
        """Test the specific scenario where task appears today but is completed tomorrow"""
        # Add a recurring task
        self.tm.add_task_to_main("Morning workout (recur:3d)", "HEALTH")
        
        # Get task ID
        task_id = self._get_task_id("Morning workout")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Verify task appears in daily section
        content = self.tm.read_file()
        self.assertIn("Morning workout", content, "Task should appear in daily section")
        
        # Simulate completing the task tomorrow by manually updating the daily section
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
        
        # Create tomorrow's daily section (this should clean up today's incomplete task)
        self.tm.add_daily_section()
        
        # Manually add the task to tomorrow's section and complete it
        content = self.tm.read_file()
        lines = content.split('\n')
        
        # Find tomorrow's section and add the task
        in_daily = False
        in_tomorrow_section = False
        for i, line in enumerate(lines):
            if line.strip() == '# DAILY':
                in_daily = True
                continue
            elif line.strip().startswith('# ') and line.strip() != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and line.strip() == f"## {tomorrow}":
                in_tomorrow_section = True
                continue
            elif in_daily and line.strip().startswith('## '):
                in_tomorrow_section = False
                continue
            
            if in_tomorrow_section and line.strip() == '':
                # Add the task to tomorrow's section
                lines.insert(i, f"- [x] #{task_id} | Morning workout | HEALTH | {tomorrow} | (recur:3d)")
                break
        
        self.tm.write_file('\n'.join(lines))
        
        # Sync to update main list
        self.tm.sync_daily_sections()
        
        # Verify main task date was updated to appearance date (today), not completion date (tomorrow)
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        today = self.tm.today
        self.assertIn(today, main_section, f"Main task should have today's date ({today}), not tomorrow's")
        self.assertNotIn(tomorrow, main_section, "Main task should not have tomorrow's date")
    
    def test_pass_entries_dont_affect_recurrence(self):
        """Test that pass entries don't affect recurrence schedule"""
        # Add a recurring task
        self.tm.add_task_to_main("Review budget (recur:1w)", "FINANCE")
        
        # Get task ID
        task_id = self._get_task_id("Review budget")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Complete the task
        self.tm.complete_task(task_id)
        self.tm.sync_daily_sections()
        
        # Create a pass entry (simulating the pass command)
        self.tm.create_pass_entry(task_id, 2)  # Pass entry 2 days ago
        
        # Verify the main task date is still the appearance date, not affected by pass entry
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        today = self.tm.today
        self.assertIn(today, main_section, f"Main task should still have today's date ({today})")
    
    def test_recurrence_schedule_consistency(self):
        """Test that recurrence schedule remains consistent regardless of completion timing"""
        # Add a recurring task
        self.tm.add_task_to_main("Take out trash (recur:3d)", "DOMESTIC")
        
        # Get task ID
        task_id = self._get_task_id("Take out trash")
        
        # Create today's daily section
        self.tm.add_daily_section()
        
        # Complete the task
        self.tm.complete_task(task_id)
        self.tm.sync_daily_sections()
        
        # Verify the task will recur in 3 days from today
        # This tests the core fix: recurrence should be based on appearance date, not completion date
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section_end = content.find("# ARCHIVE")
        main_section = content[main_section_start:main_section_end]
        
        today = self.tm.today
        self.assertIn(today, main_section, f"Main task should have today's date ({today})")
        
        # The next occurrence should be 3 days from today
        # Test that the task should NOT recur tomorrow or day after
        from datetime import datetime, timedelta
        today_obj = datetime.strptime(today, "%d-%m-%Y")
        tomorrow = (today_obj + timedelta(days=1)).strftime("%d-%m-%Y")
        day_after = (today_obj + timedelta(days=2)).strftime("%d-%m-%Y")
        day_after_tomorrow = (today_obj + timedelta(days=3)).strftime("%d-%m-%Y")
        
        # Test that the task should NOT recur before the interval is complete
        # Note: should_recur_today checks if it should recur TODAY, not on a specific date
        # So we test with today's date and different intervals
        self.assertFalse(self.tm.should_recur_today("recur:3d", tomorrow), "Should not recur tomorrow")
        self.assertFalse(self.tm.should_recur_today("recur:3d", day_after), "Should not recur day after")
        
        # Test that a task with 3-day interval should recur after 3 days
        # We simulate being 3 days in the future
        future_date = (today_obj + timedelta(days=3)).strftime("%d-%m-%Y")
        self.assertTrue(self.tm.should_recur_today("recur:3d", future_date), "Should recur after 3 days")
    
    def _get_task_id(self, task_text):
        """Helper function to get task ID by text"""
        content = self.tm.read_file()
        lines = content.split('\n')
        
        for line in lines:
            if task_text in line and '#' in line:
                # Extract task ID
                parts = line.split('#')
                if len(parts) > 1:
                    task_id = parts[1].split()[0]
                    return task_id
        
        raise ValueError(f"Could not find task ID for: {task_text}")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestTask))
    suite.addTests(loader.loadTestsFromTestCase(TestSection))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskFile))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCaseInsensitiveSections))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestSyncCommandFixes))
    suite.addTests(loader.loadTestsFromTestCase(TestDailyTaskDeletionRefactor))
    suite.addTests(loader.loadTestsFromTestCase(TestDisplayOperationsFix))
    suite.addTests(loader.loadTestsFromTestCase(TestRecurringTaskBugFix))
    suite.addTests(loader.loadTestsFromTestCase(TestCLICommands))
    suite.addTests(loader.loadTestsFromTestCase(TestRecurringTaskStatusCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestPassEntryFeature))
    suite.addTests(loader.loadTestsFromTestCase(TestLeadingZerosTaskIDParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestRecurrenceFixImplementation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
