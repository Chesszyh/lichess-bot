# X4YQN6x8 Active-Control Draw Review

Bot: `ilovecatgirl`  
Game: `game_records/CloudNetBot vs ilovecatgirl - X4YQN6x8.pgn`  
Opponent: `CloudNetBot` (`3038`)  
Result: `1/2-1/2`, bot Black, rating diff `+1`  
Time control: `90+1` bullet  
Opening: `Queen's Pawn Game: London System`

## Summary

- This was a rating-positive draw against a slightly higher-rated bot, not a lower-rated draw leak.
- The bot stayed clock-safe: the game finished with `96s` on the bot clock.
- The final draw was tablebase-backed. Logs show `Source: Lichess EGTB`, WDL `0`, and the bot offered draw on `69...g3`.
- Earlier opponent draw offers were declined while the engine/tablebase evaluation was still `0.0`, then the bot offered once online EGTB confirmed the drawn endgame.

## Evidence

- `reports/bot-game-analysis-since-2026-06-08-1936.md` now shows the post-19:36 CST window at `1` loss and `1` draw, net `-4` rating across `2` games.
- Focused opponent impact shows `CloudNetBot | bullet | 90+1` at W-D-L `0-1-0`, score `50.0%`, rating `+1`.
- Log evidence for `X4YQN6x8` shows repeated engine evaluations of `0.0` before the tablebase call, then `Got move g4g3 from tablebase.lichess.ovh (wdl: 0, dtz: 0)`.

## Decision

Do not change runtime config based on this game. The current `90+1` sample is mixed: one high-clock loss to `MEGA-NOOB-BOT`, one rating-positive draw against `CloudNetBot`. This supports continuing to collect active-control evidence before reducing or removing `90+1`.
