import asyncio
from datetime import datetime, timedelta

from application.task_notificator import TaskNotificator
from domain.task import Task
from application.task_repository import TaskRepository


class TaskApplication:
    def __init__(self, task_repository: TaskRepository, notificator: TaskNotificator):
        self._repository = task_repository
        self._notificator = notificator

    async def process_reminders(self):
        now: datetime = self._get_now()

        filter: TaskRepository.Filter = TaskRepository.Filter(
            was_reminded_about=False,
            deadline_after=now,
            deadline_before=now + timedelta(minutes=15)
        )

        tasks: list[Task] = await self._repository.get_tasks(filter)

        for task in tasks:
            await self._notificator.send_reminder(task, now)
            task.last_notified_at = now
            await self._repository.update_task(task)


        # Parallel process reminders
        await asyncio.gather(
            *(self._process_one_reminder(now, task) for task in tasks)
        )


    async def add_task(self, name : str, deadline: datetime, owner_id : int) -> int | None:
        await self._repository.add_task(name, deadline, owner_id)

    async def get_non_due_tasks(self, owner_id : int) -> list[Task]:
        filters = TaskRepository.Filter(
            owner_id=owner_id,
            status=Task.Status.NOT_DONE
        )
        return await self._repository.get_tasks(filters)



    def _get_now(self) -> datetime:
        return datetime.now()


    async def _process_one_reminder(self, now: datetime, task: Task):
        await self._notificator.send_reminder(task, now)
        task.last_notified_at = now
        await self._repository.update_task(task)
