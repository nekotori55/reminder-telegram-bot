from core.presentation.telegram_task_notificator import TelegramTaskNotificator
from bot.telegram_bot import TelegramBot
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

    tg_bot = TelegramBot(TOKEN)

    # Init application components
    repository = InMemoryTaskRepository()

    # notificator = PrintTaskNotificator()
    notificator = TelegramTaskNotificator(tg_bot)

    application = TaskApplication(task_repository=repository, notificator=notificator)

    await tg_bot.initialize(application)

    # Setup and start scheduler that calls callback every n seconds
    scheduler = Scheduler(5, application.process_reminders)
    scheduler.start()

    await tg_bot.run()

    await asyncio.Event().wait()

    await tg_bot.stop()

if __name__ == "__main__":
    asyncio.run(main())