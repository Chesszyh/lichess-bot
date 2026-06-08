"""Tests for lightweight bot game analysis."""

from pathlib import Path

from scripts.analyze_bot_games import parse_args, render_markdown, summarize_records


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
    assert summary.lower_rated_draw_count == 1
    assert "Opening risk gate: FAILED" in markdown
    assert "Lower-Rated Draws" in markdown


def test_summarize_records__default_draw_gap_includes_any_lower_rated_bot(tmp_path: Path) -> None:
    """The default lower-rated draw threshold should not hide small rating-gap draw leaks."""
    draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", "SlightlyLowerBot")
    draw_headers["WhiteElo"] = "2940"
    draw_headers["BlackElo"] = "2939"
    write_pgn(tmp_path, "slightly-lower-draw.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl")

    assert parse_args([]).lower_rated_draw_gap == 1
    assert summary.lower_rated_draws[0].path.name == "slightly-lower-draw.pgn"


def test_render_markdown__shows_loss_color_distribution(tmp_path: Path) -> None:
    """Black-loss concentration should be visible in the lightweight report."""
    write_pgn(
        tmp_path,
        "black-loss.pgn",
        base_headers("1-0", "Sicilian Defense: Najdorf Variation", "StrongBot", "ilovecatgirl"),
        "1. e4 c5 2. Nf3 d6 1-0",
    )
    write_pgn(
        tmp_path,
        "white-loss.pgn",
        base_headers("0-1", "Caro-Kann Defense", "ilovecatgirl", "StrongBot"),
        "1. e4 c6 2. d4 d5 0-1",
    )

    markdown = render_markdown(summarize_records(tmp_path, "ilovecatgirl"))

    assert "Loss Colors" in markdown
    assert "`1` x black" in markdown
    assert "`1` x white" in markdown


def test_render_markdown__shows_loss_termination_distribution(tmp_path: Path) -> None:
    """Clock and network-adjacent losses should be visible apart from opening clusters."""
    time_loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "abcd_engine")
    time_loss_headers["Termination"] = "Time forfeit"
    write_pgn(tmp_path, "time-loss.pgn", time_loss_headers, "1. d4 Nf6 0-1")
    normal_loss_headers = base_headers("1-0", "Sicilian Defense", "StrongBot", "ilovecatgirl")
    normal_loss_headers["Termination"] = "Normal"
    write_pgn(tmp_path, "normal-loss.pgn", normal_loss_headers, "1. e4 c5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.losses_by_termination == [("Normal", 1), ("Time forfeit", 1)]
    assert "Loss Terminations" in markdown
    assert "`1` x Time forfeit" in markdown


def test_render_markdown__shows_lower_rated_draw_count(tmp_path: Path) -> None:
    """The report should expose the total lower-rated draw count, not only the top examples."""
    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", f"LowerBot{index}")
        draw_headers["WhiteElo"] = "2940"
        draw_headers["BlackElo"] = str(2939 - index)
        write_pgn(tmp_path, f"lower-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")

    markdown = render_markdown(summarize_records(tmp_path, "ilovecatgirl"))

    assert "Lower-rated draws found: `2`" in markdown


def test_render_markdown__clusters_lower_rated_draw_openings_and_prefixes(tmp_path: Path) -> None:
    """Repeated lower-rated draw openings should be visible as actionable clusters."""
    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", f"LowerBot{index}")
        draw_headers["WhiteElo"] = "2940"
        draw_headers["BlackElo"] = str(2939 - index)
        write_pgn(tmp_path, f"lower-french-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    caro_headers = base_headers("1/2-1/2", "Caro-Kann Defense", "ilovecatgirl", "LowerCaroBot")
    caro_headers["WhiteElo"] = "2940"
    caro_headers["BlackElo"] = "2930"
    write_pgn(tmp_path, "lower-caro-draw.pgn", caro_headers, "1. e4 c6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl", max_prefix_plies=4)
    markdown = render_markdown(summary)

    assert summary.lower_rated_draws_by_opening[0] == ("French Defense", 2)
    assert summary.lower_rated_draw_prefixes[0] == ("e4 e6 d4 d5", 2)
    assert "Lower-Rated Draw Openings" in markdown
    assert "`2` x French Defense" in markdown
    assert "Lower-Rated Draw Prefixes" in markdown
    assert "`2` x `e4 e6 d4 d5`" in markdown
