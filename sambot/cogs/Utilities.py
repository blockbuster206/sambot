from discord.ext import commands
import logging

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


class Utilities(commands.Cog, name="Utilities"):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Utilities(bot))


def teardown(bot):
    bot.remove_cog("Utilities")
