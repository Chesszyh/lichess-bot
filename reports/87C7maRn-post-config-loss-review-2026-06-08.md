# 87C7maRn Post-Config Loss Review

Bot: `ilovecatgirl`  
Game: `game_records/MEGA-NOOB-BOT vs ilovecatgirl - 87C7maRn.pgn`  
Opponent: `MEGA-NOOB-BOT` (`3163`)  
Result: `1-0`, bot Black, rating diff `-5`  
Time control: `90+1` bullet  
Opening: `Ruy Lopez: Open, Bernstein Variation`

## Summary

- This was a high-clock normal loss, not a time-forfeit: the bot still had `67s` at game finish.
- The bot used `Source: Engine` from move 1 through move 64, then tablebases once the position was already lost.
- The largest saved bot eval drops were `gxh5` (`-0.59` to `-1.66`), `Re2` (`-0.63` to `-1.33`), and `hxg5` (`-0.39` to `-0.83`).
- Direct local and online tablebases did activate in the late phase, but only after logs already showed a losing WDL (`-2`).

## Evidence

- `reports/bot-game-analysis-since-2026-06-08-1936.md` reports this as the only post-19:36 CST game and loss.
- The focused current-control section identifies `Ruy Lopez: Open, Bernstein Variation | black | bullet | 90+1` at W-D-L `0-0-1`.
- Log lines for game `87C7maRn` show no Black opening-book source; the first move searched for `10` seconds and subsequent moves used the bullet `5000 ms` hard movetime cap.
- Tablebase sources started at move `65` from `tablebase.lichess.ovh`, then local Syzygy from move `76`, all with losing WDL.

## Decision

This single `90+1` sample does not justify removing `90+1`; the evidence supports a tactical/conversion issue
against a stronger bot, not a time-forfeit or tablebase-availability issue.

After the follow-up runtime adjustment, outgoing matchmaking should collect longer bullet controls:
`60+1` at `1/14`, `90+1` at `9/14`, and `120+1` at `4/14`. If another `90+1` Black Ruy Lopez
or repeated `MEGA-NOOB-BOT` high-clock loss appears, then reduce `90+1` or add a targeted Black anti-Ruy mitigation.
