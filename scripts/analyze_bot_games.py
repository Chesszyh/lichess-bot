#!/usr/bin/env python3
"""Analyze local lichess-bot PGNs for lightweight performance leaks."""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import io
from pathlib import Path
import sys

import chess.pgn


@dataclass(frozen=True)
class GameRecord:
    """A parsed local PGN record for one bot game."""

    path: Path
    utc_started: datetime | None
    white: str
    black: str
    result: str
    time_control: str
    opening: str
    termination: str
    white_elo: int | None
    black_elo: int | None
    white_title: str
    black_title: str
    bot_color: str
    bot_result: str
    opponent: str
    opponent_rating: int | None
    rating_gap: int | None
    move_prefix: str


@dataclass(frozen=True)
class GameSummary:
    """Aggregated evidence from local bot-vs-bot PGNs."""

    bot_name: str
    total_games: int
    result_counts: dict[str, int]
    losses_by_opening: list[tuple[str, int]]
    losses_by_color: list[tuple[str, int]]
    loss_prefixes: list[tuple[str, int]]
    lower_rated_draw_count: int
    lower_rated_draws: list[GameRecord]
    recent_losses: list[GameRecord]


def parse_int(value: str) -> int | None:
    """Parse an integer PGN tag value."""
    try:
        return int(value)
    except ValueError:
        return None


def parse_utc_started(date_value: str, time_value: str) -> datetime | None:
    """Parse PGN UTC date and time tags."""
    if not date_value or not time_value or "?" in date_value or "?" in time_value:
        return None

    try:
        return datetime.strptime(f"{date_value} {time_value}", "%Y.%m.%d %H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return None


def parse_since_utc(value: str | None) -> datetime | None:
    """Parse an optional ISO-like UTC timestamp."""
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def time_control_base_seconds(time_control: str) -> int | None:
    """Return the base seconds from a PGN TimeControl tag."""
    base_seconds = time_control.split("+", maxsplit=1)[0]
    return parse_int(base_seconds)


def is_fast_time_control(time_control: str, max_base_seconds: int) -> bool:
    """Return whether a time control is in the configured bullet/blitz scope."""
    base_seconds = time_control_base_seconds(time_control)
    return base_seconds is not None and base_seconds <= max_base_seconds


def game_move_prefix(game: chess.pgn.Game, max_prefix_plies: int) -> str:
    """Return the first plies of a game as SAN moves."""
    board = game.board()
    moves: list[str] = []
    for move in game.mainline_moves():
        if len(moves) >= max_prefix_plies:
            break
        moves.append(board.san(move))
        board.push(move)
    return " ".join(moves)


def bot_result(result: str, bot_is_white: bool) -> str:
    """Return win/loss/draw from the configured bot's perspective."""
    if result == "1/2-1/2":
        return "draw"
    if result == "1-0":
        return "win" if bot_is_white else "loss"
    if result == "0-1":
        return "loss" if bot_is_white else "win"
    return "unknown"


def parse_game(path: Path, bot_name: str, max_prefix_plies: int) -> GameRecord | None:
    """Parse one PGN file if it is a bot-vs-bot game for bot_name."""
    game = chess.pgn.read_game(io.StringIO(path.read_text(encoding="utf-8", errors="replace")))
    if game is None:
        return None

    headers = game.headers
    white = headers.get("White", "")
    black = headers.get("Black", "")
    if bot_name not in {white, black}:
        return None

    white_title = headers.get("WhiteTitle", "")
    black_title = headers.get("BlackTitle", "")
    if white_title != "BOT" or black_title != "BOT":
        return None

    white_elo = parse_int(headers.get("WhiteElo", ""))
    black_elo = parse_int(headers.get("BlackElo", ""))
    bot_is_white = white == bot_name
    opponent = black if bot_is_white else white
    opponent_rating = black_elo if bot_is_white else white_elo
    bot_rating = white_elo if bot_is_white else black_elo
    rating_gap = bot_rating - opponent_rating if bot_rating is not None and opponent_rating is not None else None

    return GameRecord(
        path=path,
        utc_started=parse_utc_started(headers.get("UTCDate", ""), headers.get("UTCTime", "")),
        white=white,
        black=black,
        result=headers.get("Result", "*"),
        time_control=headers.get("TimeControl", ""),
        opening=headers.get("Opening", "Unknown"),
        termination=headers.get("Termination", ""),
        white_elo=white_elo,
        black_elo=black_elo,
        white_title=white_title,
        black_title=black_title,
        bot_color="white" if bot_is_white else "black",
        bot_result=bot_result(headers.get("Result", "*"), bot_is_white),
        opponent=opponent,
        opponent_rating=opponent_rating,
        rating_gap=rating_gap,
        move_prefix=game_move_prefix(game, max_prefix_plies),
    )


def summarize_records(records_dir: Path,
                      bot_name: str,
                      *,
                      max_prefix_plies: int = 12,
                      lower_rated_draw_gap: int = 1,
                      max_base_seconds: int = 300,
                      since_utc: datetime | None = None) -> GameSummary:
    """Summarize local bot-vs-bot PGN records."""
    records: list[GameRecord] = []
    for path in sorted(records_dir.glob("*.pgn")):
        record = parse_game(path, bot_name, max_prefix_plies)
        if record is None:
            continue
        if not is_fast_time_control(record.time_control, max_base_seconds):
            continue
        if since_utc is not None and (record.utc_started is None or record.utc_started < since_utc):
            continue
        records.append(record)

    result_counts = Counter(record.bot_result for record in records)
    losses = [record for record in records if record.bot_result == "loss"]
    losses_by_opening = Counter(record.opening for record in losses).most_common()
    losses_by_color = Counter(record.bot_color for record in losses).most_common()
    loss_prefixes = Counter(record.move_prefix for record in losses if record.move_prefix).most_common()
    lower_rated_draws = [
        record for record in records
        if record.bot_result == "draw" and record.rating_gap is not None and record.rating_gap >= lower_rated_draw_gap
    ]
    lower_rated_draws.sort(key=lambda record: record.rating_gap or 0, reverse=True)
    recent_losses = sorted(
        losses,
        key=lambda record: record.utc_started or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )[:10]

    return GameSummary(
        bot_name=bot_name,
        total_games=len(records),
        result_counts=dict(sorted(result_counts.items())),
        losses_by_opening=losses_by_opening,
        losses_by_color=losses_by_color,
        loss_prefixes=loss_prefixes,
        lower_rated_draw_count=len(lower_rated_draws),
        lower_rated_draws=lower_rated_draws[:10],
        recent_losses=recent_losses,
    )


def game_link(record: GameRecord) -> str:
    """Return a compact report label for a game record."""
    return f"`{record.path.name}`"


def opening_risk_gate_line(summary: GameSummary, risk_threshold: int) -> str:
    """Render the opening risk gate status line."""
    top_loss_count = summary.losses_by_opening[0][1] if summary.losses_by_opening else 0
    if risk_threshold <= 0:
        return "Opening risk gate: not enabled"
    if top_loss_count >= risk_threshold:
        return f"Opening risk gate: FAILED ({top_loss_count} >= {risk_threshold})"
    return f"Opening risk gate: passed ({top_loss_count} < {risk_threshold})"


def render_markdown(summary: GameSummary, *, risk_threshold: int = 0) -> str:
    """Render a markdown analysis report."""
    lines = [
        f"# Bot Game Analysis for {summary.bot_name}",
        "",
        "## Scope",
        "",
        f"- Games analyzed: `{summary.total_games}`",
        f"- Results: `{summary.result_counts}`",
        f"- {opening_risk_gate_line(summary, risk_threshold)}",
        "- No local engine analysis was run.",
        "",
        "## Loss Openings",
        "",
    ]
    if summary.losses_by_opening:
        lines.extend(f"- `{count}` x {opening}" for opening, count in summary.losses_by_opening[:10])
    else:
        lines.append("- No losses found.")

    lines.extend(["", "## Loss Colors", ""])
    if summary.losses_by_color:
        lines.extend(f"- `{count}` x {color}" for color, count in summary.losses_by_color)
    else:
        lines.append("- No losses found.")

    lines.extend(["", "## Loss Prefixes", ""])
    if summary.loss_prefixes:
        lines.extend(f"- `{count}` x `{prefix}`" for prefix, count in summary.loss_prefixes[:10])
    else:
        lines.append("- No loss prefixes found.")

    lines.extend(["", "## Lower-Rated Draws", ""])
    lines.append(f"- Lower-rated draws found: `{summary.lower_rated_draw_count}`")
    if summary.lower_rated_draws:
        lines.extend(
                f"- gap `{record.rating_gap}` vs `{record.opponent}` "
                f"({record.opponent_rating}) in {game_link(record)}: {record.opening}"
                for record in summary.lower_rated_draws
        )
    else:
        lines.append("- No lower-rated draw leaks found at the configured threshold.")

    lines.extend(["", "## Recent Losses", ""])
    if summary.recent_losses:
        for record in summary.recent_losses:
            started = record.utc_started.isoformat(sep=" ") if record.utc_started else "unknown time"
            lines.append(f"- `{started}` {game_link(record)} vs `{record.opponent}`: {record.opening}")
    else:
        lines.append("- No recent losses found.")

    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Analyze local lichess-bot PGNs without engine searches.")
    parser.add_argument("--records-dir", default="game_records", help="Directory containing local PGN records.")
    parser.add_argument("--bot", default="ilovecatgirl", help="Bot username to analyze.")
    parser.add_argument("--since-utc", help="Only include games at or after this UTC ISO timestamp.")
    parser.add_argument("--max-prefix-plies", type=int, default=12, help="Move-prefix length for loss clustering.")
    parser.add_argument("--lower-rated-draw-gap", type=int, default=1, help="Rating gap threshold for draw leaks.")
    parser.add_argument("--max-base-seconds", type=int, default=300, help="Maximum base time to include.")
    parser.add_argument("--risk-threshold", type=int, default=0, help="Fail when any loss opening reaches this count.")
    parser.add_argument("--output", help="Optional markdown output path. Defaults to stdout.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the PGN analyzer."""
    args = parse_args(argv)
    summary = summarize_records(
        Path(args.records_dir),
        args.bot,
        max_prefix_plies=args.max_prefix_plies,
        lower_rated_draw_gap=args.lower_rated_draw_gap,
        max_base_seconds=args.max_base_seconds,
        since_utc=parse_since_utc(args.since_utc),
    )
    markdown = render_markdown(summary, risk_threshold=args.risk_threshold)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    top_loss_count = summary.losses_by_opening[0][1] if summary.losses_by_opening else 0
    return 1 if args.risk_threshold > 0 and top_loss_count >= args.risk_threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
