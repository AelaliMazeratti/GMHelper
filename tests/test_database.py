import os
import json
from types import SimpleNamespace

from database import *


def test_get_guild_data_path(tmp_path):
    path = get_guild_data_path(123456789, tmp_path)

    assert path == os.path.join(str(tmp_path), "guild_123456789")
    assert os.path.isdir(path)

def test_update_guild_metadata():
    guild = SimpleNamespace(name="Test Guild", id=123456789)

    update_guild_metadata(guild) # type: ignore

    metadata_file = os.path.join(get_guild_data_path(guild.id), "metadata.json")
    assert os.path.isfile(metadata_file)

    with open(metadata_file, "r") as file:
        metadata = json.load(file)

    assert metadata["name"] == guild.name
    assert metadata["id"] == guild.id

def test_db_init(tmp_path):
    guild = SimpleNamespace(name="Test Guild", id=123456789)

    db_init(guild, tmp_path) # type: ignore

    db_file = os.path.join(get_guild_data_path(guild.id, tmp_path), f"guild_{guild.id}.db")
    assert os.path.isfile(db_file)

    con = sqlite3.connect(db_file)
    cur = con.cursor()

    # verify that the campaigns table was created successfully
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns'")
    assert cur.fetchone() is not None

    # verify the schema of the campaigns table
    cur.execute("PRAGMA table_info(campaigns)")
    campaigns_schema = cur.fetchall()
    assert campaigns_schema[0][1] == "id"
    assert campaigns_schema[0][2] == "INTEGER"
    assert campaigns_schema[0][5] == 1

    assert campaigns_schema[1][1] == "name"
    assert campaigns_schema[1][2] == "TEXT"
    assert campaigns_schema[1][3] == 1

    # verify that the daily_stats table was created successfully
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_stats'")
    assert cur.fetchone() is not None

    # verify the schema of the daily_stats table
    cur.execute("PRAGMA table_info(daily_stats)")
    daily_stats_schema = cur.fetchall()
    assert daily_stats_schema[0][1] == "user_id"
    assert daily_stats_schema[0][2] == "TEXT"
    assert daily_stats_schema[0][5] == 1

    assert daily_stats_schema[1][1] == "date"
    assert daily_stats_schema[1][2] == "TEXT"
    assert daily_stats_schema[1][5] == 2

    assert daily_stats_schema[2][1] == "cringe"
    assert daily_stats_schema[2][2] == "INTEGER"

    assert daily_stats_schema[3][1] == "sus"
    assert daily_stats_schema[3][2] == "INTEGER"

    con.close()

# test the get_daily_stats function
def test_get_daily_stats(tmp_path):
    guild = SimpleNamespace(name="Test Guild", id=123456789)
    db_init(guild, tmp_path) # type: ignore

    user_id = "987654321"
    today = get_today()

    # insert a test record into the daily_stats table
    con = sqlite3.connect(os.path.join(get_guild_data_path(guild.id, tmp_path), f"guild_{guild.id}.db"))
    cur = con.cursor()
    cur.execute("INSERT INTO daily_stats (user_id, date, cringe, sus) VALUES (?, ?, ?, ?)", (user_id, today, 42, 84))
    con.commit()
    con.close()

    stats = get_daily_stats(guild.id, user_id, tmp_path)
    assert stats["cringe"] == 42
    assert stats["sus"] == 84

# test the get_daily_stats function when no record exists for the user
def test_get_daily_stats_no_record(tmp_path):
    guild = SimpleNamespace(name="Test Guild", id=123456789)
    db_init(guild, tmp_path) # type: ignore

    user_id = "987654321"

    stats = get_daily_stats(guild.id, user_id, tmp_path)
    assert stats["cringe"] is None
    assert stats["sus"] is None

# test the generate_daily_stats function
def test_generate_daily_stats(tmp_path):
    guild = SimpleNamespace(name="Test Guild", id=123456789, members=[SimpleNamespace(id=1, bot=False), SimpleNamespace(id=2, bot=True), SimpleNamespace(id=3, bot=False)])
    db_init(guild, tmp_path) # type: ignore

    generate_daily_stats(guild, tmp_path) # type: ignore

    con = sqlite3.connect(os.path.join(get_guild_data_path(guild.id, tmp_path), f"guild_{guild.id}.db"))
    cur = con.cursor()

    today = get_today()

    # verify that the daily stats were generated for non-bot members
    cur.execute("SELECT user_id, cringe, sus FROM daily_stats WHERE date = ?", (today,))
    rows = cur.fetchall()
    assert len(rows) == 2  # only two non-bot members
    user_ids = {row[0] for row in rows}
    assert user_ids == {"1", "3"}

    for row in rows:
        assert 1 <= row[1] <= 100  # cringe
        assert 1 <= row[2] <= 100  # sus

    con.close()

# test generate_daily_stats idempotency
def test_generate_daily_stats_idempotent(tmp_path):
    guild = SimpleNamespace(
        name="Test Guild",
        id=123456789,
        members=[
            SimpleNamespace(id=1, bot=False),
            SimpleNamespace(id=2, bot=False)
        ]
    )

    db_init(guild, tmp_path)

    # First generation
    generate_daily_stats(guild, tmp_path) # type: ignore

    stats_before = {
        "1": get_daily_stats(guild.id, "1", tmp_path),
        "2": get_daily_stats(guild.id, "2", tmp_path)
    }

    # Second generation
    generate_daily_stats(guild, tmp_path) # type: ignore

    stats_after = {
        "1": get_daily_stats(guild.id, "1", tmp_path),
        "2": get_daily_stats(guild.id, "2", tmp_path)
    }

    assert stats_after == stats_before

    con = sqlite3.connect(
        os.path.join(
            get_guild_data_path(guild.id, tmp_path),
            f"guild_{guild.id}.db"
        )
    )
    cur = con.cursor()

    today = get_today()

    cur.execute(
        "SELECT COUNT(*) FROM daily_stats WHERE date = ?",
        (today,)
    )

    assert cur.fetchone()[0] == 2

    con.close()

def test_create_campaign(tmp_path):
    guild_id = 123456
    root = str(tmp_path)

    # Initialize guild database
    db_init(type("Guild", (), {"id": guild_id, "name": "Test Guild"})(), root)

    # Create campaign
    create_campaign(guild_id, "CPR", "Night City Campaign", root)

    guild_path = os.path.join(root, f"guild_{guild_id}")
    db_file = os.path.join(guild_path, f"guild_{guild_id}.db")

    # Check database record
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    campaign = cur.execute(
        "SELECT game_system, id, name, path, active FROM campaigns"
    ).fetchone()

    con.close()

    assert campaign[0] == "CPR"
    assert campaign[1] == 1
    assert campaign[2] == "Night City Campaign"
    assert campaign[3] == "CPR/campaign_1"
    assert campaign[4] == 1

    # Check campaign directory
    campaign_path = os.path.join(guild_path, "CPR", "campaign_1")
    assert os.path.isdir(campaign_path)

    # Check game index
    index_file = os.path.join(guild_path, "game_index.json")
    assert os.path.isfile(index_file)

    with open(index_file) as file:
        game_index = json.load(file)

    assert game_index == [
        {
            "system": "CPR",
            "campaign_id": 1,
            "campaign_name": "Night City Campaign",
            "campaign_path": "CPR/campaign_1"
        }
    ]

def test_create_multiple_campaigns(tmp_path):
    guild_id = 123456
    root = str(tmp_path)

    # Initialize guild database
    db_init(type("Guild", (), {"id": guild_id, "name": "Test Guild"})(), root)

    # Create campaigns
    create_campaign(guild_id, "CPR", "Night City Campaign", root)
    create_campaign(guild_id, "CPR", "Another Campaign", root)

    guild_path = os.path.join(root, f"guild_{guild_id}")
    db_file = os.path.join(guild_path, f"guild_{guild_id}.db")

    # Check database records
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    campaigns = cur.execute(
        "SELECT game_system, id, name, path, active FROM campaigns"
    ).fetchall()

    con.close()

    assert campaigns == [
        ("CPR", 1, "Night City Campaign", "CPR/campaign_1", 1),
        ("CPR", 2, "Another Campaign", "CPR/campaign_2", 1)
    ]

    # Check campaign directories
    assert os.path.isdir(
        os.path.join(guild_path, "CPR", "campaign_1")
    )
    assert os.path.isdir(
        os.path.join(guild_path, "CPR", "campaign_2")
    )

    # Check game index
    index_file = os.path.join(guild_path, "game_index.json")

    with open(index_file) as file:
        game_index = json.load(file)

    assert game_index == [
        {
            "system": "CPR",
            "campaign_id": 1,
            "campaign_name": "Night City Campaign",
            "campaign_path": "CPR/campaign_1"
        },
        {
            "system": "CPR",
            "campaign_id": 2,
            "campaign_name": "Another Campaign",
            "campaign_path": "CPR/campaign_2"
        }
    ]

def test_campaign_deactivate(tmp_path):
    guild_id = 123456
    root = str(tmp_path)

    # Initialize guild database
    db_init(type("Guild", (), {"id": guild_id, "name": "Test Guild"})(), root)

    # Create campaign
    create_campaign(guild_id, "CPR", "Night City Campaign", root)

    # Deactivate campaign
    result = campaign_deactivate(guild_id, 1, root)

    assert result == "deactivated"

    guild_path = os.path.join(root, f"guild_{guild_id}")
    db_file = os.path.join(guild_path, f"guild_{guild_id}.db")

    # Check database record
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    campaign = cur.execute(
        "SELECT id, active FROM campaigns WHERE id = ?",
        (1,)
    ).fetchone()

    con.close()

    assert campaign == (1, 0)

    # Check game index
    index_file = os.path.join(guild_path, "game_index.json")

    with open(index_file) as file:
        game_index = json.load(file)

    assert game_index == []

    # Try to deactivate already inactive campaign
    result = campaign_deactivate(guild_id, 1, root)

    assert result == "already_inactive"

    # Try to deactivate nonexistent campaign
    result = campaign_deactivate(guild_id, 999, root)

    assert result == "not_found"

def test_campaign_reactivate(tmp_path):
    guild_id = 123456
    root = str(tmp_path)

    # Initialize guild database
    db_init(type("Guild", (), {"id": guild_id, "name": "Test Guild"})(), root)

    # Create campaign
    create_campaign(guild_id, "CPR", "Night City Campaign", root)

    # Deactivate, then reactivate
    campaign_deactivate(guild_id, 1, root)
    result = campaign_reactivate(guild_id, 1, root)

    assert result == "reactivated"

    # Try to reactivate already active campaign
    result = campaign_reactivate(guild_id, 1, root)

    assert result == "already_active"

    # Try to reactivate nonexistent campaign
    result = campaign_reactivate(guild_id, 999, root)

    assert result == "not_found"

    guild_path = os.path.join(root, f"guild_{guild_id}")
    db_file = os.path.join(guild_path, f"guild_{guild_id}.db")

    # Check database record
    con = sqlite3.connect(db_file)
    cur = con.cursor()

    campaign = cur.execute(
        "SELECT id, active FROM campaigns WHERE id = ?",
        (1,)
    ).fetchone()

    con.close()

    assert campaign == (1, 1)

    # Check game index
    index_file = os.path.join(guild_path, "game_index.json")

    with open(index_file) as file:
        game_index = json.load(file)

    assert game_index == [
        {
            "system": "CPR",
            "campaign_id": 1,
            "campaign_name": "Night City Campaign",
            "campaign_path": "CPR/campaign_1"
        }
    ]

def test_get_campaigns(tmp_path):
    guild_id = 123456
    root = str(tmp_path)

    # Initialize guild database
    db_init(type("Guild", (), {"id": guild_id, "name": "Test Guild"})(), root)

    # Create campaigns
    create_campaign(guild_id, "CPR", "Night City Campaign", root)
    create_campaign(guild_id, "CPR", "Another Campaign", root)

    # Deactivate second campaign
    campaign_deactivate(guild_id, 2, root)

    campaigns = get_campaigns(guild_id, root)

    assert campaigns == [
        (1, "CPR", "Night City Campaign", 1),
        (2, "CPR", "Another Campaign", 0)
    ]