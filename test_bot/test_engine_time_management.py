"""Tests for engine time-management helpers."""

from datetime import timedelta

import chess
import chess.engine

from lib.config import Configuration
from lib.engine_wrapper import EngineWrapper, apply_bullet_time_management
from lib.lichess_types import GameEventType
from lib.model import Game
from lib.timer import Timer


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


def repetition_draw_board() -> chess.Board:
    """Recreate the YDxZJH1Q position where Kd2-e1 allows a repetition draw claim."""
    board = chess.Board()
    for move in [
        "e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6", "e1g1", "f6e4",
        "f1e1", "e4d6", "f3e5", "f8e7", "b5f1", "c6e5", "e1e5", "e8g8",
        "d2d4", "d6e8", "d4d5", "d7d6", "e5e1", "e7g5", "b1c3", "g5c1",
        "a1c1", "c8f5", "d1f3", "f5g6", "c3e2", "e8f6", "e2d4", "f8e8",
        "f3b3", "a8b8", "e1e8", "d8e8", "c2c4", "a7a6", "h2h3", "c7c5",
        "d5c6", "b7c6", "b3a3", "c6c5", "d4e2", "e8e5", "a3a6", "f6e4",
        "c1d1", "h7h5", "b2b3", "b8e8", "a6c6", "e4f2", "g1f2", "e5e3",
        "f2e1", "e3g3", "e1d2", "g3e3", "d2e1", "e3g3", "e1d2", "g3g5",
        "d2e1", "g5h4", "e1d2", "h4g5",
    ]:
        board.push_uci(move)
    return board


def mzn_bgmqz_depth_eleven_miss_board() -> chess.Board:
    """Recreate the MznBGMQZ position before 35.Rd2 was accepted at shallow depth."""
    board = chess.Board()
    for move in [
        "d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4", "e2e3", "e8g8",
        "f1d3", "d7d5", "a2a3", "d5c4", "d3c4", "b4c3", "b2c3", "c7c5",
        "c4d3", "d8c7", "g1e2", "b8c6", "e1g1", "e6e5", "e2g3", "c8e6",
        "f2f4", "e5d4", "c3d4", "a8d8", "a1b1", "a7a6", "h2h3", "h7h6",
        "c1b2", "c5d4", "e3e4", "f6d7", "d1c2", "d8c8", "e4e5", "c7a5",
        "c2e2", "d7c5", "g3h5", "c5d3", "e2d3", "g8h8", "d3g3", "f8g8",
        "f4f5", "e6c4", "f1e1", "a5d2", "b2a1", "c6e7", "g3g4", "d4d3",
        "g1h2", "b7b5", "b1d1", "d2f2", "e5e6", "f7f6", "e1f1", "f2e2",
        "f1e1", "e2c2", "g4f4", "c4d5",
    ]:
        board.push_uci(move)
    return board


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


class PonderRecordingFakeEngine:
    """Engine protocol that records whether play was allowed to ponder."""

    id = {"name": "PonderRecordingFakeEngine"}

    def __init__(self) -> None:
        self.ponder_calls: list[bool] = []

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        self.ponder_calls.append(ponder)
        return chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(0), board.turn),
        })


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


class DepthElevenThenThirteenFakeEngine:
    """Engine protocol that reproduces a high-rated bot tactical miss depth pattern."""

    id = {"name": "DepthElevenThenThirteenFakeEngine"}

    def __init__(self) -> None:
        self.calls: list[chess.engine.Limit] = []
        self._results = [
            chess.engine.PlayResult(chess.Move.from_uci("d1d2"), None, {
                "depth": 11,
                "score": chess.engine.PovScore(chess.engine.Cp(-21), chess.WHITE),
            }),
            chess.engine.PlayResult(chess.Move.from_uci("f4d2"), None, {
                "depth": 13,
                "score": chess.engine.PovScore(chess.engine.Cp(-5), chess.WHITE),
            }),
        ]

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        _ = board, info, ponder, draw_offered, root_moves
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


class PonderingNamedFakeEngine(NamedFakeEngine):
    """Engine protocol that records ping cleanup and can return a ponder move."""

    def __init__(self, name: str, move: str, ponder: str | None = None) -> None:
        """Initialize a fake engine with an optional ponder response."""
        super().__init__(name, move)
        self.ponder = chess.Move.from_uci(ponder) if ponder else None
        self.pings = 0

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        """Record a search and return a configured move plus optional ponder."""
        _ = limit, info, ponder, draw_offered, root_moves
        self.calls += 1
        return chess.engine.PlayResult(self.move, self.ponder, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(0), board.turn),
        })

    def ping(self) -> None:
        """Record that a pending ponder search was stopped."""
        self.pings += 1


class RootMovesRecordingFakeEngine:
    """Engine protocol that records root move restrictions."""

    def __init__(self) -> None:
        """Initialize storage for root move calls."""
        self.id = {"name": "RootMovesRecordingFakeEngine"}
        self.root_move_calls: list[list[chess.Move] | None] = []

    def play(self,
             board: chess.Board,
             limit: chess.engine.Limit,
             info: chess.engine.Info = chess.engine.INFO_NONE,
             ponder: bool = False,
             draw_offered: bool = False,
             root_moves: list[chess.Move] | None = None) -> chess.engine.PlayResult:
        """Record root moves and return the first legal allowed move."""
        _ = limit, info, ponder, draw_offered
        self.root_move_calls.append(root_moves)
        move = root_moves[0] if root_moves else next(iter(board.legal_moves))
        return chess.engine.PlayResult(move, None, {
            "depth": 8,
            "score": chess.engine.PovScore(chess.engine.Cp(20), board.turn),
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


class GameFinishRaceEngineWrapper(EngineWrapper):
    """Engine wrapper whose search observes a game finish before returning a move."""

    def __init__(self, game: Game) -> None:
        super().__init__({}, draw_or_resign_cfg())
        self.game = game

    def search(self,
               board: chess.Board,
               time_limit: chess.engine.Limit,
               ponder: bool,
               draw_offered: bool,
               root_moves: chess.engine.PlayResult) -> chess.engine.PlayResult:
        self.game.state["status"] = "draw"
        return chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, {
            "depth": 12,
            "score": chess.engine.PovScore(chess.engine.Cp(0), board.turn),
        })


class MoveRecordingLichess:
    """Minimal Lichess fake that records move submissions."""

    def __init__(self) -> None:
        self.moves_made: list[str] = []
        self.resigns = 0

    def make_move(self, game_id: str, move: chess.engine.PlayResult) -> None:
        self.moves_made.append(move.move.uci())

    def resign(self, game_id: str) -> None:
        self.resigns += 1

    def abort(self, game_id: str) -> None:
        self.resigns += 1


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
        "high_rated_accept_draw_clock_pressure_enabled": False,
        "high_rated_accept_draw_clock_pressure_own_clock_ms": 30000,
        "high_rated_accept_draw_clock_pressure_opponent_clock_ms": 15000,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    })


def generic_draw_offer_cfg() -> Configuration:
    """Create draw config whose proactive offer rule triggers quickly."""
    return Configuration({
        "offer_draw_enabled": True,
        "offer_draw_moves": 2,
        "offer_draw_score": 25,
        "offer_draw_pieces": 6,
        "high_rated_accept_draw_enabled": True,
        "high_rated_accept_draw_min_rating": 3100,
        "high_rated_accept_draw_moves": 2,
        "high_rated_accept_draw_score": 25,
        "high_rated_accept_draw_pieces": 10,
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


def disabled_external_move_cfg() -> Configuration:
    """Create engine config that forces normal engine search."""
    return Configuration({
        "polyglot": {
            "enabled": False,
            "max_depth": 8,
            "selection": "weighted_random",
            "min_weight": 1,
            "normalization": "none",
            "opponent_selection": {},
        },
        "online_moves": {
            "online_egtb": {
                "enabled": False,
                "source": "lichess",
                "min_time": 20,
                "max_time": 10800,
                "max_pieces": 7,
                "move_quality": "best",
            },
            "max_out_of_book_moves": 1,
            "max_depth": 0,
            "chessdb_book": {
                "enabled": False,
                "min_time": 20,
                "max_time": 10800,
                "move_quality": "good",
                "min_depth": 20,
            },
            "lichess_cloud_analysis": {
                "enabled": False,
                "min_time": 20,
                "max_time": 10800,
                "move_quality": "best",
                "min_depth": 20,
                "min_knodes": 0,
                "max_score_difference": 50,
            },
            "lichess_opening_explorer": {
                "enabled": False,
                "min_time": 20,
                "max_time": 10800,
                "source": "masters",
                "player_name": "",
                "sort": "winrate",
                "min_games": 10,
            },
        },
        "draw_or_resign": draw_or_resign_cfg().config,
        "lichess_bot_tbs": {
            "syzygy": {"enabled": False},
            "gaviota": {"enabled": False},
        },
    })


def test_play_move__does_not_send_move_after_game_finishes_during_search() -> None:
    """A gameFinish racing with search completion must not produce a stale move POST."""
    game = bullet_game()
    wrapper = GameFinishRaceEngineWrapper(game)
    lichess = MoveRecordingLichess()

    wrapper.play_move(chess.Board(),
                      game,
                      lichess,
                      Timer(),
                      timedelta(milliseconds=100),
                      can_ponder=False,
                      is_correspondence=False,
                      correspondence_move_time=timedelta(),
                      engine_cfg=disabled_external_move_cfg(),
                      min_time=timedelta())

    assert lichess.moves_made == []
    assert lichess.resigns == 0


def test_submit_move__does_not_send_move_after_control_stream_finish() -> None:
    """A gameFinish seen by the account stream must suppress stale move POSTs."""
    game = bullet_game()
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    lichess = MoveRecordingLichess()

    wrapper.submit_move(chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None),
                        chess.Board(),
                        game,
                        lichess,
                        finished_game_ids=[game.id])

    assert lichess.moves_made == []
    assert lichess.resigns == 0


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


def test_search__disables_ponder_for_fast_exact_movetime() -> None:
    """Exact movetime caps must start a fresh search instead of accepting a stale ponderhit."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    engine = PonderRecordingFakeEngine()
    wrapper.engine = engine
    board = chess.Board()
    game = bullet_game(clock_ms=20_000)

    wrapper.search(board,
                   chess.engine.Limit(time=2.0, clock_id="bullet exact movetime"),
                   ponder=True,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None),
                   game=game,
                   engine_cfg=disabled_external_move_cfg())

    assert engine.ponder_calls == [False]


def test_search__keeps_ponder_for_fast_hard_movetime_watchdog() -> None:
    """A watchdog movetime with live clock data can still use ponder safely."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    engine = PonderRecordingFakeEngine()
    wrapper.engine = engine
    board = chess.Board()
    game = bullet_game(clock_ms=120_000)

    wrapper.search(board,
                   chess.engine.Limit(white_clock=120.0,
                                      black_clock=12.0,
                                      white_inc=1.0,
                                      black_inc=1.0,
                                      time=12.0,
                                      clock_id="bullet hard watchdog"),
                   ponder=True,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None),
                   game=game,
                   engine_cfg=disabled_external_move_cfg())

    assert engine.ponder_calls == [True]


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


def test_search__does_not_accept_high_rated_draw_offer_when_opponent_is_in_clock_pressure() -> None:
    """Do not accept elite draw offers when our clock is safe and the opponent is near flagging."""
    wrapper = EngineWrapper({}, Configuration({
        "offer_draw_enabled": True,
        "offer_draw_moves": 10,
        "offer_draw_score": 0,
        "offer_draw_pieces": 10,
        "high_rated_accept_draw_enabled": True,
        "high_rated_accept_draw_min_rating": 3000,
        "high_rated_accept_draw_moves": 2,
        "high_rated_accept_draw_score": 25,
        "high_rated_accept_draw_pieces": 32,
        "high_rated_accept_draw_clock_pressure_enabled": True,
        "high_rated_accept_draw_clock_pressure_own_clock_ms": 30000,
        "high_rated_accept_draw_clock_pressure_opponent_clock_ms": 15000,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    }))
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]
    game = high_rated_blitz_game()
    game.state["wtime"] = 93_000
    game.state["btime"] = 13_000

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=True,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=game,
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__accepts_higher_rated_draw_offer_when_bot_is_in_clock_pressure() -> None:
    """Accept stable draw offers from stronger bots when our bullet clock is critical."""
    wrapper = EngineWrapper({}, Configuration({
        "offer_draw_enabled": True,
        "offer_draw_moves": 10,
        "offer_draw_score": 0,
        "offer_draw_pieces": 10,
        "high_rated_accept_draw_enabled": True,
        "high_rated_accept_draw_min_rating": 3100,
        "high_rated_accept_draw_moves": 2,
        "high_rated_accept_draw_score": 25,
        "high_rated_accept_draw_pieces": 32,
        "high_rated_accept_draw_clock_pressure_enabled": True,
        "high_rated_accept_draw_clock_pressure_own_clock_ms": 30000,
        "high_rated_accept_draw_clock_pressure_opponent_clock_ms": 15000,
        "resign_enabled": False,
        "resign_moves": 3,
        "resign_score": -1000,
    }))
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]
    game = high_rated_blitz_game(opponent_rating=3075)
    game.me.rating = 3029
    game.state["wtime"] = 9_459
    game.state["btime"] = 21_850

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=True,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=game,
                            engine_cfg=Configuration({}))

    assert result.draw_offered


def test_search__does_not_accept_incoming_draw_via_generic_offer_rule() -> None:
    """The proactive draw rule must not accept an incoming offer from a non-elite opponent."""
    wrapper = EngineWrapper({}, generic_draw_offer_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=True,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=3031),
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__does_not_offer_generic_draw_to_lower_rated_bot() -> None:
    """The proactive draw rule should not give lower-rated bots easy draw exits."""
    wrapper = EngineWrapper({}, generic_draw_offer_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=2700),
                            engine_cfg=Configuration({}))

    assert not result.draw_offered


def test_search__can_offer_generic_draw_to_higher_rated_bot() -> None:
    """The proactive draw rule may still settle stable drawn games against stronger bots."""
    wrapper = EngineWrapper({}, generic_draw_offer_cfg())
    wrapper.engine = DrawishFakeEngine()
    wrapper.scores = [chess.engine.PovScore(chess.engine.Cp(5), chess.WHITE)]

    result = wrapper.search(chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
                            chess.engine.Limit(time=1.0),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=high_rated_blitz_game(opponent_rating=3060),
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


def test_search__stops_main_engine_ponder_before_endgame_engine_handoff() -> None:
    """Switching to the secondary engine should not leave the main engine pondering in parallel."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    main_engine = PonderingNamedFakeEngine("main", "e2e4", "e7e5")
    endgame_engine = PonderingNamedFakeEngine("endgame", "e2e3")
    wrapper.engine = main_engine
    wrapper.endgame_engine = endgame_engine
    wrapper.endgame_engine_max_pieces = 3

    wrapper.search(chess.Board(),
                   chess.engine.Limit(white_clock=60.0, black_clock=60.0),
                   ponder=True,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None))

    wrapper.search(chess.Board("4k3/8/8/8/8/8/4K3/8 w - - 0 1"),
                   chess.engine.Limit(time=1.0),
                   ponder=False,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None))

    assert main_engine.pings == 1
    assert endgame_engine.calls == 1


def test_search__filters_repetition_draw_roots_against_lower_rated_bot() -> None:
    """Fast rated games against lower-rated bots should avoid moves that allow an immediate repetition claim."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    engine = RootMovesRecordingFakeEngine()
    wrapper.engine = engine
    wrapper.last_search_score_cp = 20
    board = repetition_draw_board()

    wrapper.search(board,
                   chess.engine.Limit(time=1.0),
                   ponder=False,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None),
                   game=bullet_game(),
                   engine_cfg=disabled_external_move_cfg())

    root_moves = engine.root_move_calls[-1]
    assert root_moves is not None
    assert chess.Move.from_uci("d2e1") not in root_moves
    assert chess.Move.from_uci("e2f4") in root_moves


def test_search__allows_repetition_draw_roots_against_higher_rated_bot() -> None:
    """Draws remain acceptable against higher-rated bots."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    engine = RootMovesRecordingFakeEngine()
    wrapper.engine = engine
    wrapper.last_search_score_cp = 20
    game = bullet_game()
    game.opponent.rating = 3100
    board = repetition_draw_board()

    wrapper.search(board,
                   chess.engine.Limit(time=1.0),
                   ponder=False,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None),
                   game=game,
                   engine_cfg=disabled_external_move_cfg())

    assert engine.root_move_calls[-1] is None


def test_search__allows_repetition_draw_roots_when_score_is_losing() -> None:
    """A repetition draw should not be rejected when the previous score says the bot is losing."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    engine = RootMovesRecordingFakeEngine()
    wrapper.engine = engine
    wrapper.last_search_score_cp = -200
    board = repetition_draw_board()

    wrapper.search(board,
                   chess.engine.Limit(time=1.0),
                   ponder=False,
                   draw_offered=False,
                   root_moves=chess.engine.PlayResult(None, None),
                   game=bullet_game(),
                   engine_cfg=disabled_external_move_cfg())

    assert engine.root_move_calls[-1] is None


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


def test_search__extends_depth_eleven_result_against_higher_rated_bot() -> None:
    """A depth-11 bullet result against a stronger bot should get a tactical follow-up search."""
    wrapper = EngineWrapper({}, draw_or_resign_cfg())
    fake_engine = DepthElevenThenThirteenFakeEngine()
    wrapper.engine = fake_engine
    game = fast_game("bullet", 60000, 38000)
    game.me.rating = 3034
    game.opponent.rating = 3139
    game.opponent.title = "BOT"
    game.opponent.is_bot = True
    game.state["wtime"] = 38000
    game.state["btime"] = 28000
    engine_cfg = Configuration({
        "shallow_search_guard": {
            "enabled": True,
            "speeds": ["bullet", "blitz"],
            "min_depth": 6,
            "high_rated_bot_min_depth": 12,
            "high_rated_bot_min_rating": 3000,
            "extra_movetime_ms": 1500,
            "min_clock_ms": 30000,
            "min_ply": 10,
        },
    })

    result = wrapper.search(mzn_bgmqz_depth_eleven_miss_board(),
                            chess.engine.Limit(white_clock=38, black_clock=28),
                            ponder=False,
                            draw_offered=False,
                            root_moves=chess.engine.PlayResult(None, None),
                            game=game,
                            engine_cfg=engine_cfg)

    assert result.move == chess.Move.from_uci("f4d2")
    assert result.info["depth"] == 13
    assert len(fake_engine.calls) == 2
    assert fake_engine.calls[1].time == 1.5


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


def test_apply_bullet_time_management__uses_exact_movetime_when_opponent_is_low_on_clock() -> None:
    """When the opponent is nearly flagged and our clock is rich, spend enough time to avoid cheap tactical losses."""
    game = fast_game("bullet", 120000, 80000)
    game.state["btime"] = 5000
    game.state["winc"] = 1000
    game.state["binc"] = 1000
    engine_cfg = Configuration({
        "bullet_time_management": {
            "enabled": True,
            "speeds": ["bullet"],
            "force_movetime_caps": True,
            "force_movetime_threshold_ms": 30000,
            "hard_movetime_caps": True,
            "max_clock_ms": 12000,
            "high_clock_threshold_ms": 600000,
            "high_clock_ms": 12000,
            "low_clock_threshold_ms": 30000,
            "low_clock_ms": 5000,
            "critical_clock_threshold_ms": 5000,
            "critical_clock_ms": 1000,
            "emergency_clock_threshold_ms": 2500,
            "emergency_clock_ms": 500,
            "clock_pressure_own_clock_threshold_ms": 30000,
            "clock_pressure_opponent_clock_threshold_ms": 10000,
            "clock_pressure_min_ply": 20,
            "clock_pressure_movetime_ms": 6000,
        },
    })
    board = chess.Board()
    for move in ["g1f3", "g8f6", "g2g3", "g7g6", "f1g2", "f8g7", "e1g1", "e8g8", "d2d3", "d7d6",
                 "e2e4", "e7e5", "b1c3", "b8c6", "h2h3", "h7h6", "c1e3", "c8e6", "d1d2", "d8d7"]:
        board.push_uci(move)

    limit = chess.engine.Limit(white_clock=80.0, black_clock=5.0, white_inc=1.0, black_inc=1.0)
    capped = apply_bullet_time_management(board, game, limit, engine_cfg)

    assert capped.time == 6.0
    assert capped.white_clock is None
    assert capped.black_clock is None
    assert capped.white_inc is None
    assert capped.black_inc is None


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
