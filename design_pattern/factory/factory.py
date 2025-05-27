from abc import ABC, abstractmethod
from logic.entities import Person, Task, Milestone


class BaseEntityFactory(ABC):
    @abstractmethod
    def create_entity(self, row: tuple):
        """Create an entity from a database row."""
        pass


class PersonFactory(BaseEntityFactory):
    def create_entity(self, row: tuple) -> Person:
        return Person(id=row[0], name=row[1], email=row[2], role=row[3])


class TaskFactory(BaseEntityFactory):
    def create_entity(self, row: tuple) -> Task:
        return Task(id=row[0], title=row[1], description=row[2],
                    status=row[3], priority=row[4], start_date=row[5],
                    due_date=row[6], person_id=row[7], milestone_id=row[8])


class MilestoneFactory(BaseEntityFactory):
    def create_entity(self, row: tuple) -> Milestone:
        return Milestone(id=row[0], name=row[1])


def load_entity(factory: BaseEntityFactory, row: tuple):
    return factory.create_entity(row)
