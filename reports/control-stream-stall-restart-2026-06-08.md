# Control Stream Stall Restart for 2026-06-08

Bot: `ilovecatgirl`

## Scope

- Runtime issue found while continuing bullet/blitz optimization.
- No local engine experiment was run.
- No restart was attempted until `/api/account/playing` returned `0` ongoing games.

## Evidence

The bot process existed under launchd, but the normal bot log stopped advancing:

- launchd service: `org.chesszyh987.lichess-bot`
- stale process PID before restart: `72664`
- `run.log` stopped at `2026-06-08 23:44:12 CST`
- the next outgoing challenge had been scheduled for `2026-06-08 23:47:48 CST`
- no challenge attempt happened from the stale process before intervention

Process inspection showed an unhealthy idle state:

- launchd still reported the service as `state = running`
- `lsof -p 72664` showed only `/dev/null` for stdio and no open `run.log`
- the main process had a Lichess HTTPS socket in `CLOSE_WAIT`
- child Python workers remained alive under the main process
- a short macOS `sample` showed the main thread blocked in `os_read`

This matched a stalled control-stream/process state rather than normal quiet waiting.

## Safety Check

Before restarting:

- `/api/account/playing` returned HTTP `200`
- `ongoing_games 0`
- no PGN newer than `game_records/ilovecatgirl vs abdcebot - Zd5yy2Mj.pgn` was present

## Action

The launchd service was restarted with:

```bash
launchctl kickstart -k gui/$(id -u)/org.chesszyh987.lichess-bot
```

The command was run only after the no-active-game check above.

## Recovery Verification

After restart:

- new PID: `89275`
- launchd `runs = 38`
- startup logged `Engine configuration OK`
- startup logged `Welcome ilovecatgirl!`
- startup logged `awaiting challenges`
- the persisted challenge cadence was preserved:
  - next challenge remained `2026-06-08 23:47:48 CST`
- the bot challenged `RecklessEngine` at `23:47:48 CST`
- challenge id: `B0IiP6yC`
- Lichess accepted the challenge creation request with HTTP `200`
- the unanswered challenge was cancelled cleanly at `23:48:16 CST`
- `RecklessEngine` was cooled down for 12 hours after not answering
- next challenge was scheduled for `2026-06-09 00:03:15 CST`
- `/api/account/playing` still returned `ongoing_games 0` after recovery

## Optimization Impact

This did not directly change chess strength, but it restored the bot's ability to collect useful rated bot-vs-bot bullet samples. Without the restart, the bot would have remained below target while also failing to generate new evidence.

## Follow-Up Direction

Add lightweight runtime stall detection before future manual intervention:

1. Track the age of the latest `watchdog_tick` or bot log write.
2. Treat a stale log plus a `CLOSE_WAIT` control socket as a restart candidate.
3. Require `/api/account/playing == 0` before any automatic or manual restart.
4. Record the stale PID, last log timestamp, and next scheduled challenge time in a report before restarting.

This should stay conservative: no restart during an active game, and no restart merely because a challenge was unanswered or the bot is waiting normally.

## Code Follow-Up

After the manual recovery, the main loop was hardened so it no longer relies only on the helper watchdog process to wake stale-stream checks:

- `next_event()` now waits on the control queue with `CONTROL_STREAM_WATCHDOG_PERIOD` as a timeout.
- If no event arrives before that timeout, it returns a synthetic `watchdog_tick`.
- This lets the main loop call `ensure_control_stream_live()` even if the control-stream worker is quiet and the helper tick process fails to wake it.
- The fix preserves the existing challenge cadence; it only changes how the idle main loop wakes up.

Verification:

- RED: `test_next_event__wakes_main_loop_when_control_queue_is_quiet` failed because `next_event()` called `get()` without a timeout and propagated `queue.Empty`.
- GREEN: `pytest test_bot/test_control_stream.py::test_next_event__wakes_main_loop_when_control_queue_is_quiet -q` passed.
- RED: the first deployment attempt exposed that synthetic wakeups were not real queue items; calling `task_done()` on them caused `ValueError: task_done() called too many times`.
- GREEN: `test_complete_control_queue_task__skips_synthetic_wakeup` passed after routing queue completion through `complete_control_queue_task()`.
- `pytest test_bot/test_control_stream.py test_bot/test_main_loop.py -q`: `12 passed`.
- `ruff check --config test_bot/ruff.toml lib/lichess_bot.py lib/lichess_types.py test_bot/test_control_stream.py --select E,F`: passed.
- `git diff --check -- lib/lichess_bot.py test_bot/test_control_stream.py`: passed.

The broader strict type and full lint commands still report pre-existing unrelated issues in `lib/resource_monitor.py`, `lib/engine_wrapper.py`, `homemade.py`, and older test helper annotations. Those were not changed as part of this targeted runtime-stall fix.

Deployment notes:

- `/api/account/playing` returned `ongoing_games 0` before the restart that loaded the first fix.
- The first restart preserved challenge cadence but exited with `ValueError: task_done() called too many times` on a synthetic wakeup.
- The follow-up fix was written at `23:54:20 CST`; launchd started PID `26159` at `23:54:25 CST`, so the running process loaded the corrected code.
- The corrected process continued logging watchdog ticks through at least `23:55:22 CST` without another `task_done` crash.
- The next outgoing challenge remained scheduled for `2026-06-09 00:03:15 CST`.
