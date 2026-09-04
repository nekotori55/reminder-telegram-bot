import datetime

from application.task_notificator import TaskNotificator
from domain.task import Task


class PrintTaskNotificator(TaskNotificator):
    async def send_reminder(self, task: Task, now : datetime.datetime):
        print("reminding...")
        seconds_before_deadline = (task.deadline - now).total_seconds()
        min,sec = divmod(seconds_before_deadline, 60)
        print("Task [", task.name, "] due in", int(min), "minutes,", int(sec), "seconds" )

