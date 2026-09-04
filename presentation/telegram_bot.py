from enum import IntEnum
import application
from application.task_application import TaskApplication
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from telegram import Update

from application.task_notificator import TaskNotificator
from domain.task import Task

from telegram.ext import Application, CallbackContext, ExtBot, ContextTypes, TypeHandler, CommandHandler

logging.getLogger("httpx").setLevel(logging.WARNING)


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


class TelegramBot(TaskNotificator):

    def __init__(self, token: str):
        self._task_app: TaskApplication | None = None

        # build bot
        context_types = ContextTypes(context=CustomContext)
        self._bot = Application.builder().token(token).context_types(context_types).build()

        # add handlers
        self._bot.add_handler(CommandHandler("start", self.start))
        self._bot.add_handler(CommandHandler("add", self.add_task))
        self._bot.add_handler(CommandHandler("list", self.list_tasks))
        self._bot.add_handler(TypeHandler(type=ReminderUpdate, callback=self.reminder_update))

    async def run(self):
        await self._bot.start()
        await self._bot.updater.start_polling()  # ty: ignore[unresolved-attribute]

    async def stop(self):
        await self._bot.stop()

    async def initialize(self, app: TaskApplication):
        self._task_app = app
        await self._bot.initialize()

    # Notificator methods
    async def send_reminder(self, task: Task, now: datetime):
        await self._bot.update_queue.put(ReminderUpdate(task, now))

    # Command handlers
    async def start(self, update: Update, context: CustomContext):
        text = "haro"

        if update.message is not None:
            await update.message.reply_text(text=text)

    async def list_tasks(self, update: Update, context: CustomContext):
        tasks = await self._task_app.get_non_due_tasks(update.effective_user.id)  # ty: ignore[unresolved-attribute]

        text = '\n'.join(list(map(lambda task: task.name, tasks)))

        if len(text) == 0:
            text = "empty"

        if update.message is not None:
            await update.message.reply_text(text=text)

    async def add_task(self, update: Update, context: CustomContext):
        name = "test task"
        deadline = datetime.now() + timedelta(minutes=16)




        if update.effective_user is None:
            raise Exception("Unknown owner_id")

        if self._task_app is None:
            raise Exception("TGBOT: app uninitialized")

        await self._task_app.add_task(owner_id=update.effective_user.id, name=name, deadline=deadline)

    async def reminder_update(self, update: ReminderUpdate, context: CustomContext) -> None:
        task = update.reminded_task
        chat_id = task.owner_id
        now = update.time

        seconds_before_deadline = (task.deadline - now).total_seconds()
        min, sec = divmod(seconds_before_deadline, 60)

        message = f"Task {task.name} is due in {min} min {sec} sec"

        await context.bot.send_message(chat_id, message)
