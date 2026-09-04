import asyncio
from typing import Callable, Awaitable, Any

# TODO make it wait not for N seconds, but run every N real seconds
class Scheduler:
    def __init__(self, period_seconds : int, callback : Callable[[], Awaitable[None]]):
        self._period_seconds = period_seconds
        self._callback : Callable[[], Awaitable[None]] = callback
        self._enabled : bool = False
        self._timer_task : asyncio.Task | None = None


    def start(self):
       self._enabled = True
       print("starting scheduling")

       self._timer_task = asyncio.create_task(self._timer_func())


    def stop(self):
        print("stopping scheduling")

        self._enabled = False
        if self._timer_task is not None:
           self._timer_task.cancel()


    async def _timer_func(self):
        while self._enabled:
            await self._callback()
            await asyncio.sleep(self._period_seconds)
