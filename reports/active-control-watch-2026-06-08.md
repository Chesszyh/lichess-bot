# Active-Control Watch for 2026-06-08

Bot: `ilovecatgirl`
Scope: rated bullet controls currently active in private config: `60+1`, `90+1`, `120+1`

## Current State

- Latest local active-control PGN is `game_records/ilovecatgirl vs abdcebot - Zd5yy2Mj.pgn` at 2026-06-08 23:08 CST.
- The running bot was later restarted safely after `/api/account/playing` returned `0` active games. One
  supervisor-managed bot process remains, PID `21952`.
- The restarted bot preserved its outgoing challenge cadence after the cadence persistence fixes.
- No local engine experiment was initiated for this review.
- Outgoing active-control sampling is now `60+1:90+1:120+1 = 3:6:9`, up from `1:4:9`. `challenge_timeout`
  remains `15` minutes, so this changes control selection only, not active-challenge frequency.
- `abcd_engine` and the remaining high-risk historical active-control leak opponents are now blocked for incoming and
  outgoing bot games. See `reports/block-active-control-leak-opponents-2026-06-08.md`.

## Evidence

- `reports/bot-game-analysis-active-controls-2026-06-08.md` now filters to the active rated controls only:
  `262` games across `60+1`, `90+1`, and `120+1`.
- The active-only historical pool is rating-positive: `+217` rating over `219` rated-diff games, with `109` wins,
  `122` draws, `21` losses, and `10` unknown results.
- Exact active-control rating impact remains positive by side: `90+1 black` `+10`, `90+1 white` `+17`, `120+1 white`
  `+33`, `60+1 black` `+39`, `60+1 white` `+60`, and `120+1 black` `+58`.
- `reports/bot-game-analysis-active-controls-since-2026-06-08-1936.md` isolates the post-19:36 CST active-control window: `2` rated `90+1` bullet games, net `-4`.
- The post-19:36 CST window contains one high-clock normal loss to `MEGA-NOOB-BOT` and one rating-positive draw against `CloudNetBot`.
- `reports/bot-game-analysis-active-controls-since-2026-06-08-2016.md` isolates the post-block window: `2` rated bullet
  draws, net `+1`, with no losses and no lower-rated draw leaks.
- `reports/bot-game-analysis-active-controls-since-2026-06-08-2120.md` isolates the post-cadence-fix runtime window:
  one rated `120+1` draw against `CupchessBot`, net `+0`, no losses, and no clock leak.
- `game_records/ilovecatgirl vs abdcebot - Zd5yy2Mj.pgn` is the first post-clock-pressure active-control sample:
  a `90+1` draw against a `3144` opponent, net `+2`. It was not a clock-pressure trigger case because the opponent
  stayed clock-safe; the bot became the low-clock side but held a drawn endgame.
- The active-control analyzer now ranks lower-rated draw opponents directly. The largest historical active-control
  lower-rated draw cluster is `duchessAI | bullet | 60+1` with `5` draws; the same report shows that exact `60+1`
  sub-sample is `-6` over `6` rated-diff games. It is also the largest rating-negative draw opponent cluster, while the
  post-block windows have no lower-rated or rating-negative draw leaks.
- `reports/active-control-loss-clusters-2026-06-08.md` separates stale April active-control losses from the three June 8
  active-control losses, avoiding a broad opening/config change from historical data.
- The refreshed analyzer now ranks opponent impact across any filtered report, not only exact focused controls. In the
  active-control report, the strongest confirmed opponent leaks remain the already-blocked `abcd_engine` at `60+1`
  (`-10` over `2` rated-diff games) and `MEGA-NOOB-BOT` at `60+1`/`90+1` (`-11` over `2` rated-diff games).
- The blitz-only report shows large historical opponent leaks concentrated in controls the current config excludes,
  especially `180+0` and longer blitz pools. This is evidence against reintroducing broad blitz matchmaking before the
  active `+1` bullet envelope has a larger fresh sample.

## Decision

Keep the active rated controls at `60+1`, `90+1`, and `120+1`. The expanded block list now excludes the worst
historical active-control leak clusters, while the first post-clock-pressure sample against `abdcebot` was
rating-positive. Do not broaden controls or change openings from this sample. Continue watching for two specific
signals: actual `Using exact clock-pressure movetime` log lines, and any repeated pattern where the bot becomes the
low-clock side in drawn or winning active-control endings.
