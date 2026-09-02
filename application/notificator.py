from datetime import datetime
from abc import ABC, abstractmethod

from domain.task import Task

class Notificator(ABC):
    @abstractmethod
    def send_reminder(self, task : Task, now : datetime): ...
