import configargparse
import logging
import praw
import requests
import time
import traceback
from collections import defaultdict
from datetime import datetime
from elmerbot.logs import configure_logger
from prawcore.exceptions import RequestException, ResponseException, OAuthException


# Keeping version separate from the package version because it should only matter for changes to this module and is
# important because of its use in the praw user agent
FEED_NAME = "elmerdiscord"
FEED_VERSION = "2.0.0"
USER_AGENT = f"python:{FEED_NAME}:{FEED_VERSION}"
default_subs = ["bourbon", "scotch", "worldwhisky"]


class ReviewFeed(object):
    def __init__(self, subreddits, user, webhook, delay):
        self._logger = logging.getLogger("reviewfeed.worker")
        self._history = defaultdict(dict)
        self._user = user
        self._delay = delay
        self._webhook_url = webhook
        self._subreddits = subreddits
        self._reddit = None
        self._refresh_reddit_client()

    def start(self):
        try:
            while True:
                start = time.time()
                self._check_submissions()
                # Try to only run this once a minute
                cooldown = max(0, 60 - (time.time() - start))
                self._logger.debug(f"Sleeping {cooldown:.2f} seconds")
                time.sleep(cooldown)
        except KeyboardInterrupt:
            self._logger.warning("Exiting due to interrupt received")

    def _handle_submission(self, submission):
        human_time = datetime.utcfromtimestamp(submission.created_utc).strftime("%Y-%m-%d %H:%M")
        self._logger.info(f"Handling submission {submission.id} \"{submission.title}\" ({human_time})")
        embed = {"title": submission.title,
                 "url": f"https://www.reddit.com{submission.permalink}",
                 "description": (f"**u/{submission.author.name}** posted a review to "
                                 f"**r/{submission.subreddit.display_name}**"),
                 "thumbnail": {"url": submission.thumbnail}}
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
            posted = True
            body = review_comment.body if len(review_comment.body) <= 400 else review_comment.body[:400] + "..."
            embed["description"] += ":\n\n" + body
        response = requests.post(self._webhook_url, json={"embeds": [embed]})
        self._logger.info(f"Submitted and got code {response.status_code} and body: {response.content.decode()}")
        if response.status_code != 204:
            print(embed)

    def _check_submissions(self):
        self._logger.debug("Checking submissions")
        start = time.time()
        try:
            for sub in self._subreddits:
                seen = set()
                for submission in self._reddit.subreddit(sub).new(limit=20):
                    seen.add(submission.id)
                    if start - submission.created_utc > 10000:
                        # Skip really old ones on the first run
                        continue
                    if submission.id not in self._history[sub]:
                        if start - submission.created_utc < self._delay:
                            self._logger.debug(f"Skipping \"{submission.title}\" as too new")
                        else:
                            if "review" not in submission.title.lower():
                                self._logger.info(f"Skipping \"{submission.title}\" as not likely being a review")
                            else:
                                self._handle_submission(submission)
                            self._logger.debug(f"Added {submission.id} to history.")
                            self._history[sub][submission.id] = start
                # Now prune everything from history that wasn't seen (replaced by newer ones)
                history_submissions = set(self._history[sub].keys())
                for submission in history_submissions - seen:
                    self._history[sub].pop(submission)
                    self._logger.debug(f"Removed {submission} from history.")
        except RequestException as re:
            # PRAW routinely experiences problems and stops working. Refresh our session when this happens.
            self._logger.error(f"Error encountered during submission check: {re}")
            self._refresh_reddit_client()
            time.sleep(1)
        except Exception as e:
            self._logger.error(f"Unknown exception: {e}")
            traceback.print_exc()

    def _refresh_reddit_client(self):
        try:
            self._reddit = praw.Reddit(self._user, check_for_updates=False, user_agent=USER_AGENT)
            self._logger.info(f"Reconnected to reddit as {self._reddit.user.me().name}")
        except ResponseException:
            self._logger.error("Application ID or secret not recognized")
            raise
        except OAuthException:
            self._logger.error("Login failed")
            raise


def main():
    parser = configargparse.ArgumentParser(description="Starts a script to post reddit reviews to Discord",
                                           default_config_files=["reviewfeed.cfg"],
                                           auto_env_var_prefix="reviewfeed_")
    parser.add("-c", "--config", is_config_file=True, help="Config path if not reviewfeed.cfg")
    parser.add("-d", "--delay", help="Delay in seconds to wait for user to post comment", type=int, default=300)
    parser.add("-u", "--user", help="praw.ini section if not default", default="default")
    parser.add("-s", "--subreddits", help="Extra subs to include", action="append", default=default_subs)
    parser.add("-v", "--verbose", help="Show verbose information.", action="store_true")
    parser.add("-w", "--webhook", help="Webhook URL", required=True)
    args = parser.parse_args()
    
    configure_logger("reviewfeed", logging.DEBUG if args.verbose else logging.INFO)
    logger = logging.getLogger("reviewfeed.main")
    logger.info(f"Starting review feed to: {args.webhook}")
    logger.info(f"Using user agent: {USER_AGENT}")
    logger.info(f"Subreddits being monitored: {', '.join(args.subreddits)}")

    try:
        feed = ReviewFeed(list(set(args.subreddits)), args.user, args.webhook, args.delay)
        feed.start()
    except Exception as e:
        logger.error(f"Terminating due to exception")
        if args.verbose:
            traceback.print_exc()


if __name__ == "__main__":
    main()
