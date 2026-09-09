import logging
from dataclasses import dataclass
from datetime import datetime

from telegram.ext import ApplicationBuilder, Application, ContextTypes, CallbackContext, ExtBot, TypeHandler

from bot.telegram_module import TelegramModule
from core.domain.task import Task

logger = logging.getLogger(__name__)

@dataclass
class ReminderUpdate:
    reminded_task: Task
    time: datetime

class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    @classmethod
    def from_update(
            cls,
            update: object,
            application,
    ) -> CustomContext | CallbackContext:
        if isinstance(update, ReminderUpdate):
            return cls(application=application, user_id=update.reminded_task.owner_id)
        return super().from_update(update, application)



class TaskNotifyModule(TelegramModule):
    @staticmethod
    def attach_module_build_deps(builder: ApplicationBuilder) -> ApplicationBuilder:
        context_types = ContextTypes(context=CustomContext)
        return builder.context_types(context_types)


    def __init__(self, bot : Application):
        self._bot = bot

        self._bot.add_handler(TypeHandler(type=ReminderUpdate, callback=self._process_reminder_update))


    async def put_reminder_in_queue(self, task: Task, now: datetime):
        # Put custom update in a queue
        await self._bot.update_queue.put(ReminderUpdate(task, now))


    async def _process_reminder_update(self, update: ReminderUpdate, context: CustomContext) -> None:
        task = update.reminded_task
        chat_id = task.owner_id
        now = update.time

        seconds_before_deadline = (task.deadline - now).total_seconds()
        min, sec = divmod(seconds_before_deadline, 60)

        message = f"Task {task.name} is due at {task.deadline.time()} (in {int(min)} min {int(sec)} sec)"

        logger.info("Sending reminder for task id %s for user %s", task.id, task.owner_id)
        await context.bot.send_message(chat_id, message)