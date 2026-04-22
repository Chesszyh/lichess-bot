"""Tests for per-game stream resilience."""

import json
from queue import Queue

import chess
import chess.engine
import pytest
import yaml
from requests.exceptions import ConnectionError as RequestsConnectionError

from lib import config as config_lib
from lib import lichess_bot
from lib.config import Configuration


GAME_ID = "game12345"
BOT_NAME = "ilovecatgirl"


def _game_full(moves: str, status: str = "started", winner: str | None = None) -> dict[str, object]:
    state: dict[str, object] = {
        "type": "gameState",
        "moves": moves,
        "wtime": 9000,
        "btime": 9000,
        "winc": 0,
        "binc": 0,
        "status": status,
    }
    if winner is not None:
        state["winner"] = winner

    return {
        "id": GAME_ID,
        "variant": {"key": "standard", "name": "Standard", "short": "Std"},
        "clock": {"initial": 60000, "increment": 0},
        "speed": "bullet",
        "perf": {"name": "Bullet"},
        "rated": True,
        "createdAt": 1600000000000,
        "white": {"id": "white", "name": "WhitePlayer", "rating": 2600},
        "black": {"id": "bot", "name": BOT_NAME, "title": "BOT", "rating": 2900},
        "initialFen": "startpos",
        "type": "gameFull",
        "state": state,
    }


def _game_state(moves: str, status: str = "started", winner: str | None = None) -> dict[str, object]:
    state: dict[str, object] = {
        "type": "gameState",
        "moves": moves,
        "wtime": 9000,
        "btime": 9000,
        "winc": 0,
        "binc": 0,
        "status": status,
    }
    if winner is not None:
        state["winner"] = winner
    return state


def _config() -> Configuration:
    with open("./config.yml.default") as file:
        raw_config = yaml.safe_load(file)

    raw_config["token"] = ""
    config_lib.insert_default_values(raw_config)
    raw_config["greeting"] = {
        "hello": "",
        "goodbye": "",
        "hello_spectators": "",
        "goodbye_spectators": "",
    }
    return Configuration(raw_config)


class _FakeResponse:
    def __init__(self, owner: "_FakeLichess", events: list[dict[str, object]], failure: Exception | None = None) -> None:
        self.owner = owner
        self.events = events
        self.failure = failure
        self.closed = False

    def iter_lines(self):
        for event in self.events:
            game_state = event["state"] if event.get("type") == "gameFull" else event
            if game_state.get("status") != "started":
                self.owner.active = False
            yield json.dumps(event).encode("utf-8")

        if self.failure is not None:
            raise self.failure

    def close(self) -> None:
        self.closed = True


class _FakeLichess:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.responses = responses
        self.stream_calls = 0
        self.moves_made: list[str] = []
        self.messages: list[tuple[str, str, str]] = []
        self.active = True
        self.baseUrl = "https://lichess.org/"

    def get_game_stream(self, game_id: str) -> _FakeResponse:
        assert game_id == GAME_ID
        response = self.responses[self.stream_calls]
        self.stream_calls += 1
        return response

    def make_move(self, game_id: str, move: chess.engine.PlayResult) -> None:
        assert game_id == GAME_ID
        self.moves_made.append(move.move.uci())

    def chat(self, game_id: str, room: str, text: str) -> None:
        self.messages.append((game_id, room, text))

    def accept_takeback(self, game_id: str, accept: bool) -> bool:
        return False

    def get_ongoing_games(self) -> list[dict[str, str]]:
        return [{"gameId": GAME_ID}] if self.active else []

    def get_game_pgn(self, game_id: str) -> str:
        return f'[Site "https://lichess.org/{game_id}"]\n*'

    def abort(self, game_id: str) -> None:
        self.active = False

    def resign(self, game_id: str) -> None:
        self.active = False


class _FakeEngine:
    def __init__(self) -> None:
        self.played: list[str] = []
        self.result_sent = False
        self._moves = iter(["e7e5", "b8c6"])

    def __enter__(self) -> "_FakeEngine":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def get_opponent_info(self, game) -> None:
        pass

    def get_pid(self) -> str:
        return "123"

    def play_move(self, board, game, li, setup_timer, move_overhead, can_ponder, is_correspondence,
                  correspondence_move_time, engine_cfg, min_time) -> None:
        move = chess.Move.from_uci(next(self._moves))
        self.played.append(move.uci())
        li.make_move(game.id, chess.engine.PlayResult(move, None))

    def send_game_result(self, game, board) -> None:
        self.result_sent = True

    def discard_last_move_commentary(self) -> None:
        pass

    def ping(self) -> None:
        pass

    def quit(self) -> None:
        pass

    def name(self) -> str:
        return "FakeEngine"

    def get_stats(self, for_chat: bool = False) -> list[str]:
        return []


@pytest.mark.parametrize("failure", [RequestsConnectionError("boom"), None], ids=["connection_error", "eof"])
def test_play_game__reconnects_after_midgame_stream_drop(monkeypatch, failure: Exception | None) -> None:
    """An active game should reopen the board stream after a transient drop."""
    config = _config()
    engine = _FakeEngine()
    li = _FakeLichess([])
    li.responses = [
        _FakeResponse(li, [_game_full(""), _game_state("e2e4")], failure),
        _FakeResponse(li, [_game_full("e2e4 e7e5 g1f3"),
                           _game_state("e2e4 e7e5 g1f3 b8c6", status="mate", winner="black")]),
    ]

    monkeypatch.setattr(lichess_bot, "thread_logging_configurer", lambda _: None)
    monkeypatch.setattr(lichess_bot.time, "sleep", lambda _: None)
    monkeypatch.setattr(lichess_bot.engine_wrapper, "create_engine", lambda cfg, game=None: engine)

    state = (lichess_bot.stop.terminated, lichess_bot.stop.force_quit, lichess_bot.stop.restart)
    lichess_bot.stop.terminated = False
    lichess_bot.stop.force_quit = False
    lichess_bot.stop.restart = False

    try:
        lichess_bot.play_game.__wrapped__(
            li=li,
            game_id=GAME_ID,
            control_queue=Queue(),
            user_profile={"username": BOT_NAME},
            config=config,
            challenge_queue=[],
            correspondence_queue=Queue(),
            logging_queue=Queue(),
            pgn_queue=Queue(),
        )
    finally:
        lichess_bot.stop.terminated, lichess_bot.stop.force_quit, lichess_bot.stop.restart = state

    assert li.stream_calls == 2
    assert li.moves_made == ["e7e5", "b8c6"]
    assert engine.played == ["e7e5", "b8c6"]
    assert engine.result_sent is True
