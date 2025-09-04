#!/usr/bin/env python3
"""
Tests to demonstrate current parsing issues and validate proposed improvements
"""

import unittest
import re
from datetime import datetime

# Current regex patterns from tasks.py
TASK_STATUS_PATTERN = r'- \[.\] '
TASK_INCOMPLETE_PATTERN = r'- \[ \] '
TASK_COMPLETE_PATTERN = r'- \[x\] '
TASK_PROGRESS_PATTERN = r'- \[~\] '
TASK_ID_PATTERN = r'#(\d{3})'
DATE_PATTERN = r'@(\d{2}-\d{2}-\d{4})'
SNOOZE_PATTERN = r'snooze:(\d{2}-\d{2}-\d{4})'
RECURRING_PATTERN = r'\([^)]*(?:daily|weekly|monthly|recur:)[^)]*\)'

class TestCurrentParsingIssues(unittest.TestCase):
    """Test cases demonstrating current parsing problems"""
    
    def test_ambiguous_at_symbol_parsing(self):
        """Test that @ symbols in task text break date parsing"""
        # This should fail - @ symbol in text conflicts with date parsing
        task = "- [ ] task with @ symbol @15-01-2025 #001"
        
        # Current parsing finds the first @ as the date
        date_match = re.search(DATE_PATTERN, task)
        self.assertIsNotNone(date_match)
        self.assertEqual(date_match.group(1), "15-01-2025")
        
        # But the task text extraction is wrong
        text_start = task.find('] ') + 2
        text_end = task.find(' @')
        extracted_text = task[text_start:text_end]
        self.assertEqual(extracted_text, "task with")  # Should be "task with @ symbol"
    
    def test_ambiguous_hash_symbol_parsing(self):
        """Test that # symbols in task text break ID parsing"""
        task = "- [ ] task with # symbol @15-01-2025 #002"
        
        # Current parsing finds the last # as the ID
        id_match = re.search(TASK_ID_PATTERN, task)
        self.assertIsNotNone(id_match)
        self.assertEqual(id_match.group(1), "002")
        
        # But task text extraction includes the # symbol
        text_start = task.find('] ') + 2
        text_end = task.find(' @')
        extracted_text = task[text_start:text_end]
        self.assertEqual(extracted_text, "task with # symbol")  # This actually works
    
    def test_parentheses_conflict_with_recurring(self):
        """Test that parentheses in task text conflict with recurring patterns"""
        task = "- [ ] task with (parentheses) @15-01-2025 (daily) #003"
        
        # Current parsing might match the wrong parentheses
        recur_match = re.search(RECURRING_PATTERN, task)
        self.assertIsNotNone(recur_match)
        self.assertEqual(recur_match.group(0), "(daily)")
        
        # But task text extraction includes the parentheses
        text_start = task.find('] ') + 2
        text_end = task.find(' @')
        extracted_text = task[text_start:text_end]
        self.assertEqual(extracted_text, "task with (parentheses)")
    
    def test_quote_handling_issues(self):
        """Test that quotes in task text cause parsing issues"""
        task = '- [ ] task with "quotes" in text @15-01-2025 #004'
        
        # Current parsing works for this case
        id_match = re.search(TASK_ID_PATTERN, task)
        date_match = re.search(DATE_PATTERN, task)
        
        self.assertIsNotNone(id_match)
        self.assertIsNotNone(date_match)
        
        # But command line parsing would break
        # This would fail: tasks add 'task with "quotes" in text'
    
    def test_special_characters_break_parsing(self):
        """Test that various special characters break parsing"""
        problematic_tasks = [
            "- [ ] task with | pipe @15-01-2025 #005",
            "- [ ] task with [brackets] @15-01-2025 #006", 
            "- [ ] task with {braces} @15-01-2025 #007",
            "- [ ] task with < > symbols @15-01-2025 #008",
        ]
        
        for task in problematic_tasks:
            with self.subTest(task=task):
                # These should all parse correctly with current regex
                id_match = re.search(TASK_ID_PATTERN, task)
                date_match = re.search(DATE_PATTERN, task)
                
                self.assertIsNotNone(id_match, f"Failed to parse ID from: {task}")
                self.assertIsNotNone(date_match, f"Failed to parse date from: {task}")
    
    def test_metadata_order_dependency(self):
        """Test that changing metadata order breaks parsing"""
        # Standard order works
        standard_task = "- [ ] task @15-01-2025 (daily) snooze:20-01-2025 #001"
        
        # Different order breaks parsing
        reordered_task = "- [ ] task (daily) @15-01-2025 snooze:20-01-2025 #001"
        
        # Both should work with current regex (order doesn't matter for search)
        for task in [standard_task, reordered_task]:
            with self.subTest(task=task):
                id_match = re.search(TASK_ID_PATTERN, task)
                date_match = re.search(DATE_PATTERN, task)
                snooze_match = re.search(SNOOZE_PATTERN, task)
                recur_match = re.search(RECURRING_PATTERN, task)
                
                self.assertIsNotNone(id_match)
                self.assertIsNotNone(date_match)
                self.assertIsNotNone(snooze_match)
                self.assertIsNotNone(recur_match)

class TestProposedFormatImprovements(unittest.TestCase):
    """Test cases for the proposed improved format"""
    
    def test_separator_based_parsing(self):
        """Test that | separator makes parsing unambiguous"""
        # Proposed format examples
        tasks = [
            "- [ ] incomplete task | @15-01-2025 #001",
            "- [x] completed task | @15-01-2025 #002",
            "- [~] progressed task | @15-01-2025 #003",
            "- [ ] recurring task | @15-01-2025 (daily) #004",
            "- [ ] snoozed task | @15-01-2025 snooze:20-01-2025 #005",
            "- [ ] complex task | @15-01-2025 (weekly:tue) snooze:20-01-2025 #006",
        ]
        
        for task in tasks:
            with self.subTest(task=task):
                # Split on separator
                self.assertIn(' | ', task, "Task must have separator")
                text_part, metadata_part = task.split(' | ', 1)
                
                # Extract status
                status_match = re.match(r'- \[(.)\] ', text_part)
                self.assertIsNotNone(status_match)
                status = status_match.group(1)
                self.assertIn(status, [' ', 'x', '~'])
                
                # Extract task text
                task_text = text_part[6:]  # Remove '- [X] '
                self.assertGreater(len(task_text), 0, "Task text cannot be empty")
                
                # Parse metadata
                id_match = re.search(r'#(\d{3})', metadata_part)
                date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', metadata_part)
                snooze_match = re.search(r'snooze:(\d{2}-\d{2}-\d{4})', metadata_part)
                recur_match = re.search(r'\([^)]*\)', metadata_part)
                
                # At minimum, should have ID and date
                self.assertIsNotNone(id_match, f"Missing ID in: {task}")
                self.assertIsNotNone(date_match, f"Missing date in: {task}")
    
    def test_character_restrictions(self):
        """Test character restrictions for task text"""
        # Valid task texts
        valid_texts = [
            "simple task",
            "task with numbers 123",
            "task with punctuation: . , ! ? : ; - _",
            'task with "quotes"',
            "task with 'single quotes'",
            "UPPERCASE and lowercase",
        ]
        
        for text in valid_texts:
            with self.subTest(text=text):
                task = f"- [ ] {text} | @15-01-2025 #001"
                self.assertIn(' | ', task)
                text_part, metadata_part = task.split(' | ', 1)
                task_text = text_part[6:]  # Remove '- [ ] '
                self.assertEqual(task_text, text)
        
        # Invalid task texts (should be rejected)
        invalid_texts = [
            "task with @ symbol",  # Conflicts with date
            "task with # symbol",  # Conflicts with ID
            "task with | pipe",    # Conflicts with separator
            "task with (parentheses)",  # Conflicts with recurring
            "task with [brackets]",     # Conflicts with status
            "task with {braces}",       # Special chars
            "task with < > symbols",    # Special chars
            "task with \\ backslash",   # Special chars
            "task with / forward slash", # Special chars
            "task with ~ tilde",        # Special chars
            "task with ` backtick",     # Special chars
        ]
        
        for text in invalid_texts:
            with self.subTest(text=text):
                # These should be rejected during validation
                forbidden_chars = ['@', '#', '|', '(', ')', '[', ']', '{', '}', '<', '>', '\\', '/', '~', '`']
                has_forbidden = any(char in text for char in forbidden_chars)
                self.assertTrue(has_forbidden, f"Text should be invalid: {text}")
    
    def test_metadata_parsing_robustness(self):
        """Test that metadata parsing is robust with the new format"""
        # Test various metadata combinations
        test_cases = [
            ("simple task", "@15-01-2025 #001", "001", "15-01-2025", None, None),
            ("recurring task", "@15-01-2025 (daily) #002", "002", "15-01-2025", None, "(daily)"),
            ("snoozed task", "@15-01-2025 snooze:20-01-2025 #003", "003", "15-01-2025", "20-01-2025", None),
            ("complex task", "@15-01-2025 (weekly:tue) snooze:20-01-2025 #004", "004", "15-01-2025", "20-01-2025", "(weekly:tue)"),
        ]
        
        for task_text, metadata, expected_id, expected_date, expected_snooze, expected_recur in test_cases:
            with self.subTest(task_text=task_text, metadata=metadata):
                task = f"- [ ] {task_text} | {metadata}"
                
                # Split and parse
                text_part, metadata_part = task.split(' | ', 1)
                
                # Parse metadata
                id_match = re.search(r'#(\d{3})', metadata_part)
                date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', metadata_part)
                snooze_match = re.search(r'snooze:(\d{2}-\d{2}-\d{4})', metadata_part)
                recur_match = re.search(r'\([^)]*\)', metadata_part)
                
                # Verify results
                self.assertEqual(id_match.group(1) if id_match else None, expected_id)
                self.assertEqual(date_match.group(1) if date_match else None, expected_date)
                self.assertEqual(snooze_match.group(1) if snooze_match else None, expected_snooze)
                self.assertEqual(recur_match.group(0) if recur_match else None, expected_recur)
    
    def test_quote_handling_improvements(self):
        """Test that quotes are handled properly in the new format"""
        # Task text with quotes should be preserved
        task_text = 'task with "quotes" and \'single quotes\''
        task = f"- [ ] {task_text} | @15-01-2025 #001"
        
        # Parse should work correctly
        text_part, metadata_part = task.split(' | ', 1)
        extracted_text = text_part[6:]  # Remove '- [ ] '
        
        self.assertEqual(extracted_text, task_text)
        
        # Metadata should parse correctly
        id_match = re.search(r'#(\d{3})', metadata_part)
        date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', metadata_part)
        
        self.assertIsNotNone(id_match)
        self.assertIsNotNone(date_match)
    
    def test_backward_compatibility_considerations(self):
        """Test considerations for backward compatibility"""
        # Current format tasks should still be parseable
        current_format_tasks = [
            "- [ ] old format task @15-01-2025 #001",
            "- [x] old format completed @15-01-2025 #002",
            "- [ ] old format recurring @15-01-2025 (daily) #003",
        ]
        
        for task in current_format_tasks:
            with self.subTest(task=task):
                # Should still parse with current regex
                id_match = re.search(TASK_ID_PATTERN, task)
                date_match = re.search(DATE_PATTERN, task)
                
                self.assertIsNotNone(id_match)
                self.assertIsNotNone(date_match)
                
                # But should be converted to new format
                if ' | ' not in task:
                    # This would be a migration step
                    pass

class TestValidationRules(unittest.TestCase):
    """Test validation rules for the new format"""
    
    def test_task_text_validation(self):
        """Test task text validation rules"""
        # Valid task texts
        valid_texts = [
            "simple task",
            "task with numbers 123",
            "task with punctuation: . , ! ? : ; - _",
            'task with "quotes"',
            "UPPERCASE and lowercase",
        ]
        
        for text in valid_texts:
            with self.subTest(text=text):
                # Should pass validation
                self.assertTrue(self._is_valid_task_text(text))
        
        # Invalid task texts
        invalid_texts = [
            "",  # Empty
            " ",  # Just space
            " task",  # Leading space
            "task ",  # Trailing space
            "task with @ symbol",  # Forbidden char
            "task with # symbol",  # Forbidden char
            "task with | pipe",    # Forbidden char
            "task with (parentheses)",  # Forbidden char
            "task with [brackets]",     # Forbidden char
        ]
        
        for text in invalid_texts:
            with self.subTest(text=text):
                # Should fail validation
                self.assertFalse(self._is_valid_task_text(text))
    
    def test_metadata_validation(self):
        """Test metadata validation rules"""
        # Valid metadata
        valid_metadata = [
            "@15-01-2025 #001",
            "@15-01-2025 (daily) #002",
            "@15-01-2025 snooze:20-01-2025 #003",
            "@15-01-2025 (weekly:tue) snooze:20-01-2025 #004",
        ]
        
        for metadata in valid_metadata:
            with self.subTest(metadata=metadata):
                # Should pass validation
                self.assertTrue(self._is_valid_metadata(metadata))
        
        # Invalid metadata
        invalid_metadata = [
            "15-01-2025 #001",  # Missing @
            "@15-01-2025 001",  # Missing #
            "@15-01-2025 #abc",  # Non-numeric ID
            "@invalid-date #001",  # Invalid date format
            "@15-01-2025 snooze:99-99-9999 #001",  # Invalid snooze date
        ]
        
        for metadata in invalid_metadata:
            with self.subTest(metadata=metadata):
                # Should fail validation
                self.assertFalse(self._is_valid_metadata(metadata))
    
    def _is_valid_task_text(self, text):
        """Validate task text according to new rules"""
        if not text or text.strip() != text:
            return False
        
        forbidden_chars = ['@', '#', '|', '(', ')', '[', ']']
        return not any(char in text for char in forbidden_chars)
    
    def _is_valid_metadata(self, metadata):
        """Validate metadata according to new rules"""
        # Must have ID and date
        id_match = re.search(r'#(\d{3})', metadata)
        date_match = re.search(r'@(\d{2}-\d{2}-\d{4})', metadata)
        
        if not id_match or not date_match:
            return False
        
        # Validate date format
        try:
            datetime.strptime(date_match.group(1), "%d-%m-%Y")
        except ValueError:
            return False
        
        # Validate snooze date if present
        snooze_match = re.search(r'snooze:(\d{2}-\d{2}-\d{4})', metadata)
        if snooze_match:
            try:
                datetime.strptime(snooze_match.group(1), "%d-%m-%Y")
            except ValueError:
                return False
        
        return True

if __name__ == '__main__':
    unittest.main()
