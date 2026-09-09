from telegram.error import InvalidToken
import logging

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

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def main():
    token_tg_file = os.getenv("TG_TOKEN_FILE")

    if token_tg_file is None or len(token_tg_file) == 0:
        logger.critical("TG_TOKEN_FILE environment variable is not configured")
        raise RuntimeError("TG_TOKEN_FILE environment variable is not configured")

    with open(token_tg_file, "r") as file:
        TOKEN = file.read().strip()

    logger.info("Initializing...")


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
    scheduler = Scheduler(120, application.process_reminders)

    try:
        # Start tg bots
        await tg_bot.initialize()

        logger.info("Initialized successfully... Starting...")
        await tg_bot.updater.start_polling()  # ty: ignore[unresolved-attribute]
        await tg_bot.start()

        # Start scheduler
        scheduler.start()

        await asyncio.Event().wait()
    except InvalidToken:
        logger.critical("Error! Invalid telegram TOKEN")
        raise
    finally:
        logger.info("Trying to shutdown gracefully...")

        await scheduler.stop()

        if tg_bot.running:
            await tg_bot.stop()

        if tg_bot.updater.running:  # ty: ignore[unresolved-attribute]
            await tg_bot.updater.stop()  # ty: ignore[unresolved-attribute]

        await tg_bot.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown by user (CTRL + C)")
    except Exception:
        logger.exception("Fatal error while running the bot")
        raise
