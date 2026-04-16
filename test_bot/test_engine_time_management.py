"""Tests for engine time-management helpers."""

from datetime import timedelta

import chess
import chess.engine

from lib.config import Configuration
from lib.engine_wrapper import EngineWrapper
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
