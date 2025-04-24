# Imports
import discord, os
from discord.ext import commands

from dotenv import load_dotenv

# Globals
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Events
@bot.event
async def on_ready():
    print(f"🟢 | Bot is live")


    await bot.tree.sync()
    print(f"🟢 | Bot tree synced")

# Functions


# Commands


# Execution
if __name__ == "__main__":
    bot.run(BOT_TOKEN)