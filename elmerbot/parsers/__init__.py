from elmerbot.logs import build_logger


class ElmerParser(object):
    """Provides a base class for parsers to inherit.
    """
    name = None

    def __init__(self, registry):
        self._registry = registry
        self._logger = build_logger("{}-parser".format(self.name or "noname"))

    def check(self, contents):
        raise NotImplementedError

    async def handle(self, client, message):
        raise NotImplementedError
