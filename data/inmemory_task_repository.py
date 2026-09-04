from datetime import datetime

from domain.task import Task
from application.task_repository import TaskRepository


class InMemoryTaskRepository(TaskRepository):

    def __init__(self, initial_tasks=None):
        self._id_counter = 0
        if initial_tasks is None:
            initial_tasks = []

        self._tasks : list[Task] = initial_tasks


    async def get_tasks(self, filters: TaskRepository.Filter) -> list[Task]:
        def task_ok(task : Task) -> bool:
            if filters.was_reminded_about is not None:
                if filters.was_reminded_about == (task.last_notified_at is None):
                    return False

            if filters.owner_id is not None and filters.owner_id != task.owner_id:
                return False

            if filters.deadline_after is not None and task.deadline < filters.deadline_after:
                return False

            if filters.deadline_before is not None and task.deadline > filters.deadline_before:
                return False

            if filters.status is not None and task.status != filters.status:
                return False

            return True

        return list(filter(task_ok, self._tasks))

    async def get_task(self, id: int) -> Task | None:
        return next(filter(lambda task : task.id == id, self._tasks), None)

    async def update_task(self, task: Task) -> bool:
        updated_task_before = await self.get_task(task.id)

        if updated_task_before is None:
            return False

        index = self._tasks.index(updated_task_before)
        self._tasks[index] = task

        return True

    async def add_task(self, name: str, deadline: datetime, owner_id: int) -> int | None:
        self._id_counter += 1
        task : Task = Task(id=self._id_counter, owner_id=owner_id, deadline=deadline, name=name)
        self._tasks.append(task)

        return task.id

