"""
Database Manager Module

- Handles all database connections and CRUD operations for the
Task Management Application using MongoDB and pymongo.
"""

from typing import List, Dict, Any
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from pymongo.database import Database
import logging

# Configure logging to see database operation details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DBManager:
    """
    Manages all database connections and operations for task persistence.
    
    - This class encapsulates MongoDB interactions and provides methods for
    CRUD operations on tasks. 
    - It handles connection management, error handling,
    and provides a clean interface for database operations.
    
    Attributes:
        client (MongoClient): MongoDB client connection
        db (Database): MongoDB database instance
        collection (Collection): MongoDB collection for tasks
    """
    
    def __init__(
        self,
        connection_string: str,
        db_name: str,
        collection_name: str = 'tasks'
    ):
        """
        Initialize the database connection.
        
        Args:
            connection_string: MongoDB connection URI
            db_name: Name of the database to use
            collection_name: Name of the collection for tasks (default: 'tasks')
            
        Raises:
            ConnectionError: If connection to database fails
        """
        try:
            # Create MongoDB client with timeout
            # MongoClient is thread-safe and maintains connection pool internally
            self.client: MongoClient = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000  # 5 second timeout to ensure fast failure
            )
            # Test the connection immediately
            # This "fail-fast" approach prevents silent failures later
            self.client.server_info()
            
            # Access database and collection
            self.db: Database = self.client[db_name]
            self.collection: Collection = self.db[collection_name]
            
            # Create index on task_id for faster lookups because index is good for frequent queries and performance
            # Applied to task_id because it's the primary key for tasks and it is unique
            self.collection.create_index('task_id', unique=True)
            
            logger.info(
                f"Successfully connected to MongoDB database: {db_name}, "
                f"collection: {collection_name}"
            )

        except errors.ServerSelectionTimeoutError as e:  # Timeout: MongoDB server not reachable

            # Common causes: MongoDB not running, wrong host/port, network issues
            error_msg = f"Failed to connect to MongoDB: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)

        except errors.ConfigurationError as e:  # Configuration: Invalid connection string format

            # Example: mongodb://invalid:format
            error_msg = f"Invalid MongoDB configuration: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error connecting to database: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    def insert_task(self, task_data: Dict[str, Any]) -> bool:
        """
        Insert a new task into the database.
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            True if insertion was successful, False otherwise
            
        Raises:
            ValueError: If task_data is invalid or missing required fields
        """
        try:
            # Validate that task_data has required fields
            required_fields = ['task_id', 'title', 'description', 
                             'due_date', 'priority', 'status']
            missing_fields = [
                field for field in required_fields 
                if field not in task_data
            ]
            
            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = self.collection.insert_one(task_data)
            
            if result.inserted_id:
                logger.info(f"Task inserted successfully: {task_data['task_id']}")
                return True
            else:
                logger.warning("Task insertion returned no ID")
                return False
                
        except errors.DuplicateKeyError:
            error_msg = f"Task with ID {task_data.get('task_id')} already exists"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except errors.WriteError as e:
            error_msg = f"Database write error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error inserting task: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def fetch_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks from the database.
        
        Returns:
            List of task dictionaries
            
        Raises:
            RuntimeError: If database query fails
        """
        try:
            # Exclude MongoDB's _id field from results
            tasks = list(self.collection.find({}, {'_id': 0}))
            logger.info(f"Retrieved {len(tasks)} tasks from database")
            return tasks
            
        except errors.PyMongoError as e:
            error_msg = f"Database query error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error fetching tasks: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def fetch_tasks_by_filter(
        self,
        filter_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Retrieve tasks matching the given filter criteria.
        
        Args:
            filter_criteria: Dictionary of field-value pairs to filter by
                            (e.g., {'priority': 'High', 'status': 'Pending'})
            
        Returns:
            List of matching task dictionaries
            
        Raises:
            RuntimeError: If database query fails
        """
        try:
            # Build MongoDB query from filter criteria
            query = {}
            for key, value in filter_criteria.items():
                if value is not None:
                    query[key] = value

            tasks = list(self.collection.find(query, {'_id': 0}))
            logger.info(
                f"Retrieved {len(tasks)} tasks matching filter: {filter_criteria}"
            )
            return tasks
            
        except errors.PyMongoError as e:
            error_msg = f"Database query error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        except Exception as e:
            error_msg = f"Error fetching filtered tasks: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def update_task(
        self,
        task_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing task in the database.
        
        Args:
            task_id: Unique identifier of the task to update
            update_data: Dictionary of fields to update
            
        Returns:
            True if update was successful, False if task not found
            
        Raises:
            ValueError: If update_data is invalid
            RuntimeError: If database operation fails
        """
        try:
            # Validate update data is not empty
            if not update_data:
                raise ValueError("Update data cannot be empty")
            
            # Protect immutable fields from modification
            # Protection is critical to maintain data integrity, especially for:
            #   - task_id
            #       it is the Primary identifier, changing breaks references
            #   - creation_timestamp
            #       it is Historical data and serves as an audit, it should never change
            #   - _id
            #       it is MongoDB internal ID, changing causes corruption
            #
            # Strategy: Remove protected fields from update_data
            # This blocklist approach is flexible and safe
            protected_fields = ['task_id', 'creation_timestamp', '_id']
            for field in protected_fields:
                if field in update_data:
                    del update_data[field]
                    logger.warning(
                        f"Removed protected field '{field}' from update data"
                    )
            
            # MongoDB update operation
            # Used $set operator to update specific fields without replacing entire document
            result = self.collection.update_one(
                {'task_id': task_id},  # Query: find document by task_id
                {'$set': update_data}   # Update: set specified fields
            )
            

            # matched_count: Number of documents matching the query
            # modified_count: Number of documents actually changed
            #
            # Scenario 1: if matched_count is 0, it means that Task doesn't exist
            if result.matched_count == 0:
                logger.warning(f"No task found with ID: {task_id}")
                return False

            # Scenario 2: if matched_count > 0, modified_count > 0, it means that Task is found and fields actually changed
            elif result.modified_count > 0:
                logger.info(f"Task updated successfully: {task_id}")
                return True

            # Scenario 3: if matched_count > 0, modified_count == 0, it means that Task is found but no fields changed
            else:
                logger.info(f"Task {task_id} matched but no changes made")
                return True
                
        except errors.WriteError as e:
            error_msg = f"Database write error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error updating task: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the database.
        
        Args:
            task_id: Unique identifier of the task to delete
            
        Returns:
            True if deletion was successful, False if task not found
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            result = self.collection.delete_one({'task_id': task_id})
            
            if result.deleted_count > 0:
                logger.info(f"Task deleted successfully: {task_id}")
                return True
            else:
                logger.warning(f"No task found with ID: {task_id}")
                return False
                
        except errors.WriteError as e:
            error_msg = f"Database write error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error deleting task: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    
    def close_connection(self) -> None:
        """
        Close the database connection.
        
        This should be called when the application shuts down to properly
        release resources.
        """
        try:
            if self.client:
                self.client.close()
                logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
    
    # This is called when entering a with statement
    # Important for resource management
    def __enter__(self):
        """Context manager entry."""
        return self
    
    # This is called when exiting a with statement
    # Important for resource cleanup
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close_connection()
