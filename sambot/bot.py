### SamBot by Blockbuster206

import discord
from discord.ext import commands

from sambot.tools import botenv
from sambot.tools import botlogger

botlogger.getLogger("discord", "info")
botlogger.getLogger("sambot", "debug")
cl_loggr = botlogger.getSubLogger("client")
loggr = botlogger.getSubLogger("bot")

# discord bot status
activity = discord.Game("among us")

# cogs
cogs = (
    "General",
    "Utilities",
    "Internet"
    # "Music"
)


class SamBot(commands.Bot):
    def __init__(self, command_prefix, self_bot):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot, owner_id=346107577970458634,
                              intents=discord.Intents.all())
        self.cogs_loaded = False
        self.bot_commands()

    def bot_commands(self):
        @self.command(name="reload", aliases=['rd'], hidden=True)
        @commands.is_owner()
        async def reload(ctx):
            cl_loggr.info(f"reloading cogs...")
            msg = await ctx.send("Reloading Cogs...")

            if self.voice_clients: await self.disconnect_all_voice_clients()
            if self.cogs_loaded: await self.unload_cogs()
            loggr.debug("reloading cogs")

            await self.load_cogs()
            loggr.debug("reloaded cogs")
            await msg.edit(content="Reloaded Cogs")

    async def disconnect_all_voice_clients(self):
        loggr.debug("disconnecting all voice clients")
        for voice_client in self.voice_clients:
            await voice_client.disconnect()

    async def load_cogs(self):
        loggr.info("loading cogs")
        amt_cog_loaded = 0
        for cog in cogs:
            try:
                await bot.load_extension("cogs.{cog}".format(cog=cog))
                amt_cog_loaded += 1
            except commands.ExtensionNotFound:
                loggr.error("cog not found")
            except commands.ExtensionFailed as err:
                loggr.error(f"{cog.lower()} [ FAILED ] ({err})")
        loggr.info(f"{amt_cog_loaded}/{len(cogs)} cogs loaded")
        self.cogs_loaded = True

    async def unload_cogs(self):
        loggr.debug("unloading cogs")
        for cog in cogs:
            await bot.unload_extension(f"cogs.{cog}")
        self.cogs_loaded = False

    async def on_ready(self):
        await self.change_presence(status=discord.Status.online, activity=activity)
        await self.load_cogs()
        cl_loggr.info("[ READY ]")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            loggr.error(error)

        if isinstance(error, commands.MissingRequiredArgument):
            params = []
            for param in list(ctx.command.params.items())[2:]:
                params.append(param[0])
            await ctx.send('Missing Arguments: {args}'.format(args=", ".join(params)))


bot = SamBot(command_prefix=",", self_bot=False, )
TOKEN = botenv.getBotToken()
bot.run(TOKEN, log_handler=None)
