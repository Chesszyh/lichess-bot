#!/usr/bin/env python3
"""Analyze local lichess-bot PGNs for lightweight performance leaks."""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import io
from itertools import pairwise
from pathlib import Path
import sys

import chess.pgn
import yaml


@dataclass(frozen=True)
class BotEvalPoint:
    """A saved engine evaluation associated with one bot mainline move."""

    san: str
    ply: int
    bot_pov_cp: int


@dataclass(frozen=True)
class BotEvalDrop:
    """A largest saved-eval drop between consecutive bot move searches."""

    path: Path
    opponent: str
    opening: str
    time_control: str
    bot_color: str
    after_bot_move: str
    previous_bot_pov_cp: int
    bot_pov_cp: int
    drop_cp: int


@dataclass(frozen=True)
class GameRecord:
    """A parsed local PGN record for one bot game."""

    path: Path
    utc_started: datetime | None
    white: str
    black: str
    result: str
    mode: str
    time_control: str
    speed: str
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
    bot_rating_diff: int | None
    bot_final_clock_seconds: float | None
    opponent_final_clock_seconds: float | None
    move_prefix: str
    bot_eval_points: list[BotEvalPoint]


@dataclass(frozen=True)
class GameSummary:
    """Aggregated evidence from local bot-vs-bot PGNs."""

    bot_name: str
    since_utc: datetime | None
    modes: set[str]
    time_controls: set[str]
    speeds: set[str]
    total_games: int
    result_counts: dict[str, int]
    results_by_mode: list[tuple[str, int]]
    results_by_speed: list[tuple[str, int]]
    results_by_time_control: list[tuple[str, int]]
    rating_impact_by_mode: list[tuple[str, int, int]]
    rating_impact_by_speed: list[tuple[str, int, int]]
    rating_impact_by_time_control: list[tuple[str, int, int]]
    rating_impact_by_opening: list[tuple[str, int, int]]
    rating_impact_by_opening_context: list[tuple[str, int, int]]
    rating_impact_by_opponent: list[tuple[str, int, int]]
    score_by_opponent: list[tuple[str, int, int, int, int, float]]
    opponent_leak_watchlist: list[tuple[str, int, int, int, int, int, datetime | None]]
    focused_rating_impact_by_time_control: list[tuple[str, int, int]]
    focused_score_by_time_control: list[tuple[str, int, int, int, int, float]]
    focused_rating_impact_by_opening_context: list[tuple[str, int, int]]
    focused_score_by_opening_context: list[tuple[str, int, int, int, int, float]]
    focused_rating_impact_by_opponent: list[tuple[str, int, int]]
    focused_score_by_opponent: list[tuple[str, int, int, int, int, float]]
    worst_scoring_controls: list[tuple[str, int, int, int, int, float]]
    losses_by_opening: list[tuple[str, int]]
    losses_by_color: list[tuple[str, int]]
    losses_by_termination: list[tuple[str, int]]
    time_forfeit_loss_controls: list[tuple[str, int]]
    unknown_result_terminations: list[tuple[str, int]]
    unknown_result_contexts: list[tuple[str, int]]
    loss_prefixes: list[tuple[str, int]]
    loss_prefix_contexts: list[tuple[str, int]]
    lower_rated_draw_count: int
    lower_rated_draws_by_opponent: list[tuple[str, int]]
    lower_rated_draws_by_opening: list[tuple[str, int]]
    lower_rated_draws_by_termination: list[tuple[str, int]]
    lower_rated_draw_prefixes: list[tuple[str, int]]
    focused_lower_rated_draw_contexts: list[tuple[str, int]]
    lower_rated_draw_contexts: list[tuple[str, int]]
    lower_rated_draws: list[GameRecord]
    rating_negative_draws_by_opponent: list[tuple[str, int]]
    rating_negative_draws_by_termination: list[tuple[str, int]]
    focused_rating_negative_draw_contexts: list[tuple[str, int]]
    rating_negative_draw_contexts: list[tuple[str, int]]
    rating_negative_draws: list[GameRecord]
    clock_rich_normal_losses: list[GameRecord]
    clock_rich_normal_loss_contexts: list[tuple[str, int]]
    high_clock_normal_losses: list[GameRecord]
    focused_high_clock_normal_loss_contexts: list[tuple[str, int]]
    high_clock_normal_loss_contexts: list[tuple[str, int]]
    clock_pressure_misses: list[GameRecord]
    clock_pressure_miss_contexts: list[tuple[str, int]]
    clock_pressure_draw_leaks: list[GameRecord]
    clock_pressure_draw_leak_contexts: list[tuple[str, int]]
    largest_bot_eval_drops: list[BotEvalDrop]
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


def parse_focus_time_controls(value: str | None) -> set[str]:
    """Parse a comma-separated list of exact time controls to highlight."""
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def parse_modes(value: str | None) -> set[str]:
    """Parse a comma-separated list of game modes to include."""
    if not value:
        return set()
    return {item.strip().casefold() for item in value.split(",") if item.strip()}


def parse_speeds(value: str | None) -> set[str]:
    """Parse a comma-separated list of Lichess speed buckets to include."""
    if not value:
        return set()
    return {item.strip().casefold() for item in value.split(",") if item.strip()}


def strip_pgn_variations(pgn_text: str) -> str:
    """Remove parenthesized PGN variations while preserving mainline comments."""
    stripped: list[str] = []
    variation_depth = 0
    in_comment = False
    for character in pgn_text:
        if in_comment:
            if variation_depth == 0:
                stripped.append(character)
            if character == "}":
                in_comment = False
            continue

        if character == "{":
            in_comment = True
            if variation_depth == 0:
                stripped.append(character)
            continue
        if character == "(":
            variation_depth += 1
            continue
        if character == ")" and variation_depth > 0:
            variation_depth -= 1
            continue
        if variation_depth == 0:
            stripped.append(character)

    return "".join(stripped)


def time_control_base_seconds(time_control: str) -> int | None:
    """Return the base seconds from a PGN TimeControl tag."""
    base_seconds = time_control.split("+", maxsplit=1)[0]
    return parse_int(base_seconds)


def time_control_parts(time_control: str) -> tuple[int, int] | None:
    """Return base and increment seconds from a PGN TimeControl tag."""
    base_seconds, separator, increment_seconds = time_control.partition("+")
    if not separator:
        return None
    base = parse_int(base_seconds)
    increment = parse_int(increment_seconds)
    if base is None or increment is None:
        return None
    return base, increment


def time_control_speed(time_control: str) -> str:
    """Return the Lichess speed bucket for a standard clock time control."""
    parts = time_control_parts(time_control)
    if parts is None:
        return "unknown"
    base, increment = parts
    game_duration = base + increment * 40
    if game_duration < 179:
        return "bullet"
    if game_duration < 479:
        return "blitz"
    if game_duration < 1499:
        return "rapid"
    return "classical"


def is_fast_time_control(time_control: str, max_base_seconds: int) -> bool:
    """Return whether a time control is in the configured bullet/blitz scope."""
    base_seconds = time_control_base_seconds(time_control)
    return base_seconds is not None and base_seconds <= max_base_seconds


def result_score(result: str) -> float | None:
    """Return the bot score contribution for a result bucket."""
    if result == "win":
        return 1.0
    if result == "draw":
        return 0.5
    if result == "loss":
        return 0.0
    return None


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


def game_final_clock_seconds(game: chess.pgn.Game, target_color: chess.Color) -> float | None:
    """Return the last PGN clock value recorded after one target-color move."""
    board = game.board()
    final_clock_seconds: float | None = None
    node: chess.pgn.GameNode = game
    while node.variations:
        next_node = node.variation(0)
        move = next_node.move
        if move is None:
            break
        mover = board.turn
        board.push(move)
        clock_seconds = next_node.clock()
        if mover == target_color and clock_seconds is not None:
            final_clock_seconds = clock_seconds
        node = next_node
    return final_clock_seconds


def game_bot_final_clock_seconds(game: chess.pgn.Game, bot_is_white: bool) -> float | None:
    """Return the last PGN clock value recorded after one of the bot's moves."""
    bot_color = chess.WHITE if bot_is_white else chess.BLACK
    return game_final_clock_seconds(game, bot_color)


def game_opponent_final_clock_seconds(game: chess.pgn.Game, bot_is_white: bool) -> float | None:
    """Return the last PGN clock value recorded after one opponent move."""
    opponent_color = chess.BLACK if bot_is_white else chess.WHITE
    return game_final_clock_seconds(game, opponent_color)


def variation_terminal_eval_cp(node: chess.pgn.GameNode) -> int | None:
    """Return the final first-line eval in centipawns from White's perspective."""
    final_eval_cp: int | None = None
    current_node = node
    while True:
        eval_score = current_node.eval()
        if eval_score is not None:
            final_eval_cp = eval_score.white().score(mate_score=40000)
        if not current_node.variations:
            return final_eval_cp
        current_node = current_node.variation(0)


def game_bot_eval_points(game: chess.pgn.Game, bot_is_white: bool) -> list[BotEvalPoint]:
    """Return saved engine evals associated with bot moves, without running an engine."""
    bot_color = chess.WHITE if bot_is_white else chess.BLACK
    bot_pov_multiplier = 1 if bot_is_white else -1
    board = game.board()
    eval_points: list[BotEvalPoint] = []
    node: chess.pgn.GameNode = game
    while node.variations:
        next_node = node.variation(0)
        move = next_node.move
        if move is None:
            break
        mover = board.turn
        san = board.san(move)
        if mover == bot_color:
            for side_variation in node.variations[1:]:
                if side_variation.move != move:
                    continue
                white_pov_cp = variation_terminal_eval_cp(side_variation)
                if white_pov_cp is not None:
                    eval_points.append(
                        BotEvalPoint(
                            san=san,
                            ply=len(board.move_stack) + 1,
                            bot_pov_cp=white_pov_cp * bot_pov_multiplier,
                        ),
                    )
                    break
        board.push(move)
        node = next_node
    return eval_points


def bot_result(result: str, bot_is_white: bool) -> str:
    """Return win/loss/draw from the configured bot's perspective."""
    if result == "1/2-1/2":
        return "draw"
    if result == "1-0":
        return "win" if bot_is_white else "loss"
    if result == "0-1":
        return "loss" if bot_is_white else "win"
    return "unknown"


def game_mode(event: str) -> str:
    """Return rated/casual mode from a Lichess Event header."""
    lowered = event.casefold()
    if "rated" in lowered:
        return "rated"
    if "casual" in lowered:
        return "casual"
    return "unknown"


def headers_match_filters(headers: chess.pgn.Headers,
                          bot_name: str,
                          max_base_seconds: int | None,
                          since_utc: datetime | None) -> bool:
    """Return whether PGN headers are in analysis scope."""
    white = headers.get("White", "")
    black = headers.get("Black", "")
    if bot_name not in {white, black}:
        return False
    if headers.get("WhiteTitle", "") != "BOT" or headers.get("BlackTitle", "") != "BOT":
        return False
    if max_base_seconds is not None and not is_fast_time_control(headers.get("TimeControl", ""), max_base_seconds):
        return False
    utc_started = parse_utc_started(headers.get("UTCDate", ""), headers.get("UTCTime", ""))
    return since_utc is None or (utc_started is not None and utc_started >= since_utc)


def parse_game(path: Path,
               bot_name: str,
               max_prefix_plies: int,
               *,
               max_base_seconds: int | None = None,
               since_utc: datetime | None = None) -> GameRecord | None:
    """Parse one PGN file if it is a bot-vs-bot game for bot_name."""
    pgn_text = path.read_text(encoding="utf-8", errors="replace")
    headers = chess.pgn.read_headers(io.StringIO(pgn_text))
    if headers is None:
        return None
    if not headers_match_filters(headers, bot_name, max_base_seconds, since_utc):
        return None

    game = chess.pgn.read_game(io.StringIO(strip_pgn_variations(pgn_text)))
    if game is None:
        return None

    white = headers.get("White", "")
    black = headers.get("Black", "")
    white_title = headers.get("WhiteTitle", "")
    black_title = headers.get("BlackTitle", "")
    utc_started = parse_utc_started(headers.get("UTCDate", ""), headers.get("UTCTime", ""))
    white_elo = parse_int(headers.get("WhiteElo", ""))
    black_elo = parse_int(headers.get("BlackElo", ""))
    bot_is_white = white == bot_name
    opponent = black if bot_is_white else white
    opponent_rating = black_elo if bot_is_white else white_elo
    bot_rating = white_elo if bot_is_white else black_elo
    rating_gap = bot_rating - opponent_rating if bot_rating is not None and opponent_rating is not None else None
    bot_rating_diff = parse_int(headers.get("WhiteRatingDiff", "")) if bot_is_white else parse_int(
        headers.get("BlackRatingDiff", "")
    )

    return GameRecord(
        path=path,
        utc_started=utc_started,
        white=white,
        black=black,
        result=headers.get("Result", "*"),
        mode=game_mode(headers.get("Event", "")),
        time_control=headers.get("TimeControl", ""),
        speed=time_control_speed(headers.get("TimeControl", "")),
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
        bot_rating_diff=bot_rating_diff,
        bot_final_clock_seconds=game_bot_final_clock_seconds(game, bot_is_white),
        opponent_final_clock_seconds=game_opponent_final_clock_seconds(game, bot_is_white),
        move_prefix=game_move_prefix(game, max_prefix_plies),
        bot_eval_points=[],
    )


def summarize_records(records_dir: Path,
                      bot_name: str,
                      *,
                      max_prefix_plies: int = 12,
                      lower_rated_draw_gap: int = 1,
                      max_base_seconds: int = 300,
                      control_min_games: int = 10,
                      high_clock_loss_threshold_seconds: int = 60,
                      clock_rich_loss_base_fraction: float = 0.35,
                      opponent_low_clock_threshold_seconds: int = 10,
                      opponent_low_clock_draw_threshold_seconds: int = 15,
                      eval_drop_recent_loss_limit: int = 50,
                      focus_time_controls: set[str] | None = None,
                      time_controls: set[str] | None = None,
                      speeds: set[str] | None = None,
                      modes: set[str] | None = None,
                      since_utc: datetime | None = None) -> GameSummary:
    """Summarize local bot-vs-bot PGN records."""
    records: list[GameRecord] = []
    for path in sorted(records_dir.glob("*.pgn")):
        record = parse_game(
            path,
            bot_name,
            max_prefix_plies,
            max_base_seconds=max_base_seconds,
            since_utc=since_utc,
        )
        if record is None:
            continue
        if not is_fast_time_control(record.time_control, max_base_seconds):
            continue
        if since_utc is not None and (record.utc_started is None or record.utc_started < since_utc):
            continue
        if time_controls and record.time_control not in time_controls:
            continue
        if speeds and record.speed not in speeds:
            continue
        if modes and record.mode not in modes:
            continue
        records.append(record)

    result_counts = Counter(record.bot_result for record in records)
    results_by_mode = Counter(f"{record.mode} {record.bot_result}" for record in records).most_common()
    results_by_speed = Counter(f"{record.speed} {record.bot_result}" for record in records).most_common()
    results_by_time_control = Counter(
        f"{record.time_control} {record.bot_result}" for record in records
    ).most_common()
    rating_impact_by_mode = rating_impact_by_group(records, lambda record: record.mode)
    rating_impact_by_speed = rating_impact_by_group(records, lambda record: record.speed)
    rating_impact_by_time_control = rating_impact_by_group(
        records,
        lambda record: f"{record.time_control} {record.bot_color}",
    )
    rating_impact_by_opening = rating_impact_by_group(records, lambda record: record.opening)
    rating_impact_by_opening_context = rating_impact_by_group(
        records,
        lambda record: f"{record.opening} | {record.bot_color} | {record.speed}",
    )
    rating_impact_by_opponent = rating_impact_by_group(
        records,
        lambda record: f"{record.opponent} | {record.speed} | {record.time_control}",
    )
    score_by_opponent = score_by_group(
        records,
        lambda record: f"{record.opponent} | {record.speed} | {record.time_control}",
    )
    focus_records = [record for record in records if focus_time_controls and record.time_control in focus_time_controls]
    focused_rating_impact_by_time_control = rating_impact_by_group(
        focus_records,
        lambda record: record.time_control,
    )
    focused_score_by_time_control = score_by_group(
        focus_records,
        lambda record: record.time_control,
    )
    focused_rating_impact_by_opening_context = rating_impact_by_group(
        focus_records,
        lambda record: f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}",
    )
    focused_score_by_opening_context = score_by_group(
        focus_records,
        lambda record: f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}",
    )
    focused_rating_impact_by_opponent = rating_impact_by_group(
        focus_records,
        lambda record: f"{record.opponent} | {record.speed} | {record.time_control}",
    )
    focused_score_by_opponent = score_by_group(
        focus_records,
        lambda record: f"{record.opponent} | {record.speed} | {record.time_control}",
    )
    worst_scoring_controls = score_by_control(records, control_min_games)
    losses = [record for record in records if record.bot_result == "loss"]
    losses_by_opening = Counter(record.opening for record in losses).most_common()
    losses_by_color = Counter(record.bot_color for record in losses).most_common()
    losses_by_termination = Counter(record.termination for record in losses).most_common()
    time_forfeit_loss_controls = Counter(
        f"{record.time_control} {record.bot_color}" for record in losses if record.termination == "Time forfeit"
    ).most_common()
    unknowns = [record for record in records if record.bot_result == "unknown"]
    unknown_result_terminations = Counter(record.termination for record in unknowns).most_common()
    unknown_result_contexts = Counter(
        f"{record.termination or 'Unknown'} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in unknowns
    ).most_common()
    loss_prefixes = Counter(record.move_prefix for record in losses if record.move_prefix).most_common()
    loss_prefix_contexts = Counter(
        f"{record.move_prefix} | {record.bot_color} | {record.speed} | {record.termination or 'Unknown'}"
        for record in losses
        if record.move_prefix
    ).most_common()
    lower_rated_draws = [
        record for record in records
        if record.bot_result == "draw" and record.rating_gap is not None and record.rating_gap >= lower_rated_draw_gap
    ]
    lower_rated_draws_by_opponent = Counter(
        f"{record.opponent} | {record.speed} | {record.time_control}" for record in lower_rated_draws
    ).most_common()
    lower_rated_draws_by_opening = Counter(record.opening for record in lower_rated_draws).most_common()
    lower_rated_draws_by_termination = Counter(record.termination for record in lower_rated_draws).most_common()
    lower_rated_draw_prefixes = Counter(record.move_prefix for record in lower_rated_draws if record.move_prefix).most_common()
    lower_rated_draw_contexts = Counter(
        f"{record.move_prefix} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in lower_rated_draws
        if record.move_prefix
    ).most_common()
    focused_lower_rated_draw_contexts = Counter(
        f"{record.move_prefix} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in lower_rated_draws
        if record.move_prefix and focus_time_controls and record.time_control in focus_time_controls
    ).most_common()
    lower_rated_draws.sort(key=lambda record: record.rating_gap or 0, reverse=True)
    rating_negative_draws = [
        record for record in records
        if record.bot_result == "draw" and record.bot_rating_diff is not None and record.bot_rating_diff < 0
    ]
    rating_negative_draws_by_opponent = Counter(
        f"{record.opponent} | {record.speed} | {record.time_control}" for record in rating_negative_draws
    ).most_common()
    rating_negative_draws_by_termination = Counter(record.termination for record in rating_negative_draws).most_common()
    rating_negative_draw_contexts = Counter(
        f"{record.move_prefix} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in rating_negative_draws
        if record.move_prefix
    ).most_common()
    focused_rating_negative_draw_contexts = Counter(
        f"{record.move_prefix} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in rating_negative_draws
        if record.move_prefix and focus_time_controls and record.time_control in focus_time_controls
    ).most_common()
    rating_negative_draws.sort(key=lambda record: record.bot_rating_diff or 0)
    opponent_leak_watchlist = opponent_leak_watchlist_for_records(losses, lower_rated_draws, rating_negative_draws)
    recent_losses = sorted(
        losses,
        key=lambda record: record.utc_started or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )[:10]
    clock_rich_normal_losses = [
        record for record in losses
        if record.termination != "Time forfeit"
        and record.bot_final_clock_seconds is not None
        and (base_seconds := time_control_base_seconds(record.time_control)) is not None
        and record.bot_final_clock_seconds >= base_seconds * clock_rich_loss_base_fraction
    ]
    clock_rich_normal_losses.sort(
        key=lambda record: record.bot_final_clock_seconds or 0,
        reverse=True,
    )
    clock_rich_normal_loss_contexts = Counter(
        f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in clock_rich_normal_losses
    ).most_common()
    high_clock_normal_losses = [
        record for record in losses
        if record.termination != "Time forfeit"
        and record.bot_final_clock_seconds is not None
        and record.bot_final_clock_seconds >= high_clock_loss_threshold_seconds
    ]
    high_clock_normal_losses.sort(
        key=lambda record: record.bot_final_clock_seconds or 0,
        reverse=True,
    )
    high_clock_normal_loss_contexts = Counter(
        f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in high_clock_normal_losses
    ).most_common()
    focused_high_clock_normal_loss_contexts = Counter(
        f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in high_clock_normal_losses
        if focus_time_controls and record.time_control in focus_time_controls
    ).most_common()
    clock_pressure_misses = [
        record for record in clock_rich_normal_losses
        if record.opponent_final_clock_seconds is not None
        and record.opponent_final_clock_seconds <= opponent_low_clock_threshold_seconds
    ]
    clock_pressure_misses.sort(
        key=lambda record: (
            record.bot_final_clock_seconds or 0,
            -(record.opponent_final_clock_seconds or 0),
        ),
        reverse=True,
    )
    clock_pressure_miss_contexts = Counter(
        f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in clock_pressure_misses
    ).most_common()
    costly_draws = {record.path: record for record in lower_rated_draws + rating_negative_draws}.values()
    clock_pressure_draw_leaks = [
        record for record in costly_draws
        if record.termination != "Time forfeit"
        and record.bot_final_clock_seconds is not None
        and record.opponent_final_clock_seconds is not None
        and (base_seconds := time_control_base_seconds(record.time_control)) is not None
        and record.bot_final_clock_seconds >= base_seconds * clock_rich_loss_base_fraction
        and record.opponent_final_clock_seconds <= opponent_low_clock_draw_threshold_seconds
    ]
    clock_pressure_draw_leaks.sort(
        key=lambda record: (
            record.bot_rating_diff or 0,
            record.rating_gap or 0,
            record.bot_final_clock_seconds or 0,
            -(record.opponent_final_clock_seconds or 0),
        ),
    )
    clock_pressure_draw_leak_contexts = Counter(
        f"{record.opening} | {record.bot_color} | {record.speed} | {record.time_control}"
        for record in clock_pressure_draw_leaks
    ).most_common()
    largest_bot_eval_drops = bot_eval_drops(recent_losses[:eval_drop_recent_loss_limit])

    return GameSummary(
        bot_name=bot_name,
        since_utc=since_utc,
        modes=modes or set(),
        time_controls=time_controls or set(),
        speeds=speeds or set(),
        total_games=len(records),
        result_counts=dict(sorted(result_counts.items())),
        results_by_mode=results_by_mode,
        results_by_speed=results_by_speed,
        results_by_time_control=results_by_time_control,
        rating_impact_by_mode=rating_impact_by_mode,
        rating_impact_by_speed=rating_impact_by_speed,
        rating_impact_by_time_control=rating_impact_by_time_control,
        rating_impact_by_opening=rating_impact_by_opening,
        rating_impact_by_opening_context=rating_impact_by_opening_context,
        rating_impact_by_opponent=rating_impact_by_opponent,
        score_by_opponent=score_by_opponent,
        opponent_leak_watchlist=opponent_leak_watchlist,
        focused_rating_impact_by_time_control=focused_rating_impact_by_time_control,
        focused_score_by_time_control=focused_score_by_time_control,
        focused_rating_impact_by_opening_context=focused_rating_impact_by_opening_context,
        focused_score_by_opening_context=focused_score_by_opening_context,
        focused_rating_impact_by_opponent=focused_rating_impact_by_opponent,
        focused_score_by_opponent=focused_score_by_opponent,
        worst_scoring_controls=worst_scoring_controls,
        losses_by_opening=losses_by_opening,
        losses_by_color=losses_by_color,
        losses_by_termination=losses_by_termination,
        time_forfeit_loss_controls=time_forfeit_loss_controls,
        unknown_result_terminations=unknown_result_terminations,
        unknown_result_contexts=unknown_result_contexts,
        loss_prefixes=loss_prefixes,
        loss_prefix_contexts=loss_prefix_contexts,
        lower_rated_draw_count=len(lower_rated_draws),
        lower_rated_draws_by_opponent=lower_rated_draws_by_opponent,
        lower_rated_draws_by_opening=lower_rated_draws_by_opening,
        lower_rated_draws_by_termination=lower_rated_draws_by_termination,
        lower_rated_draw_prefixes=lower_rated_draw_prefixes,
        focused_lower_rated_draw_contexts=focused_lower_rated_draw_contexts,
        lower_rated_draw_contexts=lower_rated_draw_contexts,
        lower_rated_draws=lower_rated_draws[:10],
        rating_negative_draws_by_opponent=rating_negative_draws_by_opponent,
        rating_negative_draws_by_termination=rating_negative_draws_by_termination,
        focused_rating_negative_draw_contexts=focused_rating_negative_draw_contexts,
        rating_negative_draw_contexts=rating_negative_draw_contexts,
        rating_negative_draws=rating_negative_draws[:10],
        clock_rich_normal_losses=clock_rich_normal_losses[:10],
        clock_rich_normal_loss_contexts=clock_rich_normal_loss_contexts,
        high_clock_normal_losses=high_clock_normal_losses[:10],
        focused_high_clock_normal_loss_contexts=focused_high_clock_normal_loss_contexts,
        high_clock_normal_loss_contexts=high_clock_normal_loss_contexts,
        clock_pressure_misses=clock_pressure_misses[:10],
        clock_pressure_miss_contexts=clock_pressure_miss_contexts,
        clock_pressure_draw_leaks=clock_pressure_draw_leaks[:10],
        clock_pressure_draw_leak_contexts=clock_pressure_draw_leak_contexts,
        largest_bot_eval_drops=largest_bot_eval_drops[:10],
        recent_losses=recent_losses,
    )


def rating_impact_by_group(records: list[GameRecord],
                           label_for_record: Callable[[GameRecord], str]) -> list[tuple[str, int, int]]:
    """Return rating impact grouped by a record label."""
    totals: dict[str, tuple[int, int]] = {}
    for record in records:
        if record.bot_rating_diff is None:
            continue
        label = label_for_record(record)
        games, rating_diff = totals.get(label, (0, 0))
        totals[label] = games + 1, rating_diff + record.bot_rating_diff
    return sorted(
        ((label, games, rating_diff) for label, (games, rating_diff) in totals.items()),
        key=lambda item: (item[2], -item[1], item[0]),
    )


def score_by_group(records: list[GameRecord],
                   label_for_record: Callable[[GameRecord], str]) -> list[tuple[str, int, int, int, int, float]]:
    """Return W-D-L score rates grouped by a record label."""
    grouped_results: dict[str, Counter[str]] = {}
    for record in records:
        if result_score(record.bot_result) is None:
            continue
        grouped_results.setdefault(label_for_record(record), Counter())[record.bot_result] += 1

    scores = []
    for label, result_counter in grouped_results.items():
        wins = result_counter["win"]
        draws = result_counter["draw"]
        losses_count = result_counter["loss"]
        total = wins + draws + losses_count
        score_percent = round((wins + 0.5 * draws) * 100 / total, 1)
        scores.append((label, wins, draws, losses_count, total, score_percent))

    return sorted(scores, key=lambda item: (item[5], -item[4], item[0]))


def score_by_control(records: list[GameRecord], min_games: int) -> list[tuple[str, int, int, int, int, float]]:
    """Return weakest score rates by exact clock and bot color."""
    control_results: dict[str, Counter[str]] = {}
    for record in records:
        if result_score(record.bot_result) is None:
            continue
        control_results.setdefault(f"{record.time_control} {record.bot_color}", Counter())[record.bot_result] += 1

    scores = []
    for control, result_counter in control_results.items():
        wins = result_counter["win"]
        draws = result_counter["draw"]
        losses_count = result_counter["loss"]
        total = wins + draws + losses_count
        if total < min_games:
            continue
        score_percent = round((wins + 0.5 * draws) * 100 / total, 1)
        scores.append((control, wins, draws, losses_count, total, score_percent))

    return sorted(scores, key=lambda item: (item[5], -item[4], item[0]))


def opponent_leak_watchlist_for_records(
    losses: list[GameRecord],
    lower_rated_draws: list[GameRecord],
    rating_negative_draws: list[GameRecord],
) -> list[tuple[str, int, int, int, int, int, datetime | None]]:
    """Return opponent-control clusters combining losses and costly draw leaks."""
    implicated_records = [*losses, *lower_rated_draws, *rating_negative_draws]
    labels = {
        record.path: f"{record.opponent} | {record.speed} | {record.time_control}"
        for record in implicated_records
    }
    loss_counts = Counter(labels[record.path] for record in losses)
    lower_draw_counts = Counter(labels[record.path] for record in lower_rated_draws)
    negative_draw_counts = Counter(labels[record.path] for record in rating_negative_draws)

    rating_diffs: dict[str, int] = {}
    latest_games: dict[str, datetime] = {}
    unique_records = {record.path: record for record in implicated_records}
    for path, record in unique_records.items():
        label = labels[path]
        if record.bot_rating_diff is None:
            rating_diffs.setdefault(label, 0)
        else:
            rating_diffs[label] = rating_diffs.get(label, 0) + record.bot_rating_diff
        if record.utc_started is not None:
            latest_games[label] = max(latest_games.get(label, record.utc_started), record.utc_started)

    watchlist = []
    for label in sorted(set(labels.values())):
        losses_count = loss_counts[label]
        lower_draws_count = lower_draw_counts[label]
        negative_draws_count = negative_draw_counts[label]
        risk_score = losses_count * 3 + lower_draws_count + negative_draws_count
        watchlist.append(
            (
                label,
                losses_count,
                lower_draws_count,
                negative_draws_count,
                rating_diffs.get(label, 0),
                risk_score,
                latest_games.get(label),
            ),
        )

    return sorted(watchlist, key=lambda item: (-item[5], item[4], item[0]))


def blocked_opponents_from_config(config_path: Path) -> set[str]:
    """Return normalized challenge and matchmaking block-list names from a runtime config."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        return set()

    blocked: set[str] = set()
    for section_name in ("challenge", "matchmaking"):
        section = config.get(section_name)
        if not isinstance(section, dict):
            continue
        block_list = section.get("block_list")
        if not isinstance(block_list, list):
            continue
        for opponent in block_list:
            if isinstance(opponent, str) and opponent.strip():
                blocked.add(opponent.strip().casefold())

    return blocked


def filtered_unblocked_watchlist(
    watchlist: list[tuple[str, int, int, int, int, int, datetime | None]],
    blocked_opponents: set[str],
) -> list[tuple[str, int, int, int, int, int, datetime | None]]:
    """Return watchlist rows whose opponent is not already blocked."""
    return [
        item for item in watchlist
        if item[0].split(" | ", maxsplit=1)[0].casefold() not in blocked_opponents
    ]


def bot_eval_drops(records: list[GameRecord]) -> list[BotEvalDrop]:
    """Return largest drops between consecutive saved bot-side evaluations."""
    drops: list[BotEvalDrop] = []
    for record in records:
        eval_points = record.bot_eval_points or read_bot_eval_points(record)
        for previous_point, current_point in pairwise(eval_points):
            drop_cp = previous_point.bot_pov_cp - current_point.bot_pov_cp
            if drop_cp <= 0:
                continue
            drops.append(
                BotEvalDrop(
                    path=record.path,
                    opponent=record.opponent,
                    opening=record.opening,
                    time_control=record.time_control,
                    bot_color=record.bot_color,
                    after_bot_move=current_point.san,
                    previous_bot_pov_cp=previous_point.bot_pov_cp,
                    bot_pov_cp=current_point.bot_pov_cp,
                    drop_cp=drop_cp,
                ),
            )
    return sorted(drops, key=lambda drop: (-drop.drop_cp, drop.path.name, drop.after_bot_move))


def read_bot_eval_points(record: GameRecord) -> list[BotEvalPoint]:
    """Read saved eval points from one PGN record on demand."""
    game = chess.pgn.read_game(io.StringIO(record.path.read_text(encoding="utf-8", errors="replace")))
    if game is None:
        return []
    return game_bot_eval_points(game, record.bot_color == "white")


def game_link(record: GameRecord) -> str:
    """Return a compact report label for a game record."""
    return f"`{record.path.name}`"


def format_seconds(seconds: float) -> str:
    """Return compact whole-second clock text for report rows."""
    return f"{round(seconds):.0f}s"


def format_eval_cp(cp: int) -> str:
    """Return centipawns as signed pawn units."""
    return f"{cp / 100:+.2f}"


def opening_risk_gate_line(summary: GameSummary, risk_threshold: int) -> str:
    """Render the opening risk gate status line."""
    top_loss_count = summary.losses_by_opening[0][1] if summary.losses_by_opening else 0
    if risk_threshold <= 0:
        return "Opening risk gate: not enabled"
    if top_loss_count >= risk_threshold:
        return f"Opening risk gate: FAILED ({top_loss_count} >= {risk_threshold})"
    return f"Opening risk gate: passed ({top_loss_count} < {risk_threshold})"


def append_count_section(lines: list[str],
                         title: str,
                         counts: list[tuple[str, int]],
                         *,
                         empty_text: str,
                         quote_item: bool = False) -> None:
    """Append a markdown section containing ranked count tuples."""
    lines.extend(["", f"## {title}", ""])
    if counts:
        if quote_item:
            lines.extend(f"- `{count}` x `{item}`" for item, count in counts[:10])
        else:
            lines.extend(f"- `{count}` x {item}" for item, count in counts[:10])
    else:
        lines.append(f"- {empty_text}")


def append_score_section(lines: list[str],
                         title: str,
                         controls: list[tuple[str, int, int, int, int, float]]) -> None:
    """Append a markdown section for exact-clock score rates."""
    lines.extend(["", f"## {title}", ""])
    if not controls:
        lines.append("- No scored controls found.")
        return
    lines.extend(
        f"- `{control}`: W-D-L `{wins}-{draws}-{losses}`, score `{score_percent}%` over `{total}` games"
        for control, wins, draws, losses, total, score_percent in controls[:10]
    )


def append_rating_impact_section(lines: list[str], title: str, impacts: list[tuple[str, int, int]]) -> None:
    """Append a markdown section for rating deltas by group."""
    lines.extend(["", f"## {title}", ""])
    if not impacts:
        lines.append("- No rating-diff tags found.")
        return
    lines.extend(
        f"- `{label}`: `{rating_diff:+d}` rating over `{games}` games"
        for label, games, rating_diff in impacts[:10]
    )


def append_opponent_leak_watchlist_section(
    lines: list[str],
    watchlist: list[tuple[str, int, int, int, int, int, datetime | None]],
    *,
    title: str = "Opponent Leak Watchlist",
) -> None:
    """Append the combined opponent risk watchlist."""
    lines.extend(["", f"## {title}", ""])
    if not watchlist:
        lines.append("- No loss or costly draw opponent clusters found.")
        return
    lines.extend(
        f"- `{label}`: risk `{risk_score}`, losses `{losses_count}`, "
        f"lower-rated draws `{lower_draws_count}`, rating-negative draws `{negative_draws_count}`, "
        f"rating `{rating_diff:+d}`, latest `{latest_game.isoformat() if latest_game else 'unknown'}`"
        for (
            label,
            losses_count,
            lower_draws_count,
            negative_draws_count,
            rating_diff,
            risk_score,
            latest_game,
        ) in watchlist[:10]
    )


def append_eval_drop_section(lines: list[str], drops: list[BotEvalDrop]) -> None:
    """Append a markdown section for saved engine eval drops."""
    lines.extend(["", "## Largest Bot Eval Drops", ""])
    if not drops:
        lines.append("- No saved bot eval drops found.")
        return
    lines.extend(
        f"- `{format_eval_cp(-drop.drop_cp)}` after `{drop.after_bot_move}` in `{drop.path.name}` "
        f"vs `{drop.opponent}`: `{format_eval_cp(drop.previous_bot_pov_cp)}` "
        f"to `{format_eval_cp(drop.bot_pov_cp)}` ({drop.opening} | {drop.bot_color} | {drop.time_control})"
        for drop in drops
    )


def append_rating_negative_draw_sections(lines: list[str], summary: GameSummary) -> None:
    """Append sections for draws that cost rating."""
    append_count_section(
        lines,
        "Rating-Negative Draw Opponents",
        summary.rating_negative_draws_by_opponent,
        empty_text="No rating-negative draw opponent clusters found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Rating-Negative Draw Terminations",
        summary.rating_negative_draws_by_termination,
        empty_text="No rating-negative draw terminations found.",
    )
    append_count_section(
        lines,
        "Focused Rating-Negative Draw Contexts",
        summary.focused_rating_negative_draw_contexts,
        empty_text="No focused rating-negative draw contexts found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Rating-Negative Draw Contexts",
        summary.rating_negative_draw_contexts,
        empty_text="No rating-negative draw contexts found.",
        quote_item=True,
    )

    lines.extend(["", "## Largest Rating-Negative Draws", ""])
    if summary.rating_negative_draws:
        lines.extend(
                f"- `{record.bot_rating_diff}` rating in {game_link(record)} vs `{record.opponent}` "
                f"({record.opponent_rating}): {record.opening}"
                for record in summary.rating_negative_draws
        )
    else:
        lines.append("- No rating-negative draws found.")


def append_lower_rated_draw_sections(lines: list[str], summary: GameSummary) -> None:
    """Append sections for draws against lower-rated opponents."""
    lines.extend(["", "## Lower-Rated Draws", ""])
    lines.append(f"- Lower-rated draws found: `{summary.lower_rated_draw_count}`")
    append_count_section(
        lines,
        "Lower-Rated Draw Opponents",
        summary.lower_rated_draws_by_opponent,
        empty_text="No lower-rated draw opponent clusters found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Lower-Rated Draw Openings",
        summary.lower_rated_draws_by_opening,
        empty_text="No lower-rated draw opening clusters found.",
    )
    append_count_section(
        lines,
        "Lower-Rated Draw Terminations",
        summary.lower_rated_draws_by_termination,
        empty_text="No lower-rated draw terminations found.",
    )
    append_count_section(
        lines,
        "Lower-Rated Draw Prefixes",
        summary.lower_rated_draw_prefixes,
        empty_text="No lower-rated draw prefixes found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Focused Lower-Rated Draw Contexts",
        summary.focused_lower_rated_draw_contexts,
        empty_text="No focused lower-rated draw contexts found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Lower-Rated Draw Contexts",
        summary.lower_rated_draw_contexts,
        empty_text="No lower-rated draw contexts found.",
        quote_item=True,
    )

    lines.extend(["", "## Largest Lower-Rated Draw Gaps", ""])
    if summary.lower_rated_draws:
        lines.extend(
                f"- gap `{record.rating_gap}` vs `{record.opponent}` "
                f"({record.opponent_rating}) in {game_link(record)}: {record.opening}"
                for record in summary.lower_rated_draws
        )
    else:
        lines.append("- No lower-rated draw leaks found at the configured threshold.")


def append_clock_loss_section(lines: list[str], title: str, records: list[GameRecord], *, empty_text: str) -> None:
    """Append a markdown section for losses where the bot finished with enough clock."""
    lines.extend(["", f"## {title}", ""])
    if not records:
        lines.append(empty_text)
        return
    for record in records:
        clock = format_seconds(record.bot_final_clock_seconds or 0)
        lines.append(f"- `{clock}` left in {game_link(record)} vs `{record.opponent}`: {record.opening}")


def append_clock_pressure_miss_section(lines: list[str], records: list[GameRecord]) -> None:
    """Append losses where the bot kept clock while the opponent was nearly out of time."""
    lines.extend(["", "## Clock-Pressure Misses", ""])
    if not records:
        lines.append("- No clock-pressure misses found at the configured threshold.")
        return
    for record in records:
        bot_clock = format_seconds(record.bot_final_clock_seconds or 0)
        opponent_clock = format_seconds(record.opponent_final_clock_seconds or 0)
        lines.append(
            f"- `{bot_clock}` left vs opponent `{opponent_clock}` in "
            f"{game_link(record)} vs `{record.opponent}`: {record.opening}"
        )


def append_clock_pressure_draw_leak_section(lines: list[str], records: list[GameRecord]) -> None:
    """Append costly draws where the bot kept clock while the opponent was nearly out of time."""
    lines.extend(["", "## Clock-Pressure Draw Leaks", ""])
    if not records:
        lines.append("- No clock-pressure draw leaks found at the configured threshold.")
        return
    for record in records:
        bot_clock = format_seconds(record.bot_final_clock_seconds or 0)
        opponent_clock = format_seconds(record.opponent_final_clock_seconds or 0)
        rating = f"{record.bot_rating_diff:+d} rating" if record.bot_rating_diff is not None else "unknown rating"
        lines.append(
            f"- `{bot_clock}` left vs opponent `{opponent_clock}` in "
            f"{game_link(record)} vs `{record.opponent}` ({rating}): {record.opening}"
        )


def append_recent_losses_section(lines: list[str], records: list[GameRecord]) -> None:
    """Append a markdown section for the latest losses."""
    lines.extend(["", "## Recent Losses", ""])
    if not records:
        lines.append("- No recent losses found.")
        return
    for record in records:
        started = record.utc_started.isoformat(sep=" ") if record.utc_started else "unknown time"
        lines.append(f"- `{started}` {game_link(record)} vs `{record.opponent}`: {record.opening}")


def render_markdown(
    summary: GameSummary,
    *,
    risk_threshold: int = 0,
    blocked_opponents: set[str] | None = None,
) -> str:
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
    ]
    if summary.since_utc is not None:
        lines.insert(5, f"- Since UTC: `{summary.since_utc.isoformat()}`")
    if summary.modes:
        modes = ", ".join(sorted(summary.modes))
        lines.insert(5, f"- Modes: `{modes}`")
    if summary.time_controls:
        time_controls = ", ".join(sorted(summary.time_controls))
        lines.insert(5, f"- Time controls: `{time_controls}`")
    if summary.speeds:
        speeds = ", ".join(sorted(summary.speeds))
        lines.insert(5, f"- Speeds: `{speeds}`")
    if blocked_opponents is not None:
        append_opponent_leak_watchlist_section(
            lines,
            filtered_unblocked_watchlist(summary.opponent_leak_watchlist, blocked_opponents),
            title="Actionable Opponent Leak Watchlist",
        )
    append_opponent_leak_watchlist_section(lines, summary.opponent_leak_watchlist)
    append_count_section(lines, "Loss Openings", summary.losses_by_opening, empty_text="No losses found.")
    append_count_section(lines, "Results by Mode", summary.results_by_mode, empty_text="No games found.")
    append_count_section(lines, "Results by Speed", summary.results_by_speed, empty_text="No games found.")
    append_count_section(
        lines,
        "Results by Time Control",
        summary.results_by_time_control,
        empty_text="No games found.",
    )
    append_rating_impact_section(lines, "Rating Impact by Mode", summary.rating_impact_by_mode)
    append_rating_impact_section(lines, "Rating Impact by Speed", summary.rating_impact_by_speed)
    append_rating_impact_section(lines, "Rating Impact by Time Control", summary.rating_impact_by_time_control)
    append_rating_impact_section(lines, "Rating Impact by Opening", summary.rating_impact_by_opening)
    append_rating_impact_section(lines, "Rating Impact by Opening Context", summary.rating_impact_by_opening_context)
    append_rating_impact_section(lines, "Rating Impact by Opponent", summary.rating_impact_by_opponent)
    append_score_section(lines, "Score by Opponent", summary.score_by_opponent)
    append_rating_impact_section(lines, "Focused Rating Impact by Time Control", summary.focused_rating_impact_by_time_control)
    append_score_section(lines, "Focused Score by Time Control", summary.focused_score_by_time_control)
    append_rating_impact_section(
        lines,
        "Focused Rating Impact by Opening Context",
        summary.focused_rating_impact_by_opening_context,
    )
    append_score_section(lines, "Focused Score by Opening Context", summary.focused_score_by_opening_context)
    append_rating_impact_section(lines, "Focused Rating Impact by Opponent", summary.focused_rating_impact_by_opponent)
    append_score_section(lines, "Focused Score by Opponent", summary.focused_score_by_opponent)
    append_score_section(lines, "Worst Scoring Controls", summary.worst_scoring_controls)
    append_count_section(lines, "Loss Colors", summary.losses_by_color, empty_text="No losses found.")
    append_count_section(lines, "Loss Terminations", summary.losses_by_termination, empty_text="No losses found.")
    append_count_section(
        lines,
        "Time Forfeit Loss Controls",
        summary.time_forfeit_loss_controls,
        empty_text="No time-forfeit losses found.",
    )
    append_count_section(
        lines,
        "Unknown Result Terminations",
        summary.unknown_result_terminations,
        empty_text="No unknown-result games found.",
    )
    append_count_section(
        lines,
        "Unknown Result Contexts",
        summary.unknown_result_contexts,
        empty_text="No unknown-result contexts found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Loss Prefixes",
        summary.loss_prefixes,
        empty_text="No loss prefixes found.",
        quote_item=True,
    )
    append_count_section(
        lines,
        "Loss Prefix Contexts",
        summary.loss_prefix_contexts,
        empty_text="No loss prefix contexts found.",
        quote_item=True,
    )

    append_lower_rated_draw_sections(lines, summary)
    append_rating_negative_draw_sections(lines, summary)

    append_count_section(
        lines,
        "Clock-Rich Normal Loss Contexts",
        summary.clock_rich_normal_loss_contexts,
        empty_text="No clock-rich normal loss contexts found.",
        quote_item=True,
    )

    append_clock_loss_section(
        lines,
        "Clock-Rich Normal Losses",
        summary.clock_rich_normal_losses,
        empty_text="- No clock-rich normal losses found at the configured threshold.",
    )

    append_count_section(
        lines,
        "Focused High-Clock Normal Loss Contexts",
        summary.focused_high_clock_normal_loss_contexts,
        empty_text="No focused high-clock normal loss contexts found.",
        quote_item=True,
    )

    append_count_section(
        lines,
        "High-Clock Normal Loss Contexts",
        summary.high_clock_normal_loss_contexts,
        empty_text="No high-clock normal loss contexts found.",
        quote_item=True,
    )

    append_clock_loss_section(
        lines,
        "High-Clock Normal Losses",
        summary.high_clock_normal_losses,
        empty_text="- No high-clock normal losses found at the configured threshold.",
    )

    append_count_section(
        lines,
        "Clock-Pressure Miss Contexts",
        summary.clock_pressure_miss_contexts,
        empty_text="No clock-pressure miss contexts found.",
        quote_item=True,
    )

    append_clock_pressure_miss_section(lines, summary.clock_pressure_misses)

    append_count_section(
        lines,
        "Clock-Pressure Draw Leak Contexts",
        summary.clock_pressure_draw_leak_contexts,
        empty_text="No clock-pressure draw leak contexts found.",
        quote_item=True,
    )

    append_clock_pressure_draw_leak_section(lines, summary.clock_pressure_draw_leaks)

    append_eval_drop_section(lines, summary.largest_bot_eval_drops)
    append_recent_losses_section(lines, summary.recent_losses)

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
    parser.add_argument("--control-min-games", type=int, default=10,
                        help="Minimum scored games for exact-clock score-rate clusters.")
    parser.add_argument("--high-clock-loss-threshold-seconds", type=int, default=60,
                        help="Minimum remaining bot clock for non-time loss examples.")
    parser.add_argument("--focus-time-controls",
                        help="Comma-separated exact time controls to highlight in focused sections.")
    parser.add_argument("--time-controls", help="Comma-separated exact time controls to include.")
    parser.add_argument("--speeds", help="Comma-separated Lichess speed buckets to include, e.g. bullet or blitz.")
    parser.add_argument("--modes", help="Comma-separated game modes to include, e.g. rated or rated,casual.")
    parser.add_argument("--risk-threshold", type=int, default=0, help="Fail when any loss opening reaches this count.")
    parser.add_argument("--blocked-opponents", help="Comma-separated opponent names to hide from actionable leak rows.")
    parser.add_argument("--block-list-config",
                        help="YAML config whose challenge/matchmaking block_list hides already-blocked leak rows.")
    parser.add_argument("--output", help="Optional markdown output path. Defaults to stdout.")
    return parser.parse_args(argv)


def parse_blocked_opponents(raw_names: str | None) -> set[str]:
    """Parse comma-separated blocked opponent names."""
    if not raw_names:
        return set()
    return {name.strip().casefold() for name in raw_names.split(",") if name.strip()}


def main(argv: Sequence[str] | None = None) -> int:
    """Run the PGN analyzer."""
    args = parse_args(argv)
    summary = summarize_records(
        Path(args.records_dir),
        args.bot,
        max_prefix_plies=args.max_prefix_plies,
        lower_rated_draw_gap=args.lower_rated_draw_gap,
        max_base_seconds=args.max_base_seconds,
        control_min_games=args.control_min_games,
        high_clock_loss_threshold_seconds=args.high_clock_loss_threshold_seconds,
        focus_time_controls=parse_focus_time_controls(args.focus_time_controls),
        time_controls=parse_focus_time_controls(args.time_controls),
        speeds=parse_speeds(args.speeds),
        modes=parse_modes(args.modes),
        since_utc=parse_since_utc(args.since_utc),
    )
    blocked_opponents = parse_blocked_opponents(args.blocked_opponents)
    if args.block_list_config:
        blocked_opponents.update(blocked_opponents_from_config(Path(args.block_list_config)))

    markdown = render_markdown(
        summary,
        risk_threshold=args.risk_threshold,
        blocked_opponents=blocked_opponents or None,
    )
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    top_loss_count = summary.losses_by_opening[0][1] if summary.losses_by_opening else 0
    return 1 if args.risk_threshold > 0 and top_loss_count >= args.risk_threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
