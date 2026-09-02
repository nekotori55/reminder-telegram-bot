from datetime import datetime, timedelta

from application.notificator import Notificator
from domain.task import Task
from data.task_repository import TaskRepository


class TaskApplication:
    def __init__(self, task_repository: TaskRepository, notificator: Notificator):
        self._repository = task_repository
        self._notificator = notificator

    def process_reminders(self):
        now: datetime = self._get_now()

        filter: TaskRepository.Filter = TaskRepository.Filter(
            was_reminded_about=False,
            deadline_after=now,
            deadline_before=now + timedelta(minutes=15)
        )

        tasks: list[Task] = self._repository.get_tasks(filter)

        for task in tasks:
            self._notificator.send_reminder(task, now)
            task.last_notified_at = now
            self._repository.update_task(task)

    def _get_now(self) -> datetime:
        # TODO maybe change for something more meaningful, timezone agnostic?
        return datetime.now()
