# WE3E4UDG Post-Fix Live Verification

Game: `WE3E4UDG`
PGN: `game_records/CupchessBot vs ilovecatgirl - WE3E4UDG.pgn`
Date: `2026-06-09 CST`

## Summary

- Rated `120+1` bullet, bot played Black.
- Opponent: `CupchessBot`, `3061`.
- Bot rating before game: `3026`.
- Result: `1/2-1/2`.
- Rating impact: bot `+1`, opponent `-1`.
- Opening: Queen's Pawn Game: London System.

## Runtime Signals

- The game was played after deploying `baffddc` (`Skip stale moves after control finish`).
- No stale post-finish move submission was observed.
- No `400 Client Error` appeared after `gameFinish`.
- `gameFinish` was followed by normal `local_game_done` and PGN export.
- The draw offer was accepted with an online tablebase result:
  `Got move g6e4 from tablebase.lichess.ovh (wdl: 0, dtz: 0, dtm: 0)`.

## Time-Management Signals

- The earlier `cc6cdc7` fix did stop exact movetime searches from using the old ponderhit path.
- During this game, the running process still used the broader first version of that fix and disabled ponder for hard-watchdog searches too.
- That broader behavior was narrowed in `ca85516` (`Keep ponder for fast watchdog searches`) after the live log showed repeated lines like:
  `Disabling ponder for movetime-limited bullet search`.
- `ca85516` was committed and pushed during the game, then safely deployed only after `/api/account/playing` returned `0` ongoing games.

## Evidence Update

- `reports/bot-game-analysis-active-controls-2026-06-08.md` now includes this game:
  - active-control games: `264`
  - active-control draws: `124`
  - rated bullet rating impact: `+218` over `220` games
  - `120+1 black`: `+59` over `46` games
- `reports/bot-game-analysis-active-controls-since-2026-06-09-0020.md` isolates the post-deploy sample:
  - `1` rated `120+1` bullet draw
  - `CupchessBot | bullet | 120+1`: `+1`
  - no loss or costly lower-rated draw cluster

## Follow-Up Direction

The next live game after `ca85516` should confirm that high-clock hard-watchdog searches can again use ponder, while exact low-clock movetime searches still log `Disabling ponder for exact movetime-limited ...`.
