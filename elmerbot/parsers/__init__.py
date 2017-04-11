from elmerbot import RegisteredClass
from elmerbot.logs import build_logger


class ElmerParser(object, metaclass=RegisteredClass):
    """Provides a base class for parsers to inherit.
    """
    name = None

    def __init__(self):
        self._logger = build_logger("{}-parser".format(self.name or "noname"))

    def check(self, contents):
        raise NotImplementedError

    async def handle(self, client, message):
        raise NotImplementedError


# Load subclasses and register them
from elmerbot.parsers.currency import *
