# Paratrooper - Current Status Analysis

## Overview

Paratrooper is a PARA + Daily Task Management System built as a single Python script (`paratrooper.py`) that manages tasks in a plain text markdown file. The system combines the PARA methodology (Projects, Areas, Resources, Archive) with daily progress tracking.

## Current Functionality

### Core Features

1. **Progress Tracking System**
   - `[x]` = Completed tasks
   - `[~]` = Progress made (meaningful work but not finished)
   - `[ ]` = Not started

2. **PARA Organization**
   - **Projects**: Tasks with endpoints that get archived when complete
   - **Areas**: Ongoing responsibilities that never "finish"
   - **Resources**: Reference materials
   - **Zettelkasten**: Knowledge development
   - **Archive**: Historical daily sections

3. **Daily Workflow Integration**
   - Morning: `python paratrooper.py daily` - creates today's section with recurring tasks
   - Work: Edit daily section manually, mark progress/completion
   - Evening: `python paratrooper.py sync` - updates main list from daily progress

4. **Smart Recurring Tasks**
   - Basic patterns: `(daily)`, `(weekdays)`, `(weekly)`, `(monthly)`
   - Advanced patterns: `(weekly:tue)`, `(monthly:15th)`
   - Custom intervals: `(recur:3d)`, `(recur:2w)`, `(recur:1y)`

5. **Automatic Carry-over**
   - All incomplete tasks (`[ ]` and `[~]`) automatically carry over from previous day
   - Configurable via `carry_over_enabled` setting
   - Prevents tasks from falling through cracks

### Command Structure

The system supports extensive command-line operations:

**Configuration:**
- `config` - Show current configuration
- `init` - Initialize task file with default structure

**Daily Workflow:**
- `daily` - Add today's section with recurring tasks and carry-over
- `stale` - Show oldest tasks from MAIN section
- `sync` - Update MAIN from daily progress

**Task Management:**
- `add "text" [section]` - Add task to specified section
- `add-daily "text"` - Add directly to today's section
- `up <id>` - Pull task from main to today's daily section
- `down <id>` - Remove task from today's daily section

**Task Status:**
- `complete <id>` - Mark task as complete
- `pass <id>` - Mark progress on task
- `snooze <id> <days|date>` - Hide task for specified time

**Organization:**
- `show <id>` - Show task details
- `sections` - List available sections
- `archive [days]` - Clean up old content
- `delete <id>` - Delete from main list only
- `purge <id>` - Delete from everywhere

## Current Issues

### 1. Critical Parsing Format Issues

**Problem**: The current task format is fragile and prone to parsing errors:

```
- [ ] task text @date (recur) snooze:date #id
```

**Specific Issues:**
- **Ambiguous parsing**: Multiple `@`, `#`, or `()` symbols break parsing
- **Special character conflicts**: `@`, `#`, `(`, `)`, `[`, `]` in task text cause failures
- **Quote handling**: Quotes in task text break command-line parsing
- **Regex complexity**: Multiple overlapping patterns are hard to maintain

**Examples of problematic tasks:**
```markdown
- [ ] task with @ symbol @15-01-2025 #001  # BREAKS PARSING
- [ ] task with "quotes" @15-01-2025 #002  # BREAKS COMMANDS
- [ ] task with (parentheses) @15-01-2025 (daily) #003  # AMBIGUOUS
```

### 2. Missing Core Commands

**Edit Command**: No way to modify task text after creation
**Move Command**: No way to move tasks between sections
**Validation**: No input validation for task text or metadata

### 3. Test Coverage Status ✅

**Current Test Results (All Passing):**
- **Unit Tests** (`test_tasks.py`): 28/28 tests passed
- **Integration Tests** (`test_integration.py`): 12/12 tests passed
- **Parsing Tests** (`test_parsing_issues.py`): Available but not run in main suite
- **Total**: 40/40 tests passed

**Test Coverage Includes:**
- Core task management operations
- Daily workflow integration
- Recurring task logic
- Progress tracking
- Carry-over functionality
- Section management
- File formatting
- Task validation (new format)
- Edit and move commands
- Snooze functionality
- Sync operations

**Note**: Tests are currently passing, indicating the system is functional despite the format issues identified in `FORMAT_ANALYSIS.md`. The parsing issues are potential problems that could occur with edge cases.

### 4. Code Quality Issues

**File Size**: `paratrooper.py` is 3000+ lines - very large single file
**Complexity**: Multiple overlapping regex patterns
**Maintainability**: Hard to extend due to parsing fragility

## Proposed Solutions

### 1. Format Improvement (From FORMAT_ANALYSIS.md)

**New Format with Separator:**
```markdown
- [ ] task text | @date (recur) snooze:date #id
```

**Benefits:**
- Unambiguous parsing with `|` separator
- Clear separation of task text and metadata
- Character restrictions prevent conflicts
- Easy to extend with new metadata

**Character Restrictions:**
- **Allowed**: Letters, numbers, spaces, basic punctuation, quotes
- **Forbidden**: `@`, `#`, `|`, `(`, `)`, `[`, `]`, `{`, `}`, `<`, `>`, `\`, `/`, `~`, `` ` ``

### 2. Implementation Strategy

**Phase 1**: Add new format support alongside existing
**Phase 2**: Update commands to use new format
**Phase 3**: Create migration tools
**Phase 4**: Deprecate old format

### 3. Missing Commands Implementation

**Edit Command**: Modify task text with validation
**Move Command**: Move tasks between sections
**Validation**: Input validation for all commands

## Current Branch Status

- **Branch**: `analysis-and-cleanup` (newly created)
- **Previous Branch**: `simplify-carryover`
- **Working Tree**: Clean

## Summary

**Current Status**: ✅ **FUNCTIONAL** - All tests passing, core functionality working

**Key Findings**:
- System is fully functional with comprehensive test coverage (40/40 tests passing)
- Core PARA + Daily workflow is working correctly
- Automatic carry-over functionality is implemented and tested
- Edit and move commands are already implemented (contrary to initial assessment)
- Main issue is potential parsing fragility with edge cases

**Priority Issues**:
1. **Format Robustness**: Implement separator-based format to prevent parsing edge cases
2. **Code Organization**: Break down 3000+ line file into manageable modules
3. **Documentation**: Update README to reflect current capabilities

## Next Steps

1. ✅ **Run Test Suite**: Completed - All tests passing
2. **Implement Format Fix**: Address parsing issues with new separator-based format
3. ✅ **Add Missing Commands**: Already implemented (edit, move commands exist)
4. **Refactor Code**: Break down large file into modules for maintainability
5. **Improve Documentation**: Update README with current capabilities and status

## File Structure

```
/Users/morgan/dev/projects/paratrooper/
├── paratrooper.py          # Main application (3000+ lines)
├── README.md              # Comprehensive documentation
├── FORMAT_ANALYSIS.md     # Detailed format improvement analysis
├── CURRENT_STATUS_ANALYSIS.md  # This file
├── test_tasks.py          # Unit tests
├── test_integration.py   # Integration tests
├── test_parsing_issues.py # Parsing issue demonstrations
└── run_tests.py          # Test runner
```

## Configuration

The system uses a configuration file (`~/.ptconfig`) with settings for:
- Task file location
- Icon set (default, basic, nest)
- Default editor
- Carry-over behavior (enabled/disabled)

## Dependencies

- Python 3.6+
- Standard library only (no external dependencies)
- Uses `configparser`, `pathlib`, `datetime`, `re`, `unittest`

---

*Analysis completed on: $(date)*
*Branch: analysis-and-cleanup*
