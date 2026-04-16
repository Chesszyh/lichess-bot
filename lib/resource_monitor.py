"""Record and summarize lichess-bot process-tree resource usage."""
from __future__ import annotations

import csv
import datetime
import multiprocessing
import os
from pathlib import Path
import subprocess
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from lib.config import Configuration


CSV_FIELDS = [
    "timestamp",
    "root_pid",
    "pid_count",
    "pids",
    "active_game_ids",
    "cpu_percent",
    "rss_bytes",
    "interval_seconds",
]


SUMMARY_FIELDS = [
    "group",
    "sample_count",
    "started_at",
    "ended_at",
    "active_seconds",
    "cpu_seconds",
    "avg_cpu_percent",
    "avg_rss_mb",
    "peak_rss_mb",
]


@dataclass(frozen=True)
class ProcessStats:
    """Resource usage for one process."""

    pid: int
    ppid: int
    cpu_percent: float
    rss_bytes: int
    command: str


@dataclass(frozen=True)
class ResourceSample:
    """One sampled process-tree resource usage row."""

    timestamp: datetime.datetime
    root_pid: int
    pid_count: int
    pids: tuple[int, ...]
    active_game_ids: tuple[str, ...]
    cpu_percent: float
    rss_bytes: int
    interval_seconds: float


def parse_ps_output(output: str) -> dict[int, ProcessStats]:
    """Parse `ps -axo pid=,ppid=,pcpu=,rss=,comm=` output."""
    processes: dict[int, ProcessStats] = {}
    for line in output.splitlines():
        parts = line.strip().split(None, 4)
        if len(parts) < 4:
            continue
        pid, ppid, cpu_percent, rss_kb = parts[:4]
        command = parts[4] if len(parts) > 4 else ""
        try:
            process = ProcessStats(int(pid), int(ppid), float(cpu_percent), int(rss_kb) * 1024, command)
        except ValueError:
            continue
        processes[process.pid] = process
    return processes


def process_tree(processes: dict[int, ProcessStats], root_pid: int,
                 exclude_pids: Iterable[int] = ()) -> list[ProcessStats]:
    """Return root_pid and all known descendants, excluding explicit pids."""
    excluded = set(exclude_pids)
    by_parent: dict[int, list[ProcessStats]] = defaultdict(list)
    for process in processes.values():
        by_parent[process.ppid].append(process)

    selected: list[ProcessStats] = []
    stack = [root_pid]
    while stack:
        pid = stack.pop()
        if pid in excluded:
            continue
        process = processes.get(pid)
        if process:
            selected.append(process)
        stack.extend(child.pid for child in by_parent.get(pid, []))
    return selected


def sample_process_tree(root_pid: int, active_game_ids: Sequence[str], interval_seconds: float,
                        exclude_pids: Iterable[int] = (), ps_output: str | None = None) -> ResourceSample:
    """Sample CPU and RSS for root_pid and descendants."""
    if ps_output is None:
        ps_output = subprocess.check_output(["ps", "-axo", "pid=,ppid=,pcpu=,rss=,comm="], text=True)
    processes = process_tree(parse_ps_output(ps_output), root_pid, exclude_pids)
    return ResourceSample(timestamp=datetime.datetime.now(datetime.UTC),
                          root_pid=root_pid,
                          pid_count=len(processes),
                          pids=tuple(sorted(process.pid for process in processes)),
                          active_game_ids=tuple(sorted(filter(None, active_game_ids))),
                          cpu_percent=sum(process.cpu_percent for process in processes),
                          rss_bytes=sum(process.rss_bytes for process in processes),
                          interval_seconds=interval_seconds)


def append_sample(path: Path, sample: ResourceSample) -> None:
    """Append one resource sample to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": sample.timestamp.isoformat(),
            "root_pid": sample.root_pid,
            "pid_count": sample.pid_count,
            "pids": ";".join(str(pid) for pid in sample.pids),
            "active_game_ids": ";".join(sample.active_game_ids),
            "cpu_percent": f"{sample.cpu_percent:.3f}",
            "rss_bytes": sample.rss_bytes,
            "interval_seconds": f"{sample.interval_seconds:.3f}",
        })


def monitor_resource_usage(root_pid: int, active_game_ids: Sequence[str], resource_cfg: Configuration) -> None:
    """Continuously sample lichess-bot process-tree resource usage."""
    sample_period = float(resource_cfg.sample_period)
    output_path = Path(resource_cfg.directory) / "resource_usage.csv"
    monitor_pid = os.getpid()
    while True:
        sample = sample_process_tree(root_pid, list(active_game_ids), sample_period, exclude_pids={monitor_pid})
        append_sample(output_path, sample)
        time.sleep(sample_period)


def start_resource_monitor(root_pid: int, active_game_ids: Sequence[str],
                           resource_cfg: Configuration) -> multiprocessing.Process | None:
    """Start resource monitor process when enabled."""
    if not resource_cfg or not resource_cfg.enabled:
        return None
    process = multiprocessing.Process(target=monitor_resource_usage, args=(root_pid, active_game_ids, resource_cfg))
    process.start()
    return process


def parse_sample_row(row: dict[str, str]) -> ResourceSample:
    """Parse one CSV row into a ResourceSample."""
    active_game_ids = tuple(filter(None, row.get("active_game_ids", "").split(";")))
    pids = tuple(int(pid) for pid in filter(None, row.get("pids", "").split(";")))
    return ResourceSample(timestamp=datetime.datetime.fromisoformat(row["timestamp"]),
                          root_pid=int(row["root_pid"]),
                          pid_count=int(row["pid_count"]),
                          pids=pids,
                          active_game_ids=active_game_ids,
                          cpu_percent=float(row["cpu_percent"]),
                          rss_bytes=int(row["rss_bytes"]),
                          interval_seconds=float(row["interval_seconds"]))


def iter_resource_csv_paths(input_path: Path) -> list[Path]:
    """Return resource CSV files from a file or directory path."""
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.glob("*.csv"))


def read_resource_samples(input_path: Path) -> list[ResourceSample]:
    """Read resource samples from a CSV file or a directory of CSV files."""
    samples: list[ResourceSample] = []
    for path in iter_resource_csv_paths(input_path):
        with path.open(newline="", encoding="utf-8") as file:
            samples.extend(parse_sample_row(row) for row in csv.DictReader(file))
    return samples


def summary_keys(sample: ResourceSample, group_by: str) -> tuple[str, ...]:
    """Return grouping keys for one sample."""
    if group_by == "game":
        return sample.active_game_ids or ("idle",)
    if group_by == "day":
        return (sample.timestamp.date().isoformat(),)
    if group_by == "week":
        year, week, _ = sample.timestamp.isocalendar()
        return (f"{year}-W{week:02d}",)
    raise ValueError(f"Unsupported group: {group_by}")


def summarize_resource_samples(samples: Sequence[ResourceSample], group_by: str) -> list[dict[str, Any]]:
    """Summarize resource samples by game, day, or week."""
    groups: dict[str, list[ResourceSample]] = defaultdict(list)
    for sample in samples:
        for key in summary_keys(sample, group_by):
            groups[key].append(sample)

    summaries: list[dict[str, Any]] = []
    for key, group_samples in sorted(groups.items()):
        total_interval = sum(sample.interval_seconds for sample in group_samples)
        weighted_cpu = sum(sample.cpu_percent * sample.interval_seconds for sample in group_samples)
        weighted_rss = sum(sample.rss_bytes * sample.interval_seconds for sample in group_samples)
        cpu_seconds = sum(sample.cpu_percent / 100 * sample.interval_seconds for sample in group_samples)
        avg_cpu = weighted_cpu / total_interval if total_interval else 0
        avg_rss = weighted_rss / total_interval if total_interval else 0
        summaries.append({
            "group": key,
            "sample_count": len(group_samples),
            "started_at": min(sample.timestamp for sample in group_samples).isoformat(),
            "ended_at": max(sample.timestamp for sample in group_samples).isoformat(),
            "active_seconds": round(total_interval, 3),
            "cpu_seconds": round(cpu_seconds, 3),
            "avg_cpu_percent": round(avg_cpu, 3),
            "avg_rss_mb": round(avg_rss / 1024 / 1024, 3),
            "peak_rss_mb": round(max(sample.rss_bytes for sample in group_samples) / 1024 / 1024, 3),
        })
    return summaries


def write_summary_csv(rows: Sequence[dict[str, Any]], output_path: Path | None) -> None:
    """Write summary rows to a CSV file or stdout."""
    import sys

    file = output_path.open("w", newline="", encoding="utf-8") if output_path else sys.stdout
    try:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if output_path:
            file.close()
