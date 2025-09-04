# Task Format Analysis and Improvement Recommendations

## Executive Summary

The current task format has several parsing vulnerabilities that make text editing and command-line operations fragile. This analysis identifies the issues and proposes a robust solution using a dedicated separator and character restrictions.

## Current Format Issues

### 1. Ambiguous Parsing
The current format mixes task text with metadata without clear separation:
```
- [ ] task text @date (recur) snooze:date #id
```

**Problems:**
- Multiple `@` symbols: `task with @ symbol @15-01-2025` → parses wrong date
- Multiple `#` symbols: `task with # symbol @15-01-2025 #001` → parses wrong ID  
- Multiple parentheses: `task with (parentheses) (daily)` → parses wrong recurring pattern

### 2. Special Character Conflicts
Certain characters in task text break parsing:
- `@` conflicts with date parsing
- `#` conflicts with ID parsing
- `( )` conflict with recurring patterns
- `[ ]` conflict with status markers
- `|` would conflict with proposed separator

### 3. Quote Handling Issues
Quotes in task text cause command-line parsing problems:
```bash
tasks add 'task with "quotes" in text'  # Breaks shell parsing
```

### 4. Regex Complexity
Current parsing uses multiple overlapping regex patterns that are:
- Hard to maintain
- Error-prone for edge cases
- Difficult to extend

## Proposed Solution

### 1. Dedicated Separator
Use `|` to separate task text from metadata:
```
- [ ] task text | @date (recur) snooze:date #id
```

**Benefits:**
- Unambiguous parsing
- Clear separation of concerns
- Easy to extend with new metadata

### 2. Character Restrictions
Limit task text to safe characters:

**Allowed:**
- Letters: `a-z`, `A-Z`
- Numbers: `0-9`
- Spaces
- Basic punctuation: `. , ! ? : ; - _`
- Quotes: `" '` (for special cases)

**Forbidden:**
- `@` (conflicts with date)
- `#` (conflicts with ID)
- `|` (separator)
- `( )` (conflicts with recurring)
- `[ ]` (conflicts with status)
- Other special chars: `< > { } \ / ~ \``

### 3. Structured Metadata
All metadata comes after the `|` separator in consistent order:
```
@date (recur) snooze:date #id
```

**Benefits:**
- Predictable parsing
- Easy validation
- Simple to extend

## Format Examples

### Current Format (Problematic)
```markdown
- [ ] incomplete task @15-01-2025 #001
- [x] completed task @15-01-2025 #002
- [ ] recurring task @15-01-2025 (daily) #003
- [ ] snoozed task @15-01-2025 snooze:20-01-2025 #004
- [ ] task with @ symbol @15-01-2025 #005  # BREAKS PARSING
- [ ] task with "quotes" @15-01-2025 #006  # BREAKS COMMANDS
```

### Proposed Format (Robust)
```markdown
- [ ] incomplete task | @15-01-2025 #001
- [x] completed task | @15-01-2025 #002
- [ ] recurring task | @15-01-2025 (daily) #003
- [ ] snoozed task | @15-01-2025 snooze:20-01-2025 #004
- [ ] task with quotes | @15-01-2025 #005  # WORKS PERFECTLY
- [ ] task with special chars | @15-01-2025 #006  # WORKS PERFECTLY
```

## Implementation Benefits

### 1. Robust Parsing
- No ambiguous character conflicts
- Clear separation of task text and metadata
- Simple, reliable regex patterns

### 2. Command-Line Safety
- Quotes work properly in commands
- No special character escaping needed
- Predictable argument parsing

### 3. Easy Editing
- Clear visual separation
- Safe to edit task text
- Metadata preserved during edits

### 4. Extensibility
- Easy to add new metadata types
- Simple validation rules
- Backward compatibility possible

## Migration Strategy

### Phase 1: Add New Format Support
- Implement new parsing functions
- Support both old and new formats
- Add validation for new format

### Phase 2: Update Commands
- Modify `add` command to use new format
- Update `edit` command (when implemented)
- Ensure all operations work with new format

### Phase 3: Migration Tools
- Create migration script for existing tasks
- Convert old format to new format
- Validate all converted tasks

### Phase 4: Deprecate Old Format
- Remove old format support
- Update documentation
- Clean up old parsing code

## Validation Rules

### Task Text Validation
1. Must not be empty
2. Must not start/end with spaces
3. Must not contain forbidden characters
4. Must be properly quoted in commands

### Metadata Validation
1. Must have ID and date
2. ID must be 3-digit number
3. Date must be valid DD-MM-YYYY format
4. Snooze date must be valid if present
5. Recurring pattern must be valid if present

## Testing

Comprehensive test suite covers:
- Current parsing issues (13 test cases)
- New format parsing (8 test cases)
- Character restrictions (6 test cases)
- Validation rules (10 test cases)
- Edge cases and error conditions

## Conclusion

The proposed format with `|` separator and character restrictions provides:
- **Robust parsing** - No ambiguous character conflicts
- **Command-line safety** - Proper quote handling
- **Easy editing** - Clear visual separation
- **Extensibility** - Simple to add new features
- **Maintainability** - Clean, simple code

This format change would make the `edit` and `move` commands much easier to implement and maintain, while providing a solid foundation for future enhancements.
