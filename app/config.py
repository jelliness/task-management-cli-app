# This module contains configuration settings for the application.


#MongoDB configuration
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "task_manager_db"
COLLECTION_NAME = "tasks"


# Application settings

# Logging
LOG_LEVEL = "ERROR"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL


# Date format
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Valid Options
VALID_PRIORITIES = ["Low", "Medium", "High"]
VALID_STATUSES = ["Pending", "In Progress", "Completed"]