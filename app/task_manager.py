"""
Task Manager Module

This module contains the business logic for managing tasks. It coordinates
between the database layer and the user interface, maintaining an in-memory
cache of tasks and implementing sorting and filtering algorithms.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .task import Task
from .db_manager import DBManager


# Configure logging for easy tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manages task operations and coordinates between database and application logic.
    Maintains an in-memory cache of tasks for efficient access and implements custom sorting and filtering algorithms.
    Ensures consistency between the in-memory state and database persistence.
    
    Attributes:
        db_manager (DBManager): Database connection manager
        tasks (Dict[str, Task]): In-memory cache of tasks, keyed by task_id
    """
    
    def __init__(self, db_manager: DBManager):
        """
        Initialize the TaskManager and load existing tasks from database.
        
        Args:
            db_manager: An instance of DBManager for data persistence
            
        Raises:
            RuntimeError: If loading tasks from database fails
        """
        self.db_manager = db_manager
        self.tasks: Dict[str, Task] = {}
        
        # Load all existing tasks from database into memory
        self._load_tasks_from_database()
        logger.info(f"TaskManager initialized with {len(self.tasks)} tasks")
    
    def _load_tasks_from_database(self) -> None:
        """
        Load all tasks from the database into the in-memory cache.
        
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            task_data_list = self.db_manager.fetch_all_tasks()
            
            for task_data in task_data_list:
                try:
                    task = Task.from_dict(task_data)
                    self.tasks[task.task_id] = task
                except (KeyError, ValueError) as e:
                    logger.error(
                        f"Error loading task {task_data.get('task_id')}: {str(e)}"
                    )
                    continue
            
            logger.info(f"Loaded {len(self.tasks)} tasks from database")
            
        except Exception as e:
            error_msg = f"Failed to load tasks from database: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def add_task(
        self,
        title: str,
        description: str,
        due_date: str,
        priority: str
    ) -> Task:
        """
        Create a new task and persist it to the database.
        
        Args:
            title: Task title
            description: Task description
            due_date: Due date in YYYY-MM-DD format
            priority: Priority level (Low, Medium, High)
            
        Returns:
            The newly created Task object
            
        Raises:
            ValueError: If task validation fails or database insertion fails
        """
        try:
            # Create new Task object (validation happens in Task.__init__)
            new_task = Task(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                status='Pending'
            )
            
            # Convert to dictionary for database storage
            task_data = new_task.to_dict()
            
            # Persist to database
            self.db_manager.insert_task(task_data)
            
            # Add to in-memory cache
            self.tasks[new_task.task_id] = new_task
            
            logger.info(f"Task added successfully: {new_task.task_id}")
            return new_task
            
        except ValueError as e:
            logger.error(f"Validation error adding task: {str(e)}")
            raise
        except Exception as e:
            error_msg = f"Error adding task: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def get_tasks(
        self,
        filter_by: Optional[Dict[str, Any]] = None,
        sort_by: str = 'due_date'
    ) -> List[Task]:
        """
        Retrieve tasks with optional filtering and sorting.
        
        This method implements custom sorting logic, prioritizing tasks by
        status (Pending first) and then by the specified sort field.
        
        Args:
            filter_by: Dictionary of filter criteria (e.g., 
                      {'priority': 'High', 'status': 'Pending'})
            sort_by: Field to sort by ('due_date', 'priority', 'creation_timestamp')
                    Default is 'due_date'
            
        Returns:
            Sorted and filtered list of Task objects
        """
        task_list = list(self.tasks.values())
        
        if filter_by:
            task_list = self._apply_filters(task_list, filter_by)
        
        sorted_tasks = self._sort_tasks(task_list, sort_by)
        
        return sorted_tasks
    
    def _apply_filters(
        self,
        task_list: List[Task],
        filters: Dict[str, Any]
    ) -> List[Task]:
        """
        Apply filter criteria to a list of tasks using custom filtering logic.
        
        This is a custom filtering implementation that doesn't rely on
        external libraries or database queries. It implements a simple
        AND logic: tasks must match ALL specified filter criteria.
        
        Time Complexity: O(n * f) where n is number of tasks and f is number of filters
        Space Complexity: O(n) in worst case (all tasks match)
        
        Args:
            task_list: List of Task objects to filter
            filters: Dictionary of field-value pairs to filter by
                    Example: {'priority': 'High', 'status': 'Pending'}
            
        Returns:
            Filtered list of Task objects that match all criteria
        """
        filtered_tasks = []
        
    
        for task in task_list:
            matches = True 
            
            # Check each filter criterion
            for field, value in filters.items():
                if value is None:
                    continue
                
                task_value = getattr(task, field, None)
                
                if task_value != value:
                    matches = False
                    break 
        
            if matches:
                filtered_tasks.append(task)
        
        logger.info(
            f"Filtered {len(task_list)} tasks to {len(filtered_tasks)} "
            f"using filters: {filters}"
        )
        return filtered_tasks
    
    def _sort_tasks(
        self,
        task_list: List[Task],
        sort_by: str
    ) -> List[Task]:
        """
        Custom sorting algorithm for tasks using multi-level sort keys.
        
        This method implements a two-level sorting strategy:
        1. Primary sort: By status (Pending < In Progress < Completed)
        2. Secondary sort: By user-specified field (due_date, priority, etc.)
        
        The algorithm uses Python's sorted() function with a custom key function
        that returns a tuple. Python compares tuples element-by-element, ensuring
        status is always sorted first, then the secondary field.
        
        Time Complexity: O(n log n) - uses Python's Timsort algorithm
        Space Complexity: O(n) - creates a new sorted list
        
        Args:
            task_list: List of Task objects to sort
            sort_by: Secondary sort field ('due_date', 'priority', 'creation_timestamp')
            
        Returns:
            Sorted list of Task objects
        """
        # Define status priority mapping (lower number = higher priority)
        # This ensures pending tasks appear before in-progress and completed tasks
        status_priority = {
            'Pending': 1,
            'In Progress': 2,
            'Completed': 3
        }
        
        # Define priority level ordering (for when sort_by='priority')
        # Lower numbers appear first, so High priority tasks come before Low
        priority_levels = {
            'High': 1,
            'Medium': 2,
            'Low': 3
        }
        
        def sort_key(task: Task):
            """
            Generate a composite sort key tuple for multi-level sorting.
            
            The tuple structure: (status_value, field_value)
            Python's sort compares tuples left-to-right, so:
            - First compares status_value (element 0)
            - If equal, compares field_value (element 1)
            
            This ensures status always takes precedence in sorting.
            
            Args:
                task: Task object to generate sort key for
                
            Returns:
                Tuple of (status_priority_int, secondary_sort_value)
            """
            # First element: status priority (1=Pending, 2=In Progress, 3=Completed)
            # Lower numbers sort first, so pending tasks appear at the top
            status_value = status_priority.get(task.status, 4)
            
            # Second element: user-specified sort field
            # Determine the secondary sort value based on sort_by parameter
            if sort_by == 'priority':
                # Sort by priority level (1=High, 2=Medium, 3=Low)
                # Uses priority_levels dict to convert string to int
                field_value = priority_levels.get(task.priority, 4)

            elif sort_by == 'due_date':
                # Sort by due date string (YYYY-MM-DD format sorts correctly lexicographically)
                field_value = task.due_date
            elif sort_by == 'creation_timestamp':
                # Sort by creation datetime object
                field_value = task.creation_timestamp
            else:
                logger.warning(f"Unknown sort field: {sort_by}, using due_date")
                field_value = task.due_date
            
            return (status_value, field_value)
        
        # Use Python's built-in sorted function with custom key
        sorted_tasks = sorted(task_list, key=sort_key)
        
        logger.info(f"Sorted {len(task_list)} tasks by status and {sort_by}")
        return sorted_tasks
    
    def update_task_details(
        self,
        task_id: str,
        new_data: Dict[str, Any]
    ) -> Task:
        """
        Update a task's details in both memory and database.
        
        Supports both full and partial task ID matching for convenience.
        
        Args:
            task_id: Full or partial task identifier (e.g., "TASK-251106-A3F9" or "TASK-251106")
            new_data: Dictionary of fields to update
            
        Returns:
            The updated Task object
            
        Raises:
            KeyError: If task with given ID doesn't exist
            ValueError: If validation fails or database update fails
        """
        # Resolve task (supports partial ID matching)
        task = self.get_task_by_id(task_id)
        
        if not task:
            error_msg = f"Task with ID {task_id} not found"
            logger.error(error_msg)
            raise KeyError(error_msg)
        
        # Use the full task_id from the resolved task
        full_task_id = task.task_id
        
        try:
            # Update task attributes with validation
            for field, value in new_data.items():
                if hasattr(task, field) and not field.startswith('_'):
                    setattr(task, field, value)
            
            # Update in database using full task ID
            success = self.db_manager.update_task(full_task_id, task.to_dict())
            
            if not success:
                raise ValueError(f"Failed to update task {full_task_id} in database")
            
            logger.info(f"Task updated successfully: {full_task_id}")
            return task
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error updating task {full_task_id}: {str(e)}")
            raise ValueError(f"Update failed: {str(e)}")
    
    def mark_completed(self, task_id: str) -> Task:
        """
        Mark a task as completed.
        
        Args:
            task_id: Unique identifier of the task to mark as completed
            
        Returns:
            The updated Task object
            
        Raises:
            KeyError: If task with given ID doesn't exist
            ValueError: If database update fails
        """
        return self.update_task_details(task_id, {'status': 'Completed'})
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from both memory and database.
        
        Args:
            task_id: Full or partial unique identifier of the task to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            KeyError: If task with given ID doesn't exist
            RuntimeError: If database deletion fails
        """
        # Resolve task (supports partial ID matching)
        task = self.get_task_by_id(task_id)
        
        if not task:
            error_msg = f"Task with ID {task_id} not found"
            logger.error(error_msg)
            raise KeyError(error_msg)
        
        # Use the full task_id from the resolved task
        full_task_id = task.task_id
        
        try:
            # Delete from database
            success = self.db_manager.delete_task(full_task_id)
            
            if not success:
                raise RuntimeError(f"Failed to delete task {full_task_id} from database")
            
            # Remove from in-memory cache
            del self.tasks[full_task_id]
            
            logger.info(f"Task deleted successfully: {full_task_id}")
            return True
            
        except Exception as e:
            error_msg = f"Error deleting task {full_task_id}: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a specific task by its ID or partial ID.
        
        Supports both full ID and partial ID matching for convenience.

        If multiple tasks match a partial ID, returns the first match.
        
        Args:
            task_id: Full or partial task identifier
            
        Returns:
            Task object if found, None otherwise
        """
        # First try exact match (full ID)
        if task_id in self.tasks:
            return self.tasks[task_id]
        
        # If not found, try partial match
        # This allows users to enter shortened IDs for convenience
        for full_id, task in self.tasks.items():
            if full_id.startswith(task_id):
                logger.info(f"Matched partial ID '{task_id}' to full ID '{full_id}'")
                return task
        
        # No match found
        return None
    
    def get_task_count(self) -> int:
        """
        Get the total number of tasks.
        
        Returns:
            Count of tasks in memory
        """
        return len(self.tasks)
