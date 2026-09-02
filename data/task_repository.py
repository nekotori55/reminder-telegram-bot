from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from domain.task import Task


class TaskRepository(ABC):
    @dataclass
    class Filter:
        owner_id: int | None = None
        status: Task.Status | None = None
        deadline_before: datetime | None = None
        deadline_after: datetime | None = None
        was_reminded_about: bool | None = None

    @abstractmethod
    def add_task(self, task : Task) -> int | None: ...

    @abstractmethod
    def update_task(self, task : Task) -> bool : ...

    @abstractmethod
    def get_task(self, id : int) -> Task | None: ...

    @abstractmethod
    def get_tasks(self, filters : Filter) -> list[Task]: ...
