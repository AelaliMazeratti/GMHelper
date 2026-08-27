import discord
from discord.ext import commands
import datetime
from zoneinfo import ZoneInfo

intents = discord.Intents(messages=True, guilds=True, message_content=True, members=True) # bot permissions
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents) # bot command prefix

now = datetime.datetime.now(ZoneInfo("Asia/Yerevan")) # timezone selection