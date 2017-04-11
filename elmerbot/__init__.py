__version__ = "1.0.0"
PLATFORM = "linux"
BOTNAME = "elmerbot"


class RegisteredClass(type):
    def __init__(cls, name, bases, nmspc):
        super(RegisteredClass, cls).__init__(name, bases, nmspc)
        if not hasattr(cls, "clsregistry"):
            cls.clsregistry = set()
        cls.clsregistry.add(cls)
        cls.clsregistry -= set(bases)

    @property
    def registry(cls):
        if not hasattr(cls, "_registry"):
            cls._registry = {t() for t in cls.clsregistry}
        return cls._registry
