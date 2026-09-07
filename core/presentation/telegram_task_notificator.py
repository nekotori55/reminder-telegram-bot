from bot.task_notify_module import TaskNotifyModule
from datetime import datetime

from core.application.task_notificator import TaskNotificator
from core.domain.task import Task


class TelegramTaskNotificator(TaskNotificator):
    def __init__(self, telegram_bot : TaskNotifyModule):
        self._tgbot = telegram_bot

    async def send_reminder(self, task : Task, now : datetime):
        await self._tgbot.put_reminder_in_queue(task, now)