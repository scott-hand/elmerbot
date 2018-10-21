import logging
import re


invite_pattern = re.compile(r"discord\.gg/\w{3}")
tag_pattern = re.compile(r"add.*tag.*\d{4}")
twitch_pattern = re.compile(r"twitch\.tv")
twitter_pattern = re.compile(r"twitter\.com")
debugging_pattern = re.compile(r"elmerbot_spam_name_debugging")
name_patterns = [invite_pattern, tag_pattern, twitch_pattern, twitter_pattern, debugging_pattern]


def check_name(name):
    """This aims to catch a few common types of spammers.
    Right now it includes:
    @discord.gg/abcdefg
    @pls add blahblah (tag) 1234
    """
    logger = logging.getLogger("elmerbot.namecheck")
    for pattern in name_patterns:
        if pattern.search(name):
            logger.warn(f"Found spammer with name \"{name}\" using pattern \"{pattern.pattern}\"")
            return True
    return False
