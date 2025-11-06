"""
CLI Display Module

This module provides the interactive command-line interface for the
Task Management Application. It handles user input, displays menus,
and coordinates with the TaskManager to perform operations.
"""

from datetime import datetime
import logging
import os
import platform

from .task_manager import TaskManager
from .db_manager import DBManager
from .task import Task


# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors in CLI
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MSG_OPERATION_CANCELLED = "Operation cancelled by user."
MSG_INVALID_CHOICE = "Invalid choice. Please enter a number between 1 and 8."
MSG_EMPTY_INPUT = "Input cannot be empty. Please try again."
MSG_INVALID_DATE = "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-31)."


class TaskManagerCLI:
    """
    Command-line interface for the Task Management Application.
    
    This class provides an interactive menu system for users to manage
    their tasks, with robust input validation and error handling.
    """
    
    def __init__(self, task_manager: TaskManager):
        """
        Initialize the CLI with a TaskManager instance.
        
        Args:
            task_manager: TaskManager instance for task operations
        """
        self.task_manager = task_manager
        self.running = True
    
    def clear_screen(self) -> None:
        """Clear the terminal screen based on the operating system."""
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
    
    def pause_screen(self) -> None:
        """Pause and wait for user to press Enter to continue."""
        input("\nPress Enter to continue...")
        self.clear_screen()
    
    def display_menu(self) -> None:
        """Display the main menu options."""
        self.clear_screen()
        print("\n" + "="*60)
        print("         TASK MANAGEMENT APPLICATION")
        print("="*60)
        print("1. Add a new task")
        print("2. List all tasks")
        print("3. List tasks with filters")
        print("4. Update a task")
        print("5. Mark task as completed")
        print("6. Delete a task")
        print("7. View task details")
        print("8. Exit")
        print("="*60)
    
    def get_user_choice(self) -> str:
        """
        Get and validate user's menu choice.
        
        Returns:
            User's menu choice as a string
        """
        while True:
            choice = input("\nEnter your choice (1-8): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
                return choice
            else:
                print(MSG_INVALID_CHOICE)
    
    def add_task(self) -> None:
        """Handle the process of adding a new task."""
        print("\n" + "-"*60)
        print("ADD NEW TASK")
        print("-"*60)
        
        try:
            # Get task details from user
            title = self._get_non_empty_input("Enter task title: ")
            description = input("Enter task description: ").strip()
            due_date = self._get_valid_date("Enter due date (YYYY-MM-DD): ")
            priority = self._get_valid_priority("Enter priority (Low/Medium/High): ")
            print("\nAdding task...")
            
            # Create the task
            task = self.task_manager.add_task(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority
            )
            print("\n" + "-"*60)
            print("Task added successfully!")
            print("-"*60)
            print(f"  Task ID: {task.task_id}")
            print(f"  Title: {task.title}")
            print(f"  Priority: {task.priority}")
            print(f"  Due Date: {task.due_date}")
            print("-"*60)
            self.pause_screen()
            
        except ValueError as e:
            print(f"\nError adding task: {str(e)}")
            self.pause_screen()
        except KeyboardInterrupt:
            print(f"\n{MSG_OPERATION_CANCELLED}")
            self.pause_screen()
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            logger.exception("Unexpected error in add_task")
            self.pause_screen()
    
    def list_all_tasks(self) -> None:
        """Display all tasks in a formatted table."""
        print("\n" + "-"*60)
        print("ALL TASKS")
        print("-"*60)
        
        try:
            tasks = self.task_manager.get_tasks()
            
            if not tasks:
                print("\nNo tasks found. Add your first task!")
                self.pause_screen()
                return
            
            self._display_task_table(tasks)
            print(f"\nTotal tasks: {len(tasks)}")
            self.pause_screen()
            
        except Exception as e:
            print(f"\nError listing tasks: {str(e)}")
            logger.exception("Unexpected error in list_all_tasks")
            self.pause_screen()
    
    def list_filtered_tasks(self) -> None:
        """Display tasks with user-specified filters."""
        print("\n" + "-"*60)
        print("LIST TASKS WITH FILTERS")
        print("-"*60)
        
        try:
            filters = self._get_filter_criteria()
            sort_by = self._get_sort_preference()
            
            tasks = self.task_manager.get_tasks(filter_by=filters, sort_by=sort_by)
            
            if not tasks:
                print("\nNo tasks match the specified filters.")
                self.pause_screen()
                return
            
            print(f"\n{len(tasks)} task(s) found:")
            self._display_task_table(tasks)
            self.pause_screen()
            
        except KeyboardInterrupt:
            print(f"\n{MSG_OPERATION_CANCELLED}")
            self.pause_screen()
        except Exception as e:
            print(f"\nError filtering tasks: {str(e)}")
            logger.exception("Unexpected error in list_filtered_tasks")
            self.pause_screen()
    
    def _get_filter_criteria(self) -> dict:
        """Get filter criteria from user input."""
        filters = {}
        print("\nAvailable filters (press Enter to skip):")
        
        # Filter by status
        status = input("Filter by status (Pending/In Progress/Completed): ").strip()
        if status:
            status_capitalized = ' '.join(word.capitalize() for word in status.split())
            if status_capitalized in Task.VALID_STATUSES:
                filters['status'] = status_capitalized
            else:
                print(f"Invalid status '{status}', skipping filter.")
        
        # Filter by priority
        priority = input("Filter by priority (Low/Medium/High): ").strip()
        if priority:
            priority_capitalized = priority.capitalize()
            if priority_capitalized in Task.VALID_PRIORITIES:
                filters['priority'] = priority_capitalized
            else:
                print(f"Invalid priority '{priority}', skipping filter.")
        
        # Filter by due date
        due_date = input("Filter by due date (YYYY-MM-DD): ").strip()
        if due_date:
            try:
                datetime.strptime(due_date, '%Y-%m-%d')
                filters['due_date'] = due_date
            except ValueError:
                print(f"Invalid date format '{due_date}', skipping filter.")
        
        return filters
    
    def _get_sort_preference(self) -> str:
        """Get sort preference from user input."""
        print("\nSort options:")
        print("1. Due date (default)")
        print("2. Priority")
        print("3. Creation time")
        sort_choice = input("Choose sort option (1-3): ").strip()
        
        if sort_choice == '2':
            return 'priority'
        elif sort_choice == '3':
            return 'creation_timestamp'
        return 'due_date'
    
    def update_task(self) -> None:
        """Handle updating a task's details."""
        print("\n" + "-"*60)
        print("UPDATE TASK")
        print("-"*60)
        
        try:
            task_id = self._get_non_empty_input("Enter task ID to update: ")
            task = self.task_manager.get_task_by_id(task_id)
            
            if not task:
                print(f"\nTask with ID '{task_id}' not found.")
                self.pause_screen()
                return
            
            print("\nCurrent task details:")
            self._display_task_details(task)
            
            update_data = self._collect_update_data(task)
            
            if not update_data:
                print("\nNo changes made.")
                self.pause_screen()
                return
            
            updated_task = self.task_manager.update_task_details(task_id, update_data)
            print("\nTask updated successfully!")
            self._display_task_details(updated_task)
            self.pause_screen()
            
        except KeyError as e:
            print(f"\n{str(e)}")
            self.pause_screen()
        except ValueError as e:
            print(f"\nUpdate error: {str(e)}")
            self.pause_screen()
        except KeyboardInterrupt:
            print(f"\n{MSG_OPERATION_CANCELLED}")
            self.pause_screen()
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            logger.exception("Unexpected error in update_task")
            self.pause_screen()
    
    def _collect_update_data(self, task: Task) -> dict:
        """Collect updated field values from user input."""
        print("\nEnter new values (press Enter to keep current value):")
        update_data = {}
        
        # Title
        new_title = input(f"Title [{task.title}]: ").strip()
        if new_title:
            update_data['title'] = new_title
        
        # Description
        new_desc = input(f"Description [{task.description}]: ").strip()
        if new_desc:
            update_data['description'] = new_desc
        
        # Due date
        new_date = input(f"Due date [{task.due_date}] (YYYY-MM-DD): ").strip()
        if new_date:
            try:
                datetime.strptime(new_date, '%Y-%m-%d')
                update_data['due_date'] = new_date
            except ValueError:
                print("Invalid date format, keeping current due date.")
        
        # Priority
        new_priority = input(f"Priority [{task.priority}] (Low/Medium/High): ").strip()
        if new_priority:
            new_priority_cap = new_priority.capitalize()
            if new_priority_cap in Task.VALID_PRIORITIES:
                update_data['priority'] = new_priority_cap
            else:
                print("Invalid priority, keeping current priority.")
        
        # Status
        new_status = input(f"Status [{task.status}] (Pending/In Progress/Completed): ").strip()
        if new_status:
            new_status_cap = ' '.join(word.capitalize() for word in new_status.split())
            if new_status_cap in Task.VALID_STATUSES:
                update_data['status'] = new_status_cap
            else:
                print("Invalid status, keeping current status.")
        
        return update_data
    
    def mark_task_completed(self) -> None:
        """Mark a task as completed."""
        print("\n" + "-"*60)
        print("MARK TASK AS COMPLETED")
        print("-"*60)
        
        try:
            task_id = self._get_non_empty_input("Enter task ID to mark as completed: ")
            
            task = self.task_manager.get_task_by_id(task_id)
            if not task:
                print(f"\nTask with ID '{task_id}' not found.")
                self.pause_screen()
                return
            
            if task.status == 'Completed':
                print(f"\nTask '{task.title}' is already completed.")
                self.pause_screen()
                return
            
            updated_task = self.task_manager.mark_completed(task_id)
            
            print("\nTask marked as completed!")
            print(f"  Task: {updated_task.title}")
            print(f"  Status: {updated_task.status}")
            self.pause_screen()
            
        except KeyError as e:
            print(f"\n{str(e)}")
            self.pause_screen()
        except ValueError as e:
            print(f"\nError: {str(e)}")
            self.pause_screen()
        except KeyboardInterrupt:
            print(f"\n{MSG_OPERATION_CANCELLED}")
            self.pause_screen()
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            logger.exception("Unexpected error in mark_task_completed")
            self.pause_screen()
    
    def delete_task(self) -> None:
        """Handle deleting a task."""
        print("\n" + "-"*60)
        print("DELETE TASK")
        print("-"*60)
        
        try:
            task_id = self._get_non_empty_input("Enter task ID to delete: ")
            
            task = self.task_manager.get_task_by_id(task_id)
            if not task:
                print(f"\nTask with ID '{task_id}' not found.")
                self.pause_screen()
                return
            
            print("\nTask to delete:")
            self._display_task_details(task)
            
            confirmation = input("\nAre you sure you want to delete this task? (yes/no): ").strip().lower()
            
            if confirmation in ['yes', 'y']:
                self.task_manager.delete_task(task_id)
                print("\nTask deleted successfully!")
            else:
                print("\nDeletion cancelled.")
            self.pause_screen()
            
        except KeyError as e:
            print(f"\n{str(e)}")
            self.pause_screen()
        except RuntimeError as e:
            print(f"\nError deleting task: {str(e)}")
            self.pause_screen()
        except KeyboardInterrupt:
            print(f"\n{MSG_OPERATION_CANCELLED}")
            self.pause_screen()
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            logger.exception("Unexpected error in delete_task")
            self.pause_screen()
    
    def view_task_details(self) -> None:
        """Display detailed information about a specific task."""
        print("\n" + "-"*60)
        print("VIEW TASK DETAILS")
        print("-"*60)
        
        try:
            task_id = self._get_non_empty_input("Enter task ID: ")
            
            task = self.task_manager.get_task_by_id(task_id)
            if not task:
                print(f"\nTask with ID '{task_id}' not found.")
                self.pause_screen()
                return
            
            self._display_task_details(task)
            self.pause_screen()
            
        except KeyboardInterrupt:
            print(f"\n{MSG_OPERATION_CANCELLED}")
            self.pause_screen()
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            logger.exception("Unexpected error in view_task_details")
            self.pause_screen()
    
    def _display_task_table(self, tasks: list) -> None:
        """
        Display tasks in a formatted table.
        
        Args:
            tasks: List of Task objects to display
        """
        if not tasks:
            return
        
        # Table header
        print("\n" + "-"*120)
        print(f"{'Task ID':<20} {'Title':<25} {'Priority':<10} {'Status':<15} {'Due Date':<12} {'Created':<18}")
        print("-"*120)
        
        # Table rows
        for task in tasks:
            # Truncate title if too long
            title_display = task.title[:22] + "..." if len(task.title) > 25 else task.title
            
            # Format creation timestamp
            created_str = task.creation_timestamp.strftime('%Y-%m-%d %H:%M')
            
            print(
                f"{task.task_id:<20} {title_display:<25} {task.priority:<10} "
                f"{task.status:<15} {task.due_date:<12} {created_str:<18}"
            )
        
        print("-"*120)
    
    def _display_task_details(self, task: Task) -> None:
        """
        Display detailed information about a single task.
        
        Args:
            task: Task object to display
        """
        print("\n" + "="*60)
        print(f"Task ID:     {task.task_id}")
        print(f"Title:       {task.title}")
        print(f"Description: {task.description}")
        print(f"Priority:    {task.priority}")
        print(f"Status:      {task.status}")
        print(f"Due Date:    {task.due_date}")
        print(f"Created:     {task.creation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
    
    def _get_non_empty_input(self, prompt: str) -> str:
        """
        Get non-empty input from user with validation loop.
        
        This helper method ensures the user provides meaningful input by:
        1. Stripping whitespace from input
        2. Checking if result is non-empty
        3. Re-prompting if validation fails
        
        This prevents empty strings from being used as task titles or other
        required fields, improving data quality.
        
        Args:
            prompt: Input prompt to display to the user
            
        Returns:
            Non-empty, stripped user input string
        """
        while True:  # Continue looping until valid input is provided
            value = input(prompt).strip()  # Remove leading/trailing whitespace
            if value:  # Check if string is non-empty after stripping
                return value
            else:
                print(MSG_EMPTY_INPUT)
    
    def _get_valid_date(self, prompt: str) -> str:
        """
        Get and validate a date input from user with format checking.
        
        This method uses datetime.strptime() to validate the date format.
        strptime() will raise ValueError if the format doesn't match YYYY-MM-DD,
        which we catch and use to prompt the user to try again.
        
        The YYYY-MM-DD format (ISO 8601) is used because:
        - It's unambiguous (no MM/DD vs DD/MM confusion)
        - It sorts correctly as a string
        - It's internationally recognized
        
        Args:
            prompt: Input prompt to display to the user
            
        Returns:
            Valid date string in YYYY-MM-DD format
        """
        while True:  # Loop until a valid date is entered
            date_str = input(prompt).strip()
            try:
                # Attempt to parse the date using strict format checking
                # This validates both format AND logical validity (e.g., no Feb 30)
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str  # Return if parsing succeeds
            except ValueError:
                # strptime raises ValueError for invalid dates or wrong format
                print(MSG_INVALID_DATE)
    
    def _get_valid_priority(self, prompt: str) -> str:
        """
        Get and validate a priority level from user with case normalization.
        
        This method accepts priority in any case (low, LOW, Low) and normalizes
        it to title case (Low, Medium, High) for consistency with Task class
        validation. This provides a better user experience by being case-insensitive.
        
        Args:
            prompt: Input prompt to display to the user
            
        Returns:
            Valid priority level in title case (Low, Medium, or High)
        """
        while True:  # Loop until valid priority is entered
            # Capitalize first letter to normalize input (low -> Low, HIGH -> High)
            priority = input(prompt).strip().capitalize()
            
            # Check against Task class's valid priorities list
            if priority in Task.VALID_PRIORITIES:
                return priority
            else:
                # Show user exactly what values are acceptable
                print(f"Invalid priority. Please enter one of: {', '.join(Task.VALID_PRIORITIES)}")
    
    def run(self) -> None:
        """
        Main application loop.
        
        Displays the menu and handles user choices until exit.
        """
        print("\nWelcome to the Task Management Application!")
        print(f"Currently managing {self.task_manager.get_task_count()} tasks")
        
        while self.running:
            try:
                self.display_menu()
                choice = self.get_user_choice()
                self._handle_menu_choice(choice)
                
            except KeyboardInterrupt:
                self._handle_interrupt()
            except Exception as e:
                print(f"\nUnexpected error in main loop: {str(e)}")
                logger.exception("Critical error in main application loop")
    
    def _handle_menu_choice(self, choice: str) -> None:
        """Handle the user's menu choice."""
        menu_actions = {
            '1': self.add_task,
            '2': self.list_all_tasks,
            '3': self.list_filtered_tasks,
            '4': self.update_task,
            '5': self.mark_task_completed,
            '6': self.delete_task,
            '7': self.view_task_details,
            '8': self._exit_application
        }
        
        action = menu_actions.get(choice)
        if action:
            action()
    
    def _exit_application(self) -> None:
        """Exit the application."""
        self.running = False
        print("\nThank you for using Task Management Application!")
        print("Goodbye!\n")
    
    def _handle_interrupt(self) -> None:
        """Handle keyboard interrupt."""
        print("\nApplication interrupted by user.")
        confirm = input("Do you want to exit? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y']:
            self.running = False
            print("\nGoodbye!\n")
