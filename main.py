import os
from dotenv import load_dotenv
from discord.ext import tasks
import json
import random
from settings import *
from database import *

# load environment variables from .env file
load_dotenv()

# initialize the bot
token = os.getenv("DISCORD_TOKEN")
if token is None:
    raise RuntimeError("DISCORD_TOKEN is not set. Please set it in the .env file.")
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=INTENTS) # bot command prefix

# scheduled tasks
# task to generate daily stats for all guilds at DAILY_STATS_TIME in TIMEZONE
@tasks.loop(time=DAILY_STATS_TIME)
async def daily_stats_task():
    for guild in bot.guilds:
        try:
            generate_daily_stats(guild)
            print(f'Generated daily stats for guild: {guild.name} (id: {guild.id})')
        except Exception as e:
            print(f'Failed to generate daily stats for guild: {guild.name} (id: {guild.id})')
            print(f'Error: {e}')

#  startup sequence
@bot.event
async def on_ready():
    assert bot.user is not None
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

    # initialize the database for each guild the bot is connected to
    for guild in bot.guilds:
        try:
            db_init(guild)
            generate_daily_stats(guild)
            print(f'Initialized guild: {guild.name} (id: {guild.id})')
        except Exception as e:
            print(f'Failed to initialize guild: {guild.name} (id: {guild.id})')
            print(f'Error: {e}')

    try:
        if not daily_stats_task.is_running():
            daily_stats_task.start()
    except Exception as e:
        print('Failed to start daily stats task')
        print(f'Error: {e}')

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
# run the bot if it is not in a test environment
if __name__ == "__main__":
    bot.run(token)