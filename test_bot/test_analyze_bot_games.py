"""Tests for lightweight bot game analysis."""

from pathlib import Path

from scripts.analyze_bot_games import render_markdown, summarize_records


def write_pgn(records_dir: Path, name: str, headers: dict[str, str], moves: str) -> None:
    """Write a small PGN file with the given headers and moves."""
    header_text = "\n".join(f'[{key} "{value}"]' for key, value in headers.items())
    records_dir.joinpath(name).write_text(f"{header_text}\n\n{moves}\n", encoding="utf-8")


def base_headers(result: str, opening: str, white: str, black: str) -> dict[str, str]:
    """Create common fast bot-vs-bot PGN headers."""
    return {
        "Event": "rated blitz game",
        "Site": "https://lichess.org/testgame",
        "Date": "2026.06.08",
        "UTCDate": "2026.06.08",
        "UTCTime": "10:00:00",
        "White": white,
        "Black": black,
        "Result": result,
        "WhiteElo": "3050" if white != "ilovecatgirl" else "2940",
        "BlackElo": "3050" if black != "ilovecatgirl" else "2940",
        "WhiteTitle": "BOT",
        "BlackTitle": "BOT",
        "Variant": "Standard",
        "TimeControl": "180+3",
        "Opening": opening,
        "Termination": "Normal",
    }


def test_summarize_records__clusters_losses_and_lower_rated_draws(tmp_path: Path) -> None:
    """Loss clusters and lower-rated draw leaks should be visible without engine analysis."""
    write_pgn(
        tmp_path,
        "najdorf-loss.pgn",
        base_headers("1-0", "Sicilian Defense: Najdorf Variation, English Attack", "ArasanX", "ilovecatgirl"),
        "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 1-0",
    )
    draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", "LowerBot")
    draw_headers["WhiteElo"] = "2940"
    draw_headers["BlackElo"] = "2500"
    write_pgn(tmp_path, "lower-draw.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    write_pgn(
        tmp_path,
        "win.pgn",
        base_headers("1-0", "Caro-Kann Defense", "ilovecatgirl", "StrongBot"),
        "1. e4 c6 2. d4 d5 1-0",
    )
    slow_headers = base_headers("1-0", "Slow Opening", "SlowBot", "ilovecatgirl")
    slow_headers["TimeControl"] = "600+0"
    write_pgn(tmp_path, "slow-loss.pgn", slow_headers, "1. e4 c5 2. Nf3 d6 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", max_prefix_plies=8, lower_rated_draw_gap=200)
    markdown = render_markdown(summary, risk_threshold=1)

    assert summary.total_games == 3
    assert summary.result_counts == {"draw": 1, "loss": 1, "win": 1}
    assert summary.losses_by_opening[0][0] == "Sicilian Defense: Najdorf Variation, English Attack"
    assert summary.losses_by_opening[0][1] == 1
    assert summary.loss_prefixes[0][0] == "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6"
    assert summary.lower_rated_draws[0].path.name == "lower-draw.pgn"
    assert "Opening risk gate: FAILED" in markdown
    assert "Lower-Rated Draws" in markdown
