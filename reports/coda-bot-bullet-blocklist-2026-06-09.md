# coda_bot/codabot Bullet Blocklist

## Scope

- Objective: reduce repeated bullet rating loss while preserving the active bot process.
- Runtime config files changed locally:
  - `config.yml`
  - `.config-history/config.yml`
- Tracked code changed: none.
- No restart was performed because a bullet game was active when the config was changed.
- Later continuation was explicitly told not to wait for the active game, so this pass ends at documentation and commit/push only.
- A later safe idle restart was performed after `/api/account/playing` returned `active_count=0`.

## Evidence

- Refreshed aggregate: `69` rated fast games since `2026-06-08T00:00:00Z`.
- Later refreshed aggregate: `70` rated fast games after adding `PxsslsQe`.
- In the `70`-game aggregate, `coda_bot` and `codabot` remain in the full opponent watchlist but are removed from the actionable watchlist because `config.yml` is passed as the blocklist config.
- Bullet remains the main leak: `-61` rating over `31` scored games.
- Blitz is much less negative: `-2` rating over `21` scored games.
- Latest `70`-game aggregate moves bullet to `-66` over `32` scored games; blitz remains `-2` over `21` scored games.
- At the `69`-game decision point, `coda_bot | bullet | 120+1` was the top actionable watchlist item:
  - risk `9`
  - `3` losses
  - rating impact `-15`
  - latest sample `2026-06-09T01:44:33+00:00`
- At the `69`-game decision point, `codabot | bullet | 60+1` was the second actionable watchlist item:
  - risk `5`
  - `1` loss
  - `1` lower-rated/rating-negative draw
  - rating impact `-8`

## Local Config Change

Added both opponent names to the local incoming challenge and outgoing matchmaking blocklists:

```yaml
- coda_bot
- codabot
```

The two ignored config mirrors were parsed after the edit and confirmed aligned:

- `challenge.block_list` contains both names.
- `matchmaking.block_list` contains both names.

## Deployment State

- Safe restart completed at local `2026-06-09 16:19`.
- `/api/account/playing` returned `pre_restart_active_count=0` immediately before restart.
- LaunchAgent `org.chesszyh987.lichess-bot` changed from PID `39567` to PID `28441`.
- Startup log confirmed `Engine configuration OK`, `Welcome ilovecatgirl!`, and connection to Lichess.
- `/api/account/playing` returned `post_restart_active_count=0` after restart.
- The current process was started from the config that contains `coda_bot` and `codabot`; live effectiveness still needs log/game evidence.

## Next Evidence Check

- Verify both names are declined/not challenged in logs.
- Keep monitoring whether bullet losses shift away from `coda_bot/codabot` toward another repeated prefix/control cluster.
- Do not remove the `blitz_probe` override based on this evidence; the current regression is bullet-side.
