from enum import IntEnum
from core.application.task_application import TaskApplication
import logging
from dataclasses import dataclass
from datetime import datetime

from telegram import Update

from core.domain.task import Task

from telegram.ext import Application, CallbackContext, ExtBot, ContextTypes, TypeHandler, CommandHandler, \
    ConversationHandler, MessageHandler

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


class ConvState(IntEnum):
        ADD_TASK_NAME = 1
        ADD_TASK_DEADLINE_DATE = 2
        ADD_TASK_DEADLINE_TIME = 3
        ADD_TASK_FINISH = 4
        END = ConversationHandler.END

class TelegramBot():

    def __init__(self, token: str):
        self._task_app: TaskApplication | None = None

        # build bot
        context_types = ContextTypes(context=CustomContext)
        self._bot = Application.builder().token(token).context_types(context_types).build()


        add_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("add", self.add_task)],
            states={
                ConvState.ADD_TASK_NAME: [
                    MessageHandler(None, self.add_task_name)
                ],
                ConvState.ADD_TASK_DEADLINE_DATE: [
                    MessageHandler(None, self.add_task_deadline_date)
                ],
                ConvState.ADD_TASK_DEADLINE_TIME: [
                    MessageHandler(None, self.add_task_deadline_time)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.add_task_cancel)]
        )

        # add handlers
        self._bot.add_handler(CommandHandler("start", self.start))
        self._bot.add_handler(add_conv_handler)
        self._bot.add_handler(CommandHandler("list", self.list_tasks))
        self._bot.add_handler(TypeHandler(type=ReminderUpdate, callback=self.process_reminder_update))

    async def run(self):
        await self._bot.start()
        await self._bot.updater.start_polling()  # ty: ignore[unresolved-attribute]

    async def stop(self):
        await self._bot.stop()

    async def initialize(self, app: TaskApplication):
        self._task_app = app
        await self._bot.initialize()


    # Command handlers
    async def start(self, update: Update, context: CustomContext):
        if update.message is not None:
            await update.message.reply_text(
                "This is the simple reminder bot!\n"
                "To add a task use /add command.\n"
                "To list your tasks use /list command.\n"
                "The bot will remind you when the task is due in 15 minutes."
            )

    async def list_tasks(self, update: Update, context: CustomContext):
        tasks = await self._task_app.get_non_due_tasks(update.effective_user.id)  # ty: ignore[unresolved-attribute]

        def task_to_str(task : Task) -> str:
            info = [
                "`ID:`", str(task.id),
                "`Name:`", task.name,
                "`Deadline:`", task.deadline.time().strftime("%H:%M"), task.deadline.date().strftime("%d-%d-%Y")
            ]
            return "\n".join(info)

        text = '\n\n'.join(list(map(task_to_str, tasks)))

        if len(text) == 0:
            text = "You have no pending tasks! Good Job!"

        if update.message is not None:
            await update.message.reply_markdown(text=text)

    # Entrypoint for add task conversation, forwards to add_task_name handler
    async def add_task(self, update: Update, context: CustomContext):
        if update.message is None:
            raise Exception("Unknown owner_id")

        await update.message.reply_text(
            "Please, fill the info about the reminder"
        )
        await update.message.reply_text(
            "Enter the name of the new task or /cancel"
        )

        return ConvState.ADD_TASK_NAME


    async def add_task_name(self, update: Update, context: CustomContext):
        if update.message is None or context.user_data is None:
            raise Exception("Network Error")

        context.user_data["new_task_name"] = update.message.text

        await update.message.reply_text(
            "Please, send the deadline date in format DD-MM-YYYY"
        )

        return ConvState.ADD_TASK_DEADLINE_DATE

    async def add_task_deadline_date(self, update: Update, context: CustomContext):
        if update.message is None or context.user_data is None or update.message.text is None:
            raise Exception("Network Error")

        raw_date = update.message.text

        context.user_data["new_task_deadline_date"] = datetime.strptime(raw_date, "%d-%m-%Y").date()

        await update.message.reply_text(
            "Please, send the deadline time in format H:M"
        )

        return ConvState.ADD_TASK_DEADLINE_TIME

    async def add_task_deadline_time(self, update: Update, context: CustomContext):
        if update.message is None or context.user_data is None or update.message.text is None or update.effective_user is None:
            raise Exception("Network Error")

        raw_time = update.message.text

        date = context.user_data["new_task_deadline_date"]
        time = datetime.strptime(raw_time, "%H:%M").time()

        deadline = datetime.combine(
            date,
            time
        )

        if self._task_app is None:
            raise Exception("TGBOT: Uninitalized app")


        await self._task_app.add_task(
            name=context.user_data["new_task_name"],
            deadline = deadline,
            owner_id= update.effective_user.id
        )

        await update.message.reply_text(
            "Successfully added task!"
        )

        return ConvState.END


    async def add_task_cancel(self, update: Update, context: CustomContext):
        if update.message is None:
            raise Exception("Network Error")

        await update.message.reply_text(
            "Adding new task has been canceled"
        )

        return ConvState.END


    async def process_reminder_update(self, update: ReminderUpdate, context: CustomContext) -> None:
        task = update.reminded_task
        chat_id = task.owner_id
        now = update.time

        seconds_before_deadline = (task.deadline - now).total_seconds()
        min, sec = divmod(seconds_before_deadline, 60)

        message = f"Task {task.name} is due in {min} min {sec} sec"

        await context.bot.send_message(chat_id, message)


    async def put_reminder_in_queue(self, task: Task, now: datetime):
        # Put custom update in a queue
        await self._bot.update_queue.put(ReminderUpdate(task, now))