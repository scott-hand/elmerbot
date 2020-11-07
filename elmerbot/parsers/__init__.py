import logging
from elmerbot import RegisteredClass


class ElmerParser(object, metaclass=RegisteredClass):
    """Provides a base class for parsers to inherit."""

    name = None
    enabled = False

    def __init__(self):
        self._logger = logging.getLogger("elmerbot.{}-parser".format(self.name or "noname"))

    def check(self, contents):
        raise NotImplementedError

    async def handle(self, client, message):
        raise NotImplementedError


# Load subclasses and register them
# 6 Nov 2020 - Removing this for now until I have time to find a working API
from elmerbot.parsers.currency import *
