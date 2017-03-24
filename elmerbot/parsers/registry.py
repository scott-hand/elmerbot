import importlib
from elmerbot.logs import build_logger


class ParserRegistry(object):
    """Imports and stores parser modules
    """
    def __init__(self):
        self.parsers = []

    def register(self, parser):
        self.parsers.append(parser)

    @classmethod
    def build(cls):
        to_load = {"currency": ["CurrencyParser"]}
        registry = ParserRegistry()
        logger = build_logger("parser-registry")

        for modname, classnames in to_load.items():
            module = importlib.import_module("elmerbot.parsers.{}".format(modname))
            for classname in classnames:
                cmdclass = getattr(module, classname)
                registry.register(cmdclass(registry)) 
                logger.info("Registered parser module: {}.{}".format(modname, classname))
        cls._instance = registry
        return registry
