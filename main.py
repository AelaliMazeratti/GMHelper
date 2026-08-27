import os
from dotenv import load_dotenv
from settings import *
import json
import random

load_dotenv()
os.makedirs('data', exist_ok=True)

token = os.getenv("DISCORD_TOKEN")
if token is None:
    raise RuntimeError("DISCORD_TOKEN is not set. Please set it in the .env file.")

@bot.event
async def on_ready():
    assert bot.user is not None
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.command(help="Ping command to check if the bot is responding") # sends "Pong!" to the channel where the command was invoked
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(help="Shows your daily stats for everyone to see", brief="Get judged, idiot") # sends daily stats to the channel where the command was invoked
async def dailystats(ctx):
    if os.path.exists('data/daily_stats.json'): # if the file exists, load the data from it
        with open('data/daily_stats.json', 'r') as file:
            daily_stats = json.load(file)
    else: # if the file does not exist, create an empty dictionary
        daily_stats = {}

    user_id = str(ctx.author.id)
    today = datetime.datetime.now(ZoneInfo("Asia/Yerevan")).date().isoformat()

    if user_id not in daily_stats or daily_stats[user_id]["last_used"] != today: # user has already used the command today
        cringe = random.randint(1, 100)
        sus = random.randint(1, 100)
        
        daily_stats[user_id] = {
            "last_used": today,
            "stats": {
                "cringe": cringe,
                "sus": sus
                }
            }
        
        with open('data/daily_stats.json', 'w') as file:
            json.dump(daily_stats, file, indent=4)

    cringe = daily_stats[user_id]["stats"]["cringe"]
    sus = daily_stats[user_id]["stats"]["sus"]

    await ctx.send(f"{ctx.author.mention}'s daily stats:\n"
                       f"Cringe: {cringe}%\n"
                       f"Sus: {sus}%"
                       )

bot.run(token)