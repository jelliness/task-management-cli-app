# Task Management Application 


A CLI task maangement application build with Python and MongoDb for the technical assessment for the role Junior Data Engineer to demonstrate skills in OOP, database interaction, and problem-solving.



## Features

- Add Task: Create new tasks with relevant details.
- List Tasks: View all tasks in the database.
- Filter Tasks: Filter tasks by due date, priority or status
- Update Task: Modify existing task details.
- Mark Task Complete: Change task status to completed.
- Delete Task: Remove tasks from the database.
- Validation & Error Handling: Ensuring reliable input validation, logging, and exception management.


## Tech Stack

- Language: Python 3.12.4
- Database: MongoDB (via pymongo)
- Architecture: Object-Oriented Programming (OOP)


## Project Structure

```
task-management-cli-app/
|
-----app/
    |
    -- __init__.py #initialization of packages
    -- main.py # entry point/ run file
    -- cli.py # interface/display
    -- task_manager.py # business logic
    -- task.py # task entity model
    -- db_manager.py # db handler
    -- config.py # app configurations

-----requirements.txt #Dependencies
-----.gitignore
-----README.md  # Documentation

```

## Setup

1. Navigate to Project Directory
    ```cd task-management-cli-app```


2. Create Virtual Environment then activate
    ```python -m venv venv```

    for Windows: ```venv\Scripts\activate``
    for MacOS/Linux: ```source venv/bin/activate```

3. Install dependencies
    ```pip install -r requirements.txt```

4. Configure Database
    - Ensure MongoDB is running.
    - Update connection details in config.py.

## How to Run?

Run the application using either command:

```
python -m app.main
```

or 


```
py app/main.py

```




