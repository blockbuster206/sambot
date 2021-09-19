import discord
from discord.ext import commands
import logging

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lol", aliases=['l'])
    async def lol(self, ctx, *args):
        await ctx.send(" ".join(args))


def setup(bot):
    bot.add_cog(General(bot))


def teardown(bot):
    bot.remove_cog("General")
