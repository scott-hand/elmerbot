import importlib


class CommandRegistry(object):
    """Imports and stores commands
    """
    def __init__(self):
        self.commands = []

    def register(self, command):
        self.commands.append(command)

    def find(self, pattern):
        for command in self.commands:
            if pattern == command.command:
                return command

    @classmethod
    def build(cls):
        to_load = {"search": ["SearchCommand", "InfoCommand"],
                   "help": ["HelpCommand"]}
        registry = CommandRegistry()

        for modname, classnames in to_load.items():
            module = importlib.import_module("elmerbot.commands.{}".format(modname))
            for classname in classnames:
                cmdclass = getattr(module, classname)
                registry.register(cmdclass(registry)) 
                print("Registered command module: {}.{}".format(modname, classname))
        cls._instance = registry
        return registry
