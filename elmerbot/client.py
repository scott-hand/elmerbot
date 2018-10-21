import argparse
import discord
import logging
import yaml
from elmerbot.antispam import check_name
from elmerbot.commands import ElmerCommand
from elmerbot.logs import configure_logger
from elmerbot.parsers import ElmerParser
from elmerbot.reviews import ReviewData


class ElmerBotClient(discord.Client):
    greeting = "Slàinte Mhath"
    prefix = "!"

    def __init__(self, settings):
        self._settings = settings
        self.data = ReviewData()
        self._greeting_channel = None
        self._logger = logging.getLogger("elmerbot.client")
        for command_obj in ElmerCommand.registry:
            self._logger.info(f"Registered command module: {type(command_obj).__name__}")
        for parser_obj in ElmerParser.registry:
            self._logger.info(f"Registered parser module: {type(parser_obj).__name__}")
        super(ElmerBotClient, self).__init__()

    def run(self):
        super(ElmerBotClient, self).run(self._settings.get("token", ""))

    async def on_ready(self):
        self._logger.info("Logged in as {} {}".format(self.user.name, self.user.id))
        if "greeting_room_id" in self._settings:
            self._greeting_channel = self.get_channel(str(self._settings["greeting_room_id"]))
            self._logger.info(f"Greeting channel: {self._greeting_channel}")

    async def on_member_join(self, member):
        if "appeal_server_id" in self._settings:
            msg = ("You are being banned because your name matched a spam filter. If this "
                  "was done in error and you would like to request to be unbanned, please "
                  f"join our ban appeal server at https://discord.gg/{self._settings['appeal_server_id']}")
        else:
            msg = ("You are being banned because your name matched a spam filter. If this was done in error, please "
                  "rejoin from another IP with a username not containing any promotional information and speak with a "
                  "moderator.")
        if check_name(member.name):
            await self.send_message(member, msg)
            await self.ban(member)
        if self._greeting_channel:
            await self.send_message(self._greeting_channel, "{}, {}!".format(self.greeting, member.mention))

    async def on_member_update(self, before, after):
        if check_name(after.name):
            await self.send_message(after, msg)
            await self.ban(after)

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


def main():
    parser = argparse.ArgumentParser(description="Starts elmerbot client")
    parser.add_argument("-e", "--env", help="production or development (Default: development)", default="development")
    parser.add_argument("-s", "--settings", help="YAML file with settings", default="settings.yaml")
    args = parser.parse_args()
    settings = yaml.load(open(args.settings))
    configure_logger("elmerbot", logging.INFO)
    logger = logging.getLogger("elmerbot.main")
    logger.info("Starting bot...")
    client = ElmerBotClient(settings[args.env])
    client.run()
    logger.info("Exiting...")


if __name__ == "__main__":
    main()
