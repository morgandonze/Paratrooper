# PARA + Daily Task Management System

A powerful, flexible task management system that combines the PARA methodology with daily progress tracking. Built as a single Python script that manages a plain text file, making it portable, future-proof, and tool-agnostic.

## 🚀 Quick Start

```bash
# Install (just download tasks.py and make it executable)
chmod +x tasks.py

# Create your first task file
./tasks.py daily

# Add a task
./tasks.py add "Write blog post" PROJECTS

# Add a recurring task
./tasks.py add "morning workout (daily)" AREAS:Health

# Start your day (includes recurring tasks)
./tasks.py daily

# See what needs attention
./tasks.py stale

# Sync your progress
./tasks.py sync
```

## 📁 File Structure

Your tasks are stored in `~/home/tasks.md` with this flexible, hierarchical organization:

```markdown
# DAILY
## 15-01-2025
- [x] morning workout from AREAS > Health #004
- [~] write chapter 3 from PROJECTS #023
- [ ] review budget from AREAS #067

# MAIN
## INBOX
- [ ] unsorted tasks #001

## PROJECTS
### Website Redesign
- [ ] design homepage #002
### Marketing Campaign
- [ ] create social media posts #003

## AREAS
### Health
- [ ] morning workout @15-01-2025 (daily) #004
### Finance
- [ ] review budget @10-01-2025 (weekly) #067

## RESOURCES
- [ ] reference materials #005

## ZETTELKASTEN
- [ ] knowledge development #006

# ARCHIVE
## ARCHIVED COMPLETED TASKS
## ARCHIVED DAILY SECTIONS
```

## 🎯 Core Features

### 1. **Progress Tracking** - The Key Innovation
Distinguish between completion and progress:
- **`[x]` = Completed**: Task is finished
- **`[~]` = Progress**: Made meaningful progress but not done
- **`[ ]` = Not started**: No work done yet

This solves the problem of tasks where you make meaningful progress but don't finish.

### 2. **Daily Workflow Integration**
- **Morning**: `tasks daily` - auto-adds recurring tasks
- **Work**: Use daily section, mark tasks as you work
- **Evening**: `tasks sync` - updates main list from daily progress

### 3. **Flexible Organization**
- **PARA methodology**: Projects, Areas, Resources, Archive
- **Hierarchical sections**: Use `:` for subsections (e.g., `PROJECTS:HOME`)
- **Order-agnostic**: Script finds sections by headers, not position

### 4. **Smart Recurring Tasks**
- **Basic**: `(daily)`, `(weekdays)`, `(weekly)`, `(monthly)`
- **Advanced**: `(weekly:tue)`, `(weekly:mon,wed,fri)`, `(monthly:15th)`
- **Custom**: `(recur:3d)`, `(recur:2w)`, `(recur:1y,3m)`

## 🛠️ Commands

### Daily Workflow
```bash
tasks daily                              # Add today's section with recurring tasks
tasks stale                              # Show oldest tasks from MAIN section
tasks sync                               # Update MAIN from daily progress
```

### Task Management
```bash
tasks add "text"                         # Add to INBOX
tasks add "text" PROJECTS                # Add to specific section
tasks add "fix sink" PROJECTS:HOME       # Add to subsection
tasks add-daily "text"                   # Add to today's section
tasks up 042                             # Pull task #042 to today's daily section
```

### Adding Recurring Tasks
You can add recurring tasks directly using the `add` command by including the recurrence pattern in parentheses:

```bash
# Basic recurring patterns
tasks add "morning workout (daily)" AREAS:Health
tasks add "weekly meal prep (weekly:sun)" AREAS:Health
tasks add "review budget (monthly:1st)" AREAS:Finance

# Advanced patterns
tasks add "backup database (recur:3d)" PROJECTS
tasks add "security audit (recur:1m)" PROJECTS
tasks add "annual review (recur:1y)" AREAS:Finance
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

**Pro tip**: Use `tasks daily` after adding recurring tasks to see them automatically appear in today's section!

### Task Status
```bash
tasks complete 042                       # Mark task #042 as complete
tasks pass 042                           # Mark progress [~] on task in daily section
tasks snooze 042 3                       # Hide task #042 for 3 days
tasks snooze 042 25-12-2025             # Hide until specific date
```

### Organization
```bash
tasks show 042                          # Show task details
tasks sections                          # List all available sections
tasks archive                           # Clean up old content (7 days)
tasks archive 3                          # Clean up content older than 3 days
tasks delete 042                        # Delete from main list only
tasks down 042                          # Remove from today's daily section
tasks purge 042                         # Delete from everywhere
```

## 📝 Task Syntax

```markdown
- [ ] incomplete task @15-01-2025 #001
- [x] completed task @15-01-2025 #002
- [~] progressed task @15-01-2025 #003
- [ ] recurring task @15-01-2025 (daily) #004
- [ ] snoozed task @15-01-2025 snooze:20-01-2025 #005
- [ ] deadline task @15-01-2025 due:25-01-2025 #006
```

## 🔄 Sync Behavior

When you run `tasks sync`:

- **Completed (`[x]`)**: 
  - Non-recurring tasks: Main task becomes `[x]` 
  - Recurring tasks: Main task stays `[ ]`, date updates
  
- **Progress (`[~]`)**: 
  - All tasks: Main task stays `[ ]`, date updates to show recent engagement
  
- **Not started (`[ ]`)**: No changes to main task

### Example Sync
**Before sync (Main List):**
```markdown
- [ ] write chapter 3 @10-01-2025 #023
- [ ] morning workout @14-01-2025 (daily) #004
```

**After working (Daily Section):**
```markdown
- [~] write chapter 3 from PROJECTS #023    # Made progress
- [x] morning workout from Health #004      # Completed today
```

**After sync (Main List):**
```markdown
- [ ] write chapter 3 @15-01-2025 #023         # Still incomplete, date updated
- [ ] morning workout @15-01-2025 (daily) #004 # Recurring, date updated
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
tasks daily                              # Creates today's section with recurring tasks

# Planning - pull important tasks from main list
tasks stale                              # See what's been neglected
tasks up 023                             # Pull that important project task
tasks up 067                             # Pull that overdue task

# During work - edit daily section manually
- [x] morning workout from AREAS > Health #004       # Recurring, completed
- [~] write blog post from PROJECTS #023             # Pulled task, made progress
- [x] call client from INBOX #067                    # Pulled task, completed
- [ ] review budget from AREAS #089                  # Recurring, didn't get to it

# Evening - sync progress back to main list
tasks sync                               # Updates main list from daily progress
# Result: #004 date updates, #023 stays incomplete but date updates, #067 marked complete

# Weekly planning
tasks stale                              # See what's been neglected
tasks archive                            # Clean up old content (7 days)
tasks archive 3                           # Clean up content older than 3 days
```

## 🏃‍♂️ Setting Up Your Recurring Tasks

Here's a complete workflow for setting up a robust recurring task system:

### Step 1: Create Your Recurring Tasks
Edit `~/home/tasks.md` and add recurring tasks to appropriate sections:

```markdown
## AREAS
### Health
- [ ] morning workout @15-01-2025 (daily) #004
- [ ] weekly meal prep @15-01-2025 (weekly:sun) #005
- [ ] monthly health check @15-01-2025 (monthly:1st) #006

### Finance
- [ ] review budget @15-01-2025 (weekly:sat) #007
- [ ] pay bills @15-01-2025 (monthly:15th) #008
- [ ] quarterly tax review @15-01-2025 (recur:3m) #009

### Learning
- [ ] read for 30 minutes @15-01-2025 (daily) #010
- [ ] weekly skill practice @15-01-2025 (weekly:wed) #011

## PROJECTS
### Website Redesign
- [ ] check analytics @15-01-2025 (weekly:mon) #012
- [ ] backup database @15-01-2025 (recur:3d) #013
- [ ] security audit @15-01-2025 (monthly:1st) #014
```

### Step 2: Test Your Setup
```bash
# See all recurring tasks for today
tasks daily

# Check what's coming up
tasks stale

# Verify your patterns work
tasks sync
```

### Step 3: Daily Workflow
```bash
# Morning routine
tasks daily                              # Get today's recurring tasks
# Work on tasks, mark progress with [x] or [~]
# Evening sync
tasks sync                               # Update main list from daily progress
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
- **PARA methodology**: Organized by actionability, not category

## 🔧 Installation

1. Download `tasks.py`
2. Make it executable: `chmod +x tasks.py`
3. Optionally add to PATH or create alias: `alias tasks='./tasks.py'`
4. Run `tasks daily` to create your first task file

## 📚 Learn More

- **PARA Method**: [Forte Labs](https://fortelabs.com/blog/para/)
- **Zettelkasten**: [Ahrens, S. (2017). How to Take Smart Notes](https://www.soenkeahrens.de/en/takesmartnotes)

---

This system provides structure without rigidity, automation without lock-in, and honest progress tracking that matches how complex work actually gets done.
