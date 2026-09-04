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
    async def add_task(self, name : str, deadline: datetime, owner_id : int) -> int | None: ...

    @abstractmethod
    async def update_task(self, task : Task) -> bool : ...

    @abstractmethod
    async def get_task(self, id : int) -> Task | None: ...

    @abstractmethod
    async def get_tasks(self, filters : Filter) -> list[Task]: ...
