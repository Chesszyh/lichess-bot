"""Tests for engine time-management helpers."""

from datetime import timedelta

import chess
import chess.engine

from lib.config import Configuration
from lib.engine_wrapper import EngineWrapper, apply_bullet_time_management
from lib.lichess_types import GameEventType
from lib.model import Game


def draw_or_resign_cfg() -> Configuration:
    """Create a disabled draw/resign config for EngineWrapper tests."""
    return Configuration({
        "offer_draw_enabled": False,
        "offer_draw_moves": 5,
        "offer_draw_score": 0,
        "offer_draw_pieces": 10,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    })


def bullet_game(clock_ms: int = 60000) -> Game:
    """Create a bullet game where the bot is white and has clock_ms remaining."""
    game_event: GameEventType = {
        "id": "guard001",
        "variant": {"key": "standard", "name": "Standard", "short": "Std"},
        "clock": {"initial": 60000, "increment": 0},
        "speed": "bullet",
        "perf": {"name": "Bullet"},
        "rated": True,
        "createdAt": 1600000000000,
        "white": {"id": "bo", "name": "bo", "title": "BOT", "rating": 3000},
        "black": {"id": "alice", "name": "Alice", "title": None, "rating": 2500},
        "initialFen": "startpos",
        "type": "gameFull",
        "state": {
            "type": "gameState",
            "moves": "",
            "wtime": clock_ms,
            "btime": clock_ms,
            "winc": 0,
            "binc": 0,
            "status": "started",
        },
    }
    return Game(game_event, "bo", "https://lichess.org", timedelta(seconds=60))


def fast_game(speed: str, initial_ms: int, clock_ms: int) -> Game:
    """Create a realtime game with the bot as white."""
    game_event: GameEventType = {
        "id": f"{speed}001",
        "variant": {"key": "standard", "name": "Standard", "short": "Std"},
        "clock": {"initial": initial_ms, "increment": 0},
        "speed": speed,
        "perf": {"name": speed.title()},
        "rated": True,
        "createdAt": 1600000000000,
        "white": {"id": "bo", "name": "bo", "title": "BOT", "rating": 3000},
        "black": {"id": "alice", "name": "Alice", "title": None, "rating": 2500},
        "initialFen": "startpos",
        "type": "gameFull",
        "state": {
            "type": "gameState",
            "moves": "",
            "wtime": clock_ms,
            "btime": clock_ms,
            "winc": 0,
            "binc": 0,
            "status": "started",
        },
    }
    return Game(game_event, "bo", "https://lichess.org", timedelta(seconds=60))


class FakeEngine:
    """Engine protocol that returns predetermined depths."""

    id = {"name": "FakeEngine"}

    def __init__(self) -> None:
        self.calls: list[chess.engine.Limit] = []
        self._results = [
            chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
                "depth": 4,
                "score": chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE),
            }),
            chess.engine.PlayResult(chess.Move.from_uci("d2d4"), None, {
                "depth": 14,
                "score": chess.engine.PovScore(chess.engine.Cp(25), chess.WHITE),
            }),
        ]

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        self.calls.append(limit)
        return self._results.pop(0)


def test_search__extends_shallow_bullet_result_once() -> None:
    """A shallow result with safe clock should get one short follow-up search."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    fake_engine = FakeEngine()
    wrapper.engine = fake_engine
    engine_cfg = Configuration({
        "shallow_search_guard": {
            "enabled": True,
            "speeds": ["bullet"],
            "min_depth": 10,
            "extra_movetime_ms": 700,
            "min_clock_ms": 15000,
            "min_ply": 0,
        },
    })

    result = wrapper.search(chess.Board(),
                            chess.engine.Limit(white_clock=24, black_clock=24),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=bullet_game(),
                            engine_cfg=engine_cfg)

    assert result.move == chess.Move.from_uci("d2d4")
    assert len(fake_engine.calls) == 2
    assert fake_engine.calls[1].time == 0.7
    assert len(wrapper.scores) == 1
    assert wrapper.scores[0].relative.score() == 25


def test_apply_bullet_time_management__keeps_high_clock_blitz_uncapped() -> None:
    """Blitz with plenty of time should let Stockfish use normal clock management."""
    game = fast_game("blitz", 240000, 240000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "max_clock_ms": 12000,
            "high_clock_threshold_ms": 60000,
            "high_clock_ms": 8000,
            "low_clock_threshold_ms": 20000,
            "low_clock_ms": 3500,
            "critical_clock_threshold_ms": 8000,
            "critical_clock_ms": 900,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 180,
        },
    })

    limit = chess.engine.Limit(white_clock=240.0, black_clock=240.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.white_clock == 240.0
    assert capped.black_clock == 240.0


def test_apply_bullet_time_management__caps_low_clock_blitz_when_enabled() -> None:
    """Blitz caps should still protect the bot once its own clock is low."""
    game = fast_game("blitz", 240000, 59000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "max_clock_ms": 12000,
            "high_clock_threshold_ms": 60000,
            "high_clock_ms": 8000,
            "low_clock_threshold_ms": 20000,
            "low_clock_ms": 3500,
            "critical_clock_threshold_ms": 8000,
            "critical_clock_ms": 900,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 180,
        },
    })

    limit = chess.engine.Limit(white_clock=59.0, black_clock=240.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.white_clock == 8.0
    assert capped.black_clock == 240.0
