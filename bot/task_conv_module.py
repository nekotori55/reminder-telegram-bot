from cmath import log, e
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
        bot.add_handler(CommandHandler("done", self._mark_task_as_done))

    async def _add_task(self, update: Update, context):
        if update.message is None:
            return None

        logger.info("User %s with id %s initiated task addition", update.effective_user.name,  # ty: ignore[unresolved-attribute]
                    update.effective_user.id)  # ty: ignore[unresolved-attribute]

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
            logger.info("User %s with id %s entered invalid new task name", update.effective_user.name,  # ty: ignore[unresolved-attribute]
                        update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Task name can not be empty")
            return ConvState.ADD_TASK_NAME

        context.user_data["new_task_name"] = update.message.text

        logger.info(
            "User %s with id %s entered new task name", update.effective_user.name,  # ty: ignore[unresolved-attribute]
            update.effective_user.id)  # ty: ignore[unresolved-attribute]
        await update.message.reply_text("Please, send the deadline date in format DD-MM-YYYY")
        return ConvState.ADD_TASK_DEADLINE_DATE

    async def _add_task_deadline_date(self, update: Update, context):
        if update.message is None or context.user_data is None:
            return None

        if update.message.text is None or len(update.message.text.strip()) == 0:
            logger.info("User %s with id %s entered invalid new task date", update.effective_user.name,  # ty: ignore[unresolved-attribute]
                        update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Please, send the deadline date in format DD-MM-YYYY, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_DATE

        try:
            parsed_date: date = datetime.strptime(update.message.text, "%d-%m-%Y").date()
        except ValueError:
            logger.info("User %s with id %s entered invalid new task date", update.effective_user.name,  # ty: ignore[unresolved-attribute]
                        update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Error. Incorrect format, please use DD-MM-YYYY format, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_DATE

        context.user_data["new_task_deadline_date"] = parsed_date
        logger.info(
            f"User %s with id %s entered new task date", update.effective_user.name,  # ty: ignore[unresolved-attribute]
            update.effective_user.id)  # ty: ignore[unresolved-attribute]
        await update.message.reply_text("Please, send the deadline time in format H:M")
        return ConvState.ADD_TASK_DEADLINE_TIME

    async def _add_task_deadline_time(self, update: Update, context):
        if update.message is None or context.user_data is None or update.effective_user is None:
            return None

        if update.message.text is None or len(update.message.text.strip()) == 0:
            logger.info("User %s with id %s entered invalid new task time", update.effective_user.name,
                        update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Please, send the deadline date in format H:M, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_TIME

        try:
            parsed_time: time = datetime.strptime(update.message.text, "%H:%M").time()
        except ValueError:
            logger.info("User %s with id %s entered invalid new task time", update.effective_user.name,
                        update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Error. Incorrect format, please use H:M format, or /cancel")
            return ConvState.ADD_TASK_DEADLINE_TIME

        parsed_date: date = context.user_data["new_task_deadline_date"]

        deadline = datetime.combine(
            parsed_date,
            parsed_time
        )

        logger.info(
            "User %s with id %s entered new task time", update.effective_user.name,
            update.effective_user.id)  # ty: ignore[unresolved-attribute]

        new_task_id = await self._task_app.add_task(
            name=context.user_data["new_task_name"],
            deadline=deadline,
            owner_id=update.effective_user.id
        )

        if new_task_id is None:
            logger.error(
                "User %s with id %s failed adding new task", update.effective_user.name,
                update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text("Unknown error adding the task")
            return None

        logger.info(
            "User %s with id %s successfully added new task with id %s", update.effective_user.name,
            update.effective_user.id, new_task_id)  # ty: ignore[unresolved-attribute]
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
            "User %s with id %s canceled adding new task", update.effective_user.name,
            update.effective_user.id)  # ty: ignore[unresolved-attribute]
        await update.message.reply_text("Adding new task has been canceled")
        return ConvState.END

    async def _list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None or context.user_data is None:
            return None

        logger.info(
            "User %s with id %s requested their task list", update.effective_user.name,  # ty: ignore[unresolved-attribute]
            update.effective_user.id)  # ty: ignore[unresolved-attribute]

        def task_to_str(task: Task) -> str:
            info = [
                "`ID:`", str(task.id),
                "`Name:`", task.name,
                "`Deadline:`", task.deadline.time().strftime("%H:%M"), task.deadline.date().strftime("%d-%m-%Y")
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
                "User %s with id %s used /start", update.effective_user.name,  # ty: ignore[unresolved-attribute]
                update.effective_user.id)  # ty: ignore[unresolved-attribute]
            await update.message.reply_text(
                "This is the simple reminder bot!\n"
                "To add a task use /add command.\n"
                "To list your tasks use /list command.\n"
                "The bot will remind you when the task is due in 15 minutes."
            )

    async def _mark_task_as_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None or update.message.text is None or update.effective_user is None:
            return None

        if context.args is None or len(context.args) == 0:
            logger.info("User %s with id %s failed marking task as done (entered wrong count (%s) of args)",
                        update.effective_user.name, update.effective_user.id, len(context.args))  # ty: ignore[invalid-argument-type]
            await update.message.reply_markdown_v2("Please enter task id after the command (`/done [task_id]`)")
            return None

        raw_id = context.args[0]

        try:
            task_id = int(raw_id)
        except ValueError:
            logger.info("User %s with id %s failed marking task as done (entered non-integer id [%s])",
                        update.effective_user.name, update.effective_user.id, raw_id)
            await update.message.reply_text("Error. Enter valid integer value")
            return None

        edited_task_id = await self._task_app.mark_task_as_done(task_id, update.effective_user.id)

        if edited_task_id is None:
            logger.info("User %s with id %s failed marking task %s as done (task_application denied operation)",
                        update.effective_user.name, update.effective_user.id, task_id)
            await update.message.reply_text("Error. Enter valid task id (see /list)")
            return None
        else:
            logger.info("User %s with id %s successfully marked task %s as done", update.effective_user.name,
                        update.effective_user.id, task_id)
            await update.message.reply_text(f"Success! Task {task_id} marked as done")
            return None