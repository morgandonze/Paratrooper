"""
Command-line interface for the PARA + Daily Task Management System.
"""

import sys
from pathlib import Path
from typing import Optional

from config import Config
from task_manager import TaskManager


def main():
    """Main entry point for the CLI."""
    if len(sys.argv) < 2:
        print("Usage: tasks <command> [args...]")
        print("Use 'tasks help' for more information")
        return
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # Load configuration
    config = Config.load()
    tm = TaskManager(config)
    
    # Handle commands
    if command == "init":
        tm.init()
    elif command == "daily":
        tm.add_daily_section()
    elif command == "add" and len(args) > 0:
        # Parse section argument properly
        # No predefined sections - any section name is valid
        
        # Check if last argument looks like a section (contains : or is uppercase)
        last_arg = args[-1]
        
        if ":" in last_arg or last_arg.isupper():
            # Last argument is a section/subsection
            section = last_arg
            task_text = " ".join(args[:-1])
        else:
            # All arguments are task text
            task_text = " ".join(args)
            section = "TASKS"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-main" and len(args) > 1:
        # Parse section argument properly
        # No predefined sections - any section name is valid
        
        if len(args) == 2:
            # Just task text, no section
            task_text = args[1]
            section = "TASKS"
        else:
            # Check if last argument looks like a section
            last_arg = args[-1]
            
            if ":" in last_arg or last_arg.isupper():
                # Last argument is a section/subsection
                task_text = " ".join(args[1:-1])
                section = last_arg
            else:
                # All arguments are task text
                task_text = " ".join(args[1:])
                section = "TASKS"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-daily" and len(args) > 0:
        tm.add_task_to_daily(" ".join(args))
    elif command == "up" and len(args) > 0:
        tm.add_task_to_daily_by_id(args[0])
    elif command == "complete" and len(args) > 0:
        tm.complete_task(args[0])
    elif command == "done" and len(args) > 0:
        tm.complete_task(args[0])
    elif command == "pass" and len(args) > 0:
        tm.progress_task_in_daily(args[0])
    elif command == "snooze" and len(args) > 1:
        tm.snooze_task(args[0], args[1])
    elif command == "show" and len(args) > 0:
        # Check if it's a section:subsection format or wildcard
        if ":" in args[0] or args[0] == "*" or args[0].upper() == args[0]:
            tm.show_section(args[0])
        elif not args[0].isdigit():
            # Try as section name if it's not a number
            tm.show_section(args[0])
        else:
            tm.show_task(args[0])
    elif command == "list":
        if len(args) > 0:
            # Check if it's a section:subsection format or a known section name
            if ":" in args[0] or args[0].upper() == args[0]:
                tm.show_section(args[0])
            elif not args[0].isdigit():
                # Try as section name if it's not a number
                tm.show_section(args[0])
            else:
                tm.show_task(args[0])
        else:
            # List all main sections when no arguments provided
            tm.show_all_main()
    elif command == "edit" and len(args) > 1:
        tm.edit_task(args[0], " ".join(args[1:]))
    elif command == "move" and len(args) > 1:
        tm.move_task(args[0], args[1])
    elif command == "delete" and len(args) > 0:
        tm.delete_task_from_main(args[0])
    elif command == "purge" and len(args) > 0:
        tm.purge_task(args[0])
    elif command == "sync":
        tm.sync_daily_sections()
    elif command == "status":
        if len(args) > 0:
            tm.show_stale_tasks(args[0])
        else:
            tm.show_stale_tasks()
    elif command == "recur" and len(args) > 1:
        tm.modify_task_recurrence(args[0], args[1])
    elif command == "sections":
        tm.list_sections()
    elif command == "config":
        tm.show_config()
    elif command == "help":
        tm.show_help()
    elif command == "open":
        editor = args[0] if args else None
        tm.open_file(editor)
    else:
        print(f"Unknown command: {command}")
        print("Use 'tasks help' for available commands")


if __name__ == "__main__":
    main()
