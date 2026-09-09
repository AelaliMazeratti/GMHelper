import pytest
from types import SimpleNamespace
from unittest.mock import patch

import main

# test bot startup sequence
@pytest.mark.asyncio
async def test_on_ready_db_init_failure(capsys):
    mock_guild1 = SimpleNamespace(name="Guild One", id=111)
    mock_guild2 = SimpleNamespace(name="Guild Two", id=222)

    mock_bot = SimpleNamespace(guilds=[mock_guild1, mock_guild2], user=SimpleNamespace(name="TestBot", id=123))

    # test that db_init is called for each guild and handles exceptions
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

