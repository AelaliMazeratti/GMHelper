import os
from dotenv import load_dotenv
from settings import *
import json
import random
from database import get_today

# load environment variables from .env file
load_dotenv()

# initialize the bot
token = os.getenv("DISCORD_TOKEN")
if token is None:
    raise RuntimeError("DISCORD_TOKEN is not set. Please set it in the .env file.")
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=INTENTS) # bot command prefix

# print startup message
@bot.event
async def on_ready():
    assert bot.user is not None
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    for guild in bot.guilds:
        print(f'Connected to guild: {guild.name} (id: {guild.id})')
    print('------')

# display error message when a command is not found
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        response = [f"Fuck off, {ctx.author.mention}", "U w0t m8?", f"No such command, {ctx.author.mention}", "Use Help, dumbass"]
        await ctx.send(random.choice(response))

# sends "Pong!" to the channel where the command was invoked
@bot.command(help="Ping command to check if the bot is responding") 
async def ping(ctx):
    await ctx.send('Pong!')

# sends daily stats to the channel where the command was invoked
@bot.command(help="Shows your daily stats for everyone to see", brief="Get judged, idiot") 
async def judge(ctx, member: discord.Member | None = None):

    if member is None:
        target = ctx.author
    else:
        target = member

    if os.path.exists('data/daily_stats.json'): # if the file exists, load the data from it
        with open('data/daily_stats.json', 'r') as file:
            daily_stats = json.load(file)
    else: # if the file does not exist, create an empty dictionary
        daily_stats = {}

    user_id = str(target.id)
    today = get_today()

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

    await ctx.send(f"{target.mention}'s daily stats:\n"
                       f"Cringe: {cringe}%\n"
                       f"Sus: {sus}%"
                       )

bot.run(token)