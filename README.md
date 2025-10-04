# Paratrooper 🪂 - Daily Task Management System

A powerful, flexible task management system that combines organization with daily progress tracking. Built as a modular Python system that manages a plain text file, making it portable, future-proof, and tool-agnostic.

**The paratrooper is ready to drop into your daily tasks!**

## 🚀 Quick Start

```bash
# Install (download the script and make it executable)
chmod +x paratrooper.py

# Set up alias (add to your ~/.bashrc or ~/.zshrc)
alias pt='python3 paratrooper.py'

# Initialize your task file
pt init

# Create your first daily section
pt daily

# Add a task
pt add "Write blog post" WORK

# Add a recurring task
pt add "morning workout (daily)" HEALTH

# Start your day (includes recurring tasks)
pt daily

# See what needs attention
pt status

# Sync your progress
pt sync
```

## 📁 File Structure

Your tasks are stored in `~/tasks.md` (configurable) with this simplified, flexible organization:

```markdown
# DAILY
## 15-01-2025
- [x] morning workout from HEALTH #004
- [~] write chapter 3 from WORK #023
- [ ] review budget from FINANCE #067

# MAIN
## TASKS
- [ ] unsorted tasks #001

## WORK
### Website Redesign
- [ ] design homepage #002
### Marketing Campaign
- [ ] create social media posts #003

## HEALTH
- [ ] morning workout (daily) #004

## FINANCE
- [ ] review budget (weekly) #067

## REFERENCE
- [ ] reference materials #005

## NOTES
- [ ] knowledge development #006

# ARCHIVE
## 10-01-2025
## 11-01-2025
## 12-01-2025
```

## 🎯 Core Features

### 1. **Progress Tracking** - The Key Innovation
Distinguish between completion and progress:
- **`[x]` = Completed**: Task is finished
- **`[~]` = Progress**: Made meaningful progress but not done
- **`[ ]` = Not started**: No work done yet

This solves the problem of tasks where you make meaningful progress but don't finish.

### 1.5. **Smart Daily Task Management** - Latest Enhancement
- New daily tasks are automatically added to the **top** of daily sections
- Recurring tasks appear at the **top** when added to daily sections
- Pulled tasks from main list are added to the **top** of daily sections
- **Smart carry-over**: Only tasks that should recur today are carried over from previous day
- **Appearance vs Activity dates**: Daily section headers show when tasks appeared, task dates show last activity
- **Persistent sections**: Recurring tasks stay in their appearance date sections until new recurrence appears
- This ensures your most recent tasks are always visible first and nothing falls through the cracks

### 2. **Daily Workflow Integration**
- **Morning**: `pt daily` - auto-adds recurring tasks and carries over tasks that should recur today
- **Work**: Use daily section, mark tasks as you work
- **Evening**: `pt sync` - updates main list from daily progress

### 3. **Flexible Organization**
- **Simplified structure**: Only DAILY, MAIN, ARCHIVE sections required
- **Dynamic sections**: Create any section you need (WORK, HEALTH, FINANCE, etc.)
- **Hierarchical sections**: Use `:` for subsections (e.g., `WORK:OFFICE`, `HOME:MAINTENANCE`)
- **Order-agnostic**: Script finds sections by headers, not position

### 4. **Smart Recurring Tasks**
- **Basic**: `(daily)`, `(weekdays)`, `(weekly)`, `(monthly)`
- **Advanced**: `(weekly:tue)`, `(weekly:mon,wed,fri)`, `(monthly:15th)`
- **Custom**: `(recur:3d)`, `(recur:2w)`, `(recur:1y,3m)`

### 5. **Enhanced Archive System**
- Archive contains **daily subsections** that are no longer needed
- **Smart persistence**: Recurring tasks stay in daily sections until new recurrence appears
- Clean, organized archive with just the daily sections you've worked on

### 6. **Smart Date Management**
- **Task dates** = Last activity date (when you last worked on the task)
- **Daily section headers** = Appearance date (when task first appeared in daily section)
- **Daily task entries** = Preserve main task's activity date (not updated to today)
- **Activity updates** = Both daily and main entries get current date when you work on them
- **Persistent sections** = Recurring tasks stay in appearance date sections until new recurrence
- **Smart carry-over** = Only tasks that should recur today are carried over from previous day

### 7. **Easy Initialization**
- Use `pt init` to create your task file with proper structure
- No more manual file creation - the paratrooper handles it all!

### 8. **Advanced Task Management**
- **Task editing**: `pt edit ID "new text"` - Modify task descriptions
- **Task moving**: `pt move ID SECTION` - Reorganize tasks between sections
- **Task reopening**: `pt undone ID` - Mark completed tasks as incomplete
- **Recurrence modification**: `pt recur ID PATTERN` - Change recurring patterns
- **File editing**: `pt open` - Open task file with configured editor

## 🛠️ Commands

### Configuration
```bash
pt config             # Show current configuration
pt init               # Initialize task file with default structure
```

**Carry-over Behavior**: By default, all incomplete tasks (unfinished and progressed) are automatically carried over from the previous day's daily section. You can disable this behavior by setting `carry_over_enabled = false` in your configuration file (`~/.ptconfig`).

### Multiple Task Files Workflow

You can manage separate task files for different purposes using different configuration files:

```bash
# Set up aliases for different task files
alias mr='PTCONFIG=~/.ptconfig-recurring paratrooper'  # Recurring tasks
alias mt='PTCONFIG=~/.ptconfig-tasks paratrooper'      # Non-recurring tasks

# Use different files
mr daily              # Work with recurring tasks file
mt add "project task" WORK  # Add to non-recurring tasks file
mt status             # Check stale non-recurring tasks
```

This approach lets you:
- **Separate concerns**: Keep recurring habits separate from project work
- **Different workflows**: Use different carry-over settings for each file type
- **Cleaner organization**: Avoid mixing ongoing habits with finite projects
- **Focused daily sections**: Each file has its own daily workflow

### Daily Workflow
```bash
pt daily              # Add today's section with recurring tasks
pt day                # Alias for daily
pt stale              # Show stale tasks (oldest first, excludes recurring tasks)
pt stale 10           # Show 10 most stale tasks
pt stale WORK         # Show stale tasks from WORK section
pt stale WORK 3       # Show 3 stale tasks from WORK section
pt age                # Show tasks by age (oldest first, excludes recurring tasks)
pt age 10             # Show 10 oldest tasks
pt age WORK           # Show oldest tasks from WORK section
pt age WORK 3         # Show 3 oldest tasks from WORK section
pt size 042 quick      # Set task #042 to quick aging (2.0x scale)
pt size 043 slow       # Set task #043 to slow aging (0.5x scale)
pt size 044 2.5        # Set task #044 to custom scale factor
pt size 045 default    # Remove custom scaling from task #045
pt status             # Alias for stale (backward compatibility)
pt sync               # Update MAIN from daily progress
```

### Task Management
```bash
pt add "text" WORK    # Add to specific section
pt add "fix sink" HOME:MAINTENANCE # Add to subsection
pt up 042             # Pull task #042 to today's daily section
```

### Adding Recurring Tasks
You can add recurring tasks directly using the `add` command by including the recurrence pattern in parentheses:

```bash
# Basic recurring patterns
pt add "morning workout (daily)" HEALTH
pt add "weekly meal prep (weekly:sun)" HEALTH
pt add "review budget (monthly:1st)" FINANCE

# Advanced patterns
pt add "backup database (recur:3d)" WORK
pt add "security audit (recur:1m)" WORK
pt add "annual review (recur:1y)" FINANCE
```

**Recurrence patterns supported:**
- `(daily)` - Every day
- `(weekdays)` - Monday-Friday only
- `(weekly)` - Every Sunday (default)
- `(weekly:mon)` - Every Monday
- `(weekly:mon,wed,fri)` - Multiple days per week
- `(monthly)` - 1st of month (default)
- `(monthly:15th)` - 15th of every month
- `(recur:3d)` - Every 3 days
- `(recur:2w)` - Every 2 weeks
- `(recur:1m)` - Every month
- `(recur:1y)` - Every year

**Pro tip**: Use `pt daily` after adding recurring tasks to see them automatically appear in today's section!

### Task Status
```bash
pt done 042          # Mark task #042 as complete
pt undone 042        # Reopen completed task (mark as incomplete)
pt pass 042          # Mark progress [~] on task in daily section
pt pass 042 4        # Create pass entry 4 days ago (reduces urgency)
pt recur 042 daily   # Modify task recurrence pattern
```

#### Strategic Task Management with Pass Entries

The `pass` command has two modes that serve different purposes:

1. **`pt pass ID`** - The original behavior: marks a task as progressed [~] in today's daily section
2. **`pt pass ID N`** - **NEW**: Creates a "pass entry" N days ago in the archive section

**Flexible Usage**: The `pass` command can be used in two ways depending on your preference:

**Option 1: Strategic Urgency Management**
- Use `pt pass ID N` to **artificially reduce urgency** without necessarily having worked on the task
- This is about **capacity management** - adjusting task priority to match your actual capacity
- Example: `pt pass 042 4` makes a 10-day-old task appear only 6 days stale, reflecting your strategic decision about task priority

**Option 2: Actual Activity Recording**
- Use `pt pass ID N` to **record genuine past activity** that you forgot to log
- This is about **honest tracking** - documenting work you actually did but didn't record at the time
- Example: You worked on task 042 four days ago but forgot to mark it, so you use `pt pass 042 4` to record that actual activity

**Why use pass entries?** Both approaches help you:

- **Reduce urgency**: By creating a pass entry N days ago, the task appears less stale in `pt status`
- **Honest tracking**: Acknowledge work done without claiming completion
- **Capacity control**: Adjust task urgency to match your actual capacity and attention patterns

**Duplicate Prevention**: The system prevents duplicate pass entries for the same task on the same date - if you try to create multiple pass entries for the same task on the same date, only the first one will be created.

This flexibility makes the feature useful for both strategic capacity management and honest activity tracking, depending on your workflow preferences.

### Organization
```bash
pt list              # List all tasks from main sections
pt list WORK         # List tasks in WORK section
pt list WORK:OFFICE  # List tasks in WORK:OFFICE subsection
pt show 042         # Show task details by ID
pt show WORK        # Show tasks in WORK section
pt show *:OFFICE    # Show tasks from all sections with OFFICE subsection
pt sections         # List all available sections
pt edit 042 "new text" # Edit task text by ID
pt move 042 WORK    # Move task to new section
pt open             # Open tasks file with configured editor
pt open vim          # Open tasks file with specific editor
pt delete 042       # Delete from main list only
pt down 042         # Remove from today's daily section
pt purge 042        # Delete from everywhere
```

## 📝 Task Syntax

```markdown
- [ ] #001 | incomplete task | WORK | 
- [x] #002 | completed task | HEALTH | 
- [~] #003 | progressed task | PROJECTS | 
- [ ] #004 | recurring task | HEALTH | daily
- [ ] #005 | task with subsection | HOME:MAINTENANCE | 
```

**Format breakdown:**
- `[status]` - `[ ]` incomplete, `[x]` complete, `[~]` progress
- `#id` - Unique 3-digit task identifier
- `task_text` - Description of the task
- `section` - Section name (e.g., WORK, HEALTH) or `section:subsection` for hierarchical organization
- `recurring` - Recurrence pattern (daily, weekly, monthly, etc.) or empty for one-time tasks
```

## 🔄 Sync Behavior

When you run `pt sync`:

- **Completed (`[x]`)**: 
  - Non-recurring tasks: Main task becomes `[x]` 
  - Recurring tasks: Main task stays `[ ]`, date updates
  
- **Progress (`[~]`)**: 
  - All tasks: Main task stays `[ ]`, date updates to show recent engagement
  
- **Not started (`[ ]`)**: No changes to main task

### Example Sync
**Before sync (Main List):**
```markdown
- [ ] write chapter 3 #023
- [ ] morning workout (daily) #004
```

**After working (Daily Section):**
```markdown
- [~] write chapter 3 from WORK #023    # Made progress
- [x] morning workout from HEALTH #004      # Completed today
```

**After sync (Main List):**
```markdown
- [ ] write chapter 3 #023         # Still incomplete
- [ ] morning workout (daily) #004 # Recurring task
```

## 📅 Recurring Patterns

### Basic Patterns
```markdown
(daily)              Every day
(weekdays)           Monday-Friday only
```

### Weekly Patterns
```markdown
(weekly)             Every Sunday (default)
(weekly:tue)         Every Tuesday
(weekly:mon,wed,fri) Multiple days per week
```

### Monthly Patterns
```markdown
(monthly)            1st of month (default)
(monthly:15th)       15th of every month
```

### General Recurrence
```markdown
(recur:3d)           Every 3 days
(recur:2w)           Every 2 weeks
(recur:1m)           Every month
(recur:6m)           Every 6 months
(recur:1y)           Every year
(recur:1y,3m)        Every 1 year and 3 months
```

**Time units**: `d`=days, `w`=weeks, `m`=months, `y`=years

### Day Abbreviations
```markdown
mon = Monday
tue = Tuesday  
wed = Wednesday
thu = Thursday
fri = Friday
sat = Saturday
sun = Sunday
```

## 🎯 Example Day

```bash
# Morning - start with recurring tasks
pt daily              # Creates today's section with recurring tasks

# Planning - pull important tasks from main list
pt status             # See what's been neglected
pt up 023             # Pull that important work task
pt up 067             # Pull that overdue task

# During work - edit daily section manually
- [x] morning workout from HEALTH #004       # Recurring, completed
- [~] write blog post from WORK #023             # Pulled task, made progress
- [x] call client from TASKS #067                    # Pulled task, completed
- [ ] review budget from FINANCE #089                  # Recurring, didn't get to it

# Evening - sync progress back to main list
pt sync               # Updates main list from daily progress
# Result: #004 date updates, #023 stays incomplete but date updates, #067 marked complete

# Weekly planning
pt status             # See what's been neglected
pt list WORK          # Review all work tasks
pt show 023           # Check details of specific task
```

## 🏃‍♂️ Setting Up Your Recurring Tasks

Here's a complete workflow for setting up a robust recurring task system:

### Step 1: Create Your Recurring Tasks
Edit `~/tasks.md` and add recurring tasks to appropriate sections:

```markdown
## HEALTH
- [ ] morning workout (daily) #004
- [ ] weekly meal prep (weekly:sun) #005
- [ ] monthly health check (monthly:1st) #006

## FINANCE
- [ ] review budget (weekly:sat) #007
- [ ] pay bills (monthly:15th) #008
- [ ] quarterly tax review (recur:3m) #009

## LEARNING
- [ ] read for 30 minutes (daily) #010
- [ ] weekly skill practice (weekly:wed) #011

## WORK
### Website Redesign
- [ ] check analytics (weekly:mon) #012
- [ ] backup database (recur:3d) #013
- [ ] security audit (monthly:1st) #014
```

### Step 2: Test Your Setup
```bash
# See all recurring tasks for today
pt daily

# Check what's coming up
pt status

# Verify your patterns work
pt sync
```

### Step 3: Daily Workflow
```bash
# Morning routine
pt daily              # Get today's recurring tasks
# Work on tasks, mark progress with [x] or [~]
# Evening sync
pt sync               # Update main list from daily progress
```

**Pro Tips:**
- Start with just 2-3 recurring tasks to avoid overwhelm
- Use `(daily)` for habits, `(weekly:day)` for weekly reviews
- Use `(monthly:day)` for monthly planning and reviews
- Use `(recur:Xd)` for custom intervals (every 3 days, etc.)

## 🏗️ System Architecture

### Core Concepts

**Projects vs Areas**
- **Projects**: Have endpoints, get archived when complete
- **Areas**: Ongoing responsibilities, never "done"
- **Both**: Can have tasks that benefit from progress tracking

**Recurring vs Progress**
- **Recurring tasks**: You know ahead of time they'll never be "finished" (exercise, review)
- **Progress tasks**: You intend to complete them, but work happens incrementally (write chapter, build feature)

**Staleness Tracking**
- Only tracks tasks in MAIN section (ignores DAILY/ARCHIVE)
- Progress updates (`[~]`) prevent tasks from appearing stale

**Task Analysis Commands**
- **`pt stale`**: Shows tasks by staleness (days since last activity) - "What haven't I worked on recently?"
- **`pt age`**: Shows tasks by age score (days since creation × scale factor) - "What tasks have been hanging around forever?"
- **`pt size`**: Set task aging sensitivity - quick tasks (2.0x) age faster, slow tasks (0.5x) age slower
- **Both stale and age commands exclude recurring tasks** since they're designed to be ongoing forever
- **`pt status`**: Alias for `pt stale` (backward compatibility)

### ID System
- **Simple sequential**: #001, #002, #003, etc.
- **Auto-generated**: Finds highest existing ID and increments
- **Cross-references**: Daily tasks reference main tasks by same ID
- **Global scope**: IDs are unique across entire file


## ✨ Benefits

- **Visual clarity**: Today's work first, organized reference below
- **Flexible organization**: Rearrange sections without breaking scripts  
- **Honest progress**: Distinguish between engagement and completion
- **Robust automation**: ID-based commands, hierarchical parsing
- **Scalable structure**: Add projects/areas as needed
- **Plain text**: Portable, future-proof, tool-agnostic
- **Organized by actionability**: Tasks organized by what you can act on, not category

## 🧪 Testing

The system includes a comprehensive test suite to ensure all functionality works correctly:

```bash
# Run all tests
python3 test_paratrooper.py

# Tests cover:
# - Configuration management
# - Task creation and parsing
# - Section management
# - Daily workflow
# - Recurring tasks
# - Sync functionality
# - Complete integration scenarios
```

All tests pass, confirming the system works as documented.

## 🔧 Installation

1. Download `paratrooper.py`
2. Make it executable: `chmod +x paratrooper.py`
3. Set up alias (add to your `~/.bashrc` or `~/.zshrc`): `alias pt='python3 paratrooper.py'`
4. Run `pt init` to create your first task file

**Note**: The help text in the code shows `tasks` as the command name, but the README uses `pt` as the alias. Both work - use whichever you prefer!

---

This system provides structure without rigidity, automation without lock-in, and honest progress tracking that matches how complex work actually gets done.
