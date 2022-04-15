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

    @commands.Cog.listener()
    async def on_message(self, message):
        minecraft_channel_id = 963464111340007544
        if message.channel.id == minecraft_channel_id:
            if message.author.id == 963464417167683634:
                channel = self.bot.get_channel(minecraft_channel_id)
                messages = await channel.history().flatten()
                webhook_messages = []
                for msg in messages:
                    if msg.author.id == 963464417167683634:
                        webhook_messages.append(msg)
                try:
                    await webhook_messages[1].delete()
                except:
                    pass



def setup(bot):
    bot.add_cog(General(bot))


def teardown(bot):
    bot.remove_cog("General")
