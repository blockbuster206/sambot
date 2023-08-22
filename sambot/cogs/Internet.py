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

        link = link.split("?")[0]

        await ctx.message.delete()

        msg = await ctx.send(f"Request by **{ctx.author.name}**, getting instagram media...")

        media = self.instadl.dl_post(link)

        if isinstance(media, str):
            await msg.edit(content=f"Request by **{ctx.author.name}**, couldn't get media. Here is the link! https://www.ddinstagram.com/reel/{media}")
            return

        await msg.edit(content=f"Request by **{ctx.author.name}**, uploading instagram media...")

        files = []

        for i in media[1:]:
            files.append(discord.File(i))

        await ctx.send(f"Requested by {ctx.author.mention}: **{media[0]['caption']}**", files=files)
        await msg.delete()

        for i in media[1:]:
            os.remove(i)

        loggr.debug(f"Deleted {media[0]['shortcode']} media")


async def setup(bot):
    await bot.add_cog(Internet(bot))
    loggr.debug("[ LOADED ]")


async def teardown(bot):
    await bot.remove_cog("Internet")
