import asyncio
import discord
import random
import string
from elmerbot.reviews import ReviewData
from elmerbot.commands.registry import CommandRegistry


class ElmerClient(discord.Client):
    greeting = "Slàinte Mhath, "
    prefix = "!elmer"

    def __init__(self, settings):
        self._settings = settings
        self.data = ReviewData()
        self.registry = CommandRegistry.build()
        super(ElmerClient, self).__init__()

    def run(self):
        super(ElmerClient, self).run(self._settings.get("token", ""))

    async def on_ready(self):
        print("Logged in as {} {}".format(self.user.name, self.user.id))

    async def on_member_join(self, member):
        await self.send_message(member.server.default_channel, "{}, {}!".format(self.greeting, member.mention))

    async def on_message(self, message):
        if not message.server or not message.channel:
            return
        myself = [m for m in message.server.members if m.id == self.user.id][0]
        if not message.author == myself or message.content.startswith(self.prefix):
            return

        contents = message.content.split(" ", 1)[1]
        command, _, args = contents.strip().partition(" ")
        handler = self.registry.find(command)
        if handler:
            await handler.handle(self, message, args)
