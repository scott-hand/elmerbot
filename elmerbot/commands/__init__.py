from elmerbot import RegisteredClass
from elmerbot.logs import build_logger


class ElmerCommand(object, metaclass=RegisteredClass):
    """Provides a base class for commands to inherit. Contains the following class variables:
    
    command - The command typed in chat to trigger the execution of this object.
    description - The text sent from the help command.
    """
    command = None
    description = None

    def __init__(self):
        self._logger = build_logger("{}-cmd".format(self.command or "noname"))

    async def handle(self, message, args):
        raise NotImplementedError

    @classmethod
    def find(cls, pattern):
        for command in cls.registry:
            if command.command == pattern:
                return command


# Load subclasses and register them
from elmerbot.commands.help import *
from elmerbot.commands.search import *
