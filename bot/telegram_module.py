from telegram.ext import ApplicationBuilder, Application
from abc import ABC, abstractmethod

# TODO dead weight?
class TelegramModule(ABC):
    @staticmethod
    @abstractmethod
    def attach_module_build_deps(builder : ApplicationBuilder) -> ApplicationBuilder: ...
