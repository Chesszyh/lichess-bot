# Actionable Leak Watchlist Triage

Date: `2026-06-09 00:44 CST`

## Summary

- No local engine analysis was run.
- No bot restart was performed.
- `/api/account/playing` returned `ongoing_games = 0` during inspection.
- The bot was running as PID `96780`, started at `2026-06-09 00:40:42 CST`.
- The 00:41 outgoing challenge produced challenge id `NcxWLbJ7`, but no `gameStart` or new PGN was available yet.

## Current Actionable Rows

The block-list-aware active-control report currently surfaces these unblocked rows:

- `CloudNetBot | bullet | 120+1`: risk `3`, one loss, rating `-3`.
- `bot1e | bullet | 60+1`: risk `3`, one loss, rating `-3`.
- `AggressiveStockfish | bullet | 120+1`: risk `2`, one lower-rated rating-negative draw, rating `-1`.
- `AggressiveStockfish | bullet | 90+1`: risk `2`, one lower-rated rating-negative draw, rating `-1`.
- `DefenchessOfficial | bullet | 90+1`: risk `2`, one lower-rated rating-negative draw, rating `-1`.
- Lower risk one-off draws: `WildorderBot`, `friendlybot_1700`.

## Full Opponent Context

### CloudNetBot

- Active controls: `18` games, W-D-L `0-17-1`, total rating `+35`.
- The flagged loss was `ilovecatgirl vs CloudNetBot - AmX1ztAe.pgn`, rated bullet `120+1`, bot white, opponent `3061`, rating diff `-3`.
- Final clocks in the flagged loss: bot `74s`, opponent `61s`.
- Triage: do not block now. The opponent is high-rated, the overall rating result is strongly positive, and the flagged game is a useful high-clock normal-loss sample rather than an avoidable low-rated leak.

### bot1e

- Active controls: `3` games, W-D-L `0-1-1` plus `1` unknown, total known rating `-3`.
- The flagged loss was `bot1e vs ilovecatgirl - 0D9rqw9h.pgn`, rated bullet `60+1`, bot black, opponent `3094`, rating diff `-3`.
- Final clocks in the flagged loss: bot `32s`, opponent `48s`.
- Triage: do not block now. The loss is against a higher-rated opponent and remains useful as a high-strength bot-vs-bot sample.

### AggressiveStockfish

- Active controls: `4` games, W-D-L `2-2-0`, total rating `+3`.
- Flagged lower-rated draws:
  - `AggressiveStockfish vs ilovecatgirl - CFYHfwEL.pgn`, `120+1`, opponent `2895`, rating diff `-1`, clocks bot `93s` vs opponent `13s`.
  - `AggressiveStockfish vs ilovecatgirl - ToE3GG2C.pgn`, `90+1`, opponent `2899`, rating diff `-1`, clocks bot `33s` vs opponent `12s`.
- Triage: keep observing instead of blocking immediately. This is a direct example of the user-reported issue where the bot keeps enough clock while failing to convert against an opponent in severe time trouble, but the overall opponent result is still positive.

### DefenchessOfficial

- Active controls: `3` games, W-D-L `1-1-0` plus `1` unknown, total known rating `+3`.
- Flagged lower-rated draw: `DefenchessOfficial vs ilovecatgirl - mmJFwmO6.pgn`, `90+1`, opponent `2928`, rating diff `-1`, clocks bot `88s` vs opponent `11s`.
- Triage: keep observing instead of blocking immediately. The draw is a time-pressure conversion miss, but there is also a recent win against the same opponent profile.

### WildorderBot and friendlybot_1700

- Current actionable rows are one-off lower-rated or neutral draws.
- Triage: do not block now. The samples are too weak and total rating impact is non-negative.

## Decision

- No new block-list changes were made in this pass.
- The next code/config change should be driven by a fresh post-`ca85516` game or by a focused time-pressure conversion fix, not by blocking every unblocked actionable row.
- The highest-value follow-up evidence is a new game where the opponent falls below roughly `15s` while the bot has substantial clock left. Those games should be inspected before changing bullet time allocation again.
