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
                           [],
                           set())

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
                           [],
                           set())

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
                           [],
                           set())

    assert started == ["reserved123"]


class FakeQueue:
    """Small queue stub for correspondence start tests."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def put_nowait(self, item: str) -> None:
        self.items.append(item)

    def qsize(self) -> int:
        return len(self.items)

    def get_nowait(self) -> str:
        return self.items.pop(0)

    def task_done(self) -> None:
        pass


def test_start_game__ignores_duplicate_queued_correspondence_game(monkeypatch) -> None:
    """A correspondence game queued for later must not start from a duplicate gameStart."""
    started: list[str] = []
    queue = FakeQueue()
    pending_games: set[str] = set()
    config = Configuration({
        "url": "https://lichess.org/",
        "correspondence": {"checkin_period": 300, "move_time": 60},
    })
    monkeypatch.setattr(lichess_bot, "start_game_thread",
                        lambda _active_games, _started_games, game_id, _play_game_args, _pool: started.append(game_id))
    event = {"type": "gameStart", "game": {"id": "corr123", "isMyTurn": False}}

    lichess_bot.start_game(event, object(), {}, config, ["corr123"], queue, set(), set(), [], pending_games)
    lichess_bot.start_game(event, object(), {}, config, [], queue, set(), set(), [], pending_games)

    assert queue.items == ["corr123"]
    assert pending_games == {"corr123"}
    assert started == []


def test_start_low_time_games__removes_pending_when_worker_starts(monkeypatch) -> None:
    """Pending low-time correspondence state should clear once the worker starts."""
    started: list[str] = []
    pending_games = {"low123"}
    monkeypatch.setattr(lichess_bot, "start_game_thread",
                        lambda _active_games, _started_games, game_id, _play_game_args, _pool: started.append(game_id))

    lichess_bot.start_low_time_games([{"id": "low123"}], set(), set(), 1, object(), {}, pending_games)

    assert pending_games == set()
    assert started == ["low123"]


def test_check_in_on_correspondence_games__removes_pending_when_worker_starts(monkeypatch) -> None:
    """A queued correspondence game is no longer pending once its worker starts."""
    started: list[str] = []
    queue = FakeQueue()
    queue.put_nowait("corr456")
    pending_games = {"corr456"}
    monkeypatch.setattr(lichess_bot, "start_game_thread",
                        lambda _active_games, _started_games, game_id, _play_game_args, _pool: started.append(game_id))

    lichess_bot.check_in_on_correspondence_games(object(),
                                                {"type": "correspondence_ping"},
                                                queue,
                                                [],
                                                {},
                                                set(),
                                                set(),
                                                1,
                                                pending_games)

    assert pending_games == set()
    assert started == ["corr456"]
