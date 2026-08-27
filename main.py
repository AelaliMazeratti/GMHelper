import os
from settings import *
from dotenv import load_dotenv
import json


load_dotenv()

token = os.getenv("DISCORD_TOKEN")
if token is None:
    raise RuntimeError("DISCORD_TOKEN is not set")

@bot.event
async def on_ready():
    assert bot.user is not None
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.command()
async def ping(ctx):
    # sends "Pong!" to the channel where the command was invoked
    await ctx.send('Pong!')

bot.run(token)