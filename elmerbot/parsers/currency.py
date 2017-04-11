import arrow
import discord
import re
from elmerbot.parsers import ElmerParser
from forex_python.converter import CurrencyRates


class CurrencyParser(ElmerParser):
    name = "currency"

    def __init__(self, registry):
        super(CurrencyParser, self).__init__(registry)
        self._last_refreshed = 0
        self._cache = {}
        self._rates = CurrencyRates()
        self._currencies = ["USD", "EUR", "GBP", "SGD", "CAD", "AUD", "DKK", "HKD", "NZD"]
        self._pattern = re.compile(r"(\d+[\.,]?\d*)\s+(" + "|".join(self._currencies) + r")", re.IGNORECASE)

    def _get_unit(self, unit):
        # Force refresh every 10 minutes
        now = arrow.get().timestamp
        if now - self._last_refreshed > 600:
            self._cache = {}
            self._last_refreshed = now
        if unit not in self._cache:
            self._cache[unit] = self._rates.get_rates(unit)
        return self._cache[unit]

    def check(self, contents):
        return self._pattern.search(contents)

    async def handle(self, client, message):
        self._logger.info("Parsing message...")

        amount, unit = self._pattern.search(message.content).groups(1)
        amount = float(amount.replace(",", "."))
        unit = unit.upper()

        em = discord.Embed(title="{:.2f} {}".format(amount, unit),
                           description="Currency Conversion Table",
                           color=0x00DD00)
        rates = self._get_unit(unit)
        rates[unit] = 1
        for other_unit in self._currencies:
            display_value = str(rates[other_unit]).zfill(2)
            display_value = "{:.2f}".format(amount * rates[other_unit])
            em.add_field(name=other_unit, value=display_value)
        await client.send_message(message.channel, embed=em)
