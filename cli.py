#!/usr/bin/env python3
"""
Command-line interface for the Paratrooper task management system.

This module handles command parsing, routing, and user interaction.
"""

import sys
from models import Config
from task_manager import TaskManager


def main():
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Load configuration
    config = Config.load()
    tm = TaskManager(config)
    
    if len(args) < 1:
        tm.show_help()
        return
    
    command = args[0]
    
    if command == "help":
        tm.show_help()
    elif command == "config":
        tm.show_config()
    elif command == "init":
        tm.init()
    elif command == "daily":
        # Always check for new recurring tasks and add them
        result = tm.add_daily_section()
        if result == "show_daily_list":
            tm.show_daily_list()
    elif command == "status":
        scope = args[1] if len(args) > 1 else None
        tm.show_status_tasks(scope)
    elif command == "complete" and len(args) > 1:
        tm.complete_task(args[1])
    elif command == "done" and len(args) > 1:
        tm.complete_task(args[1])
    elif command == "reopen" and len(args) > 1:
        tm.reopen_task(args[1])
    elif command == "undone" and len(args) > 1:
        tm.reopen_task(args[1])
    elif command == "pass" and len(args) > 1:
        tm.progress_task_in_daily(args[1])
    elif command == "sync":
        tm.sync_daily_sections()
    elif command == "add" and len(args) > 1:
        # Parse section argument properly
        # No predefined sections - any section name is valid
        
        # Check if last argument looks like a section (contains : or is uppercase)
        last_arg = args[-1]
        
        if ":" in last_arg or last_arg.isupper():
            # Last argument is a section/subsection
            section = last_arg
            task_text = " ".join(args[1:-1])
        else:
            # All arguments are task text
            task_text = " ".join(args[1:])
            section = "TASKS"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-main" and len(args) > 2:
        # Parse section argument properly
        # No predefined sections - any section name is valid
        
        if len(args) == 3:
            # Just task text, no section
            task_text = args[2]
            section = "TASKS"
        else:
            # Check if last argument looks like a section
            last_arg = args[-1]
            
            if ":" in last_arg or last_arg.isupper():
                # Last argument is a section/subsection
                section = last_arg
                task_text = " ".join(args[2:-1])
            else:
                # All arguments are task text
                task_text = " ".join(args[2:])
                section = "TASKS"
        
        tm.add_task_to_main(task_text, section)
    elif command == "add-daily" and len(args) > 1:
        tm.add_task_to_daily(" ".join(args[1:]))
    elif command == "up" and len(args) > 1:
        tm.add_task_to_daily_by_id(args[1])
    elif command == "snooze" and len(args) > 2:
        tm.snooze_task(args[1], args[2])
    elif command == "recur" and len(args) > 2:
        task_id = args[1]
        new_recurrence = " ".join(args[2:])
        tm.modify_task_recurrence(task_id, new_recurrence)

    elif command == "sections":
        tm.list_sections()
    elif command == "delete" and len(args) > 1:
        tm.delete_task_from_main(args[1])
    elif command == "down" and len(args) > 1:
        tm.delete_task_from_daily(args[1])
    elif command == "purge" and len(args) > 1:
        tm.purge_task(args[1])
    elif command == "list":
        if len(args) > 1:
            # Check if it's a section:subsection format or a known section name
            if ":" in args[1] or args[1].upper() == args[1]:
                tm.show_section(args[1])
            elif not args[1].isdigit():
                # Try as section name if it's not a number
                tm.show_section(args[1])
            else:
                # Original show task by ID functionality
                tm.show_task(args[1])
        else:
            # List all main sections when no arguments provided
            tm.show_all_main()
    elif command == "show" and len(args) > 1:
        # Check if it's a section:subsection format or wildcard
        if ":" in args[1] or args[1] == "*" or args[1].upper() == args[1]:
            tm.show_section(args[1])
        elif not args[1].isdigit():
            # Try as section name if it's not a number
            tm.show_section(args[1])
        else:
            # Show details of a specific task by ID from main section
            tm.show_task_from_main(args[1])
    elif command == "edit" and len(args) > 2:
        task_id = args[1]
        new_text = " ".join(args[2:])
        tm.edit_task(task_id, new_text)
    elif command == "move" and len(args) > 2:
        task_id = args[1]
        new_section = args[2]
        tm.move_task(task_id, new_section)
    elif command == "open":
        editor = args[1] if len(args) > 1 else None
        tm.open_file(editor)
    else:
        print(f"Unknown command: {command}")
        print("Run 'tasks help' to see available commands.")


if __name__ == "__main__":
    main()
