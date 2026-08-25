import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

token: str = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix="!")
bot.run(token)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')