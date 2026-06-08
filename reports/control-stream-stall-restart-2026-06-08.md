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
