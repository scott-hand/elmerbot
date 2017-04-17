import asyncio
import discord
import random
import string
from elmerbot.feed import RedditFeed
from elmerbot.logs import build_logger


class ElmerRedditClient(discord.Client):
    review_room = "reviews"

    def __init__(self, settings):
        self._settings = settings
        self._logger = build_logger("reviews")
        super(ElmerRedditClient, self).__init__()

    def run(self):
        super(ElmerRedditClient, self).run(self._settings.get("token", ""))

    async def on_ready(self):
        self._logger.info("Logged in as {} {}".format(self.user.name, self.user.id))
        self.feed = RedditFeed(self)
        self.feed.add_channel(discord.utils.get(self.get_all_channels(), name=self.review_room))
        self.loop.create_task(self.feed.monitor())
