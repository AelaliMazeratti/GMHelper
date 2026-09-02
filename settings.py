import discord
from discord.ext import commands
from zoneinfo import ZoneInfo

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
