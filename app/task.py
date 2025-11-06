import random
import string
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import VALID_PRIORITIES, VALID_STATUSES


class Task:
    """Task entity representing a single task with validation."""
    
    # Class attributes for validation
    VALID_PRIORITIES = VALID_PRIORITIES
    VALID_STATUSES = VALID_STATUSES
    
    @staticmethod
    def _generate_readable_id() -> str:
        """
        Generate a human-readable task ID good for task management while ensuring uniqueness and traceability.
        Integrated with index so that IDs are easy and quick to reference.
        
        Format: TASK-YYMMDD-XXXX
        Example: TASK-251106-A3F9
        
        Returns:
            Human-readable task ID string
        """
        # Current date in YYMMDD format (2-digit year)
        date_part = datetime.now().strftime("%y%m%d")
        
        # Random 4-character alphanumeric string (uppercase)
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        return f"TASK-{date_part}-{random_part}"

    def __init__(
        self,
        title: str,
        description: str,
        due_date: str,
        priority: str,
        status: str = 'Pending',
        task_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):

        self._task_id = task_id if task_id else self._generate_readable_id()
        self._creation_timestamp = created_at if created_at else datetime.now()
        
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
    
    @property
    def task_id(self) -> str:
        return self._task_id
    
    @property
    def creation_timestamp(self) -> datetime:
        return self._creation_timestamp
 
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Title must be a string")
        if not value.strip():
            raise ValueError("Title cannot be empty")
        self._title = value.strip()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:

        if not isinstance(value, str):
            raise ValueError("Description must be a string")
        self._description = value.strip()
    

    @property
    def due_date(self) -> str:
        return self._due_date
    
    @due_date.setter
    def due_date(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Due date must be a string")
        
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Due date must be in YYYY-MM-DD format")
        
        self._due_date = value
    
    @property
    def priority(self) -> str:
        return self._priority
    
    @priority.setter
    def priority(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Priority must be a string")
        
        priority_capitalized = value.strip().capitalize()
        
        if priority_capitalized not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Priority must be one of: {', '.join(self.VALID_PRIORITIES)}"
            )
        
        self._priority = priority_capitalized
    
    # Status property with validation
    @property
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str) -> None:
        """
        Set the task status with validation.
        
        Args:
            value: Status (Pending, In Progress, Completed)
            
        Raises:
            ValueError: If status is not valid
        """
        # Type validation: Ensure input is a string
        if not isinstance(value, str):
            raise ValueError("Status must be a string")
        
        status_words = value.strip().split()
        status_capitalized = ' '.join(word.capitalize() for word in status_words)
        
        # Validate against allowed values
        if status_capitalized not in self.VALID_STATUSES:
            raise ValueError(
                f"Status must be one of: {', '.join(self.VALID_STATUSES)}"
            )
        
        # Store the normalized value (always title case for each word)
        # Database consistency: "In Progress" not "in progress" or "IN PROGRESS"
        self._status = status_capitalized
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Task object to a dictionary for database storage.
        
        Serialization Strategy:
            - Converts Python object to JSON-compatible dictionary
            - MongoDB stores documents as BSON (Binary JSON)
            - datetime objects must be converted to strings for JSON compatibility
        
        isoformat() is used because:
            - ISO 8601 format is internationally standardized (YYYY-MM-DDTHH:MM:SS.ffffff)
            - Preserves full precision including microseconds
            - Reversible: can be parsed back to datetime using fromisoformat()
            - Example: datetime(2024, 1, 15, 14, 30, 45) -> "2024-01-15T14:30:45"
        
        Returns:
            Dictionary representation of the task with all fields JSON-serializable
        """
        return {
            'task_id': self._task_id,           # Human-readable ID (already JSON-safe)
            'title': self._title,               # String
            'description': self._description,   # String
            'due_date': self._due_date,         # String (YYYY-MM-DD format)
            'priority': self._priority,         # String (Low/Medium/High)
            'status': self._status,             # String (Pending/In Progress/Completed)
            'creation_timestamp': self._creation_timestamp.isoformat()  # datetime -> ISO string
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'Task':
        """
        Create a Task object from a dictionary (e.g., from database).

        This method handles the reverse conversion:
        - Converts dictionary (from MongoDB) back to Task object
        - Handles different timestamp formats gracefully
        - Provides defaults for optional fields
        - Leverages __init__ validation automatically

        @classmethod wrapper is used:
            - Factory method pattern: creates instances without calling __init__ directly
            - Allows alternative constructors (from_dict vs regular __init__)
            - Returns cls (Task) not hard-coded class name (better for inheritance)
        
        Args:
            data_dict: Dictionary containing task data
            
        Returns:
            Task instance with validated fields
            
        Raises:
            KeyError: If required fields (title, description, due_date, priority) are missing
            ValueError: If data validation fails in property setters
        """
        created_at = data_dict.get('creation_timestamp')
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
        

        return cls(
            title=data_dict['title'],              
            description=data_dict['description'],  
            due_date=data_dict['due_date'],       
            priority=data_dict['priority'],        
            status=data_dict.get('status', 'Pending'),  # Optional: defaults to Pending
            task_id=data_dict.get('task_id'),      # Optional: generates readable ID if None
            created_at=created_at                  # Parsed timestamp
        )
    
    def __str__(self) -> str:
        """String representation of the task."""
        return (
            f"Task({self._task_id}): {self._title} "
            f"[{self._priority}] [{self._status}] Due: {self._due_date}"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation of the task."""
        return (
            f"Task(task_id='{self._task_id}', title='{self._title}', "
            f"priority='{self._priority}', status='{self._status}')"
        )
