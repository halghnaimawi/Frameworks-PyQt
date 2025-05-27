from dataclasses import dataclass
from typing import Optional


@dataclass
class Person:
    """
    A data class representing a person in the project management system.

    Attributes:
        id (int): Unique identifier for the person.
        name (str): Full name of the person.
        email (str): Email address of the person.
        role (str): Role of the person in the project (e.g., Developer, Manager).
    """
    id: int
    name: str
    email: str
    role: str  # Can be any string, including empty for no role


@dataclass
class Task:
    """
    A data class representing a task in the project management system.

    Attributes:
        id (int): Unique identifier for the task.
        title (str): Title or name of the task.
        description (str): Detailed description of the task.
        status (str): Current status of the task (e.g., ToDo, InProgress, Done).
        priority (str): Priority level of the task (e.g., High, Medium, Low).
        start_date (str): Start date of the task in YYYY-MM-DD format.
        due_date (str): Due date of the task in YYYY-MM-DD format.
        person_id (int): ID of the person assigned to the task.
        milestone_id (Optional[int]): ID of the associated milestone, if any.
    """
    id: int
    title: str
    description: str
    status: str
    priority: str
    start_date: str
    due_date: str
    person_id: int
    milestone_id: Optional[int]  # Optional to allow tasks without a milestone


@dataclass
class Milestone:
    """
    A data class representing a milestone in the project management system.

    Attributes:
        id (int): Unique identifier for the milestone.
        name (str): Name or description of the milestone.
    """
    id: int
    name: str