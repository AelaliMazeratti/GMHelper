import discord
from discord.ext import commands
import datetime
from zoneinfo import ZoneInfo

intents = discord.Intents(messages=True, guilds=True, message_content=True, members=True) # bot permissions
bot = commands.Bot(command_prefix="!", intents=intents) # bot command prefix
