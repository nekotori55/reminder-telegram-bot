from core.application.task_application import TaskApplication
from datetime import datetime

from enum import IntEnum

from telegram import Update
from telegram.ext import ApplicationBuilder, Application, ConversationHandler, CommandHandler, MessageHandler, \
    ContextTypes, CallbackContext

from bot.telegram_module import TelegramModule
from core.domain.task import Task


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

    def __init__(self, bot: Application, task_app : TaskApplication):
        self._task_app = task_app

        add_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("add", self._add_task)
            ],  # ty: ignore[invalid-argument-type]
            states={
                ConvState.ADD_TASK_NAME: [
                    MessageHandler(None, self._add_task_name)
                ],
                ConvState.ADD_TASK_DEADLINE_DATE: [
                    MessageHandler(None, self._add_task_deadline_date)
                ],
                ConvState.ADD_TASK_DEADLINE_TIME: [
                    MessageHandler(None, self._add_task_deadline_time)
                ],
            },  # ty: ignore[invalid-argument-type]
            fallbacks=[CommandHandler("cancel", self._add_task_cancel)]  # ty: ignore[invalid-argument-type]
        )

        bot.add_handler(add_conv_handler)
        bot.add_handler(CommandHandler("start", self._start))
        bot.add_handler(CommandHandler("list", self._list_tasks))


    async def _add_task(self, update: Update, context):
        if update.message is None:
            raise Exception("Unknown owner_id")

        await update.message.reply_text(
            "Please, fill the info about the reminder"
        )
        await update.message.reply_text(
            "Enter the name of the new task or /cancel"
        )

        return ConvState.ADD_TASK_NAME

    async def _add_task_name(self, update: Update, context):
        if update.message is None or context.user_data is None:
            raise Exception("Network Error")

        context.user_data["new_task_name"] = update.message.text

        await update.message.reply_text(
            "Please, send the deadline date in format DD-MM-YYYY"
        )

        return ConvState.ADD_TASK_DEADLINE_DATE

    async def _add_task_deadline_date(self, update: Update, context):
        if update.message is None or context.user_data is None or update.message.text is None:
            raise Exception("Network Error")

        raw_date = update.message.text

        context.user_data["new_task_deadline_date"] = datetime.strptime(raw_date, "%d-%m-%Y").date()

        await update.message.reply_text(
            "Please, send the deadline time in format H:M"
        )

        return ConvState.ADD_TASK_DEADLINE_TIME

    async def _add_task_deadline_time(self, update: Update, context):
        if update.message is None or context.user_data is None or update.message.text is None or update.effective_user is None:
            raise Exception("Network Error")

        raw_time = update.message.text

        date = context.user_data["new_task_deadline_date"]
        time = datetime.strptime(raw_time, "%H:%M").time()

        deadline = datetime.combine(
            date,
            time
        )

        await self._task_app.add_task(
            name=context.user_data["new_task_name"],
            deadline=deadline,
            owner_id=update.effective_user.id
        )

        await update.message.reply_text(
            "Successfully added task!"
        )

        return ConvState.END

    async def _add_task_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None:
            raise Exception("Network Error")

        await update.message.reply_text(
            "Adding new task has been canceled"
        )

        return ConvState.END


    async def _list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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


    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is not None:
            await update.message.reply_text(
                "This is the simple reminder bot!\n"
                "To add a task use /add command.\n"
                "To list your tasks use /list command.\n"
                "The bot will remind you when the task is due in 15 minutes."
            )
