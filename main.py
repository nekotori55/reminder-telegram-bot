from bot.task_notify_module import TaskNotifyModule
from bot.task_conv_module import TaskConvModule
from telegram.ext import Application

from core.presentation.telegram_task_notificator import TelegramTaskNotificator
from dotenv import load_dotenv
import os
import asyncio
from util.scheduler import Scheduler
from core.application.task_application import TaskApplication
from core.data.inmemory_task_repository import InMemoryTaskRepository



async def main():
    load_dotenv()
    TOKEN = os.getenv("TOKEN")

    if TOKEN is None or len(TOKEN) == 0:
        raise EnvironmentError("TOKEN environment variable is empty")


    # pass builders through modules to attach their build configuration
    bot_builder = Application.builder().token(TOKEN)
    bot_builder = TaskConvModule.attach_module_build_deps(bot_builder)
    bot_builder = TaskNotifyModule.attach_module_build_deps(bot_builder)

    # then build resulting tg bot
    tg_bot = bot_builder.build()

    # attach notify module
    tg_bot_task_notify_module = TaskNotifyModule(tg_bot)

    # build a notificator using notify module
    notificator = TelegramTaskNotificator(telegram_bot=tg_bot_task_notify_module)
    # notificator = PrintTaskNotificator()

    # init data storage
    repository = InMemoryTaskRepository()

    # create task application
    application = TaskApplication(task_repository=repository, notificator=notificator)

    # attach task_conv tg module, needs task application ref so attaching after app creation
    tg_bot_task_conv_module = TaskConvModule(bot=tg_bot, task_app=application)

    # Setup and start scheduler that calls callback every n seconds
    # that checks if some tasks need to be notified about
    scheduler = Scheduler(5, application.process_reminders)


    # Start tg bot
    await tg_bot.initialize()
    await tg_bot.updater.start_polling()  # ty: ignore[unresolved-attribute]
    await tg_bot.start()

    # Start scheduler
    scheduler.start()

    # TODO gracefully shutdown
    await asyncio.Event().wait()

    await scheduler.stop()
    await tg_bot.stop()


if __name__ == "__main__":
    asyncio.run(main())