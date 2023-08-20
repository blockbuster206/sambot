import discord
from discord.ext import commands
import logging
import random

from sambot.tools import botlogger

loggr, cog_name = botlogger.getCogLogger(__name__)


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lol", aliases=['l'])
    async def lol(self, ctx, *args):
        await ctx.send(" ".join(args))


async def setup(bot):
    await bot.add_cog(General(bot))
    loggr.debug(f"Loaded {cog_name}")


async def teardown(bot):
    await bot.remove_cog("General")
    loggr.debug(f"Unloaded {cog_name}")
