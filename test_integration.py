#!/usr/bin/env python3
"""
Integration tests for PARA + Daily Task Management System
Tests full command workflows and cross-command interactions
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Import the TaskManager class
from tasks import TaskManager

class TestIntegration(unittest.TestCase):
    """Integration tests for full command workflows"""
    
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
    
    def test_complete_daily_workflow(self):
        """Test complete daily workflow: daily -> up -> work -> sync"""
        # Step 1: Add some tasks to main list
        self.tm.add_task_to_main("Write blog post", "PROJECTS")
        self.tm.add_task_to_main("Call client", "INBOX")
        self.tm.add_task_to_main("Exercise", "AREAS")
        
        # Step 2: Create daily section
        self.tm.add_daily_section()
        content = self.tm.read_file()
        self.assertIn("## 04-09-2025", content)
        
        # Step 3: Pull tasks to daily section
        self.tm.add_task_to_daily_by_id("001")  # up command
        self.tm.add_task_to_daily_by_id("002")  # up command
        
        content = self.tm.read_file()
        self.assertIn("Write blog post (from: PROJECTS)", content)
        self.assertIn("Call client (from: INBOX)", content)
        
        # Step 4: Simulate work (mark progress and completion)
        # Manually edit daily section to simulate work
        content = self.tm.read_file()
        lines = content.split('\n')
        
        # Find and update the daily tasks
        for i, line in enumerate(lines):
            if "Write blog post" in line and "from: PROJECTS" in line:
                lines[i] = line.replace("- [ ]", "- [~]")  # Progress
            elif "Call client" in line and "from: INBOX" in line:
                lines[i] = line.replace("- [ ]", "- [x]")  # Complete
        
        self.tm.write_file('\n'.join(lines))
        
        # Verify the daily section state before sync
        content = self.tm.read_file()
        self.assertIn("- [~] Write blog post (from: PROJECTS)", content)
        self.assertIn("- [x] Call client (from: INBOX)", content)
        
        # Step 5: Sync progress back to main list
        self.tm.sync_daily_sections()
        
        # Verify sync results
        content = self.tm.read_file()
        # Write blog post should still be incomplete but date updated
        self.assertIn("- [ ] Write blog post", content)
        # Call client should be marked complete
        self.assertIn("- [x] Call client", content)
    
    def test_recurring_task_lifecycle(self):
        """Test recurring task lifecycle: add -> mark recurring -> appear in daily -> complete -> sync"""
        # Step 1: Add recurring task
        self.tm.add_task_to_main("Morning exercise", "AREAS")
        
        # Step 2: Manually make it recurring
        content = self.tm.read_file()
        content = content.replace("Morning exercise @04-09-2025 #001", 
                                "Morning exercise @04-09-2025 (daily) #001")
        self.tm.write_file(content)
        
        # Step 3: Create daily section (should include recurring task)
        self.tm.add_daily_section()
        content = self.tm.read_file()
        self.assertIn("Morning exercise (from: AREAS)", content)
        
        # Step 4: Complete the recurring task in daily section
        content = self.tm.read_file()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "Morning exercise" in line and "from: AREAS" in line:
                lines[i] = line.replace("- [ ]", "- [x]")
        self.tm.write_file('\n'.join(lines))
        
        # Step 5: Sync (recurring task should stay incomplete but date updated)
        self.tm.sync_daily_sections()
        content = self.tm.read_file()
        self.assertIn("- [ ] Morning exercise", content)  # Should stay incomplete
        # Date should be updated to today
    
    def test_up_down_commands(self):
        """Test up/down command workflow"""
        # Add task to main list
        self.tm.add_task_to_main("Test up/down task", "PROJECTS")
        
        # Up command (pull to daily)
        self.tm.add_task_to_daily_by_id("001")
        content = self.tm.read_file()
        self.assertIn("Test up/down task (from: PROJECTS)", content)
        
        # Down command (remove from daily)
        self.tm.delete_task_from_daily("001")
        content = self.tm.read_file()
        self.assertNotIn("Test up/down task (from: PROJECTS)", content)
        
        # Task should still exist in main list
        self.assertIn("Test up/down task", content)
    
    def test_progress_tracking_workflow(self):
        """Test progress tracking: up -> pass -> sync"""
        # Add task to main list
        self.tm.add_task_to_main("Long project task", "PROJECTS")
        
        # Pull to daily
        self.tm.add_task_to_daily_by_id("001")
        
        # Mark progress in daily section
        self.tm.progress_task_in_daily("001")
        content = self.tm.read_file()
        self.assertIn("- [~] Long project task", content)
        
        # Sync progress back to main
        self.tm.sync_daily_sections()
        content = self.tm.read_file()
        
        # Task should still be incomplete but date updated
        self.assertIn("- [ ] Long project task", content)
        # Date should be updated to today
    
    def test_snooze_workflow(self):
        """Test snooze workflow: add -> snooze -> check stale -> unsnooze"""
        # Add task
        self.tm.add_task_to_main("Future task", "PROJECTS")
        
        # Snooze for 5 days
        self.tm.snooze_task("001", "5")
        content = self.tm.read_file()
        self.assertIn("snooze:", content)
        
        # Check that it doesn't appear in stale tasks
        with patch('builtins.print') as mock_print:
            self.tm.show_stale_tasks()
            output = str(mock_print.call_args_list)
            self.assertNotIn("Future task", output)
        
        # Remove snooze (by snoozing until yesterday)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
        self.tm.snooze_task("001", yesterday)
        
        # Now it should appear in stale tasks
        with patch('builtins.print') as mock_print:
            self.tm.show_stale_tasks()
            output = str(mock_print.call_args_list)
            self.assertIn("Future task", output)
    
    def test_delete_purge_commands(self):
        """Test delete and purge commands"""
        # Add task to main list
        self.tm.add_task_to_main("Delete test task", "INBOX")
        
        # Pull to daily
        self.tm.add_task_to_daily_by_id("001")
        
        # Delete from main only
        self.tm.delete_task_from_main("001")
        content = self.tm.read_file()
        
        # Check that task is removed from main list
        main_section = self.tm.find_section("MAIN", level=1)
        main_content = '\n'.join(main_section) if main_section else ""
        self.assertNotIn("Delete test task", main_content)
        
        # But it should still be in daily section
        self.assertIn("Delete test task", content)
        
        # Add another task for purge test
        self.tm.add_task_to_main("Purge test task", "INBOX")
        self.tm.add_task_to_daily_by_id("002")
        
        # Purge from everywhere
        self.tm.purge_task("002")
        content = self.tm.read_file()
        self.assertNotIn("Purge test task", content)
    
    def test_section_management(self):
        """Test section management and organization"""
        # Add tasks to different sections
        self.tm.add_task_to_main("Inbox task", "INBOX")
        self.tm.add_task_to_main("Project task", "PROJECTS")
        self.tm.add_task_to_main("Area task", "AREAS")
        self.tm.add_task_to_main("Resource task", "RESOURCES")
        self.tm.add_task_to_main("Zettel task", "ZETTELKASTEN")
        
        # Add to subsections
        self.tm.add_task_to_main("Home project", "PROJECTS:HOME")
        self.tm.add_task_to_main("Health area", "AREAS:HEALTH")
        
        content = self.tm.read_file()
        
        # Check all sections exist
        self.assertIn("## INBOX", content)
        self.assertIn("## PROJECTS", content)
        self.assertIn("## AREAS", content)
        self.assertIn("## RESOURCES", content)
        self.assertIn("## ZETTELKASTEN", content)
        
        # Check subsections exist
        self.assertIn("### HOME", content)
        self.assertIn("### HEALTH", content)
        
        # Check tasks are in correct sections
        self.assertIn("Inbox task", content)
        self.assertIn("Project task", content)
        self.assertIn("Area task", content)
        self.assertIn("Resource task", content)
        self.assertIn("Zettel task", content)
        self.assertIn("Home project", content)
        self.assertIn("Health area", content)
    
    def test_file_formatting_consistency(self):
        """Test that file formatting remains consistent across operations"""
        # Perform multiple operations
        self.tm.add_task_to_main("Task 1", "INBOX")
        self.tm.add_task_to_main("Task 2", "PROJECTS")
        self.tm.add_task_to_main("Task 3", "AREAS")
        self.tm.add_daily_section()
        self.tm.add_task_to_daily_by_id("001")
        self.tm.add_task_to_daily_by_id("002")
        
        content = self.tm.read_file()
        lines = content.split('\n')
        
        # Check for proper spacing
        # Should have empty lines between sections and tasks
        empty_line_count = lines.count('')
        
        # Should have reasonable number of empty lines (not too many, not too few)
        self.assertGreater(empty_line_count, 5)
        self.assertLess(empty_line_count, 50)
        
        # Check no consecutive empty lines
        consecutive_empty = 0
        for i in range(len(lines) - 1):
            if lines[i] == '' and lines[i + 1] == '':
                consecutive_empty += 1
        
        self.assertEqual(consecutive_empty, 0)
    
    def test_id_consistency(self):
        """Test that IDs remain consistent across operations"""
        # Add multiple tasks
        self.tm.add_task_to_main("Task 1", "INBOX")
        self.tm.add_task_to_main("Task 2", "PROJECTS")
        self.tm.add_task_to_main("Task 3", "AREAS")
        
        # Pull tasks to daily
        self.tm.add_task_to_daily_by_id("001")
        self.tm.add_task_to_daily_by_id("002")
        
        content = self.tm.read_file()
        
        # Check that IDs match between main and daily sections
        self.assertIn("#001", content)
        self.assertIn("#002", content)
        
        # Count occurrences of each ID
        id_001_count = content.count("#001")
        id_002_count = content.count("#002")
        
        # Each ID should appear exactly twice (once in main, once in daily)
        self.assertEqual(id_001_count, 2)
        self.assertEqual(id_002_count, 2)

if __name__ == '__main__':
    unittest.main()
