from discord.ext import commands

from sambot.tools import botlogger

loggr, cog_name = botlogger.getCogLogger(__name__)


class Utilities(commands.Cog, name="Utilities"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def logout(self, ctx):
        await ctx.send("Logging out!")
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(Utilities(bot))
    loggr.debug(f"Loaded {cog_name}")


async def teardown(bot):
    await bot.remove_cog("Utilities")
    loggr.debug(f"Unloaded {cog_name}")
