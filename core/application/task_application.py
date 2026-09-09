import asyncio
import logging
from datetime import datetime, timedelta

from core.application.task_notificator import TaskNotificator
from core.domain.task import Task
from core.application.task_repository import TaskRepository

logger = logging.getLogger(__name__)

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

        logger.info("Sending reminders for %s tasks...", len(tasks))

        # Parallel process reminders
        await asyncio.gather(
            *(self._process_one_reminder(now, task) for task in tasks)
        )


    async def add_task(self, name : str, deadline: datetime, owner_id : int) -> int | None:
        new_task_id = await self._repository.add_task(name, deadline, owner_id)
        logger.info(f"Added new task with id %s, name %s, deadline %s", new_task_id, name, deadline)
        return new_task_id

    async def get_non_due_tasks(self, owner_id : int) -> list[Task]:
        filters = TaskRepository.Filter(
            owner_id=owner_id,
            status=Task.Status.NOT_DONE
        )
        tasks = await self._repository.get_tasks(filters)
        logger.info(f"Returning requested %s tasks of user %s", len(tasks), owner_id)
        return tasks

    async def mark_task_as_done(self, task_id : int, owner_id : int) -> int | None:
        edited_task : Task | None = await self._repository.get_task(task_id)

        if edited_task is not None:
            if edited_task.owner_id != owner_id:
                logger.warning("User %s tried editing task %s that is not his", owner_id, task_id)
                return None

            logger.info("Marking task %s as DONE", task_id)
            edited_task.status = Task.Status.DONE
            success = await self._repository.update_task(edited_task)
            return edited_task.id if success else None
        else:
            logger.info("Updating task %s failed. Id not found", task_id)
            return None


    def _get_now(self) -> datetime:
        return datetime.now()


    async def _process_one_reminder(self, now: datetime, task: Task):
        await self._notificator.send_reminder(task, now)
        task.last_notified_at = now
        await self._repository.update_task(task)
