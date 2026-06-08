"""Tests for lightweight bot game analysis."""

from datetime import UTC, datetime
from pathlib import Path

from scripts.analyze_bot_games import parse_args, render_markdown, strip_pgn_variations, summarize_records


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


def test_render_markdown__shows_since_utc_scope(tmp_path: Path) -> None:
    """Post-config reports should declare the UTC cutoff used for filtering."""
    old_headers = base_headers("0-1", "Old Opening", "ilovecatgirl", "OldBot")
    old_headers["UTCTime"] = "09:00:00"
    write_pgn(tmp_path, "old-loss.pgn", old_headers, "1. d4 Nf6 0-1")
    new_headers = base_headers("1-0", "New Opening", "ilovecatgirl", "NewBot")
    new_headers["UTCTime"] = "11:00:00"
    write_pgn(tmp_path, "new-win.pgn", new_headers, "1. e4 c6 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", since_utc=datetime(2026, 6, 8, 10, 30, tzinfo=UTC))
    markdown = render_markdown(summary)

    assert summary.total_games == 1
    assert summary.result_counts == {"win": 1}
    assert "Since UTC: `2026-06-08T10:30:00+00:00`" in markdown


def test_render_markdown__shows_rated_mode_distribution(tmp_path: Path) -> None:
    """Rating-focused tuning should distinguish rated games from casual resource usage."""
    rated_headers = base_headers("1-0", "Rated Opening", "ilovecatgirl", "RatedBot")
    rated_headers["Event"] = "rated bullet game"
    rated_headers["TimeControl"] = "60+1"
    rated_headers["WhiteRatingDiff"] = "+5"
    write_pgn(tmp_path, "rated-win.pgn", rated_headers, "1. e4 c5 1-0")
    casual_headers = base_headers("0-1", "Casual Opening", "ilovecatgirl", "CasualBot")
    casual_headers["Event"] = "casual blitz game"
    casual_headers.pop("WhiteRatingDiff", None)
    casual_headers.pop("BlackRatingDiff", None)
    write_pgn(tmp_path, "casual-loss.pgn", casual_headers, "1. d4 Nf6 0-1")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.results_by_mode == [("casual loss", 1), ("rated win", 1)]
    assert summary.rating_impact_by_mode == [("rated", 1, 5)]
    assert "Results by Mode" in markdown
    assert "`1` x casual loss" in markdown
    assert "Rating Impact by Mode" in markdown
    assert "`rated`: `+5` rating over `1` games" in markdown


def test_summarize_records__can_filter_to_rated_games(tmp_path: Path) -> None:
    """Rating-target reports should be able to exclude historical casual games."""
    rated_headers = base_headers("1-0", "Rated Opening", "ilovecatgirl", "RatedBot")
    rated_headers["Event"] = "rated bullet game"
    rated_headers["WhiteRatingDiff"] = "+5"
    write_pgn(tmp_path, "rated-win.pgn", rated_headers, "1. e4 c5 1-0")
    casual_headers = base_headers("0-1", "Casual Opening", "ilovecatgirl", "CasualBot")
    casual_headers["Event"] = "casual blitz game"
    write_pgn(tmp_path, "casual-loss.pgn", casual_headers, "1. d4 Nf6 0-1")

    summary = summarize_records(tmp_path, "ilovecatgirl", modes={"rated"})
    markdown = render_markdown(summary)

    assert parse_args(["--modes", "rated"]).modes == "rated"
    assert summary.total_games == 1
    assert summary.modes == {"rated"}
    assert summary.results_by_mode == [("rated win", 1)]
    assert summary.rating_impact_by_mode == [("rated", 1, 5)]
    assert "Modes: `rated`" in markdown
    assert "casual" not in markdown


def test_summarize_records__can_filter_to_exact_time_controls(tmp_path: Path) -> None:
    """Active-control reports should be able to exclude abandoned historical controls."""
    active_headers = base_headers("1-0", "Active Opening", "ilovecatgirl", "ActiveBot")
    active_headers["TimeControl"] = "90+1"
    active_headers["WhiteRatingDiff"] = "+4"
    write_pgn(tmp_path, "active-win.pgn", active_headers, "1. e4 c5 1-0")
    abandoned_headers = base_headers("0-1", "Abandoned Opening", "ilovecatgirl", "OldBot")
    abandoned_headers["TimeControl"] = "180+2"
    abandoned_headers["WhiteRatingDiff"] = "-6"
    write_pgn(tmp_path, "abandoned-loss.pgn", abandoned_headers, "1. d4 Nf6 0-1")

    summary = summarize_records(tmp_path, "ilovecatgirl", time_controls={"90+1"})
    markdown = render_markdown(summary)

    assert parse_args(["--time-controls", "90+1"]).time_controls == "90+1"
    assert summary.total_games == 1
    assert summary.time_controls == {"90+1"}
    assert summary.results_by_time_control == [("90+1 win", 1)]
    assert summary.rating_impact_by_time_control == [("90+1 white", 1, 4)]
    assert "Time controls: `90+1`" in markdown
    assert "180+2" not in markdown


def test_summarize_records__can_filter_to_speed_bucket(tmp_path: Path) -> None:
    """Bullet/blitz tuning should be able to isolate one Lichess speed bucket."""
    bullet_headers = base_headers("1-0", "Bullet Opening", "ilovecatgirl", "BulletBot")
    bullet_headers["TimeControl"] = "60+1"
    bullet_headers["WhiteRatingDiff"] = "+4"
    write_pgn(tmp_path, "bullet-win.pgn", bullet_headers, "1. e4 c5 1-0")
    blitz_headers = base_headers("0-1", "Blitz Opening", "ilovecatgirl", "BlitzBot")
    blitz_headers["TimeControl"] = "180+2"
    blitz_headers["WhiteRatingDiff"] = "-6"
    write_pgn(tmp_path, "blitz-loss.pgn", blitz_headers, "1. d4 Nf6 0-1")

    summary = summarize_records(tmp_path, "ilovecatgirl", speeds={"blitz"})
    markdown = render_markdown(summary)

    assert parse_args(["--speeds", "blitz"]).speeds == "blitz"
    assert summary.total_games == 1
    assert summary.speeds == {"blitz"}
    assert summary.results_by_speed == [("blitz loss", 1)]
    assert summary.rating_impact_by_speed == [("blitz", 1, -6)]
    assert "Speeds: `blitz`" in markdown
    assert "bullet" not in markdown


def test_render_markdown__shows_unknown_result_terminations(tmp_path: Path) -> None:
    """Abandoned games should not be hidden inside the generic unknown bucket."""
    abandoned_headers = base_headers("*", "King's Pawn Game", "AbandonBot", "ilovecatgirl")
    abandoned_headers["TimeControl"] = "60+1"
    abandoned_headers["Termination"] = "Abandoned"
    abandoned_headers.pop("WhiteRatingDiff", None)
    abandoned_headers.pop("BlackRatingDiff", None)
    write_pgn(tmp_path, "abandoned-active.pgn", abandoned_headers, "1. e4 *")
    loss_headers = base_headers("1-0", "Sicilian Defense", "StrongBot", "ilovecatgirl")
    loss_headers["TimeControl"] = "60+1"
    write_pgn(tmp_path, "rated-loss.pgn", loss_headers, "1. e4 c5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", time_controls={"60+1"})
    markdown = render_markdown(summary)

    assert summary.unknown_result_terminations == [("Abandoned", 1)]
    assert summary.unknown_result_contexts == [("Abandoned | black | bullet | 60+1", 1)]
    assert "Unknown Result Terminations" in markdown
    assert "`1` x Abandoned" in markdown
    assert "Unknown Result Contexts" in markdown
    assert "`1` x `Abandoned | black | bullet | 60+1`" in markdown


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


def test_render_markdown__clusters_time_forfeit_losses_by_time_control_and_color(tmp_path: Path) -> None:
    """Time-forfeit losses should show whether a clock setting or color is concentrated."""
    for index in range(2):
        loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", f"ClockBot{index}")
        loss_headers["Termination"] = "Time forfeit"
        loss_headers["TimeControl"] = "180+0"
        write_pgn(tmp_path, f"white-180-zero-loss-{index}.pgn", loss_headers, "1. d4 Nf6 0-1")
    black_loss_headers = base_headers("1-0", "Sicilian Defense", "StrongBot", "ilovecatgirl")
    black_loss_headers["Termination"] = "Time forfeit"
    black_loss_headers["TimeControl"] = "60+1"
    write_pgn(tmp_path, "black-60-one-loss.pgn", black_loss_headers, "1. e4 c5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.time_forfeit_loss_controls[0] == ("180+0 white", 2)
    assert "Time Forfeit Loss Controls" in markdown
    assert "`2` x 180+0 white" in markdown


def test_render_markdown__clusters_results_by_speed_and_time_control(tmp_path: Path) -> None:
    """Bullet weighting needs a visible result split by speed and exact clock."""
    for index in range(2):
        loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", f"BulletBot{index}")
        loss_headers["TimeControl"] = "60+1"
        write_pgn(tmp_path, f"bullet-loss-{index}.pgn", loss_headers, "1. d4 Nf6 0-1")
    win_headers = base_headers("1-0", "Sicilian Defense", "ilovecatgirl", "BlitzBot")
    win_headers["TimeControl"] = "180+2"
    write_pgn(tmp_path, "blitz-win.pgn", win_headers, "1. e4 c5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.results_by_speed[0] == ("bullet loss", 2)
    assert ("blitz win", 1) in summary.results_by_speed
    assert "Results by Speed" in markdown
    assert "`2` x 60+1 loss" in markdown


def test_render_markdown__shows_rating_impact_by_speed_and_time_control(tmp_path: Path) -> None:
    """Rating deltas should expose which speed and clock pools are costing rating."""
    bullet_loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "BulletBot")
    bullet_loss_headers["TimeControl"] = "60+1"
    bullet_loss_headers["WhiteRatingDiff"] = "-8"
    bullet_loss_headers["BlackRatingDiff"] = "+8"
    write_pgn(tmp_path, "bullet-loss.pgn", bullet_loss_headers, "1. d4 Nf6 0-1")
    bullet_win_headers = base_headers("1-0", "Caro-Kann Defense", "ilovecatgirl", "AnotherBulletBot")
    bullet_win_headers["TimeControl"] = "60+1"
    bullet_win_headers["WhiteRatingDiff"] = "+3"
    bullet_win_headers["BlackRatingDiff"] = "-3"
    write_pgn(tmp_path, "bullet-win.pgn", bullet_win_headers, "1. e4 c6 1-0")
    blitz_loss_headers = base_headers("1-0", "Sicilian Defense", "BlitzBot", "ilovecatgirl")
    blitz_loss_headers["TimeControl"] = "180+2"
    blitz_loss_headers["WhiteRatingDiff"] = "+6"
    blitz_loss_headers["BlackRatingDiff"] = "-6"
    write_pgn(tmp_path, "blitz-loss.pgn", blitz_loss_headers, "1. e4 c5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.rating_impact_by_speed[0] == ("blitz", 1, -6)
    assert summary.rating_impact_by_speed[1] == ("bullet", 2, -5)
    assert summary.rating_impact_by_time_control[0] == ("180+2 black", 1, -6)
    assert summary.rating_impact_by_time_control[1] == ("60+1 white", 2, -5)
    assert "Rating Impact by Speed" in markdown
    assert "`blitz`: `-6` rating over `1` games" in markdown
    assert "Rating Impact by Time Control" in markdown
    assert "`60+1 white`: `-5` rating over `2` games" in markdown


def test_render_markdown__shows_rating_impact_by_opening_and_context(tmp_path: Path) -> None:
    """Opening rating impact should expose which color and speed contexts are costing rating."""
    for index in range(2):
        najdorf_headers = base_headers(
            "1-0",
            "Sicilian Defense: Najdorf Variation, English Attack",
            f"NajdorfBot{index}",
            "ilovecatgirl",
        )
        najdorf_headers["TimeControl"] = "60+1"
        najdorf_headers["WhiteRatingDiff"] = "+7"
        najdorf_headers["BlackRatingDiff"] = "-7"
        write_pgn(tmp_path, f"black-bullet-najdorf-loss-{index}.pgn", najdorf_headers, "1. e4 c5 1-0")
    win_headers = base_headers("0-1", "Caro-Kann Defense", "CaroBot", "ilovecatgirl")
    win_headers["TimeControl"] = "180+2"
    win_headers["WhiteRatingDiff"] = "-3"
    win_headers["BlackRatingDiff"] = "+3"
    write_pgn(tmp_path, "black-blitz-caro-win.pgn", win_headers, "1. e4 c6 0-1")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.rating_impact_by_opening[0] == ("Sicilian Defense: Najdorf Variation, English Attack", 2, -14)
    assert summary.rating_impact_by_opening_context[0] == (
        "Sicilian Defense: Najdorf Variation, English Attack | black | bullet",
        2,
        -14,
    )
    assert "Rating Impact by Opening" in markdown
    assert "`Sicilian Defense: Najdorf Variation, English Attack`: `-14` rating over `2` games" in markdown
    assert "Rating Impact by Opening Context" in markdown
    assert "`Sicilian Defense: Najdorf Variation, English Attack | black | bullet`: `-14` rating over `2` games" in markdown


def test_render_markdown__shows_high_clock_normal_losses(tmp_path: Path) -> None:
    """Normal losses with plenty of remaining clock should be separated from clock losses."""
    high_clock_headers = base_headers("1-0", "Queen's Gambit Accepted", "Cheszter", "ilovecatgirl")
    high_clock_headers["TimeControl"] = "60+2"
    write_pgn(
        tmp_path,
        "high-clock-normal-loss.pgn",
        high_clock_headers,
        "1. d4 { [%clk 0:01:01] } d5 { [%clk 0:01:27] } 1-0",
    )
    low_clock_headers = base_headers("1-0", "Sicilian Defense", "FastBot", "ilovecatgirl")
    low_clock_headers["TimeControl"] = "60+1"
    write_pgn(
        tmp_path,
        "low-clock-normal-loss.pgn",
        low_clock_headers,
        "1. e4 { [%clk 0:00:59] } c5 { [%clk 0:00:12] } 1-0",
    )
    time_forfeit_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "ClockBot")
    time_forfeit_headers["Termination"] = "Time forfeit"
    write_pgn(
        tmp_path,
        "high-clock-time-forfeit-loss.pgn",
        time_forfeit_headers,
        "1. d4 { [%clk 0:01:27] } Nf6 { [%clk 0:00:59] } 0-1",
    )

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert [record.path.name for record in summary.high_clock_normal_losses] == ["high-clock-normal-loss.pgn"]
    assert summary.high_clock_normal_loss_contexts == [("Queen's Gambit Accepted | black | bullet | 60+2", 1)]
    assert "High-Clock Normal Loss Contexts" in markdown
    assert "`1` x `Queen's Gambit Accepted | black | bullet | 60+2`" in markdown
    assert "High-Clock Normal Losses" in markdown
    high_clock_section = markdown.split("## High-Clock Normal Losses", maxsplit=1)[1].split("## Recent Losses")[0]
    assert "`87s` left in `high-clock-normal-loss.pgn` vs `Cheszter`: Queen's Gambit Accepted" in high_clock_section
    assert "low-clock-normal-loss.pgn" not in high_clock_section
    assert "high-clock-time-forfeit-loss.pgn" not in high_clock_section


def test_render_markdown__shows_clock_rich_normal_losses_by_base_fraction(tmp_path: Path) -> None:
    """Bullet losses with substantial remaining clock should not be hidden by a fixed 60s threshold."""
    clock_rich_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "StrongBot")
    clock_rich_headers["TimeControl"] = "60+1"
    write_pgn(
        tmp_path,
        "clock-rich-bullet-loss.pgn",
        clock_rich_headers,
        "1. d4 { [%clk 0:00:28] } Nf6 { [%clk 0:00:34] } 0-1",
    )
    low_clock_headers = base_headers("0-1", "Scotch Game", "ilovecatgirl", "FastBot")
    low_clock_headers["TimeControl"] = "60+1"
    write_pgn(
        tmp_path,
        "low-clock-bullet-loss.pgn",
        low_clock_headers,
        "1. e4 { [%clk 0:00:12] } e5 { [%clk 0:00:30] } 0-1",
    )

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.clock_rich_normal_loss_contexts == [("Nimzo-Indian Defense | white | bullet | 60+1", 1)]
    assert "Clock-Rich Normal Loss Contexts" in markdown
    assert "`1` x `Nimzo-Indian Defense | white | bullet | 60+1`" in markdown
    clock_rich_section = markdown.split("## Clock-Rich Normal Losses", maxsplit=1)[1].split(
        "## Recent Losses",
    )[0]
    assert "`28s` left in `clock-rich-bullet-loss.pgn` vs `StrongBot`: Nimzo-Indian Defense" in clock_rich_section
    assert "low-clock-bullet-loss.pgn" not in clock_rich_section


def test_render_markdown__shows_clock_pressure_misses(tmp_path: Path) -> None:
    """Losses with bot clock rich and opponent clock low should be called out as time-use misses."""
    pressure_headers = base_headers("1-0", "Semi-Slav Defense", "PressureBot", "ilovecatgirl")
    pressure_headers["TimeControl"] = "120+1"
    write_pgn(
        tmp_path,
        "pressure-miss-loss.pgn",
        pressure_headers,
        "1. d4 { [%clk 0:00:04] } d5 { [%clk 0:01:20] } 1-0",
    )
    ordinary_headers = base_headers("1-0", "Caro-Kann Defense", "SteadyBot", "ilovecatgirl")
    ordinary_headers["TimeControl"] = "120+1"
    write_pgn(
        tmp_path,
        "ordinary-clock-rich-loss.pgn",
        ordinary_headers,
        "1. e4 { [%clk 0:00:40] } c6 { [%clk 0:01:20] } 1-0",
    )

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert [record.path.name for record in summary.clock_pressure_misses] == ["pressure-miss-loss.pgn"]
    pressure_section = markdown.split("## Clock-Pressure Misses", maxsplit=1)[1].split("## Largest Bot Eval Drops")[0]
    assert "`80s` left vs opponent `4s` in `pressure-miss-loss.pgn` vs `PressureBot`: Semi-Slav Defense" in pressure_section
    assert "ordinary-clock-rich-loss.pgn" not in pressure_section


def test_render_markdown__shows_largest_bot_eval_drops(tmp_path: Path) -> None:
    """Saved engine evals should identify tactical/conversion drops without rerunning engines."""
    loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "StrongBot")
    loss_headers["TimeControl"] = "60+1"
    write_pgn(
        tmp_path,
        "eval-drop-loss.pgn",
        loss_headers,
        (
            "1. d4 ( 1. d4 Nf6 { [%eval 1.20,10] } ) Nf6 "
            "2. c4 ( 2. c4 e6 { [%eval 0.40,10] } ) e6 "
            "3. Nc3 ( 3. Nc3 Bb4 { [%eval 0.35,10] } ) Bb4 0-1"
        ),
    )

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    eval_drop = summary.largest_bot_eval_drops[0]
    assert eval_drop.path.name == "eval-drop-loss.pgn"
    assert eval_drop.after_bot_move == "c4"
    assert eval_drop.drop_cp == 80
    assert "Largest Bot Eval Drops" in markdown
    assert "`-0.80` after `c4` in `eval-drop-loss.pgn` vs `StrongBot`: `+1.20` to `+0.40`" in markdown


def test_strip_pgn_variations__preserves_mainline_comments_and_removes_side_lines() -> None:
    """Large saved engine PVs should not be parsed for mainline-only summary fields."""
    pgn_text = (
        "1. d4 { [%clk 0:01:00] } ( 1. d4 Nf6 2. c4 e6 { [%eval 0.32,10] } ) "
        "1... Nf6 { [%clk 0:01:00] } 2. c4 { [%clk 0:00:59] } 1/2-1/2"
    )

    assert strip_pgn_variations(pgn_text) == (
        "1. d4 { [%clk 0:01:00] }  "
        "1... Nf6 { [%clk 0:01:00] } 2. c4 { [%clk 0:00:59] } 1/2-1/2"
    )


def test_render_markdown__shows_focused_high_clock_normal_loss_contexts(tmp_path: Path) -> None:
    """Focused high-clock loss contexts should separate current controls from abandoned historical controls."""
    current_headers = base_headers("1-0", "Queen's Gambit Accepted", "Cheszter", "ilovecatgirl")
    current_headers["TimeControl"] = "60+2"
    write_pgn(
        tmp_path,
        "current-control-loss.pgn",
        current_headers,
        "1. d4 { [%clk 0:01:01] } d5 { [%clk 0:01:27] } 1-0",
    )
    abandoned_headers = base_headers("1-0", "Caro-Kann Defense", "SlowBot", "ilovecatgirl")
    abandoned_headers["TimeControl"] = "300+2"
    write_pgn(
        tmp_path,
        "abandoned-control-loss.pgn",
        abandoned_headers,
        "1. e4 { [%clk 0:05:00] } c6 { [%clk 0:05:00] } 1-0",
    )

    summary = summarize_records(tmp_path, "ilovecatgirl", focus_time_controls={"60+2"})
    markdown = render_markdown(summary)

    assert summary.focused_high_clock_normal_loss_contexts == [("Queen's Gambit Accepted | black | bullet | 60+2", 1)]
    assert "Focused High-Clock Normal Loss Contexts" in markdown
    assert "`1` x `Queen's Gambit Accepted | black | bullet | 60+2`" in markdown
    focused_section = markdown.split("## Focused High-Clock Normal Loss Contexts", maxsplit=1)[1].split(
        "## High-Clock Normal Loss Contexts",
    )[0]
    assert "300+2" not in focused_section


def test_render_markdown__shows_rating_negative_draws(tmp_path: Path) -> None:
    """Draw leak triage should prioritize draws that actually cost rating."""
    negative_headers = base_headers("1/2-1/2", "Sicilian Defense", "ilovecatgirl", "LowerBot")
    negative_headers["WhiteElo"] = "3020"
    negative_headers["BlackElo"] = "2950"
    negative_headers["WhiteRatingDiff"] = "-2"
    negative_headers["BlackRatingDiff"] = "+2"
    negative_headers["TimeControl"] = "60+1"
    write_pgn(tmp_path, "rating-negative-draw.pgn", negative_headers, "1. e4 c5 2. Nf3 d6 1/2-1/2")
    positive_headers = base_headers("1/2-1/2", "Queen's Pawn Game", "HigherBot", "ilovecatgirl")
    positive_headers["WhiteElo"] = "3038"
    positive_headers["BlackElo"] = "3029"
    positive_headers["WhiteRatingDiff"] = "-1"
    positive_headers["BlackRatingDiff"] = "+1"
    positive_headers["TimeControl"] = "90+1"
    write_pgn(tmp_path, "rating-positive-draw.pgn", positive_headers, "1. Nf3 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl", max_prefix_plies=4, focus_time_controls={"60+1", "90+1"})
    markdown = render_markdown(summary)

    assert summary.rating_negative_draw_contexts == [("e4 c5 Nf3 d6 | white | bullet | 60+1", 1)]
    assert summary.focused_rating_negative_draw_contexts == [("e4 c5 Nf3 d6 | white | bullet | 60+1", 1)]
    assert summary.rating_negative_draws[0].path.name == "rating-negative-draw.pgn"
    assert "Rating-Negative Draw Contexts" in markdown
    assert "`1` x `e4 c5 Nf3 d6 | white | bullet | 60+1`" in markdown
    assert "Largest Rating-Negative Draws" in markdown
    assert "rating-positive-draw.pgn" not in markdown


def test_render_markdown__clusters_rating_negative_draw_opponents(tmp_path: Path) -> None:
    """Rating-negative draw opponents should be visible as repeated matchmaking leaks."""
    for index in range(2):
        negative_headers = base_headers("1/2-1/2", "French Defense", "duchessAI", "ilovecatgirl")
        negative_headers["WhiteElo"] = str(2800 + index)
        negative_headers["BlackElo"] = "2940"
        negative_headers["WhiteRatingDiff"] = "+2"
        negative_headers["BlackRatingDiff"] = "-2"
        negative_headers["TimeControl"] = "60+1"
        write_pgn(tmp_path, f"duchess-negative-draw-{index}.pgn", negative_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    positive_headers = base_headers("1/2-1/2", "Queen's Pawn Game", "HigherBot", "ilovecatgirl")
    positive_headers["WhiteElo"] = "3038"
    positive_headers["BlackElo"] = "3029"
    positive_headers["WhiteRatingDiff"] = "-1"
    positive_headers["BlackRatingDiff"] = "+1"
    positive_headers["TimeControl"] = "90+1"
    write_pgn(tmp_path, "rating-positive-draw.pgn", positive_headers, "1. Nf3 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.rating_negative_draws_by_opponent[0] == ("duchessAI | bullet | 60+1", 2)
    assert "Rating-Negative Draw Opponents" in markdown
    assert "`2` x `duchessAI | bullet | 60+1`" in markdown
    opponent_section = markdown.split("## Rating-Negative Draw Opponents", maxsplit=1)[1].split(
        "## Rating-Negative Draw Terminations",
        maxsplit=1,
    )[0]
    assert "HigherBot | bullet | 90+1" not in opponent_section


def test_render_markdown__ranks_combined_opponent_leaks(tmp_path: Path) -> None:
    """Losses and costly lower-rated draws should combine into one opponent risk list."""
    loss_headers = base_headers("1-0", "Ruy Lopez: Open", "MEGA-NOOB-BOT", "ilovecatgirl")
    loss_headers["TimeControl"] = "90+1"
    loss_headers["WhiteRatingDiff"] = "+5"
    loss_headers["BlackRatingDiff"] = "-5"
    write_pgn(tmp_path, "mega-loss.pgn", loss_headers, "1. e4 e5 1-0")

    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "duchessAI", "ilovecatgirl")
        draw_headers["WhiteElo"] = str(2810 + index)
        draw_headers["BlackElo"] = "2940"
        draw_headers["WhiteRatingDiff"] = "+2"
        draw_headers["BlackRatingDiff"] = "-2"
        draw_headers["TimeControl"] = "60+1"
        write_pgn(tmp_path, f"duchess-negative-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")

    harmless_draw = base_headers("1/2-1/2", "Queen's Pawn Game", "HigherBot", "ilovecatgirl")
    harmless_draw["WhiteElo"] = "3040"
    harmless_draw["BlackElo"] = "3020"
    harmless_draw["WhiteRatingDiff"] = "-1"
    harmless_draw["BlackRatingDiff"] = "+1"
    harmless_draw["TimeControl"] = "60+1"
    write_pgn(tmp_path, "higher-rated-draw.pgn", harmless_draw, "1. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.opponent_leak_watchlist == [
        ("duchessAI | bullet | 60+1", 0, 2, 2, -4, 4, datetime(2026, 6, 8, 10, 0, tzinfo=UTC)),
        ("MEGA-NOOB-BOT | bullet | 90+1", 1, 0, 0, -5, 3, datetime(2026, 6, 8, 10, 0, tzinfo=UTC)),
    ]
    assert "Opponent Leak Watchlist" in markdown
    duchess_line = (
        "`duchessAI | bullet | 60+1`: risk `4`, losses `0`, lower-rated draws `2`, "
        "rating-negative draws `2`, rating `-4`, latest `2026-06-08T10:00:00+00:00`"
    )
    mega_line = (
        "`MEGA-NOOB-BOT | bullet | 90+1`: risk `3`, losses `1`, lower-rated draws `0`, "
        "rating-negative draws `0`, rating `-5`, latest `2026-06-08T10:00:00+00:00`"
    )
    assert duchess_line in markdown
    assert mega_line in markdown
    watchlist_section = markdown.split("## Opponent Leak Watchlist", maxsplit=1)[1].split(
        "## Loss Openings",
        maxsplit=1,
    )[0]
    assert "HigherBot" not in watchlist_section


def test_render_markdown__shows_focused_rating_impact_by_opening_context(tmp_path: Path) -> None:
    """Focused rating impact should keep active controls separate from abandoned historical controls."""
    current_headers = base_headers("1-0", "Queen's Gambit Accepted", "Cheszter", "ilovecatgirl")
    current_headers["TimeControl"] = "60+2"
    current_headers["WhiteRatingDiff"] = "+7"
    current_headers["BlackRatingDiff"] = "-7"
    write_pgn(tmp_path, "current-control-rating-loss.pgn", current_headers, "1. d4 d5 1-0")
    abandoned_headers = base_headers("1-0", "Caro-Kann Defense", "SlowBot", "ilovecatgirl")
    abandoned_headers["TimeControl"] = "300+2"
    abandoned_headers["WhiteRatingDiff"] = "+20"
    abandoned_headers["BlackRatingDiff"] = "-20"
    write_pgn(tmp_path, "abandoned-control-rating-loss.pgn", abandoned_headers, "1. e4 c6 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", focus_time_controls={"60+2"})
    markdown = render_markdown(summary)

    assert summary.focused_rating_impact_by_opening_context == [
        ("Queen's Gambit Accepted | black | bullet | 60+2", 1, -7),
    ]
    assert "Focused Rating Impact by Opening Context" in markdown
    assert "`Queen's Gambit Accepted | black | bullet | 60+2`: `-7` rating over `1` games" in markdown
    focused_section = markdown.split("## Focused Rating Impact by Opening Context", maxsplit=1)[1].split(
        "## Worst Scoring Controls",
    )[0]
    assert "300+2" not in focused_section


def test_render_markdown__shows_focused_score_by_opening_context(tmp_path: Path) -> None:
    """Focused score rates should rank active-control opening contexts by game result."""
    for index in range(2):
        loss_headers = base_headers("1-0", "Sicilian Defense: Modern Variations", f"ModernBot{index}", "ilovecatgirl")
        loss_headers["TimeControl"] = "60+2"
        write_pgn(tmp_path, f"modern-active-loss-{index}.pgn", loss_headers, "1. e4 c5 1-0")
    draw_headers = base_headers("1/2-1/2", "Sicilian Defense: Modern Variations", "DrawBot", "ilovecatgirl")
    draw_headers["TimeControl"] = "60+2"
    write_pgn(tmp_path, "modern-active-draw.pgn", draw_headers, "1. e4 c5 1/2-1/2")
    abandoned_headers = base_headers("1-0", "Caro-Kann Defense", "SlowBot", "ilovecatgirl")
    abandoned_headers["TimeControl"] = "300+2"
    write_pgn(tmp_path, "abandoned-control-loss.pgn", abandoned_headers, "1. e4 c6 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", focus_time_controls={"60+2"})
    markdown = render_markdown(summary)

    assert summary.focused_score_by_opening_context == [
        ("Sicilian Defense: Modern Variations | black | bullet | 60+2", 0, 1, 2, 3, 16.7),
    ]
    assert "Focused Score by Opening Context" in markdown
    assert (
        "`Sicilian Defense: Modern Variations | black | bullet | 60+2`: "
        "W-D-L `0-1-2`, score `16.7%` over `3` games"
    ) in markdown
    focused_section = markdown.split("## Focused Score by Opening Context", maxsplit=1)[1].split(
        "## Worst Scoring Controls",
    )[0]
    assert "300+2" not in focused_section


def test_render_markdown__shows_focused_opponent_impact(tmp_path: Path) -> None:
    """Repeated active-control losses to one bot should be visible before changing matchmaking."""
    for index in range(2):
        loss_headers = base_headers("1-0", "Ruy Lopez: Open", f"RepeatBot{index}", "ilovecatgirl")
        loss_headers["White"] = "MEGA-NOOB-BOT"
        loss_headers["TimeControl"] = "90+1"
        loss_headers["WhiteRatingDiff"] = "+5"
        loss_headers["BlackRatingDiff"] = "-5"
        write_pgn(tmp_path, f"repeat-opponent-loss-{index}.pgn", loss_headers, "1. e4 e5 1-0")
    win_headers = base_headers("0-1", "Caro-Kann Defense", "OtherBot", "ilovecatgirl")
    win_headers["TimeControl"] = "90+1"
    win_headers["WhiteRatingDiff"] = "-4"
    win_headers["BlackRatingDiff"] = "+4"
    write_pgn(tmp_path, "other-opponent-win.pgn", win_headers, "1. e4 c6 0-1")
    abandoned_headers = base_headers("1-0", "Semi-Slav Defense", "OldBot", "ilovecatgirl")
    abandoned_headers["TimeControl"] = "300+2"
    abandoned_headers["WhiteRatingDiff"] = "+20"
    abandoned_headers["BlackRatingDiff"] = "-20"
    write_pgn(tmp_path, "abandoned-opponent-loss.pgn", abandoned_headers, "1. d4 d5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", focus_time_controls={"90+1"})
    markdown = render_markdown(summary)

    assert summary.focused_rating_impact_by_opponent == [
        ("MEGA-NOOB-BOT | bullet | 90+1", 2, -10),
        ("OtherBot | bullet | 90+1", 1, 4),
    ]
    assert summary.focused_score_by_opponent == [
        ("MEGA-NOOB-BOT | bullet | 90+1", 0, 0, 2, 2, 0.0),
        ("OtherBot | bullet | 90+1", 1, 0, 0, 1, 100.0),
    ]
    assert "Focused Rating Impact by Opponent" in markdown
    assert "`MEGA-NOOB-BOT | bullet | 90+1`: `-10` rating over `2` games" in markdown
    assert "Focused Score by Opponent" in markdown
    assert "`MEGA-NOOB-BOT | bullet | 90+1`: W-D-L `0-0-2`, score `0.0%` over `2` games" in markdown
    focused_section = markdown.split("## Focused Rating Impact by Opponent", maxsplit=1)[1].split(
        "## Focused Score by Opponent",
    )[0]
    assert "300+2" not in focused_section


def test_render_markdown__shows_speed_filtered_opponent_impact(tmp_path: Path) -> None:
    """Blitz-only reports should rank opponent leaks without requiring exact-control focus."""
    for index in range(2):
        loss_headers = base_headers("1-0", "Najdorf English Attack", f"LeakBot{index}", "ilovecatgirl")
        loss_headers["White"] = "TakticproChess"
        loss_headers["TimeControl"] = "180+2"
        loss_headers["WhiteRatingDiff"] = "+6"
        loss_headers["BlackRatingDiff"] = "-6"
        write_pgn(tmp_path, f"blitz-opponent-loss-{index}.pgn", loss_headers, "1. e4 c5 1-0")
    draw_headers = base_headers("1/2-1/2", "London System", "CloudNetBot", "ilovecatgirl")
    draw_headers["TimeControl"] = "180+2"
    draw_headers["WhiteRatingDiff"] = "-1"
    draw_headers["BlackRatingDiff"] = "+1"
    write_pgn(tmp_path, "blitz-opponent-draw.pgn", draw_headers, "1. d4 d5 1/2-1/2")
    bullet_headers = base_headers("1-0", "Old Bullet Leak", "BulletBot", "ilovecatgirl")
    bullet_headers["TimeControl"] = "60+1"
    bullet_headers["WhiteRatingDiff"] = "+20"
    bullet_headers["BlackRatingDiff"] = "-20"
    write_pgn(tmp_path, "bullet-opponent-loss.pgn", bullet_headers, "1. e4 c5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", speeds={"blitz"})
    markdown = render_markdown(summary)

    assert summary.rating_impact_by_opponent == [
        ("TakticproChess | blitz | 180+2", 2, -12),
        ("CloudNetBot | blitz | 180+2", 1, 1),
    ]
    assert summary.score_by_opponent == [
        ("TakticproChess | blitz | 180+2", 0, 0, 2, 2, 0.0),
        ("CloudNetBot | blitz | 180+2", 0, 1, 0, 1, 50.0),
    ]
    assert "Rating Impact by Opponent" in markdown
    assert "`TakticproChess | blitz | 180+2`: `-12` rating over `2` games" in markdown
    assert "Score by Opponent" in markdown
    assert "`TakticproChess | blitz | 180+2`: W-D-L `0-0-2`, score `0.0%` over `2` games" in markdown
    opponent_section = markdown.split("## Rating Impact by Opponent", maxsplit=1)[1].split(
        "## Score by Opponent",
    )[0]
    assert "BulletBot" not in opponent_section


def test_render_markdown__shows_focused_time_control_score_and_rating(tmp_path: Path) -> None:
    """Active-control tuning should compare exact controls directly before changing weights."""
    loss_headers = base_headers("1-0", "Ruy Lopez: Open", "LossBot", "ilovecatgirl")
    loss_headers["TimeControl"] = "90+1"
    loss_headers["WhiteRatingDiff"] = "+5"
    loss_headers["BlackRatingDiff"] = "-5"
    write_pgn(tmp_path, "ninety-loss.pgn", loss_headers, "1. e4 e5 1-0")
    draw_headers = base_headers("1/2-1/2", "Queen's Pawn Game", "DrawBot", "ilovecatgirl")
    draw_headers["TimeControl"] = "90+1"
    draw_headers["WhiteRatingDiff"] = "-1"
    draw_headers["BlackRatingDiff"] = "+1"
    write_pgn(tmp_path, "ninety-draw.pgn", draw_headers, "1. d4 d5 1/2-1/2")
    win_headers = base_headers("0-1", "Caro-Kann Defense", "WinBot", "ilovecatgirl")
    win_headers["TimeControl"] = "120+1"
    win_headers["WhiteRatingDiff"] = "-4"
    win_headers["BlackRatingDiff"] = "+4"
    write_pgn(tmp_path, "one-twenty-win.pgn", win_headers, "1. e4 c6 0-1")
    abandoned_headers = base_headers("1-0", "Semi-Slav Defense", "OldBot", "ilovecatgirl")
    abandoned_headers["TimeControl"] = "300+2"
    abandoned_headers["WhiteRatingDiff"] = "+20"
    abandoned_headers["BlackRatingDiff"] = "-20"
    write_pgn(tmp_path, "abandoned-loss.pgn", abandoned_headers, "1. d4 d5 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", focus_time_controls={"90+1", "120+1"})
    markdown = render_markdown(summary)

    assert summary.focused_rating_impact_by_time_control == [("90+1", 2, -4), ("120+1", 1, 4)]
    assert summary.focused_score_by_time_control == [("90+1", 0, 1, 1, 2, 25.0), ("120+1", 1, 0, 0, 1, 100.0)]
    assert "Focused Rating Impact by Time Control" in markdown
    assert "`90+1`: `-4` rating over `2` games" in markdown
    assert "Focused Score by Time Control" in markdown
    assert "`90+1`: W-D-L `0-1-1`, score `25.0%` over `2` games" in markdown
    focused_section = markdown.split("## Focused Rating Impact by Time Control", maxsplit=1)[1].split(
        "## Focused Rating Impact by Opening Context",
    )[0]
    assert "300+2" not in focused_section


def test_render_markdown__shows_worst_scoring_controls(tmp_path: Path) -> None:
    """Score rate by exact clock and color should expose weak pools, not only raw counts."""
    loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "ClockBot")
    loss_headers["TimeControl"] = "180+0"
    write_pgn(tmp_path, "white-180-zero-loss.pgn", loss_headers, "1. d4 Nf6 0-1")
    draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", "DrawBot")
    draw_headers["TimeControl"] = "180+0"
    write_pgn(tmp_path, "white-180-zero-draw.pgn", draw_headers, "1. e4 e6 1/2-1/2")
    win_headers = base_headers("1-0", "Caro-Kann Defense", "ilovecatgirl", "WinBot")
    win_headers["TimeControl"] = "60+1"
    write_pgn(tmp_path, "white-60-one-win.pgn", win_headers, "1. e4 c6 1-0")

    summary = summarize_records(tmp_path, "ilovecatgirl", control_min_games=1)
    markdown = render_markdown(summary)

    assert summary.worst_scoring_controls[0] == ("180+0 white", 0, 1, 1, 2, 25.0)
    assert "Worst Scoring Controls" in markdown
    assert "`180+0 white`: W-D-L `0-1-1`, score `25.0%` over `2` games" in markdown


def test_render_markdown__clusters_loss_prefix_context(tmp_path: Path) -> None:
    """Opening-prefix risks should show color, speed, and termination context."""
    for index in range(2):
        loss_headers = base_headers("1-0", "Sicilian Defense: Najdorf Variation", f"NajdorfBot{index}", "ilovecatgirl")
        loss_headers["TimeControl"] = "60+1"
        loss_headers["Termination"] = "Normal"
        write_pgn(
            tmp_path,
            f"black-bullet-najdorf-loss-{index}.pgn",
            loss_headers,
            "1. e4 c5 2. Nf3 d6 1-0",
        )
    time_loss_headers = base_headers("0-1", "Nimzo-Indian Defense", "ilovecatgirl", "ClockBot")
    time_loss_headers["TimeControl"] = "180+0"
    time_loss_headers["Termination"] = "Time forfeit"
    write_pgn(tmp_path, "white-blitz-time-loss.pgn", time_loss_headers, "1. d4 Nf6 0-1")

    summary = summarize_records(tmp_path, "ilovecatgirl", max_prefix_plies=4)
    markdown = render_markdown(summary)

    assert summary.loss_prefix_contexts[0] == ("e4 c5 Nf3 d6 | black | bullet | Normal", 2)
    assert "Loss Prefix Contexts" in markdown
    assert "`2` x `e4 c5 Nf3 d6 | black | bullet | Normal`" in markdown


def test_render_markdown__shows_lower_rated_draw_count(tmp_path: Path) -> None:
    """The report should expose the total lower-rated draw count, not only the top examples."""
    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", f"LowerBot{index}")
        draw_headers["WhiteElo"] = "2940"
        draw_headers["BlackElo"] = str(2939 - index)
        write_pgn(tmp_path, f"lower-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")

    markdown = render_markdown(summarize_records(tmp_path, "ilovecatgirl"))

    assert "Lower-rated draws found: `2`" in markdown


def test_render_markdown__clusters_lower_rated_draw_opponents(tmp_path: Path) -> None:
    """Repeated lower-rated draw opponents should be visible as matchmaking evidence."""
    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "duchessAI", "ilovecatgirl")
        draw_headers["WhiteElo"] = str(2800 + index)
        draw_headers["BlackElo"] = "2940"
        draw_headers["TimeControl"] = "60+1"
        write_pgn(tmp_path, f"duchess-lower-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    singleton_headers = base_headers("1/2-1/2", "Caro-Kann Defense", "ilovecatgirl", "OneOffBot")
    singleton_headers["WhiteElo"] = "2940"
    singleton_headers["BlackElo"] = "2860"
    singleton_headers["TimeControl"] = "90+1"
    write_pgn(tmp_path, "one-off-lower-draw.pgn", singleton_headers, "1. e4 c6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.lower_rated_draws_by_opponent[0] == ("duchessAI | bullet | 60+1", 2)
    assert "Lower-Rated Draw Opponents" in markdown
    assert "`2` x `duchessAI | bullet | 60+1`" in markdown


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


def test_render_markdown__clusters_lower_rated_draw_contexts(tmp_path: Path) -> None:
    """Lower-rated draw leaks should expose color, speed, and exact clock context."""
    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", f"LowerBot{index}")
        draw_headers["WhiteElo"] = "2940"
        draw_headers["BlackElo"] = str(2939 - index)
        draw_headers["TimeControl"] = "60+1"
        write_pgn(tmp_path, f"white-bullet-lower-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    black_draw_headers = base_headers("1/2-1/2", "Caro-Kann Defense", "LowerCaroBot", "ilovecatgirl")
    black_draw_headers["WhiteElo"] = "2930"
    black_draw_headers["BlackElo"] = "2940"
    black_draw_headers["TimeControl"] = "180+2"
    write_pgn(tmp_path, "black-blitz-lower-draw.pgn", black_draw_headers, "1. e4 c6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl", max_prefix_plies=4)
    markdown = render_markdown(summary)

    assert summary.lower_rated_draw_contexts[0] == ("e4 e6 d4 d5 | white | bullet | 60+1", 2)
    assert "Lower-Rated Draw Contexts" in markdown
    assert "`2` x `e4 e6 d4 d5 | white | bullet | 60+1`" in markdown


def test_render_markdown__clusters_lower_rated_draw_terminations(tmp_path: Path) -> None:
    """Lower-rated draw leaks should show whether they came from agreement or clock-adjacent outcomes."""
    for index in range(2):
        draw_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", f"LowerBot{index}")
        draw_headers["WhiteElo"] = "2940"
        draw_headers["BlackElo"] = str(2939 - index)
        draw_headers["Termination"] = "Normal"
        write_pgn(tmp_path, f"normal-lower-draw-{index}.pgn", draw_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    clock_draw_headers = base_headers("1/2-1/2", "Caro-Kann Defense", "ilovecatgirl", "ClockLowerBot")
    clock_draw_headers["WhiteElo"] = "2940"
    clock_draw_headers["BlackElo"] = "2800"
    clock_draw_headers["Termination"] = "Time forfeit"
    write_pgn(tmp_path, "clock-lower-draw.pgn", clock_draw_headers, "1. e4 c6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.lower_rated_draws_by_termination == [("Normal", 2), ("Time forfeit", 1)]
    assert "Lower-Rated Draw Terminations" in markdown
    assert "`2` x Normal" in markdown


def test_render_markdown__shows_focused_lower_rated_draw_contexts(tmp_path: Path) -> None:
    """Focused lower-rated draws should expose active-control draw leaks."""
    current_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", "LowerBot")
    current_headers["WhiteElo"] = "2940"
    current_headers["BlackElo"] = "2800"
    current_headers["TimeControl"] = "60+1"
    write_pgn(tmp_path, "current-lower-draw.pgn", current_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    abandoned_headers = base_headers("1/2-1/2", "Caro-Kann Defense", "ilovecatgirl", "OldLowerBot")
    abandoned_headers["WhiteElo"] = "2940"
    abandoned_headers["BlackElo"] = "2700"
    abandoned_headers["TimeControl"] = "300+2"
    write_pgn(tmp_path, "abandoned-lower-draw.pgn", abandoned_headers, "1. e4 c6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl", max_prefix_plies=4, focus_time_controls={"60+1"})
    markdown = render_markdown(summary)

    assert summary.focused_lower_rated_draw_contexts == [("e4 e6 d4 d5 | white | bullet | 60+1", 1)]
    assert "Focused Lower-Rated Draw Contexts" in markdown
    assert "`1` x `e4 e6 d4 d5 | white | bullet | 60+1`" in markdown
    focused_section = markdown.split("## Focused Lower-Rated Draw Contexts", maxsplit=1)[1].split(
        "## Lower-Rated Draw Contexts",
    )[0]
    assert "300+2" not in focused_section


def test_render_markdown__clusters_rating_negative_draw_terminations(tmp_path: Path) -> None:
    """Rating-negative draws should show the terminal cause separately from opening context."""
    normal_headers = base_headers("1/2-1/2", "French Defense", "ilovecatgirl", "LowerBot")
    normal_headers["WhiteRatingDiff"] = "-4"
    normal_headers["Termination"] = "Normal"
    write_pgn(tmp_path, "normal-negative-draw.pgn", normal_headers, "1. e4 e6 2. d4 d5 1/2-1/2")
    time_headers = base_headers("1/2-1/2", "Caro-Kann Defense", "ilovecatgirl", "ClockBot")
    time_headers["WhiteRatingDiff"] = "-2"
    time_headers["Termination"] = "Time forfeit"
    write_pgn(tmp_path, "time-negative-draw.pgn", time_headers, "1. e4 c6 2. d4 d5 1/2-1/2")

    summary = summarize_records(tmp_path, "ilovecatgirl")
    markdown = render_markdown(summary)

    assert summary.rating_negative_draws_by_termination == [("Normal", 1), ("Time forfeit", 1)]
    assert "Rating-Negative Draw Terminations" in markdown
    assert "`1` x Time forfeit" in markdown
