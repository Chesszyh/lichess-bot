# Rated-Only Fast Game Runtime Review

Bot: `ilovecatgirl`  
Scope: incoming fast challenges and arena participation under current lc0/Stockfish tuning

## Evidence

- `reports/bot-game-analysis-2026-06-08.md` now separates rated and casual games.
- The current local record set contains substantial casual volume: `299` casual draws, `112` casual losses, `40` casual wins, and `1` casual unknown.
- `Rating Impact by Mode` shows only rated games move rating: rated games are `+226` rating over `1626` rated games, while casual games have no rating-diff tags.
- The active objective is to stabilize bullet/blitz ratings around `3080`, so casual games consume bot runtime, challenge slots, and Mac mini resources without directly improving the measured rating target.
- Outgoing matchmaking was already rated-only; the remaining casual exposure was incoming challenges and arena participation.

## Runtime Mitigation

- Set ignored local `challenge.modes` from `rated, casual` to `rated`.
- Set ignored local `arena.rated_modes` from `rated, casual` to `rated`.
- Mirrored the same ignored config changes in `.config-history/config.yml` for private config tracking.
- `challenge.always_allow_users` still contains `Chesszyh`, so owner testing remains possible through the existing bypass path.

## Decision

Keep fast-game runtime concentrated on rated evidence. This is narrower than disabling incoming challenges or arenas and aligns resource use with the rating-stability objective while the bot continues collecting active-control data.
