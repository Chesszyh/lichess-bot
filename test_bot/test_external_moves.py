"""Test the functions that get the external moves."""
import pytest
import backoff
import requests
import yaml
import os
import chess
import logging
import chess.engine
from datetime import timedelta
from copy import deepcopy
from types import SimpleNamespace, TracebackType
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError, ReadTimeout, RequestException
from http.client import RemoteDisconnected
from lib.lichess_types import OnlineType, GameEventType
from typing import Literal, cast
from lib.lichess import is_final, backoff_handler, Lichess
from lib.config import Configuration, insert_default_values
from lib.model import Game
from lib.engine_wrapper import get_online_move, get_book_move, is_op1_position


class MockLichess(Lichess):
    """A modified Lichess class for communication with external move sources."""

    def __init__(self) -> None:
        """Initialize only self.other_session and not self.session."""
        self.max_retries = 3
        self.other_session = requests.Session()

    def online_book_get(self, path: str, params: dict[str, str | int] | None = None, *,
                        stream: bool = False, authenticated: bool = False) -> OnlineType:
        """
        Get an external move from online sources (chessdb or lichess.org).

        Ignore authentication for tests.
        """
        del authenticated

        @backoff.on_exception(backoff.constant,
                              (RemoteDisconnected, RequestsConnectionError, HTTPError, ReadTimeout),
                              max_time=60,
                              max_tries=self.max_retries,
                              interval=0.1,
                              giveup=is_final,
                              on_backoff=backoff_handler,
                              backoff_log_level=logging.DEBUG,
                              giveup_log_level=logging.DEBUG)
        def online_book_get() -> OnlineType:
            json_response: OnlineType = self.other_session.get(path, timeout=2, params=params, stream=stream).json()
            return json_response

        return online_book_get()

    def is_website_up(self, url: str) -> bool:
        """Check if a website is up."""
        try:
            self.other_session.get(url, timeout=2)
            return True
        except RequestException:
            return False


def get_configs() -> tuple[Configuration, Configuration, Configuration, Configuration]:
    """Create the configs used for the tests."""
    with open("./config.yml.default") as file:
        CONFIG = yaml.safe_load(file)
    insert_default_values(CONFIG)
    CONFIG["engine"]["online_moves"]["lichess_cloud_analysis"]["enabled"] = True
    CONFIG["engine"]["online_moves"]["online_egtb"]["enabled"] = True
    CONFIG["engine"]["draw_or_resign"]["resign_enabled"] = True
    CONFIG["engine"]["polyglot"]["enabled"] = True
    CONFIG["engine"]["polyglot"]["book"]["standard"] = ["TEMP/gm2001.bin"]
    engine_cfg = Configuration(CONFIG).engine
    CONFIG_2 = deepcopy(CONFIG)
    CONFIG_2["engine"]["online_moves"]["chessdb_book"]["enabled"] = True
    CONFIG_2["engine"]["online_moves"]["online_egtb"]["source"] = "chessdb"
    engine_cfg_2 = Configuration(CONFIG_2).engine
    return engine_cfg.online_moves, engine_cfg_2.online_moves, engine_cfg.draw_or_resign, engine_cfg.polyglot


def get_game() -> Game:
    """Create a model.Game to be used in the tests."""
    game_event: GameEventType = {"id": "zzzzzzzz",
                                 "variant": {"key": "standard",
                                             "name": "Standard",
                                             "short": "Std"},
                                 "clock": {"initial": 60000,
                                           "increment": 2000},
                                 "speed": "bullet",
                                 "perf": {"name": "Bullet"},
                                 "rated": True,
                                 "createdAt": 1600000000000,
                                 "white": {"id": "bo",
                                           "name": "bo",
                                           "title": "BOT",
                                           "rating": 3000},
                                 "black": {"id": "b",
                                           "name": "b",
                                           "title": "BOT",
                                           "rating": 3000,
                                           "provisional": True},
                                 "initialFen": "startpos",
                                 "type": "gameFull",
                                 "state": {"type": "gameState",
                                           "moves": "",
                                           "wtime": 1000000,
                                           "btime": 1000000,
                                           "winc": 2000,
                                           "binc": 2000,
                                           "status": "started"}}
    return Game(game_event, "b", "https://lichess.org", timedelta(seconds=60))


def get_human_game() -> Game:
    """Create a model.Game with a human opponent."""
    game_event: GameEventType = {"id": "yyyyyyyy",
                                 "variant": {"key": "standard",
                                             "name": "Standard",
                                             "short": "Std"},
                                 "clock": {"initial": 60000,
                                           "increment": 2000},
                                 "speed": "bullet",
                                 "perf": {"name": "Bullet"},
                                 "rated": True,
                                 "createdAt": 1600000000000,
                                 "white": {"id": "alice",
                                           "name": "Alice",
                                           "title": None,
                                           "rating": 2600},
                                 "black": {"id": "b",
                                           "name": "b",
                                           "title": "BOT",
                                           "rating": 3000,
                                           "provisional": True},
                                 "initialFen": "startpos",
                                 "type": "gameFull",
                                 "state": {"type": "gameState",
                                           "moves": "",
                                           "wtime": 1000000,
                                           "btime": 1000000,
                                           "winc": 2000,
                                           "binc": 2000,
                                           "status": "started"}}
    return Game(game_event, "b", "https://lichess.org", timedelta(seconds=60))


def download_opening_book() -> None:
    """Download gm2001.bin."""
    if os.path.exists("./TEMP/gm2001.bin"):
        return

    os.makedirs("TEMP", exist_ok=True)
    response = requests.get("https://github.com/gmcheems-org/free-opening-books/raw/main/books/bin/gm2001.bin",
                            allow_redirects=True, timeout=60)
    if response.status_code != 200:
        pytest.xfail("Could not download opening book.")
    with open("./TEMP/gm2001.bin", "wb") as file:
        file.write(response.content)


def get_online_move_wrapper(li: Lichess, board: chess.Board, game: Game, online_moves_cfg: Configuration,
                            draw_or_resign_cfg: Configuration, *, expect_none: bool = False) -> chess.engine.PlayResult:
    """Wrap `lib.engine_wrapper.get_online_move` so that it only returns a PlayResult type."""
    online_move = get_online_move(li, board, game, online_moves_cfg, draw_or_resign_cfg)
    online_move = cast(chess.engine.PlayResult, online_move)
    if not expect_none and online_move.move is None:
        pytest.xfail("Could not contact external move source.")
    return online_move


class TestExternalMoves:
    """Test that the code for external moves works properly."""

    li = MockLichess()
    game = get_game()
    online_cfg, online_cfg_2, draw_or_resign_cfg, polyglot_cfg = get_configs()

    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    opening_fen = "rn1q1rk1/pbp1bpp1/1p2pn1p/3p4/2PP3B/2N1PN2/PP2BPPP/R2QK2R w KQ - 2 9"
    middlegame_fen = "8/5p2/1n1p1nk1/1p1Pp1p1/1Pp1P1Pp/r1P2B1P/2RNKP2/8 w - - 0 31"
    endgame_wdl2_fen = "2k5/4n2Q/5N2/8/8/8/1r6/2K5 b - - 0 123"
    endgame_wdl1_fen = "6N1/3n4/3k1b2/8/8/7Q/1r6/5K2 b - - 6 9"
    endgame_wdl0_fen = "6N1/3n4/3k1b2/8/8/7Q/5K2/1r6 b - - 8 10"
    endgame_op1_fen = "r7/p1b1k3/8/8/P7/8/8/K2R1R2 w - - 1 2"

    def test_lichess_cloud_analysis(self) -> None:
        """Test lichess_cloud_analysis."""
        if not self.li.is_website_up("https://lichess.org/api/cloud-eval"):
            pytest.xfail("Lichess cloud eval is down.")

        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.starting_fen),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg).move is not None
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.opening_fen),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg).move is not None
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.middlegame_fen),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg,
                                        expect_none=True).move is None

    def test_chessdb_book(self) -> None:
        """Test chessdb_book."""
        if not self.li.is_website_up("https://www.chessdb.cn/cdb.php"):
            pytest.xfail("ChessDB is down.")

        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.starting_fen),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg).move is not None
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.opening_fen),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg).move is not None
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.middlegame_fen),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg,
                                        expect_none=True).move is None

    def test_online_egtb_with_lichess(self) -> None:
        """Test online_egtb with lichess."""
        if not self.li.is_website_up("https://tablebase.lichess.ovh/standard"):
            pytest.xfail("Lichess tablebase is down.")

        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl2_fen),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg).resigned
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl0_fen),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg).draw_offered
        wdl1_move = get_online_move_wrapper(self.li,
                                            chess.Board(self.endgame_wdl1_fen),
                                            self.game,
                                            self.online_cfg,
                                            self.draw_or_resign_cfg)
        assert not wdl1_move.resigned and not wdl1_move.draw_offered
        op1_move = get_online_move_wrapper(self.li,
                                           chess.Board(self.endgame_op1_fen),
                                           self.game,
                                           self.online_cfg,
                                           self.draw_or_resign_cfg)
        assert op1_move.move == chess.Move.from_uci("f1e1")

        # Test with reversed colors.
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl2_fen).mirror(),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg).resigned
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl0_fen).mirror(),
                                        self.game,
                                        self.online_cfg,
                                        self.draw_or_resign_cfg).draw_offered
        wdl1_move = get_online_move_wrapper(self.li,
                                            chess.Board(self.endgame_wdl1_fen).mirror(),
                                            self.game,
                                            self.online_cfg,
                                            self.draw_or_resign_cfg)
        assert not wdl1_move.resigned and not wdl1_move.draw_offered

    def test_online_egtb_with_chessdb(self) -> None:
        """Test online_egtb with chessdb."""
        if not self.li.is_website_up("https://www.chessdb.cn/cdb.php"):
            pytest.xfail("ChessDB is down.")

        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl2_fen),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg).resigned
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl0_fen),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg).draw_offered
        wdl1_move = get_online_move_wrapper(self.li,
                                            chess.Board(self.endgame_wdl1_fen),
                                            self.game,
                                            self.online_cfg_2,
                                            self.draw_or_resign_cfg)
        assert not wdl1_move.resigned and not wdl1_move.draw_offered

        # Test with reversed colors.
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl2_fen).mirror(),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg).resigned
        assert get_online_move_wrapper(self.li,
                                        chess.Board(self.endgame_wdl0_fen).mirror(),
                                        self.game,
                                        self.online_cfg_2,
                                        self.draw_or_resign_cfg).draw_offered
        wdl1_move = get_online_move_wrapper(self.li,
                                            chess.Board(self.endgame_wdl1_fen).mirror(),
                                            self.game,
                                            self.online_cfg_2,
                                            self.draw_or_resign_cfg)
        assert not wdl1_move.resigned and not wdl1_move.draw_offered

    def test_opening_book(self) -> None:
        """Test opening book."""
        download_opening_book()
        assert get_book_move(chess.Board(self.opening_fen), self.game, self.polyglot_cfg).move == chess.Move.from_uci("h4f6")


class TestExternalMoveHelpers:
    """Test the helper functions for external moves."""

    def test_op1_positions(self) -> None:
        """Test that a position is op1."""
        fens_op1 = ["r7/p1b1k3/8/8/P7/8/8/K2R1R2 w - - 1 2", "3qk3/1n1pp3/8/8/8/8/4P2P/4K3 w - - 0 1"]
        fens_not_op1 = ["r3k3/2b5/8/p7/P7/8/8/K2R1R2 w q - 0 2", "3qk3/1n1pp1n1/8/8/8/8/4P3/4K3 w - - 0 1"]
        for fen in fens_op1:
            assert is_op1_position(chess.Board(fen))
        for fen in fens_not_op1:
            assert not is_op1_position(chess.Board(fen))


def test_get_book_move__uses_opponent_specific_polyglot_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Human and bot opponents should use different polyglot settings."""
    human_game = get_human_game()
    bot_game = get_game()
    board = chess.Board()
    polyglot_cfg = Configuration({
        "enabled": True,
        "book": {"standard": ["human.bin"]},
        "min_weight": 10,
        "selection": "uniform_random",
        "max_depth": 10,
        "normalization": "max",
        "opponent_selection": {
            "human": {
                "selection": "uniform_random",
                "min_weight": 25,
            },
            "bot": {
                "book": {"standard": ["bot.bin"]},
                "selection": "best_move",
                "min_weight": 40,
            },
        },
    })

    find_all_calls: list[str] = []
    random_choice_calls: list[list[chess.Move]] = []

    class FakeReader:
        def __init__(self, book_name: str) -> None:
            self.book_name = book_name

        def __enter__(self) -> "FakeReader":  # noqa: PYI034 - Keep tests compatible with Python 3.10.
            return self

        def __exit__(self,
                     exc_type: type[BaseException] | None,
                     exc: BaseException | None,
                     tb: TracebackType | None) -> Literal[False]:
            del exc_type, exc, tb
            return False

        def find_all(self, board: chess.Board) -> list[SimpleNamespace]:
            del board
            find_all_calls.append(self.book_name)
            if self.book_name == "bot.bin":
                return [
                    SimpleNamespace(move=chess.Move.from_uci("e2e4"), weight=100),
                    SimpleNamespace(move=chess.Move.from_uci("g1f3"), weight=60),
                ]

            return [
                SimpleNamespace(move=chess.Move.from_uci("g1f3"), weight=100),
                SimpleNamespace(move=chess.Move.from_uci("e2e4"), weight=60),
            ]

    def open_fake_reader(book: str) -> FakeReader:
        return FakeReader(book)

    def keep_book_order(books: list[str]) -> None:
        del books

    def fake_choice(population: list[SimpleNamespace]) -> SimpleNamespace:
        random_choice_calls.append([entry.move for entry in population])
        return population[0]

    monkeypatch.setattr("chess.polyglot.open_reader", open_fake_reader)
    monkeypatch.setattr("random.shuffle", keep_book_order)
    monkeypatch.setattr("random.choice", fake_choice)

    human_move = get_book_move(board, human_game, polyglot_cfg)
    bot_move = get_book_move(board, bot_game, polyglot_cfg)

    assert human_move.move == chess.Move.from_uci("g1f3")
    assert bot_move.move == chess.Move.from_uci("e2e4")
    assert find_all_calls == ["human.bin", "bot.bin"]
    assert random_choice_calls == [[chess.Move.from_uci("g1f3"), chess.Move.from_uci("e2e4")]]


def test_get_book_move__weighted_random_respects_min_weight(monkeypatch: pytest.MonkeyPatch) -> None:
    """Weighted book randomization should not include very low-weight sidelines."""
    board = chess.Board()
    game = get_game()
    polyglot_cfg = Configuration({
        "enabled": True,
        "book": {"standard": ["book.bin"]},
        "min_weight": 50,
        "selection": "weighted_random",
        "max_depth": 10,
        "normalization": "max",
    })
    high_weight_entry = SimpleNamespace(move=chess.Move.from_uci("e2e4"), weight=100)
    low_weight_entry = SimpleNamespace(move=chess.Move.from_uci("g1f3"), weight=40)
    find_all_calls: list[float] = []
    weighted_choices_calls: list[tuple[list[chess.Move], list[int], int]] = []

    class FakeReader:
        def __enter__(self) -> "FakeReader":  # noqa: PYI034 - Keep tests compatible with Python 3.10.
            return self

        def __exit__(self,
                     exc_type: type[BaseException] | None,
                     exc: BaseException | None,
                     tb: TracebackType | None) -> Literal[False]:
            del exc_type, exc, tb
            return False

        def find_all(self, board: chess.Board, minimum_weight: float = 1) -> list[SimpleNamespace]:
            del board
            find_all_calls.append(minimum_weight)
            return [entry for entry in [high_weight_entry, low_weight_entry] if entry.weight >= minimum_weight]

        def weighted_choice(self, board: chess.Board) -> SimpleNamespace:
            del board
            raise AssertionError("weighted_random must filter entries before choosing")

    def fake_choices(population: list[SimpleNamespace], weights: list[int], k: int) -> list[SimpleNamespace]:
        weighted_choices_calls.append(([entry.move for entry in population], list(weights), k))
        return [population[0]]

    def open_fake_reader(book: str) -> FakeReader:
        del book
        return FakeReader()

    def keep_book_order(books: list[str]) -> None:
        del books

    monkeypatch.setattr("chess.polyglot.open_reader", open_fake_reader)
    monkeypatch.setattr("random.shuffle", keep_book_order)
    monkeypatch.setattr("random.choices", fake_choices)

    move = get_book_move(board, game, polyglot_cfg)

    assert move.move == chess.Move.from_uci("e2e4")
    assert find_all_calls == [1]
    assert weighted_choices_calls == [([chess.Move.from_uci("e2e4")], [100], 1)]


def test_get_book_move__avoid_moves_filters_configured_san_line(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bot-specific book filters should avoid repeated drawish opening lines without disabling the book."""
    board = chess.Board()
    for san in ["e4", "e5", "Nf3", "Nc6"]:
        board.push_san(san)

    bot_game = get_game()
    human_game = get_human_game()
    polyglot_cfg = Configuration({
        "enabled": True,
        "book": {"standard": ["book.bin"]},
        "min_weight": 1,
        "selection": "weighted_random",
        "max_depth": 10,
        "normalization": "none",
        "opponent_selection": {
            "bot": {
                "avoid_moves": [
                    {"after": "e4 e5 Nf3 Nc6", "moves": ["Bb5"]},
                ],
            },
        },
    })
    ruy_lopez_entry = SimpleNamespace(move=chess.Move.from_uci("f1b5"), weight=100)
    italian_entry = SimpleNamespace(move=chess.Move.from_uci("f1c4"), weight=90)
    weighted_choices_calls: list[list[chess.Move]] = []

    class FakeReader:
        def __enter__(self) -> "FakeReader":  # noqa: PYI034 - Keep tests compatible with Python 3.10.
            return self

        def __exit__(self,
                     exc_type: type[BaseException] | None,
                     exc: BaseException | None,
                     tb: TracebackType | None) -> Literal[False]:
            del exc_type, exc, tb
            return False

        def find_all(self, board: chess.Board) -> list[SimpleNamespace]:
            del board
            return [ruy_lopez_entry, italian_entry]

    def fake_choices(population: list[SimpleNamespace], weights: list[int], k: int) -> list[SimpleNamespace]:
        del weights, k
        weighted_choices_calls.append([entry.move for entry in population])
        return [population[0]]

    def open_fake_reader(book: str) -> FakeReader:
        del book
        return FakeReader()

    def keep_book_order(books: list[str]) -> None:
        del books

    monkeypatch.setattr("chess.polyglot.open_reader", open_fake_reader)
    monkeypatch.setattr("random.shuffle", keep_book_order)
    monkeypatch.setattr("random.choices", fake_choices)

    bot_move = get_book_move(board, bot_game, polyglot_cfg)
    human_move = get_book_move(board, human_game, polyglot_cfg)

    assert bot_move.move == chess.Move.from_uci("f1c4")
    assert human_move.move == chess.Move.from_uci("f1b5")
    assert weighted_choices_calls == [
        [chess.Move.from_uci("f1c4")],
        [chess.Move.from_uci("f1b5"), chess.Move.from_uci("f1c4")],
    ]


def test_get_book_move__lockout_after_avoid_moves_exhaust_book(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoiding every book move in a tabiya should keep nearby follow-up positions out of book briefly."""
    tabiya = chess.Board()
    for san in ["e4", "e5"]:
        tabiya.push_san(san)

    follow_up = tabiya.copy()
    for san in ["Nf3", "Nc6"]:
        follow_up.push_san(san)

    after_lockout = follow_up.copy()
    for san in ["Bb5", "a6"]:
        after_lockout.push_san(san)

    game = get_game()
    game.id = "polyglot-lockout"
    polyglot_cfg = Configuration({
        "enabled": True,
        "book": {"standard": ["book.bin"]},
        "min_weight": 1,
        "selection": "best_move",
        "max_depth": 10,
        "normalization": "none",
        "book_exit_lockout_plies": 4,
        "avoid_moves": [
            {"after": "e4 e5", "moves": ["Nf3"]},
        ],
    })
    book_entry = SimpleNamespace(move=chess.Move.from_uci("g1f3"), weight=100)
    opened_positions: list[int] = []

    class FakeReader:
        def __enter__(self) -> "FakeReader":  # noqa: PYI034 - Keep tests compatible with Python 3.10.
            return self

        def __exit__(self,
                     exc_type: type[BaseException] | None,
                     exc: BaseException | None,
                     tb: TracebackType | None) -> Literal[False]:
            del exc_type, exc, tb
            return False

        def find_all(self, board: chess.Board) -> list[SimpleNamespace]:
            opened_positions.append(len(board.move_stack))
            return [book_entry]

    def open_fake_reader(book: str) -> FakeReader:
        del book
        return FakeReader()

    def keep_book_order(books: list[str]) -> None:
        del books

    monkeypatch.setattr("chess.polyglot.open_reader", open_fake_reader)
    monkeypatch.setattr("random.shuffle", keep_book_order)

    assert get_book_move(tabiya, game, polyglot_cfg).move is None
    assert get_book_move(follow_up, game, polyglot_cfg).move is None
    assert get_book_move(after_lockout, game, polyglot_cfg).move == chess.Move.from_uci("g1f3")
    assert opened_positions == [2, 6]


def test_get_online_move__egtb_zero_respects_clock_edge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tablebase draws should not offer a draw while the opponent is under clock pressure."""
    game = get_game()
    game.speed = "bullet"
    game.state["wtime"] = 18120
    game.state["btime"] = 51509
    online_moves_cfg = Configuration({})
    draw_or_resign_cfg = Configuration({
        "offer_draw_enabled": True,
        "offer_draw_for_egtb_zero": True,
        "offer_draw_clock_advantage_enabled": True,
        "offer_draw_clock_advantage_speeds": ["bullet", "blitz"],
        "offer_draw_clock_advantage_opponent_ms": 45000,
        "offer_draw_clock_advantage_min_ms": 30000,
        "resign_enabled": True,
        "resign_for_egtb_minus_two": True,
    })

    def fake_online_egtb_move(
        li: Lichess,
        board: chess.Board,
        game: Game,
        online_egtb_cfg: Configuration,
    ) -> tuple[str, int, chess.engine.InfoDict]:
        del li, board, game, online_egtb_cfg
        return "e2e3", 0, {"string": "lichess-bot-source:Lichess EGTB"}

    monkeypatch.setattr("lib.engine_wrapper.get_online_egtb_move", fake_online_egtb_move)

    result = get_online_move_wrapper(
        MockLichess(),
        chess.Board("8/8/8/8/8/8/4K3/4k3 w - - 0 1"),
        game,
        online_moves_cfg,
        draw_or_resign_cfg,
    )

    assert result.move == chess.Move.from_uci("e2e3")
    assert not result.draw_offered
