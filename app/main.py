"""
Task Management Application - Main Entry Point

This is the main entry point for the Task Management Application.
Running this file will start the interactive command-line interface.

Usage:
    python -m app.main
    OR
    python app/main.py

Requirements:
    - Python 3.12.4
    - MongoDB running (local or Atlas)
    - Dependencies installed (pip install -r requirements.txt)
"""

import sys
from app.db_manager import DBManager
from app.task_manager import TaskManager
from app.cli import TaskManagerCLI
from app.config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME


def main():
    """
    Application entry point and initialization coordinator.
    
    This function manages the startup sequence of the application:
    1. Establishes database connection
    2. Initializes TaskManager
    3. Starts the CLI display
    4. Handles cleanup on exit
    
    Raises:
        ConnectionError: If database connection cannot be established
        SystemExit: On fatal errors or connection failures
    """
    # Display startup banner
    print("="*30)
    print("     TASK MANAGEMENT APPLICATION - STARTING UP")
    print("="*30)

    try:
        # Initialize database manager
        # DBManager handles MongoDB connection, CRUD operations, and indexes
        print("\nConnecting to database...")
        db_manager = DBManager(
            connection_string=MONGODB_URI,  # From config.py
            db_name=DATABASE_NAME,
            collection_name=COLLECTION_NAME
        )
        print("Database connection established")
        
        # Initialize task manager
        # TaskManager loads existing tasks into memory for fast access
        # and implements business logic (filtering, sorting, validation)
        print("Loading tasks...")
        task_manager = TaskManager(db_manager)
        print(f"Loaded {task_manager.get_task_count()} tasks")
        
        # Initialize and run CLI
        # CLI handles user interaction and delegates operations to TaskManager
        cli = TaskManagerCLI(task_manager)
        cli.run()  # Blocks here until user chooses to exit
        
        # Cleanup resources
        # Properly close database connection to release resources
        print("\nClosing database connection...")
        db_manager.close_connection()
        print("Connection closed successfully")
        
    except ConnectionError as e:
        # Handle database connection failures gracefully
        # This could happen if MongoDB is not running or connection string is wrong
        print(f"\nDatabase connection error: {str(e)}")
        print("\nPlease ensure MongoDB is running and accessible.")
        print(f"   Connection string: {MONGODB_URI}")
        sys.exit(1)  # Exit with error code
        
    except Exception as e:
        # Catch-all for unexpected errors
        # Log full stack trace for debugging while showing user-friendly message
        print(f"\nFatal error: {str(e)}")
        import logging
        logging.exception("Fatal error in main")
        sys.exit(1)


if __name__ == "__main__":
    main()
