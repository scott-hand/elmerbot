import discord
import string
from elmerbot.commands import ElmerCommand


class SearchCommand(ElmerCommand):
    command = "search"
    description = ("Search for a whisky by name. Optionally put a number of results to limit it to in front of "
                   "your query.\n"
                   "Examples: `!search stagg 2014` or `!search 10 stagg`"
                   )

    def __init__(self, registry):
        super(SearchCommand, self).__init__(registry)

    async def handle(self, client, message, args):
        self._logger.info("Got search command")
        if client.data.stale:
            await client.send_message(message.channel, "One moment, reloading review data...")
        await client.send_typing(message.channel)
        first, _, rest = args.partition(" ")
        pattern = args
        choices = 5
        if first.isnumeric():
            choices = int(first)
            pattern = rest
        # Whitelist characters to eliminate Markdown injection
        whitelist = string.ascii_letters + string.digits + "'()-., "
        pattern = "".join([c for c in pattern if c in whitelist])
        results = client.data.search(pattern, choices)

        # Stop now if there's nothing to show
        if not results:
            em = discord.Embed(title="No results found for \"{}\".".format(pattern),
                               colour=0xDD0000)
            await client.send_message(message.channel, embed=em)
            return

        # Compile results, stopping when there's a large drop in confidence.
        output = []
        last_conf = results[0][2]
        for token, whisky_id, conf in results:
            if last_conf - conf > 3:
                break
            last_conf = conf
            output.append("**{}** [#{}]".format(token, whisky_id))
        hits = len(output)
        output += ["", "Use **!info <id>** to get review information. The <id> is the number in brackets \
                from search results."]
        em = discord.Embed(title="{} Results for \"{}\":".format(hits, pattern),
                           description="\n".join(output),
                           colour=0x00DD00)
        await client.send_message(message.channel, embed=em)


class InfoCommand(ElmerCommand):
    command = "info"
    description = ("Search for a whisky by name. Optionally put a number of results to limit it to in front of your "
                   "query.\n"
                   "Examples: `!search stagg 2014` or `!search 10 stagg`"
                   )

    def __init__(self, registry):
        super(InfoCommand, self).__init__(registry)

    async def handle(self, client, message, args):
        self._logger.info("Got info command")
        pending_msg = None
        if client.data.stale:
            pending_msg = await client.send_message(message.channel, "One moment, reloading review data...")
        await client.send_typing(message.channel)
        if args.isnumeric():
            whisky_id = int(args)
        else:
            # Whitelist characters to eliminate Markdown injection
            whitelist = string.ascii_letters + string.digits + "'()-., "
            pattern = "".join([c for c in args if c in whitelist])
            result = client.data.search(pattern, 1)
            if not result:
                em = discord.Embed(title="Could not find \"{}\"".format(pattern),
                                   description="Try using **!search** first.",
                                   colour=0xDD0000)
                await client.send_message(message.channel, embed=em)
                return
            whisky_id = result[0][1]
        data = client.data.find(whisky_id)
        if pending_msg:
            await client.delete_message(pending_msg)
        output = []

        # Generate stats
        ratings = [row["rating"] for row in data if row["rating"]]
        if ratings:
            avg_rating = round(sum(ratings) / float(len(ratings)), 2)
            delta = round(avg_rating - client.data.avg, 2)
            delta = "+" + str(delta) if delta >= 0.0 else str(delta)
            output.append("**Average rating:** {} based on {} reviews with scores.".format(avg_rating, len(ratings)))
            output.append("It is {} from the global average \
                    of {} with standard deviation {}".format(delta, client.data.avg, client.data.stddev))
            output.append("**Most recent reviews:**")
            for idx, review in enumerate(client.data.most_recent(whisky_id=whisky_id)):
                output.append("{}. {} gave it {}. [Link]({})".format(idx + 1, review["username"],
                                                                     review["rating"] or "no rating", review["link"]))
        else:
            output.append("**Average rating:** No reviews with scores.")
        em = discord.Embed(title="{}".format(data[0]["name"]),
                           description="\n".join(output),
                           colour=0x00DD00)
        await client.send_message(message.channel, embed=em)
