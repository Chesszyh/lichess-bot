# Active-Control Watch for 2026-06-08

Bot: `ilovecatgirl`
Scope: rated bullet controls currently active in private config: `60+1`, `90+1`, `120+1`

## Current State

- Latest local PGN remains `game_records/CloudNetBot vs ilovecatgirl - X4YQN6x8.pgn` at 2026-06-08 20:20 CST.
- The running bot is idle and, after a 20:56 CST process restart, scheduled its next outgoing challenge after 2026-06-08
  21:11:46 CST.
- No local engine experiment was initiated for this review.
- Outgoing active-control sampling is now `60+1:90+1:120+1 = 3:6:9`, up from `1:4:9`. `challenge_timeout`
  remains `15` minutes, so this changes control selection only, not active-challenge frequency.
- `abcd_engine` is now blocked for incoming and outgoing bot games after the active-control sample showed W-D-L
  `0-3-1`, net `-10`, including the 2026-06-08 `60+1` white loss while `ilovecatgirl` was the higher-rated bot.

## Evidence

- `reports/bot-game-analysis-active-controls-2026-06-08.md` now filters to the active rated controls only:
  `259` games across `60+1`, `90+1`, and `120+1`.
- The active-only historical pool is rating-positive: `+221` rating over `216` rated-diff games, with `109` wins,
  `120` draws, `20` losses, and `10` unknown results.
- Exact active-control rating impact remains positive by side: `90+1 black` `+10`, `90+1 white` `+15`, `120+1 white`
  `+33`, `60+1 black` `+39`, `60+1 white` `+60`, and `120+1 black` `+64`.
- `reports/bot-game-analysis-active-controls-since-2026-06-08-1936.md` isolates the post-19:36 CST active-control window: `2` rated `90+1` bullet games, net `-4`.
- The post-19:36 CST window contains one high-clock normal loss to `MEGA-NOOB-BOT` and one rating-positive draw against `CloudNetBot`.
- `reports/bot-game-analysis-active-controls-since-2026-06-08-2016.md` isolates the post-block window: `1` rated `90+1` bullet draw, net `+1`.
- `reports/active-control-loss-clusters-2026-06-08.md` separates stale April active-control losses from the three June 8
  active-control losses, avoiding a broad opening/config change from historical data.
- The refreshed analyzer now ranks opponent impact across any filtered report, not only exact focused controls. In the
  active-control report, the strongest confirmed opponent leaks remain the already-blocked `abcd_engine` at `60+1`
  (`-10` over `2` rated-diff games) and `MEGA-NOOB-BOT` at `60+1`/`90+1` (`-11` over `2` rated-diff games).
- The blitz-only report shows large historical opponent leaks concentrated in controls the current config excludes,
  especially `180+0` and longer blitz pools. This is evidence against reintroducing broad blitz matchmaking before the
  active `+1` bullet envelope has a larger fresh sample.

## Decision

Keep the active rated controls at `60+1`, `90+1`, and `120+1`, but collect more short-bullet evidence by increasing the
outgoing `60+1` and `90+1` weights. The repeated recent loss source, `MEGA-NOOB-BOT`, is already blocked in private
config, and the only post-block active-control game is rating-positive. Also block `abcd_engine` as a narrow
mitigation for the June 8 `60+1` time-forfeit loss. Do not broaden controls or change openings from this sample.
Do not add a new block for `ToromBot`, `MDBOT`, `duchessAI`, or `TakticproChess` yet: their active-control evidence is
either stale, low-sample, or already mitigated by the current control envelope. Re-evaluate after fresh post-block games.
