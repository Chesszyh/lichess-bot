# MEGA-NOOB-BOT Active-Control Risk Review

Bot: `ilovecatgirl`  
Opponent: `MEGA-NOOB-BOT`  
Scope: bullet active controls after the current lc0/Stockfish tuning window

## Evidence

- `reports/bot-game-analysis-2026-06-08.md` shows `MEGA-NOOB-BOT | bullet | 60+1` at W-D-L `0-0-1`, score `0.0%` over `1` game.
- `reports/bot-game-analysis-2026-06-08.md` shows `MEGA-NOOB-BOT | bullet | 90+1` at W-D-L `0-0-1`, score `0.0%` over `1` game.
- The latest focused window `reports/bot-game-analysis-since-2026-06-08-1936.md` still isolates `MEGA-NOOB-BOT | bullet | 90+1` at `-5` rating over `1` game.
- The `90+1` loss was not a time-forfeit cluster: it finished with `67s` on the bot clock, so the immediate issue is opponent/control/opening performance rather than clock survival.

## Runtime Mitigation

- Added `MEGA-NOOB-BOT` to the local ignored `challenge.block_list` to decline incoming challenges from this opponent.
- Added `MEGA-NOOB-BOT` to the local ignored `matchmaking.block_list` to stop outgoing matchmaking challenges to this opponent.
- Mirrored the same ignored config change in `.config-history/config.yml` for private config tracking.

## Decision

This is a narrow rating-preservation change. It avoids a repeated recent active-control loss source without removing `90+1` globally, because the same `90+1` window also contains a rating-positive draw against `CloudNetBot`.
