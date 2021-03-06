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
        self._newuser_role = None
        self._logger = logging.getLogger("elmerbot.client")
        for command_obj in ElmerCommand.registry:
            self._logger.info(f"Registered command module: {type(command_obj).__name__}")
        for parser_obj in ElmerParser.registry:
            self._logger.info(f"Registered parser module: {type(parser_obj).__name__}")
        super(ElmerBotClient, self).__init__(intents=discord.Intents.all())

    def run(self):
        super(ElmerBotClient, self).run(self._settings.get("token", ""))

    async def on_ready(self):
        self._logger.info("Logged in as {} {}".format(self.user.name, self.user.id))
        if "greeting_room_id" in self._settings:
            self._greeting_channel = self.get_channel(self._settings["greeting_room_id"])
            self._logger.info(f"Greeting channel: {self._greeting_channel}")
            if "newuser_role_id" in self._settings:
                for role in self._greeting_channel.guild.roles:
                    if role.id == self._settings["newuser_role_id"]:
                        self._newuser_role = role
                        self._logger.info(f"New user role: {role.name} (#{role.id})")
                if self._newuser_role is None:
                    self._logger.warning("New user role not found")

    async def on_member_join(self, member):
        if "appeal_server_id" in self._settings:
            msg = (
                "You are being banned because your name matched a spam filter. If this "
                "was done in error and you would like to request to be unbanned, please "
                f"join our ban appeal server at https://discord.gg/{self._settings['appeal_server_id']}"
            )
        else:
            msg = (
                "You are being banned because your name matched a spam filter. If this was done in error, please "
                "rejoin from another IP with a username not containing any promotional information and speak with a "
                "moderator."
            )
        if check_name(member.name):
            await member.send(msg)
            await member.ban()
        if self._greeting_channel:
            await self._greeting_channel.send("{}, {}!".format(self.greeting, member.mention))
        if self._newuser_role:
            await member.add_roles(self._newuser_role)

    async def on_member_update(self, before, after):
        if check_name(after.name):
            await after.send(msg)
            await after.ban()

    async def on_message(self, message):
        if not message.guild or not message.channel:
            return

        # Prevent bot answering itself
        myself = [m for m in message.guild.members if m.id == self.user.id][0]
        if message.author == myself:
            return

        # Check all parsers
        for parser in ElmerParser.registry:
            if parser.enabled and parser.check(message.content):
                await parser.handle(self, message)

        # Validate against prefix
        if not message.content.lower().startswith(self.prefix):
            return

        # Just for a while to ease the transition
        if message.content.startswith("!elmer"):
            await message.channel.send("I've been tweaked to use **!** instead of **!elmer** now.")
            return

        # Parse out command and check against all commands
        contents = message.content[len(self.prefix) :]
        command, _, args = contents.strip().partition(" ")
        handler = ElmerCommand.find(command)
        if handler:
            await handler.handle(self, message, args)


def main():
    parser = argparse.ArgumentParser(description="Starts elmerbot client")
    parser.add_argument("-e", "--env", help="production or development (Default: development)", default="development")
    parser.add_argument("-s", "--settings", help="YAML file with settings", default="settings.yaml")
    args = parser.parse_args()
    settings = yaml.load(open(args.settings), Loader=yaml.SafeLoader)
    configure_logger("elmerbot", logging.INFO)
    logger = logging.getLogger("elmerbot.main")
    logger.info("Starting bot...")
    client = ElmerBotClient(settings[args.env])
    client.run()
    logger.info("Exiting...")


if __name__ == "__main__":
    main()
