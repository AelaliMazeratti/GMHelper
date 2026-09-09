import pytest
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import main

# test that the database initialization fails gracefully
@pytest.mark.asyncio
async def test_on_ready_db_init_failure(capsys):
    mock_guild1 = SimpleNamespace(name="Guild One", id=111)
    mock_guild2 = SimpleNamespace(name="Guild Two", id=222)

    mock_bot = SimpleNamespace(guilds=[mock_guild1, mock_guild2], user=SimpleNamespace(name="TestBot", id=123))

    # test that db_init handles exceptions
    with patch("main.bot", mock_bot), \
        patch("main.db_init") as mock_db_init, \
        patch("main.generate_daily_stats") as mock_generate: 
        mock_db_init.side_effect = [Exception("Database failure"), None] # Simulate failure for the first guild and success for the second
        await main.on_ready()

        # verify that db_init was called for both guilds     
        mock_db_init.assert_any_call(mock_guild1)
        mock_db_init.assert_any_call(mock_guild2)
        
        mock_generate.assert_called_once_with(mock_guild2) # verify that failed guild did not prevent initialization of the second guild

        # verify that the error message was printed for the failed guild
        captured = capsys.readouterr()
        assert "Failed to initialize guild: Guild One (id: 111)" in captured.out
        assert "Error: Database failure" in captured.out

# test that bot initialization works correctly
@pytest.mark.asyncio
async def test_on_ready_success(capsys):
    mock_guild1 = SimpleNamespace(name="Guild One", id=111)
    mock_guild2 = SimpleNamespace(name="Guild Two", id=222)

    mock_bot = SimpleNamespace(
        guilds=[mock_guild1, mock_guild2],
        user=SimpleNamespace(name="TestBot", id=123)
    )

    # verify that db_init and generate_daily_stats are called for each guild
    with patch("main.bot", mock_bot), \
        patch("main.db_init") as mock_db_init, \
        patch("main.generate_daily_stats") as mock_generate:

        await main.on_ready()

        mock_db_init.assert_any_call(mock_guild1)
        mock_db_init.assert_any_call(mock_guild2)

        mock_generate.assert_any_call(mock_guild1)
        mock_generate.assert_any_call(mock_guild2)

        captured = capsys.readouterr()

        assert "Initialized guild: Guild One (id: 111)" in captured.out
        assert "Initialized guild: Guild Two (id: 222)" in captured.out

# test that the daily_stats_task generates stats for all guilds
@pytest.mark.asyncio
async def test_daily_stats_task():
    mock_guild1 = SimpleNamespace(name="Guild One", id=111)
    mock_guild2 = SimpleNamespace(name="Guild Two", id=222)

    mock_bot = SimpleNamespace(
        guilds=[mock_guild1, mock_guild2]
    )

    with patch("main.bot", mock_bot), \
        patch("main.generate_daily_stats") as mock_generate:

        await main.daily_stats_task.coro()

        mock_generate.assert_any_call(mock_guild1)
        mock_generate.assert_any_call(mock_guild2)
        assert mock_generate.call_count == 2

# test that the daily_stats_task handles exceptions gracefully
@pytest.mark.asyncio
async def test_daily_stats_task_failure(capsys):
    mock_guild1 = SimpleNamespace(name="Guild One", id=111)
    mock_guild2 = SimpleNamespace(name="Guild Two", id=222)

    mock_bot = SimpleNamespace(
        guilds=[mock_guild1, mock_guild2]
    )

    with patch("main.bot", mock_bot), \
        patch("main.generate_daily_stats") as mock_generate:

        mock_generate.side_effect = [
            Exception("Database failure"),
            None
        ]

        await main.daily_stats_task.coro()

        mock_generate.assert_any_call(mock_guild1)
        mock_generate.assert_any_call(mock_guild2)

        captured = capsys.readouterr()

        assert "Failed to generate daily stats for guild: Guild One (id: 111)" in captured.out
        assert "Error: Database failure" in captured.out
        assert "Generated daily stats for guild: Guild Two (id: 222)" in captured.out

# test that daily_stats_task starts when not already running
@pytest.mark.asyncio
async def test_on_ready_starts_daily_stats_task():
    mock_guild = SimpleNamespace(name="Guild One", id=111)

    mock_bot = SimpleNamespace(
        guilds=[mock_guild],
        user=SimpleNamespace(name="TestBot", id=123)
    )

    with patch("main.bot", mock_bot), \
        patch("main.db_init"), \
        patch("main.generate_daily_stats"), \
        patch.object(main.daily_stats_task, "is_running", return_value=False), \
        patch.object(main.daily_stats_task, "start") as mock_start:

        await main.on_ready()

        mock_start.assert_called_once()

# test that daily_stats_task does not start when already running
@pytest.mark.asyncio
async def test_on_ready_does_not_restart_daily_stats_task():
    mock_guild = SimpleNamespace(name="Guild One", id=111)

    mock_bot = SimpleNamespace(
        guilds=[mock_guild],
        user=SimpleNamespace(name="TestBot", id=123)
    )

    with patch("main.bot", mock_bot), \
        patch("main.db_init"), \
        patch("main.generate_daily_stats"), \
        patch.object(main.daily_stats_task, "is_running", return_value=True), \
        patch.object(main.daily_stats_task, "start") as mock_start:

        await main.on_ready()

        mock_start.assert_not_called()

# test judge
@pytest.mark.asyncio
async def test_judge():
    mock_ctx = SimpleNamespace(
    guild=SimpleNamespace(id=123),
    author=SimpleNamespace(id=456, mention="@author"),
    send=AsyncMock()
    )

    with patch("main.get_daily_stats", return_value={"cringe": 42, "sus": 69}):
        await main.judge.callback(mock_ctx) # type: ignore
 
    mock_ctx.send.assert_called_once_with("@member is 42% cringe and 69% sus today.") # verify that the final output is correct

# test judge with member argument
@pytest.mark.asyncio
async def test_judge_with_member():
    mock_member = SimpleNamespace(id=789, mention="@member")
    mock_ctx = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(id=456, mention="@author"),
        send=AsyncMock()
    )

    with patch(
        "main.get_daily_stats",
        return_value={"cringe": 42, "sus": 69}
        ) as mock_get_stats:
        await main.judge.callback(mock_ctx, member=mock_member)  # type: ignore

    mock_get_stats.assert_called_once_with(123, "789") #verify that get_daily_stats was called with the correct guild id and member id
    mock_ctx.send.assert_called_once_with("@member is 42% cringe and 69% sus today.") # verify that the final output is correct

# test judge missing stats fallback
@pytest.mark.asyncio
async def test_judge_missing_stats():
    mock_ctx = SimpleNamespace(
        guild=SimpleNamespace(id=123),
        author=SimpleNamespace(id=456, mention="@author"),
        send=AsyncMock()
    )

    with patch(
        "main.get_daily_stats",
        side_effect=[
            {"cringe": None, "sus": None},
            {"cringe": 42, "sus": 69}
        ]
    ) as mock_get_stats:
        with patch("main.generate_daily_stats") as mock_generate:
            await main.judge.callback(mock_ctx)  # type: ignore

    mock_generate.assert_called_once_with(mock_ctx.guild) # verify that fallback was triggered
    assert mock_get_stats.call_count == 2 # verify that fallback triggered a second call to get_daily_stats
    mock_ctx.send.assert_called_once_with("@author is 42% cringe and 69% sus today.") # verify that the final output is correct

# test judge command outside of a guild
@pytest.mark.asyncio
async def test_judge_outside_guild():
    mock_ctx = SimpleNamespace(
        guild=None,
        author=SimpleNamespace(id=456, mention="@author"),
        send=AsyncMock()
    )

    with pytest.raises(RuntimeError) as excinfo:
        await main.judge.callback(mock_ctx)  # type: ignore

    assert str(excinfo.value) == "judge command invoked outside of a guild"