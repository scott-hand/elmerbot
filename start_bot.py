import argparse
import json
import sys
import yaml
from elmerbot.logs import build_logger
from elmerbot.bot.client import ElmerBotClient
from elmerbot.reddit.client import ElmerRedditClient


def main():
    parser = argparse.ArgumentParser(description="Starts elmerbot client")
    parser.add_argument("mode", help="Which mode to start (bot or reddit)")
    parser.add_argument("-e", "--env", help="production or development (Default: development)", default="development")
    parser.add_argument("-s", "--settings", help="YAML file with settings", default="settings.yaml")
    args = parser.parse_args()
    settings = yaml.load(open(args.settings))
    logger = build_logger("application")
    logger.info("Starting bot...")
    if args.mode == "bot":
        client = ElmerBotClient(settings[args.env])
    elif args.mode == "reddit":
        client = ElmerRedditClient(settings[args.env])
    else:
        logger.error(f"Mode \"{args.mode}\" not recognized.")
        return
    client.run()
    logger.info("Exiting...")


if __name__ == "__main__":
    main()
