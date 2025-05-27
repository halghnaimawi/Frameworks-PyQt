import sqlite3
import re
from datetime import datetime
from typing import List, Optional
from logic.entities import Person, Task, Milestone
from design_pattern.factory.factory import EntityFactory, load_entity, MilestoneFactory, TaskFactory, PersonFactory
import logging

logger = logging.getLogger(__name__)


class ProjectManagementRepository:
    """
    A repository class for managing project-related data (Persons, Tasks, Milestones) in a SQLite database.
    Provides CRUD operations and validation for entities, ensuring data integrity and consistency.
    """

    VALID_STATUSES = {"ToDo", "InProgress", "Done"}  # Valid task status options
    VALID_PRIORITIES = {"High", "Medium", "Low"}  # Valid task priority options
    DATE_FORMAT = r'^\d{4}-\d{2}-\d{2}$'  # Regex for YYYY-MM-DD date format
    EMAIL_FORMAT = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Regex for email validation

    def __init__(self, db_path: str):
        """
        Initialize the repository with a database path and set up the database schema.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._initialize_database()

    def _get_connection(self):
        """
        Establish a connection to the SQLite database with foreign key support enabled.

        Returns:
            sqlite3.Connection: A connection object to the database.

        Raises:
            sqlite3.Error: If the connection fails.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise sqlite3.Error(f"Database connection error: {e}")

    def _initialize_database(self):
        """
        Create the necessary tables (Person, Milestone, Task) in the database if they don't exist.

        Raises:
            sqlite3.Error: If table creation fails.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Create Person table with id, name, email, and role
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Person (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        role TEXT 
                    )
                ''')

                # Create Milestone table with id and name
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Milestone (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL
                    )
                ''')
                # Create Task table with foreign keys to Person and Milestone
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Task (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        status TEXT,
                        priority TEXT,
                        start_date TEXT,
                        due_date TEXT,
                        person_id INTEGER,
                        milestone_id INTEGER,
                        FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE,
                        FOREIGN KEY (milestone_id) REFERENCES Milestone(id) ON DELETE SET NULL
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise sqlite3.Error(f"Database initialization error: {e}")

    def _validate_email(self, email: str):
        """
        Validate that the provided email matches the expected format.

        Args:
            email (str): Email address to validate.

        Raises:
            ValueError: If the email format is invalid.
        """
        if not re.match(self.EMAIL_FORMAT, email):
            raise ValueError(f"Invalid email format: {email}")

    def _validate_date(self, date_str: str):
        """
        Validate that the provided date string is in YYYY-MM-DD format and is a valid date.

        Args:
            date_str (str): Date string to validate.

        Raises:
            ValueError: If the date format is invalid or the date is not valid.
        """
        if not re.match(self.DATE_FORMAT, date_str):
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date: {date_str}")

    def _validate_status(self, status: str):
        """
        Validate that the provided status is one of the allowed task statuses.

        Args:
            status (str): Status to validate.

        Raises:
            ValueError: If the status is not in VALID_STATUSES.
        """
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {self.VALID_STATUSES}")

    def _validate_priority(self, priority: str):
        """
        Validate that the provided priority is one of the allowed task priorities.

        Args:
            priority (str): Priority to validate.

        Raises:
            ValueError: If the priority is not in VALID_PRIORITIES.
        """
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority: {priority}. Must be one of {self.VALID_PRIORITIES}")

    def _validate_foreign_key(self, table: str, column: str, value: int) -> bool:
        """
        Check if a record exists in the specified table with the given column value.

        Args:
            table (str): Name of the table to check.
            column (str): Column name to check.
            value (int): Value to look for.

        Returns:
            bool: True if the record exists.

        Raises:
            LookupError: If no record is found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT 1 FROM {table} WHERE {column} = ?', (value,))
            if not cursor.fetchone():
                raise LookupError(f"No {table} found with {column} = {value}")
            return True

    # Person CRUD Operations
    def add_person(self, name: str, email: str, role: str or None) -> Person:
        """
        Add a new person to the database.

        Args:
            name (str): Name of the person.
            email (str): Email address of the person.
            role (str or None): Role of the person (optional).

        Returns:
            Person: The created Person object.

        Raises:
            sqlite3.Error: If the insertion fails (e.g., due to duplicate email).
        """
        self._validate_email(email)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO Person (name, email, role) VALUES (?, ?, ?)', (name, email, role))
                conn.commit()
                # person = EntityFactory.create_person((cursor.lastrowid, name, email, role))
                person = load_entity(PersonFactory(), (cursor.lastrowid, name, email, role))
                logger.info(f"Added person: {person}")
                return person
        except sqlite3.IntegrityError as e:
            logger.error(f"Person insertion error: {e}")
            raise sqlite3.Error(f"Person insertion error: {e}")

    def get_person(self, person_id: int) -> Optional[Person]:
        """
        Retrieve a person by their ID.

        Args:
            person_id (int): ID of the person to retrieve.

        Returns:
            Optional[Person]: The Person object if found, None otherwise.

        Raises:
            LookupError: If no person is found with the given ID.
            sqlite3.Error: If a database error occurs.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Person WHERE id = ?', (person_id,))
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Person with id {person_id} not found")
                    raise LookupError(f"Person with id {person_id} not found")
                # person = EntityFactory.create_person(row)
                person = load_entity(PersonFactory(), row)
                logger.info(f"Retrieved person: {person}")
                return person
        except sqlite3.Error as e:
            logger.error(f"Person retrieval error: {e}")
            raise sqlite3.Error(f"Person retrieval error: {e}")

    def update_person(self, person_id: int, name: str, email: str, role: Optional[str] = None) -> Person:
        """
        Update an existing person's details.

        Args:
            person_id (int): ID of the person to update.
            name (str): New name (or existing if None).
            email (str): New email (or existing if None).
            role (Optional[str]): New role (or existing if None).

        Returns:
            Person: The updated Person object.

        Raises:
            LookupError: If no person is found with the given ID.
            sqlite3.Error: If the update fails (e.g., due to duplicate email).
        """
        person = self.get_person(person_id)
        name = name or person.name
        email = email or person.email
        role = role or person.role
        self._validate_email(email)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE Person SET name = ?, email = ? , role=? WHERE id = ?',
                               (name, email, role, person_id))
                conn.commit()
                updated_person = Person(id=person_id, name=name, email=email, role=role)
                logger.info(f"Updated person: {updated_person}")
                return updated_person
        except sqlite3.IntegrityError as e:
            logger.error(f"Person update error: {e}")
            raise sqlite3.Error(f"Person update error: {e}")

    def delete_person(self, person_id: int):
        """
        Delete a person from the database.

        Args:
            person_id (int): ID of the person to delete.

        Raises:
            LookupError: If no person is found with the given ID.
            sqlite3.Error: If the deletion fails.
        """
        self._validate_foreign_key("Person", "id", person_id)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM Person WHERE id = ?', (person_id,))
                conn.commit()
                logger.info(f"Deleted person with id {person_id}")
        except sqlite3.Error as e:
            logger.error(f"Person deletion error: {e}")
            raise sqlite3.Error(f"Person deletion error: {e}")

    def get_all_persons(self, sort_by: str = "name") -> List[Person]:
        """
        Retrieve all persons, sorted by the specified field.

        Args:
            sort_by (str): Field to sort by (default: "name").

        Returns:
            List[Person]: List of all Person objects.

        Raises:
            ValueError: If the sort field is invalid.
            sqlite3.Error: If a database error occurs.
        """
        valid_sort_fields = {"id", "name", "email", "role"}
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort field: {sort_by}. Must be one of {valid_sort_fields}")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM Person ORDER BY {sort_by}')
                persons = [load_entity(PersonFactory(), row) for row in cursor.fetchall()]
                logger.info(f"Retrieved {len(persons)} persons, sorted by {sort_by}")
                return persons
        except sqlite3.Error as e:
            logger.error(f"Person list retrieval error: {e}")
            raise sqlite3.Error(f"Person list retrieval error: {e}")

    # Task CRUD Operations
    def get_all_tasks(self, sort_by: str = "title") -> List[Task]:
        """
        Retrieve all tasks, sorted by the specified field.

        Args:
            sort_by (str): Field to sort by (default: "title").

        Returns:
            List[Task]: List of all Task objects.

        Raises:
            ValueError: If the sort field is invalid.
            sqlite3.Error: If a database error occurs.
        """
        valid_sort_fields = {"title", "priority", "person_id", "status"}
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort field: {sort_by}. Must be one of {valid_sort_fields}")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM Task ORDER BY {sort_by}')
                tasks = [load_entity(TaskFactory(), row) for row in cursor.fetchall()]
                logger.info(f"Retrieved {len(tasks)} tasks, sorted by {sort_by}")
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Task list retrieval error: {e}")
            raise sqlite3.Error(f"Task list retrieval error: {e}")

    def add_task(self, title: str, description: str, status: str, priority: str, start_date: str, due_date: str,
                 person_id: int, milestone_id: Optional[int] = None) -> Task:
        """
        Add a new task to the database.

        Args:
            title (str): Task title.
            description (str): Task description.
            status (str): Task status.
            priority (str): Task priority.
            start_date (str): Task start date (YYYY-MM-DD).
            due_date (str): Task due date (YYYY-MM-DD).
            person_id (int): ID of the assigned person.
            milestone_id (Optional[int]): ID of the associated milestone (optional).

        Returns:
            Task: The created Task object.

        Raises:
            ValueError: If status, priority, or dates are invalid.
            LookupError: If person_id or milestone_id (if provided) is invalid.
            sqlite3.Error: If the insertion fails.
        """
        self._validate_status(status)
        self._validate_priority(priority)
        self._validate_date(start_date)
        self._validate_date(due_date)
        self._validate_foreign_key("Person", "id", person_id)
        if milestone_id:
            self._validate_foreign_key("Milestone", "id", milestone_id)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO Task (title, description, status, priority, start_date, due_date, person_id, milestone_id) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (title, description, status, priority, start_date, due_date, person_id, milestone_id))
                conn.commit()
                task = load_entity(TaskFactory(), (cursor.lastrowid, title, description, status, priority, start_date,
                                                   due_date, person_id, milestone_id))
                # task = EntityFactory.create_task((cursor.lastrowid, title, description, status, priority, start_date,
                #                                   due_date, person_id, milestone_id))
                logger.info(f"Added task: {task}")
                return task
        except sqlite3.Error as e:
            logger.error(f"Task insertion error: {e}")
            raise sqlite3.Error(f"Task insertion error: {e}")

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Retrieve a task by its ID.

        Args:
            task_id (int): ID of the task to retrieve.

        Returns:
            Optional[Task]: The Task object if found, None otherwise.

        Raises:
            LookupError: If no task is found with the given ID.
            sqlite3.Error: If a database error occurs.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Task WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Task with id {task_id} not found")
                    raise LookupError(f"Task with id {task_id} not found")
                # task = EntityFactory.create_task(row)
                task = load_entity(TaskFactory(), row)
                logger.info(f"Retrieved task: {task}")
                return task
        except sqlite3.Error as e:
            logger.error(f"Task retrieval error: {e}")
            raise sqlite3.Error(f"Task retrieval error: {e}")

    def update_task(self, task_id: int, title: Optional[str] = None, description: Optional[str] = None,
                    status: Optional[str] = None, priority: Optional[str] = None, start_date: Optional[str] = None,
                    due_date: Optional[str] = None, person_id: Optional[int] = None,
                    milestone_id: Optional[int] = None) -> Task:
        """
        Update an existing task's details.

        Args:
            task_id (int): ID of the task to update.
            title (Optional[str]): New title (or existing if None).
            description (Optional[str]): New description (or existing if None).
            status (Optional[str]): New status (or existing if None).
            priority (Optional[str]): New priority (or existing if None).
            start_date (Optional[str]): New start date (or existing if None).
            due_date (Optional[str]): New due date (or existing if None).
            person_id (Optional[int]): New person ID (or existing if None).
            milestone_id (Optional[int]): New milestone ID (or existing if None).

        Returns:
            Task: The updated Task object.

        Raises:
            ValueError: If status, priority, or dates are invalid.
            LookupError: If task_id, person_id, or milestone_id (if provided) is invalid.
            sqlite3.Error: If the update fails.
        """
        task = self.get_task(task_id)
        title = title or task.title
        description = description or task.description
        status = status or task.status
        priority = priority or task.priority
        start_date = start_date or task.start_date
        due_date = due_date or task.due_date
        person_id = person_id or task.person_id
        milestone_id = milestone_id if milestone_id is not None else task.milestone_id
        self._validate_status(status)
        self._validate_priority(priority)
        self._validate_date(start_date)
        self._validate_date(due_date)
        self._validate_foreign_key("Person", "id", person_id)
        if milestone_id:
            self._validate_foreign_key("Milestone", "id", milestone_id)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE Task SET title = ?, description = ?, status = ?, priority = ?, start_date = ?, '
                    'due_date = ?, person_id = ?, milestone_id = ? WHERE id = ?',
                    (title, description, status, priority, start_date, due_date, person_id, milestone_id,
                     task_id))
                conn.commit()
                updated_task = Task(id=task_id, title=title, description=description, status=status,
                                    priority=priority, start_date=start_date, due_date=due_date,
                                    person_id=person_id, milestone_id=milestone_id)
                logger.info(f"Updated task: {updated_task}")
                return updated_task
        except sqlite3.Error as e:
            logger.error(f"Task update error: {e}")
            raise sqlite3.Error(f"Task update error: {e}")

    def delete_task(self, task_id: int):
        """
        Delete a task from the database.

        Args:
            task_id (int): ID of the task to delete.

        Raises:
            LookupError: If no task is found with the given ID.
            sqlite3.Error: If the deletion fails.
        """
        self._validate_foreign_key("Task", "id", task_id)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM Task WHERE id = ?', (task_id,))
                conn.commit()
                logger.info(f"Deleted task with id {task_id}")
        except sqlite3.Error as e:
            logger.error(f"Task deletion error: {e}")
            raise sqlite3.Error(f"Task deletion error: {e}")

    def get_tasks_by_milestone(self, milestone_id: int, status: Optional[str] = None, priority: Optional[str] = None,
                               sort_by: str = "due_date") -> List[Task]:
        """
        Retrieve tasks associated with a milestone, optionally filtered by status and priority.

        Args:
            milestone_id (int): ID of the milestone.
            status (Optional[str]): Filter by task status (optional).
            priority (Optional[str]): Filter by task priority (optional).
            sort_by (str): Field to sort by (default: "due_date").

        Returns:
            List[Task]: List of matching Task objects.

        Raises:
            ValueError: If sort field, status, or priority is invalid.
            LookupError: If milestone_id is invalid.
            sqlite3.Error: If a database error occurs.
        """
        valid_sort_fields = {"id", "title", "status", "priority", "start_date", "due_date"}
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort field: {sort_by}. Must be one of {valid_sort_fields}")
        if status and status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status filter: {status}")
        if priority and priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Invalid priority filter: {priority}")
        self._validate_foreign_key("Milestone", "id", milestone_id)
        query = 'SELECT * FROM Task WHERE milestone_id = ?'
        params = [milestone_id]
        if status:
            query += ' AND status = ?'
            params.append(status)
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        query += f' ORDER BY {sort_by}'
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                tasks = [load_entity(TaskFactory(), row) for row in cursor.fetchall()]
                logger.info(
                    f"Retrieved {len(tasks)} tasks for milestone {milestone_id}, status={status}, priority={priority}, sorted by {sort_by}")
                return tasks
        except sqlite3.Error as e:
            logger.error(f"Task list retrieval error: {e}")
            raise sqlite3.Error(f"Task list retrieval error: {e}")

    # Milestone CRUD Operations
    def add_milestone(self, name: str) -> Milestone:
        """
        Add a new milestone to the database.

        Args:
            name (str): Name of the milestone.

        Returns:
            Milestone: The created Milestone object.

        Raises:
            sqlite3.Error: If the insertion fails.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO Milestone (name) VALUES (?)', (name,))
                conn.commit()
                # milestone = EntityFactory.create_milestone((cursor.lastrowid, name))
                milestone = load_entity(MilestoneFactory(), (cursor.lastrowid, name))
                logger.info(f"Added milestone: {milestone}")
                return milestone
        except sqlite3.Error as e:
            logger.error(f"Milestone insertion error: {e}")
            raise sqlite3.Error(f"Milestone insertion error: {e}")

    def get_milestone(self, milestone_id: int) -> Optional[Milestone]:
        """
        Retrieve a milestone by its ID.

        Args:
            milestone_id (int): ID of the milestone to retrieve.

        Returns:
            Optional[Milestone]: The Milestone object if found, None otherwise.

        Raises:
            LookupError: If no milestone is found with the given ID.
            sqlite3.Error: If a database error occurs.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Milestone WHERE id = ?', (milestone_id,))
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Milestone with id {milestone_id} not found")
                    raise LookupError(f"Milestone with id {milestone_id} not found")
                # milestone = EntityFactory.create_milestone(row)
                milestone = load_entity(MilestoneFactory(), row)
                logger.info(f"Retrieved milestone: {milestone}")
                return milestone
        except sqlite3.Error as e:
            logger.error(f"Milestone retrieval error: {e}")
            raise sqlite3.Error(f"Milestone retrieval error: {e}")

    def update_milestone(self, milestone_id: int, name: Optional[str] = None) -> Milestone:
        """
        Update an existing milestone's name.

        Args:
            milestone_id (int): ID of the milestone to update.
            name (Optional[str]): New name (or existing if None).

        Returns:
            Milestone: The updated Milestone object.

        Raises:
            LookupError: If no milestone is found with the given ID.
            sqlite3.Error: If the update fails.
        """
        milestone = self.get_milestone(milestone_id)
        name = name or milestone.name
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE Milestone SET name = ? WHERE id = ?',
                               (name, milestone_id))
                conn.commit()
                updated_milestone = Milestone(id=milestone_id, name=name)
                logger.info(f"Updated milestone: {updated_milestone}")
                return updated_milestone
        except sqlite3.Error as e:
            logger.error(f"Milestone update error: {e}")
            raise sqlite3.Error(f"Milestone update error: {e}")

    def delete_milestone(self, milestone_id: int):
        """
        Delete a milestone from the database.

        Args:
            milestone_id (int): ID of the milestone to delete.

        Raises:
            LookupError: If no milestone is found with the given ID.
            sqlite3.Error: If the deletion fails.
        """
        self._validate_foreign_key("Milestone", "id", milestone_id)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM Milestone WHERE id = ?', (milestone_id,))
                conn.commit()
                logger.info(f"Deleted milestone with id {milestone_id}")
        except sqlite3.Error as e:
            logger.error(f"Milestone deletion error: {e}")
            raise sqlite3.Error(f"Milestone deletion error: {e}")

    def get_all_milestones(self, sort_by: str = "name") -> List[Milestone]:
        """
        Retrieve all milestones, sorted by the specified field.

        Args:
            sort_by (str): Field to sort by (default: "name").

        Returns:
            List[Milestone]: List of all Milestone objects.

        Raises:
            ValueError: If the sort field is invalid.
            sqlite3.Error: If a database error occurs.
        """
        valid_sort_fields = {"name"}
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort field: {sort_by}. Must be one of {valid_sort_fields}")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM Milestone ORDER BY {sort_by}')
                milestones = [load_entity(MilestoneFactory(), row) for row in cursor.fetchall()]
                logger.info(f"Retrieved {len(milestones)} milestones, sorted by {sort_by}")
                return milestones
        except sqlite3.Error as e:
            logger.error(f"Milestone list retrieval error: {e}")
            raise sqlite3.Error(f"Milestone list retrieval error: {e}")
