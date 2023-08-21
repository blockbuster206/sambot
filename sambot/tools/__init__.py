import logging
import os
from dotenv import load_dotenv

class botlogger:
    @staticmethod
    def getLogger(name, log_level: str):
        loggr = logging.getLogger(name)
        loggr.setLevel(log_level.upper())
        # Add handlers
        loggr.addHandler(botlogger.file_handler)
        loggr.addHandler(botlogger.consoleHandler)
        return loggr

    @staticmethod
    def getSubLogger(name: str):
        if "cogs" in name: name = name.replace("cogs.", 'cog.').lower()
        loggr = logging.getLogger(f"sambot.{name}")
        return loggr

    logFormatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    file_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
    file_handler.setFormatter(logFormatter)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)


env_loggr = botlogger.getSubLogger("botenv")


class botenv:
    @staticmethod
    def setBotToken(TOKEN):
        with open("../.env", 'w') as env:
            env.write(f"DISCORD_TOKEN={TOKEN}")
            env.close()

    @staticmethod
    def getBotToken():
        TOKEN = os.getenv("DISCORD_TOKEN")
        # if the .env file doesn't have the discord token in it
        if not TOKEN:
            env_loggr.info("token does not exist: https://discord.com/developers/applications")
            TOKEN = input("Enter you bot token: ")
            botenv.setBotToken(TOKEN)
        env_loggr.debug("found token")
        return TOKEN

    load_dotenv()
