import discord
from discord.ext import commands
import os
import sys
# logger
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
file_handler.setFormatter(logFormatter)
logger.addHandler(file_handler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

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


class SamBot(commands.Bot):
    def __init__(self, command_prefix, self_bot):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot)

    async def on_ready(self):
        print("{username} is online".format(username=self.user.name))
        await self.change_presence(status=discord.Status.online, activity=activity)

    def bot_commands(self):
        @self.command(name="lol")
        async def lol(ctx, args):
            await ctx.send(args)

        @self.command(name="yourmom")
        async def yourmom(ctx):
            await ctx.send("lol you mom")


bot = SamBot(command_prefix="~", self_bot=False)
bot.bot_commands()
bot.run(TOKEN)
