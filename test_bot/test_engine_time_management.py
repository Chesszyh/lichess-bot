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


class NamedFakeEngine:
    """Engine protocol that records calls and returns one fixed move."""

    def __init__(self, name: str, move: str) -> None:
        self.id = {"name": name}
        self.calls = 0
        self.move = chess.Move.from_uci(move)

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        self.calls += 1
        return chess.engine.PlayResult(self.move, None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(0), board.turn),
        })


class MateFakeEngine:
    """Engine protocol that returns a forcing mate score."""

    id = {"name": "MateFakeEngine"}

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        return chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Mate(8), board.turn),
        })


def test_search__uses_endgame_engine_under_piece_threshold() -> None:
    """Configured endgames should be searched by the secondary engine."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    main_engine = NamedFakeEngine("main", "e2e4")
    endgame_engine = NamedFakeEngine("endgame", "e2e3")
    wrapper.engine = main_engine
    wrapper.endgame_engine = endgame_engine
    wrapper.endgame_engine_max_pieces = 3

    board = chess.Board("4k3/8/8/8/8/8/4K3/8 w - - 0 1")
    result = wrapper.search(board,
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None))

    assert result.move == chess.Move.from_uci("e2e3")
    assert main_engine.calls == 0
    assert endgame_engine.calls == 1


def test_search__keeps_main_engine_above_endgame_threshold() -> None:
    """The secondary engine must not replace the main engine in normal middlegames."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    main_engine = NamedFakeEngine("main", "e2e4")
    endgame_engine = NamedFakeEngine("endgame", "e2e3")
    wrapper.engine = main_engine
    wrapper.endgame_engine = endgame_engine
    wrapper.endgame_engine_max_pieces = 3

    result = wrapper.search(chess.Board(),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None))

    assert result.move == chess.Move.from_uci("e2e4")
    assert main_engine.calls == 1
    assert endgame_engine.calls == 0


def test_search__records_forcing_mate_for_fast_win_time_management() -> None:
    """A positive mate score should make the next fast-game move eligible for the quick win cap."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    wrapper.engine = MateFakeEngine()

    wrapper.search(chess.Board(),
                   chess.engine.Limit(time=1.0),
                   ponder=False,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None))

    assert wrapper.last_search_was_forcing_mate


def test_record_search_result__does_not_treat_missing_score_as_forcing_mate() -> None:
    """Missing score data should not enable fast-win timing."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    result = chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {})

    wrapper.record_search_result(result, chess.Board())

    assert not wrapper.last_search_was_forcing_mate


def test_search__uses_endgame_engine_for_configured_queenless_positions() -> None:
    """Queenless technical positions can be handed to the secondary engine before low piece count."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    main_engine = NamedFakeEngine("main", "e2e4")
    endgame_engine = NamedFakeEngine("endgame", "e2e3")
    wrapper.engine = main_engine
    wrapper.endgame_engine = endgame_engine
    wrapper.endgame_engine_max_pieces = 7
    wrapper.endgame_engine_queenless_max_pieces = 32

    board = chess.Board("rnb1kbnr/pppp1ppp/8/8/8/8/PPPP1PPP/RNB1KBNR w KQkq - 0 1")
    result = wrapper.search(board,
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None))

    assert result.move == chess.Move.from_uci("e2e3")
    assert main_engine.calls == 0
    assert endgame_engine.calls == 1


def test_search__keeps_main_engine_for_queenless_positions_above_configured_limit() -> None:
    """Queenless handoff should still respect its configured piece ceiling."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    main_engine = NamedFakeEngine("main", "e2e4")
    endgame_engine = NamedFakeEngine("endgame", "e2e3")
    wrapper.engine = main_engine
    wrapper.endgame_engine = endgame_engine
    wrapper.endgame_engine_max_pieces = 7
    wrapper.endgame_engine_queenless_max_pieces = 20

    result = wrapper.search(chess.Board("rnb1kbnr/pppp1ppp/8/8/8/8/PPPP1PPP/RNB1KBNR w KQkq - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None))

    assert result.move == chess.Move.from_uci("e2e4")
    assert main_engine.calls == 1
    assert endgame_engine.calls == 0


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


def test_apply_bullet_time_management__can_force_movetime_caps() -> None:
    """Engines with loose clock management can receive an exact movetime cap."""
    game = fast_game("blitz", 240000, 59000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "force_movetime_caps": True,
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

    limit = chess.engine.Limit(white_clock=59.0, black_clock=240.0, white_inc=0.0, black_inc=0.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.time == 8.0
    assert capped.white_clock is None
    assert capped.black_clock is None
    assert capped.white_inc is None
    assert capped.black_inc is None


def test_apply_bullet_time_management__can_force_movetime_caps_on_high_clock() -> None:
    """A large threshold lets Lc0-style configs cap every fast-game move."""
    game = fast_game("blitz", 300000, 260000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "force_movetime_caps": True,
            "max_clock_ms": 8000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 5000,
            "low_clock_threshold_ms": 20000,
            "low_clock_ms": 2200,
            "critical_clock_threshold_ms": 8000,
            "critical_clock_ms": 700,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 100,
        },
    })

    limit = chess.engine.Limit(white_clock=260.0, black_clock=260.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.time == 5.0
    assert capped.white_clock is None
    assert capped.black_clock is None


def test_apply_bullet_time_management__can_limit_high_clock_without_forcing_movetime() -> None:
    """High-clock Lc0 configs can cap the reported clock while preserving engine time management."""
    game = fast_game("blitz", 300000, 220000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "force_movetime_caps": True,
            "force_movetime_threshold_ms": 30000,
            "max_clock_ms": 30000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 30000,
            "low_clock_threshold_ms": 30000,
            "low_clock_ms": 5000,
            "critical_clock_threshold_ms": 5000,
            "critical_clock_ms": 1000,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 500,
        },
    })

    limit = chess.engine.Limit(white_clock=220.0, black_clock=220.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.time is None
    assert capped.white_clock == 30.0
    assert capped.black_clock == 220.0


def test_apply_bullet_time_management__adds_hard_cap_while_preserving_clock_management() -> None:
    """Lc0 can receive clock data and a movetime watchdog in the same fast-game search."""
    game = fast_game("blitz", 300000, 220000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "force_movetime_caps": True,
            "force_movetime_threshold_ms": 30000,
            "hard_movetime_caps": True,
            "max_clock_ms": 30000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 30000,
            "low_clock_threshold_ms": 30000,
            "low_clock_ms": 5000,
            "critical_clock_threshold_ms": 5000,
            "critical_clock_ms": 1000,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 500,
        },
    })

    limit = chess.engine.Limit(white_clock=220.0, black_clock=220.0, white_inc=2.0, black_inc=2.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.time == 30.0
    assert capped.white_clock == 30.0
    assert capped.black_clock == 220.0
    assert capped.white_inc == 2.0
    assert capped.black_inc == 2.0


def test_apply_bullet_time_management__forces_movetime_under_threshold() -> None:
    """Once the bot clock is low, cap the move with exact movetime."""
    game = fast_game("blitz", 300000, 29000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "force_movetime_caps": True,
            "force_movetime_threshold_ms": 30000,
            "max_clock_ms": 30000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 30000,
            "low_clock_threshold_ms": 30000,
            "low_clock_ms": 5000,
            "critical_clock_threshold_ms": 5000,
            "critical_clock_ms": 1000,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 500,
        },
    })

    limit = chess.engine.Limit(white_clock=29.0, black_clock=220.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.time == 5.0
    assert capped.white_clock is None
    assert capped.black_clock is None


def test_apply_bullet_time_management__uses_fast_win_cap_after_forcing_mate() -> None:
    """Once a forced mate is known, low-clock blitz should convert quickly instead of using the full low cap."""
    game = fast_game("blitz", 300000, 24000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "force_movetime_caps": True,
            "force_movetime_threshold_ms": 30000,
            "max_clock_ms": 30000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 30000,
            "low_clock_threshold_ms": 30000,
            "low_clock_ms": 5000,
            "critical_clock_threshold_ms": 5000,
            "critical_clock_ms": 1000,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 500,
            "winning_mate_clock_threshold_ms": 30000,
            "winning_mate_clock_ms": 1000,
        },
    })

    limit = chess.engine.Limit(white_clock=24.0, black_clock=220.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg, fast_win=True)

    assert capped.time == 1.0
    assert capped.white_clock is None
    assert capped.black_clock is None
