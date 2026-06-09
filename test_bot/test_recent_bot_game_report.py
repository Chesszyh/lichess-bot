"""Tests for the recent bot game report script."""

from __future__ import annotations

from scripts import recent_bot_game_report


def game_json(game_id: str, winner: str | None, opponent_rating: int, opening: str) -> dict:
    """Build a minimal Lichess JSON game."""
    game = {
        "id": game_id,
        "speed": "bullet",
        "status": "draw" if winner is None else "resign",
        "players": {
            "white": {"user": {"name": "NeuroSoCute", "title": "BOT"}, "rating": 3050},
            "black": {"user": {"name": "TargetBot", "title": "BOT"}, "rating": opponent_rating},
        },
        "opening": {"name": opening},
        "moves": "e4 e5 Nf3",
    }
    if winner is not None:
        game["winner"] = winner

    return game


def test_render_report__prioritizes_losses_and_low_rated_draws() -> None:
    """The report should focus review time on losses and below-floor draws."""
    games = [
        recent_bot_game_report.summarize_game(game_json("loss1", "black", 3090, "Ruy Lopez"), "NeuroSoCute"),
        recent_bot_game_report.summarize_game(game_json("draw1", None, 3020, "Ruy Lopez"), "NeuroSoCute"),
        recent_bot_game_report.summarize_game(game_json("draw2", None, 3180, "English Opening"), "NeuroSoCute"),
    ]

    report = recent_bot_game_report.render_report([game for game in games if game is not None], 3080)

    assert "LOSS loss1" in report
    assert "LOW_DRAW draw1" in report
    assert "LOW_DRAW draw2" not in report
    assert "2x Ruy Lopez" in report
