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
    elif command == "daily" or command == "day":
        # Always check for new recurring tasks and add them
        result = pt.add_daily_section()
        if result == "show_daily_list":
            pt.show_daily_list()
    elif command == "stale":
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
        pt.show_stale_tasks(scope, limit)
    elif command == "age":
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
        pt.show_age_tasks(scope, limit)
    elif command == "size":
        if len(args) < 3:
            print("Error: 'size' command requires a task ID and size")
            print("Usage: t size <ID> <SIZE>")
            print("Example: t size 042 quick")
            print("Example: t size 042 slow")
            print("Example: t size 042 2.5")
            print("Example: t size 042 default")
            return
        
        # Normalize task ID by removing leading zeros
        normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
        size_arg = args[2]
        
        pt.set_task_size(normalized_id, size_arg)
    elif command == "status":
        # Keep status as alias to stale for backward compatibility
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
        pt.show_stale_tasks(scope, limit)
    elif command == "done":
        if len(args) > 1:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.complete_task(normalized_id)
        else:
            print("Error: 'done' command requires a task ID")
            print("Usage: t done <ID>")
            print("Example: t done 042")
    elif command == "undone":
        if len(args) > 1:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.reopen_task(normalized_id)
        else:
            print("Error: 'undone' command requires a task ID")
            print("Usage: t undone <ID>")
            print("Example: t undone 042")
    elif command == "pass":
        if len(args) == 2:
            # Original behavior: pt pass <ID>
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.progress_task_in_daily(normalized_id)
        elif len(args) == 3 and args[2].isdigit():
            # New behavior: pt pass <ID> <n>
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.create_pass_entry(normalized_id, int(args[2]))
        else:
            print("Error: 'pass' command expects either 1 or 2 arguments")
            print("Usage: t pass <ID> [n]")
            print("  t pass <ID>     - Mark task as progressed in today's daily section")
            print("  t pass <ID> <n>  - Create pass entry n days ago in archive section")
    elif command == "add":
        if len(args) != 3:
            print("Error: 'add' command expects exactly 2 arguments: task_text and section")
            print("Usage: t add \"task text (optional:recurrence)\" SECTION")
            print("Example: t add \"Email ORG (weekly:fri)\" WORK")
            return
        
        # Parse arguments: task_text and section
        task_text = args[1]
        section = args[2].upper()
        
        pt.add_task_to_main(task_text, section)
    elif command == "up":
        if len(args) > 1:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.add_task_to_daily_by_id(normalized_id)
        else:
            print("Error: 'up' command requires a task ID")
            print("Usage: t up <ID>")
            print("Example: t up 042")
    elif command == "snooze":
        if len(args) > 2:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.snooze_task(normalized_id, args[2])
        else:
            print("Error: 'snooze' command requires a task ID and days/date")
            print("Usage: t snooze <ID> <DAYS|DATE>")
            print("Example: t snooze 042 7")
            print("Example: t snooze 042 25-12-2025")
    elif command == "recur":
        if len(args) > 2:
            # Normalize task ID by removing leading zeros
            task_id = str(int(args[1])) if args[1].isdigit() else args[1]
            new_recurrence = " ".join(args[2:])
            pt.modify_task_recurrence(task_id, new_recurrence)
        else:
            print("Error: 'recur' command requires a task ID and recurrence pattern")
            print("Usage: t recur <ID> <PATTERN>")
            print("Example: t recur 042 daily")
            print("Example: t recur 042 weekly:mon,wed,fri")

    elif command == "sections":
        pt.list_sections()
    elif command == "delete":
        if len(args) > 1:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.delete_task_from_main(normalized_id)
        else:
            print("Error: 'delete' command requires a task ID")
            print("Usage: t delete <ID>")
            print("Example: t delete 042")
    elif command == "down":
        if len(args) > 1:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.delete_task_from_daily(normalized_id)
        else:
            print("Error: 'down' command requires a task ID")
            print("Usage: t down <ID>")
            print("Example: t down 042")
    elif command == "purge":
        if len(args) > 1:
            # Normalize task ID by removing leading zeros
            normalized_id = str(int(args[1])) if args[1].isdigit() else args[1]
            pt.purge_task(normalized_id)
        else:
            print("Error: 'purge' command requires a task ID")
            print("Usage: t purge <ID>")
            print("Example: t purge 042")
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
    elif command == "show":
        if len(args) > 1:
            # Check if it's a section:subsection format or wildcard
            if ":" in args[1] or args[1] == "*":
                pt.show_section(args[1])
            elif args[1].isdigit():
                # Show details of a specific task by ID from main section
                # Normalize task ID by removing leading zeros
                normalized_id = str(int(args[1]))
                pt.show_task_from_main(normalized_id)
            else:
                # Try as section name if it's not a number
                pt.show_section(args[1])
        else:
            print("Error: 'show' command requires a task ID or section name")
            print("Usage: t show <ID|SECTION>")
            print("Example: t show 042")
            print("Example: t show PROJECTS")
            print("Example: t show PROJECTS:HOME")
    elif command == "edit":
        if len(args) > 2:
            # Normalize task ID by removing leading zeros
            task_id = str(int(args[1])) if args[1].isdigit() else args[1]
            new_text = " ".join(args[2:])
            pt.edit_task(task_id, new_text)
        else:
            print("Error: 'edit' command requires a task ID and new text")
            print("Usage: t edit <ID> <NEW_TEXT>")
            print("Example: t edit 042 \"updated task description\"")
    elif command == "move":
        if len(args) > 2:
            # Normalize task ID by removing leading zeros
            task_id = str(int(args[1])) if args[1].isdigit() else args[1]
            new_section = args[2].upper()
            pt.move_task(task_id, new_section)
        else:
            print("Error: 'move' command requires a task ID and new section")
            print("Usage: t move <ID> <SECTION>")
            print("Example: t move 042 PROJECTS")
            print("Example: t move 042 PROJECTS:HOME")
    elif command == "open":
        editor = args[1] if len(args) > 1 else None
        pt.open_file(editor)
    else:
        print(f"Unknown command: {command}")
        print("Run 'tasks help' to see available commands.")


if __name__ == "__main__":
    main()
