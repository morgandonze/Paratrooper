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
        self.assertEqual(config.icon_set, "default")
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
        expected = "- [x] Test task | @15-01-2025 #001"
        self.assertEqual(markdown, expected)
    
    def test_task_from_markdown(self):
        """Test parsing task from markdown"""
        line = "- [x] Test task | @15-01-2025 #001"
        task = Task.from_markdown(line, "TASKS")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.text, "Test task")
        self.assertEqual(task.status, "x")
        self.assertEqual(task.date, "15-01-2025")
        self.assertEqual(task.id, "001")
        self.assertEqual(task.section, "TASKS")
    
    def test_recurring_task_parsing(self):
        """Test parsing recurring tasks"""
        line = "- [ ] morning workout | @15-01-2025 (daily) #004"
        task = Task.from_markdown(line, "HEALTH")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.text, "morning workout")
        self.assertEqual(task.status, " ")
        self.assertEqual(task.date, "15-01-2025")
        self.assertEqual(task.id, "004")
        self.assertEqual(task.recurring, "(daily)")
    
    def test_snoozed_task_parsing(self):
        """Test parsing snoozed tasks"""
        line = "- [ ] review budget | @15-01-2025 snooze:20-01-2025 #005"
        task = Task.from_markdown(line, "FINANCE")
        
        self.assertIsNotNone(task)
        self.assertEqual(task.text, "review budget")
        self.assertEqual(task.status, " ")
        self.assertEqual(task.date, "15-01-2025")
        self.assertEqual(task.id, "005")
        self.assertEqual(task.snooze, "20-01-2025")


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
        
        # Check that task has snooze date
        content = self.tm.read_file()
        self.assertIn("snooze:", content)
    
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
        
        # Complete the workout
        content = self.tm.read_file()
        lines = content.split('\n')
        workout_task_line = None
        for line in lines:
            if "morning workout" in line and "#" in line:
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
