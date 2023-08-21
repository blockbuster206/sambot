import discord
from discord.ext import commands
import os

from sambot.tools.instagram import InstaDL
from sambot.tools import botlogger

loggr = botlogger.getSubLogger(__name__)


class Internet(commands.Cog, name="Internet"):
    def __init__(self, bot):
        self.bot = bot
        self.instadl = InstaDL()

    @commands.command(name="insta", aliases=['ig'])
    async def insta(self, ctx, link):

        await ctx.message.delete()

        msg = await ctx.send(f"Request by **{ctx.author.name}**, getting instagram media...")

        media = self.instadl.dl_post(link)

        files = []

        for i in media[1:]:
            files.append(discord.File(i))

        await msg.delete()
        await ctx.send(f"Requested by {ctx.author.mention}: **{media[0]}**", files=files)

        for i in media[1:]:
            os.remove(i)


async def setup(bot):
    await bot.add_cog(Internet(bot))
    loggr.debug("[ LOADED ]")


async def teardown(bot):
    await bot.remove_cog("Internet")
