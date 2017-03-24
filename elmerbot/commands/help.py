import discord
from elmerbot.commands import ElmerCommand


class HelpCommand(ElmerCommand):
    command = "help"
    description = "Send this help message."

    def __init__(self, registry):
        super(HelpCommand, self).__init__(registry)

    async def handle(self, client, message, args):
        self._logger.info("Got help command!")
        # First add high level usage info

        output = ["**Usage**: `{} <command> <arguments>`\n".format(client.prefix)]
        # Now dynamically generate command help
        output.append("**Commands**\n")
        for command in client.registry.commands:
            output.append("**{}**\n{}\n".format(command.command, command.description))
        # Combine, send, and clean up the help command message
        help_msg = "\n".join(output)
        em = discord.Embed(title="ElmerBot Help", description=help_msg, colour=0x00DD00)
        await client.send_message(message.author, embed=em)
        await client.delete_message(message)
