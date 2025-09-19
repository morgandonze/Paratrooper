# Paratrooper 🪂 - Daily Task Management System

A powerful, flexible task management system that combines organization with daily progress tracking. Built as a modular Python system that manages a plain text file, making it portable, future-proof, and tool-agnostic.

**The paratrooper is ready to drop into your daily tasks!**

> **Note**: This is the current working implementation with a modular architecture. The system has been tested and verified to work correctly. A comprehensive test suite (`test_paratrooper.py`) ensures all functionality works as expected.

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
- [ ] morning workout @15-01-2025 (daily) #004

## FINANCE
- [ ] review budget @10-01-2025 (weekly) #067

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
- **All incomplete tasks automatically carry over** from the previous day's daily section
- **Simple behavior**: All unfinished and progressed tasks carry over by default (configurable)
- This ensures your most recent tasks are always visible first and nothing falls through the cracks

### 2. **Daily Workflow Integration**
- **Morning**: `pt daily` - auto-adds recurring tasks and carries over all incomplete tasks from previous day
- **Work**: Use daily section, mark tasks as you work
- **Evening**: `pt sync` - updates main list from daily progress

### 3. **Flexible Organization**
- **Simplified structure**: Only DAILY, MAIN, ARCHIVE sections required
- **Dynamic sections**: Create any section you need (WORK, HEALTH, FINANCE, etc.)
- **Hierarchical sections**: Use `:` for subsections (e.g., `WORK:HOME`)
- **Order-agnostic**: Script finds sections by headers, not position

### 4. **Smart Recurring Tasks**
- **Basic**: `(daily)`, `(weekdays)`, `(weekly)`, `(monthly)`
- **Advanced**: `(weekly:tue)`, `(weekly:mon,wed,fri)`, `(monthly:15th)`
- **Custom**: `(recur:3d)`, `(recur:2w)`, `(recur:1y,3m)`

### 5. **Enhanced Archive System**
- Archive only contains **daily subsections** (no completed task clutter)
- Clean, organized archive with just the daily sections you've worked on
- Use `pt archive` to clean up old daily sections

### 6. **Easy Initialization**
- Use `pt init` to create your task file with proper structure
- No more manual file creation - the paratrooper handles it all!

## 🛠️ Commands

### Configuration
```bash
pt config             # Show current configuration
pt init               # Initialize task file with default structure
```

**Carry-over Behavior**: By default, all incomplete tasks (unfinished and progressed) are automatically carried over from the previous day's daily section. You can disable this behavior by setting `carry_over_enabled = false` in your configuration file (`~/.ptconfig`).

### Daily Workflow
```bash
pt daily              # Add today's section with recurring tasks
pt stale              # Show oldest tasks from MAIN section (staleness tracking)
pt sync               # Update MAIN from daily progress
```

### Task Management
```bash
pt add "text"         # Add to TASKS section
pt add "text" WORK    # Add to specific section
pt add "fix sink" WORK:HOME # Add to subsection
pt add-daily "text"   # Add to today's section
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
pt complete 042       # Mark task #042 as complete
pt pass 042           # Mark progress [~] on task in daily section
pt snooze 042 3       # Hide task #042 for 3 days
pt snooze 042 25-12-2025 # Hide until specific date
```

### Organization
```bash
pt show 042          # Show task details
pt sections          # List all available sections
pt archive           # Clean up old content (7 days)
pt archive 3         # Clean up content older than 3 days
pt delete 042        # Delete from main list only
pt down 042          # Remove from today's daily section
pt purge 042         # Delete from everywhere
```

## 📝 Task Syntax

```markdown
- [ ] #001 | incomplete task | WORK | @15-01-2025 | 
- [x] #002 | completed task | HEALTH | @15-01-2025 | 
- [~] #003 | progressed task | PROJECTS | @15-01-2025 | 
- [ ] #004 | recurring task | HEALTH | @15-01-2025 | daily
- [ ] #005 | task with subsection | WORK:HOME | @15-01-2025 | 
```

**Format breakdown:**
- `[status]` - `[ ]` incomplete, `[x]` complete, `[~]` progress
- `#id` - Unique 3-digit task identifier
- `task_text` - Description of the task
- `section` - Section name (e.g., WORK, HEALTH) or `section:subsection` for hierarchical organization
- `@date` - Last engagement date (for staleness tracking)
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
- [ ] write chapter 3 | @10-01-2025 #023
- [ ] morning workout | @14-01-2025 (daily) #004
```

**After working (Daily Section):**
```markdown
- [~] write chapter 3 from WORK #023    # Made progress
- [x] morning workout from HEALTH #004      # Completed today
```

**After sync (Main List):**
```markdown
- [ ] write chapter 3 | @15-01-2025 #023         # Still incomplete, date updated
- [ ] morning workout | @15-01-2025 (daily) #004 # Recurring, date updated
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
pt archive            # Clean up old content (7 days)
pt archive 3          # Clean up content older than 3 days
```

## 🏃‍♂️ Setting Up Your Recurring Tasks

Here's a complete workflow for setting up a robust recurring task system:

### Step 1: Create Your Recurring Tasks
Edit `~/tasks.md` and add recurring tasks to appropriate sections:

```markdown
## HEALTH
- [ ] morning workout @15-01-2025 (daily) #004
- [ ] weekly meal prep @15-01-2025 (weekly:sun) #005
- [ ] monthly health check @15-01-2025 (monthly:1st) #006

## FINANCE
- [ ] review budget @15-01-2025 (weekly:sat) #007
- [ ] pay bills @15-01-2025 (monthly:15th) #008
- [ ] quarterly tax review @15-01-2025 (recur:3m) #009

## LEARNING
- [ ] read for 30 minutes @15-01-2025 (daily) #010
- [ ] weekly skill practice @15-01-2025 (weekly:wed) #011

## WORK
### Website Redesign
- [ ] check analytics @15-01-2025 (weekly:mon) #012
- [ ] backup database @15-01-2025 (recur:3d) #013
- [ ] security audit @15-01-2025 (monthly:1st) #014
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
- Shows days since last `@date` update
- Ignores future-snoozed tasks
- Progress updates (`[~]`) prevent tasks from appearing stale

### ID System
- **Simple sequential**: #001, #002, #003, etc.
- **Auto-generated**: Finds highest existing ID and increments
- **Cross-references**: Daily tasks reference main tasks by same ID
- **Global scope**: IDs are unique across entire file

### Date System
- `@date` = last engagement/completion (for staleness tracking)
- `snooze:date` = hide from stale reports until this date
- `due:date` = external deadline (optional)

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

---

This system provides structure without rigidity, automation without lock-in, and honest progress tracking that matches how complex work actually gets done.
