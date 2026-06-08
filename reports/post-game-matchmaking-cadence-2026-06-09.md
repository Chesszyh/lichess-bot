# Post-Game Matchmaking Cadence

Date: `2026-06-09 CST`

## Summary

- Reduced local matchmaking `challenge_timeout` from `15` to `10` minutes.
- Mirrored the private runtime config change in `.config-history/config.yml`.
- Kept the one-game-at-a-time constraint and existing opponent cooldowns unchanged.
- No local engine analysis was run.

## Evidence

- The first rated fast game after the latest deploy was `ilovecatgirl vs coda_bot - tLbp18c5.pgn`.
- Result: win as White in `120+1`, rating impact `+7` against a `3042` opponent.
- After the game ended at `01:18:05 CST`, the bot scheduled the next challenge for `01:33:05 CST`.
- A shorter post-game cadence increases rated bot-vs-bot sampling and rating-climb opportunity while still leaving a meaningful cooldown between games.

## Verification

- YAML parse check passed for `config.yml` and `.config-history/config.yml`.
- `reports/bot-game-analysis-active-controls-since-2026-06-09-0110.md` confirms `1` rated bullet win, `+7` rating, and no loss/draw leak rows since `2026-06-08T17:10:00Z`.
