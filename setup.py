"""Setup script for elmerbot.
"""
from setuptools import setup
from codecs import open
from os import path

VERSION = "2.0.0"
DESCRIPTION = "Whisky review helper bot for discord"

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as filein:
    long_description = filein.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as filein:
    requirements = [line.strip() for line in filein.readlines()]

setup(
    name="elmerbot",
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    author="Scott Hand",
    classifiers=["Development Status :: 5 - Production/Stable",
                 "Intended Audience :: Developers",
                 "Programming Language :: Python :: 3.6"],
    packages=["elmerbot", "elmerbot.bot", "elmerbot.commands", "elmerbot.parsers"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "elmerbot=elmerbot.box.client:main",
            "elmerfeed=elmerbot.feed:main"
        ]
    }
)
