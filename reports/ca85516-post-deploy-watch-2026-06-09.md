# ca85516 Post-Deploy Watch

## Scope

- Time checked: `2026-06-09 00:33 CST`
- Branch: `lc0+stockfish`
- Running bot PID: `45831`
- Deployed commits in this process: `ca85516`, `baffddc`
- Local engine experiments: none

## Runtime State

- `/api/account/playing`: `200`, `ongoing_games = 0`
- Bot process was running and idle.
- Latest log mtime was current at the time of inspection.
- Matchmaking had scheduled the next outgoing challenge after `Tue Jun 9 00:41:28 2026`.

## Evidence Reviewed

- `lichess_bot_auto_logs/run.log`
- `reports/bot-game-analysis-active-controls-2026-06-08.md`
- `reports/bot-game-analysis-active-controls-since-2026-06-09-0020.md`
- Latest saved active-control PGN: `game_records/CupchessBot vs ilovecatgirl - WE3E4UDG.pgn`

## Findings

- No active game was interrupted or restarted.
- No new completed game was available after the `ca85516` restart window.
- The only post-`2026-06-09 00:20 CST` active-control sample remains `WE3E4UDG`: rated bullet `120+1`, black vs `CupchessBot`, draw, bot rating `+1`.
- `WE3E4UDG` was played before the narrowed ponder behavior from `ca85516` took effect, so its repeated `Disabling ponder for movetime-limited bullet search` log lines are old-version evidence and should not be used to judge `ca85516`.
- No new `400 Client Error`, stale move submission, traceback, or post-finish move-submit failure appeared in the inspected log window.

## Next Verification Target

After the next bullet/blitz bot game completes under `ca85516`, inspect:

- Whether hard-watchdog searches with live clock data avoid the old `Disabling ponder...` log line.
- Whether exact low-clock movetime searches still disable ponder.
- Whether the bot still loses with large remaining clock against opponents in severe time trouble.
- Whether any `gameFinish` race produces either a stale move skip log or a `400 Client Error`.

## Current Risk Interpretation

- The historical active-control risk gate still fails on accumulated data, led by repeated losses or costly draws against specific bots such as `Fischer_Bot`, `MDBOT`, `duchessAI`, `ToromBot`, and related blocked opponents.
- The latest single live sample is not negative: it was a draw against a higher-rated bot with positive rating impact.
- There is not yet enough post-`ca85516` evidence to change matchmaking or time-management policy again.
