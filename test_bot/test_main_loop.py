"""Tests for top-level game event handling."""

from lib import lichess_bot
from lib.config import Configuration


def test_start_game__ignores_duplicate_game_start(monkeypatch) -> None:
    """A repeated gameStart event for an active game must not spawn a second worker."""
    started: list[str] = []
    monkeypatch.setattr(lichess_bot, "start_game_thread",
                        lambda _active_games, _started_games, game_id, _play_game_args, _pool: started.append(game_id))

    lichess_bot.start_game({"type": "gameStart", "game": {"id": "dup123"}},
                           object(),
                           {},
                           Configuration({"url": "https://lichess.org/"}),
                           [],
                           object(),
                           {"dup123"},
                           {"dup123"},
                           [])

    assert started == []


def test_start_game__starts_new_game(monkeypatch) -> None:
    """A new gameStart event should still spawn a worker."""
    started: list[str] = []
    monkeypatch.setattr(lichess_bot, "start_game_thread",
                        lambda _active_games, _started_games, game_id, _play_game_args, _pool: started.append(game_id))

    lichess_bot.start_game({"type": "gameStart", "game": {"id": "new123"}},
                           object(),
                           {},
                           Configuration({"url": "https://lichess.org/"}),
                           [],
                           object(),
                           set(),
                           set(),
                           [])

    assert started == ["new123"]


def test_start_game__starts_reserved_accepted_challenge(monkeypatch) -> None:
    """A challenge reserved in active_games should still start on its first gameStart."""
    started: list[str] = []
    monkeypatch.setattr(lichess_bot, "start_game_thread",
                        lambda _active_games, _started_games, game_id, _play_game_args, _pool: started.append(game_id))

    lichess_bot.start_game({"type": "gameStart", "game": {"id": "reserved123"}},
                           object(),
                           {},
                           Configuration({"url": "https://lichess.org/"}),
                           [],
                           object(),
                           {"reserved123"},
                           set(),
                           [])

    assert started == ["reserved123"]
