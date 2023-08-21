import discord
from discord.ext import commands
import logging
import random

from sambot.tools import botlogger

loggr = botlogger.getSubLogger(__name__)


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lol", aliases=['l'])
    async def lol(self, ctx, *args):
        await ctx.send(" ".join(args))


async def setup(bot):
    await bot.add_cog(General(bot))
    loggr.debug("[ LOADED ]")


async def teardown(bot):
    await bot.remove_cog("General")
