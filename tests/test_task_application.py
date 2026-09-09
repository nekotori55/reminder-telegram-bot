from core.application.task_notificator import TaskNotificator
from datetime import datetime, timedelta

from core.application.task_repository import TaskRepository
from core.application.task_application import TaskApplication
import pytest

from core.domain.task import Task


class FakeTaskRepository(TaskRepository):
    def __init__(self):
        self.added_tasks : list[Task] = []
        self.updated_tasks : list[Task] = []
        self.last_filter = None
        self._id_counter = 1

    async def get_tasks(self, filters: TaskRepository.Filter) -> list[Task]:
        self.last_filter = filters
        return self.added_tasks

    async def get_task(self, id: int) -> Task | None:
        return next((task for task in self.added_tasks if task.id == id), None)

    async def update_task(self, task: Task) -> bool:
        self.updated_tasks.append(task)
        return True

    async def add_task(self, name: str, deadline: datetime, owner_id: int) -> int | None:
        new_task = Task(self._id_counter, owner_id, name, deadline)
        self._id_counter += 1
        self.added_tasks.append(new_task)
        return new_task.id


class FakeTaskNotificator(TaskNotificator):
    def __init__(self):
        self.sent_tasks : list[Task] = []

    async def send_reminder(self, task: Task, now: datetime):
        self.sent_tasks.append(task)


@pytest.mark.asyncio
async def test_add_task():
    repo = FakeTaskRepository()
    notificator = FakeTaskNotificator()

    fake_now = datetime(2026, 9, 9, 15, 55)
    non_due_deadline = datetime(2026, 9, 9, 16, 55)
    due_deadline = datetime(2026, 9, 9, 14, 55)

    task_app : TaskApplication = TaskApplication(repo, notificator, lambda: fake_now)

    assert len(repo.added_tasks) == 0

    new_id = await task_app.add_task("Amogus", due_deadline, 1337)
    assert new_id is None
    assert len(repo.added_tasks) == 0

    new_id = await task_app.add_task("Amogus", non_due_deadline, 1337)
    assert new_id == 1
    assert len(repo.added_tasks) == 1


@pytest.mark.asyncio
async def test_mark_task_as_done():
    repo = FakeTaskRepository()
    notificator = FakeTaskNotificator()


    task_app : TaskApplication = TaskApplication(repo, notificator)

    repo.added_tasks.append(
        Task(1, 1337, "Amogus", datetime(2026, 9, 9, 16,55))
    )

    fail_result = await task_app.mark_task_as_done(1, 10)
    assert fail_result is None
    assert len(repo.updated_tasks) == 0

    succ_result = await task_app.mark_task_as_done(1, 1337)
    assert succ_result == 1
    assert len(repo.updated_tasks) == 1
    assert repo.updated_tasks[0].status == Task.Status.DONE



@pytest.mark.asyncio
async def test_get_non_due_tasks():
    repo = FakeTaskRepository()
    notificator = FakeTaskNotificator()

    fake_now = datetime(2026, 9, 9, 15, 55)

    task_app : TaskApplication = TaskApplication(repo, notificator, lambda: fake_now)

    await task_app.get_non_due_tasks(133)

    used_filter = repo.last_filter
    assert used_filter is not None

    uf : TaskRepository.Filter = used_filter
    assert uf.owner_id == 133
    assert uf.status is Task.Status.NOT_DONE
    assert uf.deadline_after == fake_now

    assert uf.was_reminded_about is None
    assert uf.deadline_before is None



@pytest.mark.asyncio
async def test_reminders():
    repo = FakeTaskRepository()
    notificator = FakeTaskNotificator()

    fake_now = datetime(2026, 9, 9, 18, 00)
    deadline = datetime(2026, 9, 9, 18, 15)

    task_app: TaskApplication = TaskApplication(repo, notificator, lambda: fake_now)

    mytask = Task(0,12,"testask", deadline)
    repo.added_tasks.append(mytask)

    await task_app.process_reminders()

    used_filter = repo.last_filter
    assert used_filter is not None

    uf : TaskRepository.Filter = used_filter
    assert uf.owner_id is None
    assert uf.status == Task.Status.NOT_DONE
    assert uf.deadline_after == fake_now
    assert uf.deadline_before == fake_now + timedelta(minutes=15)
    assert uf.was_reminded_about is False

    # assuming every task matches this filter (due to dumb repo returning all tasks)
    assert len(notificator.sent_tasks) == 1
    assert notificator.sent_tasks[0].last_notified_at == fake_now
    assert len(repo.updated_tasks) == 1
    assert repo.updated_tasks[0].last_notified_at == fake_now
    assert repo.updated_tasks[0] == mytask