"""Tests for engine time-management helpers."""

from datetime import timedelta
from typing import cast

import chess
import chess.engine

from lib.config import Configuration
from lib.engine_wrapper import EngineWrapper, FillerEngine, apply_bullet_time_management
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


class WorseFollowUpFakeEngine:
    """Engine protocol whose follow-up search is shallower than the original result."""

    id = {"name": "WorseFollowUpFakeEngine"}

    def __init__(self) -> None:
        self.calls: list[chess.engine.Limit] = []
        self._results = [
            chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
                "depth": 8,
                "score": chess.engine.PovScore(chess.engine.Cp(20), chess.WHITE),
            }),
            chess.engine.PlayResult(chess.Move.from_uci("d2d4"), None, {
                "depth": 4,
                "score": chess.engine.PovScore(chess.engine.Cp(-20), chess.WHITE),
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


class WinningScoreFakeEngine:
    """Engine protocol that returns a large positive centipawn score."""

    id = {"name": "WinningScoreFakeEngine"}

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        return chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(900), board.turn),
        })


class DrawishFakeEngine:
    """Engine protocol that returns a near-equal score."""

    id = {"name": "DrawishFakeEngine"}

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        return chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
            "depth": 20,
            "score": chess.engine.PovScore(chess.engine.Cp(10), board.turn),
        })


class RepetitionFakeEngine:
    """Engine protocol that exposes root move filtering behavior."""

    def __init__(self, repeated_move: str) -> None:
        """Create a fake engine that falls back to repeated_move when no root moves are supplied."""
        self.id = {"name": "RepetitionFakeEngine"}
        self.repeated_move = chess.Move.from_uci(repeated_move)
        self.root_moves: list[chess.Move] | None = None

    def play(self,
             board: chess.Board,
             _limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        """Record root moves and return the first available move."""
        del info, ponder, draw_offered
        self.root_moves = root_moves
        move = root_moves[0] if root_moves else self.repeated_move
        return chess.engine.PlayResult(move, None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(0), board.turn),
        })


class IgnoringRootMovesRepetitionFakeEngine(RepetitionFakeEngine):
    """Engine protocol that records root moves but returns the repeated move anyway."""

    def play(self,
             board: chess.Board,
             _limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        """Record root moves and return the repeated move."""
        del board, info, ponder, draw_offered
        self.root_moves = root_moves
        return chess.engine.PlayResult(self.repeated_move, None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE),
        })


class LosingAlternativeRepetitionFakeEngine(RepetitionFakeEngine):
    """Engine protocol where avoiding an immediate repetition is much worse."""

    def play(self,
             board: chess.Board,
             _limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        """Return a drawish repeated move unless root moves force a bad alternative."""
        del board, info, ponder, draw_offered
        self.root_moves = root_moves
        if root_moves and self.repeated_move not in root_moves:
            return chess.engine.PlayResult(root_moves[0], None, {
                "depth": 20,
                "score": chess.engine.PovScore(chess.engine.Cp(-600), chess.WHITE),
            })

        return chess.engine.PlayResult(self.repeated_move, None, {
            "depth": 20,
            "score": chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE),
        })


def high_rated_draw_cfg() -> Configuration:
    """Create draw config that accepts stable equal positions from elite opponents."""
    return Configuration({
        "offer_draw_enabled": True,
        "offer_draw_moves": 10,
        "offer_draw_score": 0,
        "offer_draw_pieces": 10,
        "high_rated_accept_draw_enabled": True,
        "high_rated_accept_draw_min_rating": 3000,
        "high_rated_accept_draw_moves": 2,
        "high_rated_accept_draw_score": 25,
        "high_rated_accept_draw_pieces": 32,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    })


def lower_rated_draw_guard_cfg() -> Configuration:
    """Create draw config that refuses normal draw offers when we substantially outrate the opponent."""
    return Configuration({
        "offer_draw_enabled": True,
        "offer_draw_moves": 2,
        "offer_draw_score": 25,
        "offer_draw_pieces": 32,
        "offer_draw_rating_gap_limit": 40,
        "high_rated_accept_draw_enabled": False,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    })


def target_floor_draw_cfg() -> Configuration:
    """Create draw config that only proactively offers normal draws inside the target rating band."""
    return Configuration({
        "offer_draw_enabled": True,
        "offer_draw_moves": 2,
        "offer_draw_score": 25,
        "offer_draw_pieces": 32,
        "offer_draw_rating_gap_limit": 0,
        "offer_draw_min_rating": 3080,
        "high_rated_accept_draw_enabled": False,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    })


def high_rated_blitz_game(opponent_rating: int = 3060) -> Game:
    """Create a blitz game against a high-rated bot opponent."""
    game = fast_game("blitz", 180000, 120000)
    game.black.rating = opponent_rating
    game.black.title = "BOT"
    game.black.is_bot = True
    return game


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


def test_search__records_winning_score_for_fast_win_time_management() -> None:
    """A large positive score should make the next fast-game move eligible for the quick win cap."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    wrapper.engine = WinningScoreFakeEngine()

    wrapper.search(chess.Board(),
                   chess.engine.Limit(time=1.0),
                   ponder=False,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None))

    assert wrapper.last_search_score_cp == 900


def test_search__accepts_high_rated_draw_offer_in_stable_equal_endgame() -> None:
    """A high-rated opponent's draw offer should be accepted in a stable equal simplified position."""
    wrapper = EngineWrapper({}, high_rated_draw_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=True,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(),
                            engine_cfg=Configuration({}))

    assert result.draw_offered


def test_search__does_not_accept_high_rated_draw_rule_without_incoming_offer() -> None:
    """The elite draw rule should not make us offer draws proactively."""
    wrapper = EngineWrapper({}, high_rated_draw_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(),
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__does_not_accept_high_rated_draw_rule_for_lower_rated_opponent() -> None:
    """The elite draw rule should not accept offers from ordinary lower-rated opponents."""
    wrapper = EngineWrapper({}, high_rated_draw_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=True,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=2700),
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__does_not_accept_normal_draw_offer_when_lower_rated_gap_exceeds_limit() -> None:
    """The normal draw rule should keep playing against lower-rated opponents when configured."""
    wrapper = EngineWrapper({}, lower_rated_draw_guard_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=True,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=2950),
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__does_not_offer_normal_draw_below_target_rating_floor() -> None:
    """The normal draw rule should not voluntarily lock in draws below the target opponent band."""
    wrapper = EngineWrapper({}, target_floor_draw_cfg())
    wrapper.engine = cast(FillerEngine, DrawishFakeEngine())
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=3060),
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__offers_normal_draw_at_target_rating_floor() -> None:
    """The target floor should still allow normal draw offers against target-band opponents."""
    wrapper = EngineWrapper({}, target_floor_draw_cfg())
    wrapper.engine = cast(FillerEngine, DrawishFakeEngine())
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=3080),
                            engine_cfg=Configuration({}))

    assert result.draw_offered


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


def test_search__keeps_original_result_when_shallow_extension_is_worse() -> None:
    """A follow-up shallow search should not replace a deeper original result."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    fake_engine = WorseFollowUpFakeEngine()
    wrapper.engine = fake_engine
    engine_cfg = Configuration({
        "shallow_search_guard": {
            "enabled": True,
            "speeds": ["blitz"],
            "min_depth": 12,
            "extra_movetime_ms": 1200,
            "min_clock_ms": 30000,
            "min_ply": 0,
        },
    })

    result = wrapper.search(chess.Board(),
                            chess.engine.Limit(white_clock=180, black_clock=180),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=fast_game("blitz", 180000, 180000),
                            engine_cfg=engine_cfg)

    assert result.move == chess.Move.from_uci("e2e4")
    assert result.info["depth"] == 8
    assert len(fake_engine.calls) == 2


def test_search__filters_immediate_threefold_repetition_when_enabled() -> None:
    """Against lower-rated bots, do not let the engine choose an immediate threefold repetition."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    fake_engine = RepetitionFakeEngine("d7g4")
    wrapper.engine = fake_engine
    board = chess.Board()
    for move in ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "f8c5",
                 "c1e3", "d8f6", "c2c3", "g8e7", "f1c4", "c6e5", "c4e2", "f6g6",
                 "e1g1", "d7d6", "f1e1", "c8h3", "e2f1", "h3g4", "f1e2", "g4h3",
                 "e2f1", "h3g4", "d1a4", "g4d7", "a4d1"]:
        board.push(chess.Move.from_uci(move))
    repeated_move = chess.Move.from_uci("d7g4")
    repeated_board = board.copy(stack=True)
    repeated_board.push(repeated_move)
    assert repeated_board.is_repetition(3)
    engine_cfg = Configuration({
        "repetition_guard": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
        },
    })

    result = wrapper.search(board,
                            chess.engine.Limit(white_clock=60, black_clock=60),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=bullet_game(),
                            engine_cfg=engine_cfg)

    assert fake_engine.root_moves
    assert repeated_move not in fake_engine.root_moves
    assert result.move != repeated_move


def test_search__does_not_play_filtered_repetition_if_engine_returns_it() -> None:
    """Do not trust an engine result that violates repetition-guard root moves."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    fake_engine = IgnoringRootMovesRepetitionFakeEngine("d7g4")
    wrapper.engine = cast(FillerEngine, fake_engine)
    board = chess.Board()
    for move in ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "f8c5",
                 "c1e3", "d8f6", "c2c3", "g8e7", "f1c4", "c6e5", "c4e2", "f6g6",
                 "e1g1", "d7d6", "f1e1", "c8h3", "e2f1", "h3g4", "f1e2", "g4h3",
                 "e2f1", "h3g4", "d1a4", "g4d7", "a4d1"]:
        board.push(chess.Move.from_uci(move))
    repeated_move = chess.Move.from_uci("d7g4")
    repeated_board = board.copy(stack=True)
    repeated_board.push(repeated_move)
    assert repeated_board.is_repetition(3)
    engine_cfg = Configuration({
        "repetition_guard": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
        },
    })

    result = wrapper.search(board,
                            chess.engine.Limit(white_clock=60, black_clock=60),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=bullet_game(),
                            engine_cfg=engine_cfg)

    assert fake_engine.root_moves
    assert repeated_move not in fake_engine.root_moves
    assert result.move in fake_engine.root_moves
    assert result.move != repeated_move


def test_search__keeps_repetition_when_safe_alternative_loses_too_much() -> None:
    """Avoiding a repetition should not force a clearly losing move."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    fake_engine = LosingAlternativeRepetitionFakeEngine("d7g4")
    wrapper.engine = cast(FillerEngine, fake_engine)
    board = chess.Board()
    for move in ["e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4", "f8c5",
                 "c1e3", "d8f6", "c2c3", "g8e7", "f1c4", "c6e5", "c4e2", "f6g6",
                 "e1g1", "d7d6", "f1e1", "c8h3", "e2f1", "h3g4", "f1e2", "g4h3",
                 "e2f1", "h3g4", "d1a4", "g4d7", "a4d1"]:
        board.push(chess.Move.from_uci(move))
    repeated_move = chess.Move.from_uci("d7g4")
    repeated_board = board.copy(stack=True)
    repeated_board.push(repeated_move)
    assert repeated_board.is_repetition(3)
    engine_cfg = Configuration({
        "repetition_guard": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "max_score_loss_cp": 150,
        },
    })

    result = wrapper.search(board,
                            chess.engine.Limit(white_clock=60, black_clock=60),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=bullet_game(),
                            engine_cfg=engine_cfg)

    assert result.move == repeated_move


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


def test_apply_bullet_time_management__uses_fast_win_cap_after_large_winning_score() -> None:
    """A large previous score should reduce low-clock conversion time without requiring mate."""
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
            "winning_score_threshold_cp": 800,
            "winning_score_clock_threshold_ms": 30000,
            "winning_score_clock_ms": 1500,
        },
    })

    limit = chess.engine.Limit(white_clock=24.0, black_clock=220.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg, last_score_cp=900)

    assert capped.time == 1.5
    assert capped.white_clock is None
    assert capped.black_clock is None


def test_apply_bullet_time_management__caps_equal_simplified_blitz_positions() -> None:
    """Stable equal simplified blitz positions should not burn the full high-clock watchdog."""
    game = fast_game("blitz", 300000, 270000)
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
            "equal_simplified_score_threshold_cp": 25,
            "equal_simplified_piece_threshold": 12,
            "equal_simplified_clock_threshold_ms": 600000,
            "equal_simplified_clock_ms": 4000,
        },
    })
    board = chess.Board("8/8/8/4k3/8/4K3/8/8 w - - 0 1")

    limit = chess.engine.Limit(white_clock=270.0, black_clock=270.0, white_inc=2.0, black_inc=2.0)
    capped = apply_bullet_time_management(board, game, limit, engine_cfg, last_score_cp=10)

    assert capped.time == 4.0
    assert capped.white_clock == 4.0
    assert capped.black_clock == 270.0


def test_apply_bullet_time_management__keeps_complex_equal_blitz_positions_uncapped_by_equal_rule() -> None:
    """The equal-position cap should not shorten complex middlegames just because the score is near 0."""
    game = fast_game("blitz", 300000, 270000)
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
            "equal_simplified_score_threshold_cp": 25,
            "equal_simplified_piece_threshold": 12,
            "equal_simplified_clock_threshold_ms": 600000,
            "equal_simplified_clock_ms": 4000,
        },
    })

    limit = chess.engine.Limit(white_clock=270.0, black_clock=270.0, white_inc=2.0, black_inc=2.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg, last_score_cp=10)

    assert capped.time == 30.0
    assert capped.white_clock == 30.0
    assert capped.black_clock == 270.0


def test_apply_bullet_time_management__prefers_blitz_time_management_for_blitz() -> None:
    """If blitz_time_management is defined and enabled, it should be preferred over bullet_time_management for blitz."""
    game = fast_game("blitz", 300000, 270000)
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet"],
            "max_clock_ms": 10000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 10000,
            "low_clock_threshold_ms": 0,
            "low_clock_ms": 0,
            "critical_clock_threshold_ms": 0,
            "critical_clock_ms": 0,
            "emergency_clock_threshold_ms": 0,
            "emergency_clock_ms": 0,
        },
        "blitz_time_management": {
            "enabled": True,
            "max_clock_ms": 120000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 120000,
            "low_clock_threshold_ms": 0,
            "low_clock_ms": 0,
            "critical_clock_threshold_ms": 0,
            "critical_clock_ms": 0,
            "emergency_clock_threshold_ms": 0,
            "emergency_clock_ms": 0,
        }
    })

    limit = chess.engine.Limit(white_clock=270.0, black_clock=270.0)
    capped = apply_bullet_time_management(chess.Board(), game, limit, engine_cfg)

    assert capped.white_clock == 120.0
