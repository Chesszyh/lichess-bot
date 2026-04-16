"""Tests for resource monitoring and export helpers."""

import datetime

from lib.resource_monitor import (ResourceSample, parse_ps_output, process_tree, summarize_resource_samples)


def test_process_tree__selects_root_and_descendants() -> None:
    """Process tree filtering should include descendants and skip unrelated processes."""
    ps_output = """
      10     1   1.5  1000 python
      11    10   2.0  2000 stockfish
      12    11   3.0  3000 helper
      20     1  10.0  9000 unrelated
    """

    processes = parse_ps_output(ps_output)
    selected = process_tree(processes, 10)

    assert [process.pid for process in selected] == [10, 11, 12]
    assert sum(process.cpu_percent for process in selected) == 6.5
    assert sum(process.rss_bytes for process in selected) == 6000 * 1024


def test_summarize_resource_samples__groups_by_game_day_and_week() -> None:
    """Resource samples should summarize CPU seconds and memory by requested grouping."""
    samples = [
        ResourceSample(datetime.datetime(2026, 4, 17, 1, tzinfo=datetime.UTC),
                       100,
                       2,
                       (100, 101),
                       ("gameA",),
                       50,
                       100 * 1024 * 1024,
                       5),
        ResourceSample(datetime.datetime(2026, 4, 17, 1, 0, 5, tzinfo=datetime.UTC),
                       100,
                       2,
                       (100, 101),
                       ("gameA",),
                       100,
                       200 * 1024 * 1024,
                       5),
        ResourceSample(datetime.datetime(2026, 4, 18, 1, tzinfo=datetime.UTC),
                       100,
                       1,
                       (100,),
                       (),
                       20,
                       50 * 1024 * 1024,
                       10),
    ]

    by_game = summarize_resource_samples(samples, "game")
    by_day = summarize_resource_samples(samples, "day")
    by_week = summarize_resource_samples(samples, "week")

    assert by_game[0]["group"] == "gameA"
    assert by_game[0]["cpu_seconds"] == 7.5
    assert by_game[0]["avg_cpu_percent"] == 75
    assert by_game[0]["avg_rss_mb"] == 150
    assert by_game[1]["group"] == "idle"
    assert [row["group"] for row in by_day] == ["2026-04-17", "2026-04-18"]
    assert by_week[0]["group"] == "2026-W16"
