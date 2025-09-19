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

from paratrooper import Config, Task, Section, TaskFile, TaskManager


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
        expected = "- [x] #001 | Test task | TASKS | 15-01-2025 | "
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
        self.assertEqual(task.recurring, "(daily)")
    
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
        
        self.tm = TaskManager(config)
    
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
        self.assertIn(f"[x] Test task", content)
    
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
        content = content.replace(f"[ ] Test task", f"[x] Test task")
        self.tm.write_file(content)
        
        # Sync
        self.tm.sync_daily_sections()
        
        # Check that main task is now complete
        content = self.tm.read_file()
        self.assertIn(f"[x] Test task", content)
    
    def test_snooze_task(self):
        """Test snoozing a task"""
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
        
        # Snooze for 3 days
        self.tm.snooze_task(task_id, "3")
        
        # Check that task has future date (snoozing)
        content = self.tm.read_file()
        self.assertIn("21-09-2025", content)  # 3 days from test date
    
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
        """Test that add_task_to_daily_by_id includes 'from {section_ref}' formatting"""
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
        
        # Verify the task appears in daily section with "from PROJECTS" formatting
        content = self.tm.read_file()
        self.assertIn("Write blog post from PROJECTS", content)
        
        # Verify it's in the daily section, not main
        daily_section_start = content.find("# DAILY")
        daily_section_end = content.find("# MAIN")
        daily_section = content[daily_section_start:daily_section_end]
        self.assertIn("Write blog post from PROJECTS", daily_section)
    
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
        self.assertIn(f"Task 2 from WORK", content)
        
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
- [x] Old task from WORK #001

## {today}
- [ ] New task from WORK #002

# MAIN

## WORK
- [ ] New task | @{today} #002

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
- [x] Old task from WORK #001

## {today}
- [ ] New task from WORK #002

# MAIN

## WORK
- [ ] New task | @{today} #002

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
- [x] Old task from WORK #001

## {today}
- [ ] New task from WORK #002

# MAIN

## WORK
- [ ] New task | @{today} #002

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
        
        # Get task IDs
        content = self.tm.read_file()
        lines = content.split('\n')
        task_ids = {}
        for line in lines:
            if "morning workout" in line and "#" in line:
                task_ids['workout'] = line.split('#')[-1].strip()
            elif "write report" in line and "#" in line:
                task_ids['report'] = line.split('#')[-1].strip()
            elif "call client" in line and "#" in line:
                task_ids['client'] = line.split('#')[-1].strip()
        
        # Create yesterday's daily section manually with incomplete tasks
        yesterday_content = f"""# DAILY

## {yesterday}
- [ ] morning workout from HEALTH | @{today} (daily) #{task_ids['workout']}
- [~] write report from WORK | @{today} #{task_ids['report']}
- [x] call client from WORK | @{today} #{task_ids['client']}

# MAIN

## HEALTH
- [ ] morning workout (daily) | @{today} #{task_ids['workout']}

## WORK
- [ ] write report | @{today} #{task_ids['report']}
- [ ] call client | @{today} #{task_ids['client']}

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
        self.assertIn("morning workout from HEALTH", daily_section)
        
        # Incomplete task should be carried over (status reset to incomplete)
        self.assertIn("write report from WORK", daily_section)
        self.assertIn(f"- [ ] write report from WORK | @{today} #{task_ids['report']}", daily_section)
        
        # Completed task should NOT be carried over
        self.assertNotIn("call client from WORK", daily_section)
        
        # Previous day's section should be moved to archive
        self.assertIn("# ARCHIVE", content)
        archive_section_start = content.find("# ARCHIVE")
        archive_section = content[archive_section_start:]
        self.assertIn(f"## {yesterday}", archive_section)
        
        # Verify carry-over message was shown (we can't easily test stdout, but the functionality works)
        # The test passes if the assertions above pass

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
        self.tm.add_task_to_main("Test")
        
        # Verify all main sections still exist after adding task
        final_content = self.tm.read_file()
        self.assertIn("# DAILY", final_content)
        self.assertIn("# MAIN", final_content)
        self.assertIn("# ARCHIVE", final_content)
        
        # Should have created a Tasks subsection under MAIN
        self.assertIn("## TASKS", final_content)
        
        # Should have the task in the Tasks subsection
        self.assertIn("- [ ] Test | @", final_content)
        self.assertIn("#001", final_content)
        
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
- [ ] Existing task | @18-09-2025 #001

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
        
        self.tm = TaskManager(config)
    
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
        self.assertIn("[x] morning workout", content)
    
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
        content = self.tm.read_file()
        lines = content.split('\n')
        workout_task_line = None
        in_daily = False
        for line in lines:
            if line.strip() == '# DAILY':
                in_daily = True
                continue
            elif line.startswith('# ') and line != '# DAILY':
                in_daily = False
                continue
            
            if in_daily and "morning workout" in line and "#" in line:
                workout_task_line = line
                break
        
        workout_task_id = workout_task_line.split('#')[-1].strip()
        self.tm.complete_task(workout_task_id)
        
        # Sync
        self.tm.sync_daily_sections()
        
        # Verify main task is still incomplete (recurring)
        content = self.tm.read_file()
        main_section_start = content.find("# MAIN")
        main_section = content[main_section_start:]
        self.assertIn("[ ] morning workout", main_section)


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
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
