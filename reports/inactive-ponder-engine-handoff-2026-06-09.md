# Inactive Ponder Engine Handoff

生成时间: 2026-06-09T01:48:22+08:00

## Problem Description

- Bullet/blitz runtime logs showed lc0 continuing to search after the position had handed off to the secondary Stockfish endgame engine.
- The overlap wastes CPU/GPU budget during the most time-sensitive phase and can reduce effective search quality.
- No local engine experiment was run; the change is based on live bot logs plus a focused regression test.

## Environment and Scope

- Repository: `/Users/chesszyh987/Develop/lichess-bot`
- Branch: `lc0+stockfish`
- Primary engine: `lc0/build/release/lc0`
- Endgame engine: `Stockfish/src/stockfish`
- Runtime evidence: `lichess_bot_auto_logs/lichess-bot.log`
- Game evidence: `game_records/ilovecatgirl vs CupchessBot - C0SjBNos.pgn`

## Symptoms and Reproduction

- Game `C0SjBNos` was a rated `90+1` bullet game against `CupchessBot`.
- The main engine PID was `93171`.
- The secondary endgame engine PID was `93172`.
- At move `20`, the wrapper selected the endgame engine and issued Stockfish `go`.
- PID `93171` continued emitting lc0 `info` lines while PID `93172` was actively searching.

Representative log sequence:

```text
2026-06-09 01:39:04,380 ... INFO move: 20
2026-06-09 01:39:04,382 ... <UciProtocol (pid=93172)>: << setoption name Ponder value true
2026-06-09 01:39:04,676 ... <UciProtocol (pid=93172)>: << go wtime 12000 btime 98510 ...
2026-06-09 01:39:08,902 ... <UciProtocol (pid=93171)>: >> info depth 10 ...
2026-06-09 01:39:09,506 ... <UciProtocol (pid=93172)>: >> info depth 19 ...
2026-06-09 01:39:13,765 ... <UciProtocol (pid=93171)>: >> info depth 11 ...
2026-06-09 01:39:14,096 ... <UciProtocol (pid=93172)>: >> info depth 23 ...
```

## Investigation Timeline

- Confirmed from `C0SjBNos` logs that the endgame handoff happened at move `20`.
- Confirmed PID `93172` was Stockfish and began the active search.
- Confirmed PID `93171` continued lc0 search output during that Stockfish search window.
- Inspected python-chess `SimpleEngine.ping()` and `Protocol.communicate()`.
- Confirmed `ping()` schedules a new command through `communicate()`, and `communicate()` cancels the previous command.
- Confirmed UCI play command cancellation sends `stop` unless same-engine `ponderhit` is possible.

## Root Cause

`EngineWrapper.search()` selected the active engine for the current position, but it did not track which engine was left pondering after the previous move. When `engine_for_position()` switched from the main lc0 engine to the Stockfish endgame engine, the old lc0 ponder command remained alive because no command was issued to that inactive engine.

This is not a same-engine ponderhit problem. Python-chess already handles same-engine follow-up searches through `communicate()` and can convert an expected continuation into `ponderhit`. The missing case was cross-engine cleanup.

## Changes Made

- Added `EngineWrapper.pondering_engine` to remember which engine was left in ponder mode.
- Added `EngineWrapper.stop_inactive_ponder(active_engine)` to call `ping()` only when the previous pondering engine is a different object from the next active engine.
- Called inactive-ponder cleanup before starting the next active engine search.
- Updated tracking after each search:
  - set `pondering_engine` when `ponder=True` and the result contains a ponder move
  - clear it when the current active engine no longer remains in ponder mode
- Added regression coverage using a fake engine that records `ping()` cleanup.

## Verification

- RED evidence from the first regression run: `test_search__stops_main_engine_ponder_before_endgame_engine_handoff` failed with `main_engine.pings == 0`.
- GREEN focused test run:

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py -q && git diff --check'
```

Result:

```text
34 passed, 4 warnings in 0.12s
```

- Additional lint command run on changed files:

```bash
rtk sh -c '. .venv/bin/activate && ruff check --config test_bot/ruff.toml lib/engine_wrapper.py test_bot/test_engine_time_management.py'
```

Result: failed with existing unrelated lint debt in `lib/engine_wrapper.py` complexity checks and older fake-test helper docstring/unused-argument findings. The new fake helper was adjusted so it does not add its own docstring/unused-argument findings.

## Problems Encountered During Debugging

- A direct `mypy --strict lib/engine_wrapper.py test_bot/test_engine_time_management.py` check is not a clean gate for this WIP because the selected modules already have broader strict typing debt unrelated to inactive ponder cleanup.
- A full-file `ruff check` is also not clean because the file already violates complexity and historical test-helper rules.
- The focused behavioral gate is therefore the relevant regression test plus whitespace validation, with broader debt recorded rather than hidden.

## Reuse Notes and Lessons

- Any future multi-engine handoff should explicitly clean up engine-local background state.
- Same-engine follow-up searches should continue to rely on python-chess for `ponderhit`; manual `ping()` before same-engine play would harm that path.
- If future logs show two engine PIDs emitting `info` during a single active search window, first check whether the previous engine had been left pondering.

## Appendix: Reusable Commands

Find handoff evidence:

```bash
rtk sed -n '23230,23340p' lichess_bot_auto_logs/lichess-bot.log
```

Run focused verification:

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py -q && git diff --check'
```

Inspect python-chess cancellation behavior:

```bash
rtk sh -c '. .venv/bin/activate && python - <<'"'"'PY'"'"'
import inspect
import chess.engine
print(inspect.getsource(chess.engine.SimpleEngine.ping))
print(inspect.getsource(chess.engine.Protocol.communicate))
print(inspect.getsource(chess.engine.UciProtocol.play))
PY'
```
