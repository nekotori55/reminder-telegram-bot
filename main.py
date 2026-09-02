from datetime import datetime, timedelta
import asyncio
from application.scheduler import Scheduler
from application.taskapplication import TaskApplication
from application.print_notificator import PrintNotificator
from domain.task import Task
from repository.mock_task_repository import MockTaskRepository


async def main():
    print("main executed")

    test_tasks: list[Task] = [
        Task(0, 0, "Do dishes", datetime.now() + timedelta(minutes=20))
    ]

    repository = MockTaskRepository(test_tasks)
    notificator = PrintNotificator()
    application = TaskApplication(task_repository=repository, notificator=notificator)

    scheduler = Scheduler(5, application.process_reminders)
    scheduler.start()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())