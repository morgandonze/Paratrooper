#!/usr/bin/env python3
"""
Command-line interface for the Paratrooper task management system.

This module handles command parsing, routing, and user interaction.
"""

import sys
from models import Config
from paratrooper import Paratrooper


def main():
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Load configuration
    config = Config.load()
    pt = Paratrooper(config)
    
    if len(args) < 1:
        pt.show_help()
        return
    
    command = args[0]
    
    if command == "help":
        pt.show_help()
    elif command == "config":
        pt.show_config()
    elif command == "init":
        pt.init()
    elif command == "daily":
        # Always check for new recurring tasks and add them
        result = pt.add_daily_section()
        if result == "show_daily_list":
            pt.show_daily_list()
    elif command == "status":
        # Parse arguments: first arg could be scope or number, second could be number
        if len(args) > 1:
            # Check if first argument is a number (limit)
            if args[1].isdigit():
                limit = int(args[1])
                scope = None
            else:
                # First argument is scope, check if second is number
                scope = args[1]
                limit = int(args[2]) if len(args) > 2 and args[2].isdigit() else 5
        else:
            scope = None
            limit = 5
        pt.show_status_tasks(scope, limit)
    elif command == "done" and len(args) > 1:
        pt.complete_task(args[1])
    elif command == "reopen" and len(args) > 1:
        pt.reopen_task(args[1])
    elif command == "undone" and len(args) > 1:
        pt.reopen_task(args[1])
    elif command == "pass" and len(args) > 1:
        pt.progress_task_in_daily(args[1])
    elif command == "sync":
        pt.sync_daily_sections()
    elif command == "add" and len(args) > 1:
        # Parse section argument properly
        # No predefined sections - any section name is valid
        
        # Check if last argument looks like a section (contains : or is uppercase or is a single word)
        last_arg = args[-1]
        
        if ":" in last_arg or last_arg.isupper() or (len(last_arg) < 20 and not " " in last_arg and not last_arg.isdigit()):
            # Last argument is a section/subsection
            section = last_arg
            task_text = " ".join(args[1:-1])
        else:
            # All arguments are task text
            task_text = " ".join(args[1:])
            section = "TASKS"
        
        pt.add_task_to_main(task_text, section.upper())
    elif command == "up" and len(args) > 1:
        pt.add_task_to_daily_by_id(args[1])
    elif command == "snooze" and len(args) > 2:
        pt.snooze_task(args[1], args[2])
    elif command == "recur" and len(args) > 2:
        task_id = args[1]
        new_recurrence = " ".join(args[2:])
        pt.modify_task_recurrence(task_id, new_recurrence)

    elif command == "sections":
        pt.list_sections()
    elif command == "delete" and len(args) > 1:
        pt.delete_task_from_main(args[1])
    elif command == "down" and len(args) > 1:
        pt.delete_task_from_daily(args[1])
    elif command == "purge" and len(args) > 1:
        pt.purge_task(args[1])
    elif command == "list":
        if len(args) > 1:
            # Check if it's a section:subsection format or a known section name
            if ":" in args[1] or args[1].upper() == args[1]:
                pt.show_section(args[1])
            elif not args[1].isdigit():
                # Try as section name if it's not a number
                pt.show_section(args[1])
            else:
                # Numbers should be treated as section names for list command
                pt.show_section(args[1])
        else:
            # List all main sections when no arguments provided
            pt.show_all_main()
    elif command == "show" and len(args) > 1:
        # Check if it's a section:subsection format or wildcard
        if ":" in args[1] or args[1] == "*":
            pt.show_section(args[1])
        elif args[1].isdigit():
            # Show details of a specific task by ID from main section
            pt.show_task_from_main(args[1])
        else:
            # Try as section name if it's not a number
            pt.show_section(args[1])
    elif command == "edit" and len(args) > 2:
        task_id = args[1]
        new_text = " ".join(args[2:])
        pt.edit_task(task_id, new_text)
    elif command == "move" and len(args) > 2:
        task_id = args[1]
        new_section = args[2].upper()
        pt.move_task(task_id, new_section)
    elif command == "open":
        editor = args[1] if len(args) > 1 else None
        pt.open_file(editor)
    else:
        print(f"Unknown command: {command}")
        print("Run 'tasks help' to see available commands.")


if __name__ == "__main__":
    main()
