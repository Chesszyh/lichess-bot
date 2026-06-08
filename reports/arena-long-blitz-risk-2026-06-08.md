# Arena Long-Blitz Risk Review

Bot: `ilovecatgirl`  
Scope: arena-created bullet/blitz controls under current lc0/Stockfish tuning

## Evidence

- Active incoming challenge and matchmaking config already stay within the 60-120s base-time envelope, but `arena.max_base` was still `300`.
- `reports/bot-game-analysis-2026-06-08.md` shows the worst scoring controls are long-blitz arena-shaped controls:
  - `180+0 black`: W-D-L `8-26-51`, score `24.7%` over `85` games.
  - `180+0 white`: W-D-L `12-32-45`, score `31.5%` over `89` games.
  - `300+2 black`: W-D-L `2-60-36`, score `32.7%` over `98` games.
  - `180+2 black`: W-D-L `10-87-47`, score `37.2%` over `144` games.
- High-clock normal loss clusters are also concentrated in long-blitz controls such as `300+2`, `240+1`, and `240+2`, which means these are not primarily flagging/time-management failures.
- Rating-negative draw contexts include repeated long-blitz prefixes at `180+2` and `240+1`, so longer arenas create both loss and draw-leak rating drag.

## Runtime Mitigation

- Set ignored local `arena.max_base` from `300` to `120`.
- Mirrored the same ignored config change in `.config-history/config.yml` for private config tracking.

## Decision

Keep arena participation inside the current active-control envelope while collecting cleaner 60-120s evidence. This is narrower than disabling arenas entirely and avoids globally changing the engine or opening setup while the bot is running.
