from abc import ABC

from domain.task import Task
from data.task_repository import TaskRepository


class MockTaskRepository(TaskRepository):
    def __init__(self, initial_tasks=None):
        if initial_tasks is None:
            initial_tasks = []

        self._tasks : list[Task] = initial_tasks


    def get_tasks(self, filters: TaskRepository.Filter) -> list[Task]:
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

    def get_task(self, id: int) -> Task | None:
        return next(filter(lambda task : task.owner_id == id, self._tasks), None)

    def update_task(self, task: Task) -> bool:
        updated_task_before = self.get_task(task.id)

        if updated_task_before is None:
            return False

        index = self._tasks.index(updated_task_before)
        self._tasks[index] = task

        return True


    def add_task(self, task: Task) -> int | None:
        self._tasks.append(task)
        pass
