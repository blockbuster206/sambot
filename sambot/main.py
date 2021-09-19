import discord
from discord.ext import commands
import os
import sys

# logger
import logging

# discord.py logging
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
# sambot's logger
sam_logger = logging.getLogger("SAM-Bot")
sam_logger.setLevel(logging.DEBUG)

logFormatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

file_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
file_handler.setFormatter(logFormatter)
discord_logger.addHandler(file_handler)
sam_logger.addHandler(file_handler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
discord_logger.addHandler(consoleHandler)
sam_logger.addHandler(consoleHandler)

# for the .env file and discord token
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# if the .env file doesn't have the discord token in it
if not TOKEN:
    print("Token doesnt exist\nGo to https://discord.com/developers/applications to get your bot token")
    TOKEN = input("Enter you bot token: ")
    with open("../.env", 'w') as env:
        env.write("DISCORD_TOKEN={TOKEN}".format(TOKEN=TOKEN))
        env.close()

# discord bot status
activity = discord.Game("with you balls")

# cogs
cogs = (
    "General",
    "Utilities",
    "Music"
)


class SamBot(commands.Bot):
    def __init__(self, command_prefix, self_bot):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot, owner_id=346107577970458634)
        self.cogs_loaded = False
        self.bot_commands()

    def bot_commands(self):
        @self.command(name="reload", aliases=['rd'], hidden=True)
        @commands.is_owner()
        async def reload(ctx):
            sam_logger.info("Unloading Cogs")
            if not self.unload_cogs():
                sam_logger.error("Cogs already unloaded baka")
                await ctx.send("Cogs already unloaded baka")
                return
            sam_logger.debug("Reloading cogs")
            if not self.load_cogs():
                sam_logger.error("Already loaded cogs")
                await ctx.send("Already loaded cogs")
                return
            sam_logger.info("Reloaded cogs")
            await ctx.send("Reloaded Cogs")

    def load_cogs(self):
        if not self.cogs_loaded:
            for cog in cogs:
                try:
                    bot.load_extension("cogs.{cog}".format(cog=cog))
                    sam_logger.debug("Loaded {cog_name}".format(cog_name=cog))
                except commands.ExtensionNotFound:
                    sam_logger.error("Cog Not found")
            self.cogs_loaded = True
            return True
        return False

    def unload_cogs(self):
        if self.cogs_loaded:
            for cog in cogs:
                bot.unload_extension("cogs.{cog}".format(cog=cog))
                sam_logger.debug("Loaded {cog_name}".format(cog_name=cog))
            self.cogs_loaded = False
            return True
        return False

    async def on_ready(self):
        sam_logger.info("{username} is online".format(username=self.user.name))
        await self.change_presence(status=discord.Status.online, activity=activity)
        sam_logger.debug("Loading Cogs")
        self.load_cogs()
        sam_logger.info("SAM-Bot is ready")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            params = []
            for param in list(ctx.command.params.items())[2:]:
                params.append(param[0])
            await ctx.send('Missing Arguments: {args}'.format(args=", ".join(params)))


bot = SamBot(command_prefix=",", self_bot=False)
bot.run(TOKEN)
