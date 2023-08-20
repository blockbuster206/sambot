import logging

import os
from dotenv import load_dotenv


class botenv:
    load_dotenv()

    @staticmethod
    def getBotToken():
        TOKEN = os.getenv("DISCORD_TOKEN")
        # if the .env file doesn't have the discord token in it
        if not TOKEN:
            print("Token doesnt exist\nGo to https://discord.com/developers/applications to get your bot token")
            TOKEN = input("Enter you bot token: ")
            with open("../.env", 'w') as env:
                env.write(f"DISCORD_TOKEN={TOKEN}")
                env.close()
        return TOKEN

class botlogger:
    # Handlers setup for loggers
    logFormatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

    file_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
    file_handler.setFormatter(logFormatter)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)

    @staticmethod
    def getLogger(name, log_level: str):
        loggr = logging.getLogger(name)
        loggr.setLevel(log_level.upper())
        # Add handlers
        loggr.addHandler(botlogger.file_handler)
        loggr.addHandler(botlogger.consoleHandler)
        return loggr

    @staticmethod
    def getCogLogger(name:str):
        cog_name = name.replace("cogs.", '').lower()
        loggr = logging.getLogger(f"sambot.{name.lower()}")
        return loggr, cog_name
