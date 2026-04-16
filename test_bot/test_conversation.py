"""Tests for in-game chat commands."""

from datetime import timedelta

from lib.config import Configuration
from lib.conversation import ChatLine, Conversation
from lib.lichess_types import GameEventType
from lib.model import Game


def get_admin_game() -> Game:
    """Create a game between the bot and the admin user."""
    game_event: GameEventType = {
        "id": "rating01",
        "variant": {"key": "standard", "name": "Standard", "short": "Std"},
        "clock": {"initial": 60000, "increment": 0},
        "speed": "bullet",
        "perf": {"name": "Bullet"},
        "rated": False,
        "createdAt": 1600000000000,
        "white": {"id": "chesszyh", "name": "Chesszyh", "title": None, "rating": 2600},
        "black": {"id": "bot", "name": "ilovecatgirl", "title": "BOT", "rating": 2900},
        "initialFen": "startpos",
        "type": "gameFull",
        "state": {
            "type": "gameState",
            "moves": "",
            "wtime": 60000,
            "btime": 60000,
            "winc": 0,
            "binc": 0,
            "status": "started",
        },
    }
    return Game(game_event, "ilovecatgirl", "https://lichess.org", timedelta(seconds=60))


class FakeEngine:
    """Engine wrapper with runtime strength controls."""

    def __init__(self) -> None:
        self.strength_limit_elo: int | None = None

    def set_strength_limit(self, elo: int) -> None:
        self.strength_limit_elo = elo

    def clear_strength_limit(self) -> None:
        self.strength_limit_elo = None

    def name(self) -> str:
        return "FakeEngine"


class FakeLichess:
    """Capture chat replies."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    def chat(self, game_id: str, room: str, text: str) -> None:
        self.messages.append((game_id, room, text))


def rating_control_cfg() -> Configuration:
    """Create rating-control config for tests."""
    return Configuration({
        "enabled": True,
        "admins": ["Chesszyh"],
        "min_elo": 1320,
        "max_elo": 3190,
    })


def test_rating_command__admin_can_limit_and_restore_engine_strength() -> None:
    """The admin should be able to set and clear Stockfish UCI_Elo during a game."""
    engine = FakeEngine()
    li = FakeLichess()
    conversation = Conversation(get_admin_game(), engine, li, "test", [], rating_control_cfg())

    conversation.react(ChatLine({"room": "player", "username": "Chesszyh", "text": "!rating 2500"}))
    conversation.react(ChatLine({"room": "player", "username": "Chesszyh", "text": "!rating full"}))

    assert engine.strength_limit_elo is None
    assert li.messages == [
        ("rating01", "player", "Playing at UCI_Elo 2500."),
        ("rating01", "player", "Playing at full strength."),
    ]
