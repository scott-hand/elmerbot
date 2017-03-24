from elmerbot.logs import build_logger


class ElmerCommand(object):
    """Provides a base class for commands to inherit. Contains the following class variables:
    
    command - The command typed in chat to trigger the execution of this object.
    description - The text sent from the help command.
    """
    command = None
    description = None

    def __init__(self, registry):
        self._registry = registry
        self._logger = build_logger("{}-cmd".format(self.command or "noname"))

    async def handle(self, message, args):
        raise NotImplementedError
