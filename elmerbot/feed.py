import asyncio
import discord
import praw
import time
import traceback
from elmerbot.logs import build_logger
from prawcore.exceptions import RequestException


class RedditFeed(object):
    subreddits = ["bourbon", "scotch", "worldwhisky"]

    def __init__(self, client):
        self._reddit = None
        self._refresh_reddit_client()
        self._last = time.time()
        self._client = client
        self._channels = []
        self._logger = build_logger("reddit")

    def add_channel(self, channel):
        self._channels.append(channel)

    def _refresh_reddit_client(self):
        self._reddit = praw.Reddit("default", check_for_updates=False, user_agent="python:elmerdiscord:v1.0.0")

    async def _handle_submission(self, submission):
        # Sleep for 5 minutes to give OP time to make the review comment
        try:
            self._logger.info("Handling {}".format(submission.title))
            await asyncio.sleep(300.0)
            output = []
            output.append("https://www.reddit.com{}\n".format(submission.permalink))
            # Search for oldest comment from author. There should be a way to do this directly with PRAW, but I don't
            # see it, so just doing a linear search for now...
            submission.comments.replace_more(limit=0)
            oldest = None
            review_comment = None
            for comment in submission.comments.list():
                if comment.author == submission.author:
                    if not oldest or comment.created < oldest:
                        oldest = comment.created
                        review_comment = comment
            if review_comment:
                blurb = review_comment.body if len(review_comment.body) <= 400 else review_comment.body[:400] + "..."
                output.append(blurb)

            em = discord.Embed(title="**New Review from u/{}: {}**".format(submission.author.name, submission.title),
                               description="\n".join(output),
                               colour=0x00DD00)
            em.set_thumbnail(url=submission.url)

            for channel in self._channels:
                await self._client.send_message(channel, embed=em)
        except Exception as e:
            self._logger.error("Got exception: {}".format(e))
            await asyncio.sleep(0)

    async def _check_submissions(self):
        self._logger.info("Checking reddit submissions...")
        try:
            for sub in self.subreddits:
                for submission in self._reddit.subreddit(sub).new(limit=20):
                    if submission.created_utc > self._last and "review" in submission.title.lower():
                        asyncio.ensure_future(self._handle_submission(submission))
            self._last = time.time()
        except RequestException as e:
            # For some reason, PRAW just craps out eventually and stops working. Refresh our session so that hopefully
            # it will work next time...
            self._logger.error("Error encountered during submission check: {}".format(e))
            self._refresh_reddit_client()
            await asyncio.sleep(1)
        except Exception as exc:
            # Take note and handle next time
            self._logger.error("Unknown exception: {}".format(exc))
            traceback.print_exc()

    async def monitor(self):
        while True:
            await self._check_submissions()
            await asyncio.sleep(30)