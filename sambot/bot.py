### SamBot by Blockbuster206

import discord
from discord.ext import commands

from sambot.tools import botenv
from sambot.tools import botlogger

botlogger.getLogger("discord", "info")
loggr = botlogger.getLogger("sambot", "debug")

# discord bot status
activity = discord.Game("among us")

# cogs
cogs = (
    "General",
    "Utilities",
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
            if self.voice_clients: await self.disconnect_all_voice_clients()
            loggr.debug("Unloading Cogs")

            msg = await ctx.send("Reloading Cogs...")

            if self.cogs_loaded: await self.unload_cogs()
            loggr.debug("Reloading Cogs")

            await self.load_cogs()
            loggr.debug("Reloaded cogs")
            await msg.edit(content="Reloaded Cogs")

    async def disconnect_all_voice_clients(self):
        loggr.debug("Disconnecting all voice clients")
        for voice_client in self.voice_clients:
            await voice_client.disconnect()

    async def load_cogs(self):
        for cog in cogs:
            try:
                await bot.load_extension("cogs.{cog}".format(cog=cog))
            except commands.ExtensionNotFound:
                loggr.error("Cog not found")
        self.cogs_loaded = True

    async def unload_cogs(self):
        for cog in cogs:
            await bot.unload_extension(f"cogs.{cog}")
        self.cogs_loaded = False

    async def on_ready(self):
        loggr.info("{username} is online".format(username=self.user.name))
        await self.change_presence(status=discord.Status.online, activity=activity)
        loggr.debug("Loading Cogs")
        await self.load_cogs()
        loggr.info("SamBot is ready")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            loggr.error(error)

        if isinstance(error, commands.MissingRequiredArgument):
            params = []
            for param in list(ctx.command.params.items())[2:]:
                params.append(param[0])
            await ctx.send('Missing Arguments: {args}'.format(args=", ".join(params)))


bot = SamBot(command_prefix=",", self_bot=False, )
bot.run(botenv.getBotToken(), log_handler=None)
