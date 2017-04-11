import asyncio
import discord
import random
import string
from elmerbot.commands import ElmerCommand
from elmerbot.logs import build_logger
from elmerbot.parsers import ElmerParser
from elmerbot.reviews import ReviewData


class ElmerBotClient(discord.Client):
    greeting = "Slàinte Mhath, "
    prefix = "!"

    def __init__(self, settings):
        self._settings = settings
        self.data = ReviewData()
        self._logger = build_logger("client")
        for command_obj in ElmerCommand.registry:
            self._logger.info(f"Registered command module: {type(command_obj).__name__}")
        for parser_obj in ElmerParser.registry:
            self._logger.info(f"Registered parser module: {type(parser_obj).__name__}")
        super(ElmerBotClient, self).__init__()

    def run(self):
        super(ElmerBotClient, self).run(self._settings.get("token", ""))

    async def on_ready(self):
        self._logger.info("Logged in as {} {}".format(self.user.name, self.user.id))

    async def on_member_join(self, member):
        await self.send_message(member.server.default_channel, "{}, {}!".format(self.greeting, member.mention))

    async def on_message(self, message):
        if not message.server or not message.channel:
            return

        # Prevent bot answering itself
        myself = [m for m in message.server.members if m.id == self.user.id][0]
        if  message.author == myself:
            return

        # Check all parsers
        for parser in ElmerParser.registry:
            if parser.check(message.content):
                await parser.handle(self, message)

        # Validate against prefix
        if not message.content.lower().startswith(self.prefix):
            return

        # Just for a while to ease the transition
        if message.content.startswith("!elmer"):
            await self.send_message(message.channel, "I've been tweaked to use **!** instead of **!elmer** now.")
            return

        # Parse out command and check against all commands
        contents = message.content[len(self.prefix):]
        command, _, args = contents.strip().partition(" ")
        handler = ElmerCommand.find(command)
        if handler:
            await handler.handle(self, message, args)
