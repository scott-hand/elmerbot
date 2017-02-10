import asyncio
import discord
import praw
import time


class RedditFeed(object):
    subreddits = ["bourbon", "scotch", "worldwhisky"]

    def __init__(self, client):
        self._reddit = praw.Reddit("default", check_for_updates=False, user_agent="python:elmerdiscord:v1.0.0")
        self._last = time.time()
        self._client = client
        self._channels = []

    def add_channel(self, channel):
        self._channels.append(channel)

    async def _handle_submission(self, submission):
        # Sleep for 5 minutes to give OP time to make the review comment
        print("Handling {}".format(submission.title))
        await asyncio.sleep(300.0)
        output = []
        output.append("https://www.reddit.com{}\n".format(submission.permalink))
        # Search for oldest comment from author. There should be a way to do this directly with PRAW, but I don't see
        # it, so just doing a linear search for now...
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

    async def _check_submissions(self):
        for sub in self.subreddits:
            for submission in self._reddit.subreddit(sub).new(limit=20):
                if submission.created_utc > self._last and "review" in submission.title.lower():
                    asyncio.ensure_future(self._handle_submission(submission))
        self._last = time.time()

    async def monitor(self):
        while True:
            await self._check_submissions()
            await asyncio.sleep(10)
