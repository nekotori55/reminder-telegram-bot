from datetime import datetime
from enum import Enum


class Task:
    class Status(Enum):
        NOT_DONE = 0
        DONE = 1

    def __init__(self, id : int, owner_id : int, name : str, deadline : datetime):
        self._id = id
        self._owner_id = owner_id
        self.status = Task.Status.NOT_DONE
        self.name : str = name
        self.deadline : datetime = deadline
        self.last_notified_at : datetime | None = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def status(self) -> Task.Status:
        return self._status

    @status.setter
    def status(self, new_status : Task.Status):
        if new_status is None:
            raise ValueError("Status cannot be null")

        self._status = new_status

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name : str):
        if new_name is None:
            raise ValueError("Name must not be null")

        if not new_name:
            raise ValueError("Name must not be empty")

        self._name = new_name


    @property
    def deadline(self) -> datetime:
        return self._deadline

    @deadline.setter
    def deadline(self, new_deadline : datetime):
        if new_deadline is None:
            raise ValueError("Deadline must not be None")

        self._deadline = new_deadline


    @property
    def owner_id(self) -> int:
        return self._owner_id


    @property
    def last_notified_at(self) -> datetime | None:
        return self._last_notified_at

    @last_notified_at.setter
    def last_notified_at(self, time : datetime):
        self._last_notified_at = time