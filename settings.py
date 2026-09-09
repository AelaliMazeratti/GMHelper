import discord
from discord.ext import commands
from zoneinfo import ZoneInfo
from datetime import time

# bot command prefix
COMMAND_PREFIX = commands.when_mentioned_or('!')

# bot permissions
INTENTS = discord.Intents(
    messages=True,
    guilds=True,
    message_content=True,
    members=True
) 

# timezone selection
TIMEZONE = ZoneInfo("UTC")

# daily stats generation time
DAILY_STATS_TIME = time(hour=0, minute=0, second=0, tzinfo=TIMEZONE)
