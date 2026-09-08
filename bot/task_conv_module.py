from cmath import log
import logging
from time import strptime
from core.application.task_application import TaskApplication
from datetime import datetime, date, time

from enum import IntEnum

from telegram import Update
from telegram.ext import ApplicationBuilder, Application, ConversationHandler, CommandHandler, MessageHandler, \
    ContextTypes, filters

from bot.telegram_module import TelegramModule
from core.domain.task import Task

logger = logging.getLogger(__name__)


class ConvState(IntEnum):
    ADD_TASK_NAME = 1
    ADD_TASK_DEADLINE_DATE = 2
    ADD_TASK_DEADLINE_TIME = 3
    ADD_TASK_FINISH = 4
    END = ConversationHandler.END


class TaskConvModule(TelegramModule):
    @staticmethod
    def attach_module_build_deps(builder: ApplicationBuilder) -> ApplicationBuilder:
        return builder

    def __init__(self, bot: Application, task_app: TaskApplication):
        self._task_app = task_app

        add_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("add", self._add_task)
            ],  # ty: ignore[invalid-argument-type]
            states={
                ConvState.ADD_TASK_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._add_task_name)
                ],
                ConvState.ADD_TASK_DEADLINE_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._add_task_deadline_date)
                ],
                ConvState.ADD_TASK_DEADLINE_TIME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._add_task_deadline_time)
                ],
            },  # ty: ignore[invalid-argument-type]
            fallbacks=[CommandHandler("cancel", self._add_task_cancel)]  # ty: ignore[invalid-argument-type]
        )

        bot.add_handler(add_conv_handler)
        bot.add_handler(CommandHandler("start", self._start))
        bot.add_handler(CommandHandler("list", self._list_tasks))

    async def _add_task(self, update: Update, context):
        if update.message is None:
            return None

        logger.info(f"User {update.effective_user.name} with id {update.effective_user.id} initiated task addition")  # ty: ignore[unresolved-attribute]

        await update.message.reply_text(
            "Please, fill the info about the reminder"
        )
        await update.message.reply_text(
            "Enter the name of the new task or /cancel"
        )

        return ConvState.ADD_TASK_NAME

    async def _add_task_name(self, update: Update, context):
        if update.message is None or context.user_data is None:
            return None

        if update.message.text is None or len(update.message.text.strip()) == 0:
            logger.info(f"User {update.effective_user.name} with id {update.effective_user.id} entered invalid new task name")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Task name can not be empty")
            return ConvState.ADD_TASK_NAME

        context.user_data["new_task_name"] = update.message.text

        logger.info(
            f"User {update.effective_user.name} with id {update.effective_user.id} entered new task name")  # ty: ignore[unresolved-attribute]
        await update.message.reply_text("Please, send the deadline date in format DD-MM-YYYY")
        return ConvState.ADD_TASK_DEADLINE_DATE

    async def _add_task_deadline_date(self, update: Update, context):
        if update.message is None or context.user_data is None:
            return None

        if update.message.text is None or len(update.message.text.strip()) == 0:
            logger.info(f"User {update.effective_user.name} with id {update.effective_user.id} entered invalid new task date")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Please, send the deadline date in format DD-MM-YYYY, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_DATE

        try:
            parsed_date: date = datetime.strptime(update.message.text, "%d-%m-%Y").date()
        except:
            logger.info(f"User {update.effective_user.name} with id {update.effective_user.id} entered invalid new task date")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Error. Incorrect format, please use DD-MM-YYYY format, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_DATE

        context.user_data["new_task_deadline_date"] = parsed_date
        logger.info(
            f"User {update.effective_user.name} with id {update.effective_user.id} entered new task date")  # ty: ignore[unresolved-attribute]
        await update.message.reply_text("Please, send the deadline time in format H:M")
        return ConvState.ADD_TASK_DEADLINE_TIME

    async def _add_task_deadline_time(self, update: Update, context):
        if update.message is None or context.user_data is None or update.effective_user is None:
            return None

        if update.message.text is None or len(update.message.text.strip()) == 0:
            logger.info(f"User {update.effective_user.name} with id {update.effective_user.id} entered invalid new task time")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Please, send the deadline date in format H:M, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_TIME

        try:
            parsed_time: time = datetime.strptime(update.message.text, "%H:%M").time()
        except:
            logger.info(f"User {update.effective_user.name} with id {update.effective_user.id} entered invalid new task time")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Error. Incorrect format, please use H:M format, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_TIME

        parsed_date: date = context.user_data["new_task_deadline_date"]

        deadline = datetime.combine(
            parsed_date,
            parsed_time
        )

        logger.info(
            f"User {update.effective_user.name} with id {update.effective_user.id} entered new task time")  # ty: ignore[unresolved-attribute]


        new_task_id = await self._task_app.add_task(
            name=context.user_data["new_task_name"],
            deadline=deadline,
            owner_id=update.effective_user.id
        )

        if new_task_id is None:
            logger.error(
                f"User {update.effective_user.name} with id {update.effective_user.id} failed adding new task")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Unknown error adding the task")
            return None

        logger.info(
            f"User {update.effective_user.name} with id {update.effective_user.id} successfully added new task with id {new_task_id}")  # ty: ignore[unresolved-attribute]
        await update.message.reply_text(
            "Successfully added task! Use /list to see"
        )

        return ConvState.END

    async def _add_task_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None or context.user_data is None or update.effective_user is None:
            return None

        context.user_data["new_task_name"] = None
        context.user_data["new_task_deadline_date"] = None

        logger.info(
            f"User {update.effective_user.name} with id {update.effective_user.id} canceled adding new task")  # ty: ignore[unresolved-attribute]
        await update.message.reply_text("Adding new task has been canceled")
        return ConvState.END

    async def _list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None or context.user_data is None:
            return None

        logger.info(
            f"User {update.effective_user.name} with id {update.effective_user.id} requested their task list")  # ty: ignore[unresolved-attribute]

        def task_to_str(task: Task) -> str:
            info = [
                "`ID:`", str(task.id),
                "`Name:`", task.name,
                "`Deadline:`", task.deadline.time().strftime("%H:%M"), task.deadline.date().strftime("%d-%d-%Y")
            ]
            return "\n".join(info)

        tasks = await self._task_app.get_non_due_tasks(update.effective_user.id)  # ty: ignore[unresolved-attribute]

        if len(tasks) == 0:
            await update.message.reply_text("You have no pending tasks! Good Job!")
            return None

        reply = '\n\n'.join(list(map(task_to_str, tasks)))
        await update.message.reply_markdown(text=reply)
        return None

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is not None:
            logger.info(
                f"User {update.effective_user.name} with id {update.effective_user.id} used /start")  # ty: ignore[unresolved-attribute]
            await update.message.reply_text(
                "This is the simple reminder bot!\n"
                "To add a task use /add command.\n"
                "To list your tasks use /list command.\n"
                "The bot will remind you when the task is due in 15 minutes."
            )
