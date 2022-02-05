import discord
from discord.ext import commands
import logging
import random

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lol", aliases=['l'])
    async def lol(self, ctx, *args):
        await ctx.send(" ".join(args))

    @commands.command(name="roll")
    async def lol(self, ctx):
        rand_number = str(random.randint(1, 999))
        if len(rand_number) == 3:
            rand_number = "0" + rand_number
        elif len(rand_number) == 2:
            rand_number = "00" + rand_number
        elif len(rand_number) == 1:
            rand_number = "000" + rand_number
        await ctx.send(f"Number Rolled: {rand_number}")




def setup(bot):
    bot.add_cog(General(bot))


def teardown(bot):
    bot.remove_cog("General")
