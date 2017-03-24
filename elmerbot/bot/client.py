import asyncio
import discord
import random
import string
from elmerbot.commands.registry import CommandRegistry
from elmerbot.logs import build_logger
from elmerbot.reviews import ReviewData


class ElmerBotClient(discord.Client):
    greeting = "Slàinte Mhath, "
    prefix = "!"

    def __init__(self, settings):
        self._settings = settings
        self.data = ReviewData()
        self.registry = CommandRegistry.build()
        self._logger = build_logger("client")
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
        myself = [m for m in message.server.members if m.id == self.user.id][0]
        if  message.author == myself or not message.content.lower().startswith(self.prefix):
            return

        # Just for a while to ease the transition
        if message.content.startswith("!elmer"):
            await self.send_message(message.channel, "I've been tweaked to use **!** instead of **!elmer** now.")
            return

        contents = message.content[len(self.prefix):]
        command, _, args = contents.strip().partition(" ")
        handler = self.registry.find(command)
        if handler:
            await handler.handle(self, message, args)
