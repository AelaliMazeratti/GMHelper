import random
import sqlite3
import os
import discord
from datetime import datetime

from discord import guild
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

# creates or updates the game_index.json file for a guild
def update_game_index(guild_id: int, root: str = "data") -> None:
    path = get_guild_data_path(guild_id, root)
    db_file = os.path.join(path, f"guild_{guild_id}.db")
    game_index_file = os.path.join(path, "game_index.json")

    con = sqlite3.connect(db_file)
    cur = con.cursor()
    campaigns = cur.execute("SELECT game_system, id, name, path FROM campaigns WHERE active = 1").fetchall()
    con.close()

    game_index = []

    for campaign in campaigns:
        game_index.append({
            "system": campaign[0],
            "campaign_id": campaign[1],
            "campaign_name": campaign[2],
            "campaign_path": campaign[3]
        })

    with open(game_index_file, "w") as file:
        json.dump(game_index, file, indent=4)

# creates campaign
def create_campaign(guild_id: int, game_system: str, campaign_name: str, root: str = "data") -> None:
    path = get_guild_data_path(guild_id, root)
    db_file = os.path.join(path, f"guild_{guild_id}.db")

    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("INSERT INTO campaigns (game_system, name, path) VALUES (?, ?, ?)",
                (game_system, campaign_name, "")
    )
    campaign_id = cur.lastrowid
    campaign_path = os.path.join(path, game_system, f"campaign_{campaign_id}")
    os.makedirs(campaign_path, exist_ok=True)

    cur.execute("UPDATE campaigns SET path = ? WHERE id = ?",
                (os.path.relpath(campaign_path, path), campaign_id)
    )

    con.commit()
    con.close()

    update_game_index(guild_id, root)

# deactivates active campaign
def campaign_deactivate(guild_id: int, campaign_id: int, root: str = "data") -> str:
    path = get_guild_data_path(guild_id, root)
    db_file = os.path.join(path, f"guild_{guild_id}.db")

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # check the current status for error handling purposes
    campaign = cur.execute("SELECT active FROM campaigns WHERE id = ?",
        (campaign_id,)
    ).fetchone()

    if campaign is None:
        con.close()
        return "not_found"

    if campaign[0] == 0:
        con.close()
        return "already_inactive"

    cur.execute(
        "UPDATE campaigns SET active = 0 WHERE id = ?",
        (campaign_id,)
    )

    con.commit()
    con.close()

    update_game_index(guild_id, root)

    return "deactivated"

# reactivates existing but inactive campaign
def campaign_reactivate(guild_id: int, campaign_id: int, root: str = "data") -> str:
    path = get_guild_data_path(guild_id, root)
    db_file = os.path.join(path, f"guild_{guild_id}.db")

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # check the current status for error handling purposes
    campaign = cur.execute("SELECT active FROM campaigns WHERE id = ?",
        (campaign_id,)
    ).fetchone()

    if campaign is None:
        con.close()
        return "not_found"

    if campaign[0] == 1:
        con.close()
        return "already_active"

    cur.execute("UPDATE campaigns SET active = 1 WHERE id = ?",
        (campaign_id,)
    )

    con.commit()
    con.close()

    update_game_index(guild_id, root)

    return "reactivated"

def get_campaigns(guild_id: int, root: str = "data"):
    path = get_guild_data_path(guild_id, root)
    db_file = os.path.join(path, f"guild_{guild_id}.db")

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    campaigns = cur.execute("SELECT id, game_system, name, active FROM campaigns").fetchall()

    con.close()        
    return campaigns                   

# initializes the database and create relevant tables if they don't exist
def db_init(guild, root: str = "data") -> None:
    guild_id = guild.id
    path = get_guild_data_path(guild_id, root) 
    update_guild_metadata(guild, root) 
    name = f"guild_{guild_id}.db"
    con = sqlite3.connect(os.path.join(path, name))
    cur = con.cursor()

    # create the campaigns table if it doesn't exist
    cur.execute("CREATE TABLE IF NOT EXISTS campaigns (" \
            "id INTEGER PRIMARY KEY AUTOINCREMENT," \
            "name TEXT NOT NULL," \
            "game_system TEXT NOT NULL," \
            "path TEXT NOT NULL," \
            "active INTEGER NOT NULL DEFAULT 1" \
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

# fetches the daily stats for a specific user in a specific guild from the database
def get_daily_stats(guild_id: int, user_id: str, root: str = "data") -> dict:
    path = get_guild_data_path(guild_id, root)
    db_file = os.path.join(path, f"guild_{guild_id}.db")
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    today = get_today()
    cur.execute("SELECT cringe, sus FROM daily_stats WHERE user_id = ? AND date = ?", (user_id, today))
    row = cur.fetchone()
    con.close()

    if row:
        return {"cringe": row[0], "sus": row[1]}
    else:
        return {"cringe": None, "sus": None}

# generates daily stats for all members of a guild and stores them in the database
def generate_daily_stats(guild: discord.Guild, root: str = "data"):
    path = get_guild_data_path(guild.id, root)
    db_file = os.path.join(path, f"guild_{guild.id}.db")
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    today = get_today()

    for member in guild.members:
        if member.bot:
            continue  # skip bots
        cringe = random.randint(1, 100)
        sus = random.randint(1, 100)
        cur.execute("INSERT OR IGNORE INTO daily_stats (user_id, date, cringe, sus) VALUES (?, ?, ?, ?)", (member.id, today, cringe, sus))
        
    con.commit()
    con.close()
