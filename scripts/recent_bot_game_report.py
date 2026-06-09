"""Summarize recent Lichess bot games for Stockfish tuning."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections.abc import Iterable
from collections import Counter
from dataclasses import dataclass


DEFAULT_USER = "NeuroSoCute"
DEFAULT_PERFS = "bullet,blitz"
DEFAULT_RATING_FLOOR = 3080


@dataclass(frozen=True)
class GameSummary:
    """A compact view of one Lichess game from the bot's perspective."""

    game_id: str
    speed: str
    result: str
    bot_color: str
    opponent_name: str
    opponent_rating: int | None
    opponent_is_bot: bool
    status: str
    opening: str
    moves: str

    @property
    def is_priority(self) -> bool:
        """Return true for games that deserve manual tuning review."""
        return self.result == "loss" or self.is_low_rated_draw

    @property
    def is_low_rated_draw(self) -> bool:
        """Return true for draws against below-floor opponents."""
        return self.result == "draw" and self.opponent_rating is not None and self.opponent_rating < DEFAULT_RATING_FLOOR


def _player(game: dict, color: str) -> dict:
    return game.get("players", {}).get(color, {})


def _user(player: dict) -> dict:
    return player.get("user", {}) or {}


def _player_name(game: dict, color: str) -> str:
    user = _user(_player(game, color))
    return str(user.get("name", ""))


def bot_color_for(game: dict, bot_name: str) -> str | None:
    """Return the color played by the bot, or None when the game is unrelated."""
    wanted = bot_name.casefold()
    for color in ("white", "black"):
        if _player_name(game, color).casefold() == wanted:
            return color

    return None


def summarize_game(game: dict, bot_name: str) -> GameSummary | None:
    """Convert one Lichess game JSON object into a stable summary."""
    bot_color = bot_color_for(game, bot_name)
    if bot_color is None:
        return None

    opponent_color = "black" if bot_color == "white" else "white"
    opponent = _player(game, opponent_color)
    opponent_user = _user(opponent)
    winner = game.get("winner")
    if winner is None:
        result = "draw"
    elif winner == bot_color:
        result = "win"
    else:
        result = "loss"

    return GameSummary(
        game_id=str(game.get("id", "")),
        speed=str(game.get("speed", "")),
        result=result,
        bot_color=bot_color,
        opponent_name=str(opponent_user.get("name", "")),
        opponent_rating=opponent.get("rating"),
        opponent_is_bot=opponent_user.get("title") == "BOT",
        status=str(game.get("status", "")),
        opening=str((game.get("opening") or {}).get("name", "")),
        moves=str(game.get("moves", "")),
    )


def parse_ndjson(lines: Iterable[str], bot_name: str) -> list[GameSummary]:
    """Parse Lichess NDJSON export lines."""
    games: list[GameSummary] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        summary = summarize_game(json.loads(stripped), bot_name)
        if summary is not None:
            games.append(summary)

    return games


def fetch_recent_games(bot_name: str, max_games: int, perf_types: str) -> list[GameSummary]:
    """Fetch recent rated games from the public Lichess export API."""
    params = urllib.parse.urlencode({
        "max": str(max_games),
        "rated": "true",
        "perfType": perf_types,
        "moves": "true",
        "pgnInJson": "false",
        "tags": "true",
        "clocks": "true",
        "evals": "false",
        "opening": "true",
        "sort": "dateDesc",
    })
    url = f"https://lichess.org/api/games/user/{urllib.parse.quote(bot_name)}?{params}"
    request = urllib.request.Request(url, headers={"Accept": "application/x-ndjson"})  # noqa: S310
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
        body = response.read().decode()

    return parse_ndjson(body.splitlines(), bot_name)


def _format_rating(rating: int | None) -> str:
    return "?" if rating is None else str(rating)


def render_report(games: list[GameSummary], rating_floor: int) -> str:
    """Render a plain-text report for fast terminal review."""
    priority_games = [
        game for game in games
        if game.result == "loss" or (
            game.result == "draw" and game.opponent_rating is not None and game.opponent_rating < rating_floor
        )
    ]
    draw_or_loss_openings = Counter(game.opening or "(unknown)" for game in games if game.result != "win")

    lines = [
        f"games={len(games)} rating_floor={rating_floor}",
        "",
        "priority_games:",
    ]
    if priority_games:
        for game in priority_games:
            tag = "LOSS" if game.result == "loss" else "LOW_DRAW"
            lines.append(
                f"- {tag} {game.game_id} {game.speed} {game.bot_color} vs "
                f"{game.opponent_name} {_format_rating(game.opponent_rating)} {game.opening}"
            )
    else:
        lines.append("- none")

    lines.extend(["", "repeated_draw_or_loss_openings:"])
    repeated = [(opening, count) for opening, count in draw_or_loss_openings.most_common() if count > 1]
    if repeated:
        for opening, count in repeated[:10]:
            lines.append(f"- {count}x {opening}")
    else:
        lines.append("- none")

    lines.extend(["", "recent_games:"])
    lines.extend(
        (
            f"- {game.game_id} {game.result} {game.speed} {game.bot_color} vs "
            f"{game.opponent_name} {_format_rating(game.opponent_rating)} {game.opening}"
        )
        for game in games[:20]
    )

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--max", type=int, default=40)
    parser.add_argument("--perf-type", default=DEFAULT_PERFS)
    parser.add_argument("--rating-floor", type=int, default=DEFAULT_RATING_FLOOR)
    parser.add_argument("--ndjson-file", help="Read already exported Lichess NDJSON instead of calling the API.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.ndjson_file:
        with open(args.ndjson_file, encoding="utf-8") as file:
            games = parse_ndjson(file, args.user)
    else:
        games = fetch_recent_games(args.user, args.max, args.perf_type)

    sys.stdout.write(f"{render_report(games, args.rating_floor)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
