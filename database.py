import sqlite3
import os
import discord
from datetime import datetime
from settings import TIMEZONE
import json

# returns the path to the guild's data directory, creating it if it doesn't exist
def get_guild_data_path(guild_id: int, root: str = "data") -> str:
    path = os.path.join(root, f"guild_{guild_id}")
    os.makedirs(path, exist_ok=True)
    return path

# creates or updates the metadata.json file for a guild
def update_guild_metadata(guild: discord.Guild, root: str = "data") -> None:
    path = get_guild_data_path(guild.id, root)
    metadata_file = os.path.join(path, "metadata.json")

    metadata = {
        "name": guild.name,
        "id": guild.id
    }

    with open(metadata_file, "w") as file:
        json.dump(metadata, file, indent=4)

# create campaign, NOT FINISHED YET
def create_campaign(guild_id: int, campaign_name: str, root: str = "data") -> None:
    path = get_guild_data_path(guild_id, root)
    campaign_path = os.path.join(path, "campaigns", campaign_name)
    os.makedirs(campaign_path, exist_ok=True)
    cleaned_campaign_name = campaign_name.replace(" ", "_").lower()
    db_file = os.path.join(campaign_path, f"{cleaned_campaign_name}.db")

# initializes the database and create relevant tables if they don't exist
def db_init(guild, root: str = "data") -> None:
    guild_id = guild.id
    path = get_guild_data_path(guild_id, root)  # ensure the guild data directory exists
    update_guild_metadata(guild, root)  # update the metadata.json file
    name = f"guild_{guild_id}.db"
    con = sqlite3.connect(os.path.join(path, name))
    cur = con.cursor()

    # create the campaigns table if it doesn't exist
    cur.execute("CREATE TABLE IF NOT EXISTS campaigns (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "name TEXT NOT NULL," \
            "game_system TEXT NOT NULL" \
        ")"
    )

    # create the daily_stats table if it doesn't exist
    cur.execute("CREATE TABLE IF NOT EXISTS daily_stats (" \
            "user_id TEXT," \
            "date TEXT," \
            "cringe INTEGER," \
            "sus INTEGER," \
            "PRIMARY KEY (user_id, date)" \
        ")"
    )
    con.commit()

    # verify that the campaigns table was created successfully
    campaigns = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns'")
    if campaigns.fetchone() is None:
        raise RuntimeError("Failed to create or access the campaigns table in the database. Please check the database file and ensure it is accessible.")

    # verify that the daily_stats table was created successfully
    daily_stats = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_stats'")
    if daily_stats.fetchone() is None:
        raise RuntimeError("Failed to create or access the daily_stats table in the database. Please check the database file and ensure it is accessible.")

    con.close()

# returns the current date in the specified timezone as a string in ISO format
def get_today() -> str:
    return datetime.now(TIMEZONE).date().isoformat()
