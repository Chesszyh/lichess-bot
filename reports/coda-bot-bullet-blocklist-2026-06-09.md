# coda_bot/codabot Bullet Blocklist

## Scope

- Objective: reduce repeated bullet rating loss while preserving the active bot process.
- Runtime config files changed locally:
  - `config.yml`
  - `.config-history/config.yml`
- Tracked code changed: none.
- No restart was performed because a bullet game was active when the config was changed.
- Later continuation was explicitly told not to wait for the active game, so this pass ends at documentation and commit/push only.

## Evidence

- Refreshed aggregate: `69` rated fast games since `2026-06-08T00:00:00Z`.
- Bullet remains the main leak: `-61` rating over `31` scored games.
- Blitz is much less negative: `-2` rating over `21` scored games.
- `coda_bot | bullet | 120+1` is the top actionable watchlist item:
  - risk `9`
  - `3` losses
  - rating impact `-15`
  - latest sample `2026-06-09T01:44:33+00:00`
- `codabot | bullet | 60+1` is the second actionable watchlist item:
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

- The current bot process still uses the pre-edit config until a safe idle restart.
- This report intentionally does not claim the blocklist is live.
- Do not restart while `/api/account/playing` reports any active game.
- Before restart, also check the log tail for an active game and confirm the LaunchAgent PID.

## Next Evidence Check

- After a safe restart, verify both names are declined/not challenged in logs.
- Keep monitoring whether bullet losses shift away from `coda_bot/codabot` toward another repeated prefix/control cluster.
- Do not remove the `blitz_probe` override based on this evidence; the current regression is bullet-side.
