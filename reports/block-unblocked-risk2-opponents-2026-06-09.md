# Block Unblocked Risk-2 Opponent Clusters

Date: `2026-06-09 CST`

## Summary

- Added four unblocked opponent-control leak clusters to the local challenge and matchmaking block lists.
- Blocked: `CloudNetBot`, `bot1e`, `AggressiveStockfish`, and `DefenchessOfficial`.
- Left risk-1 rows unblocked to avoid over-filtering marginal `+0` rating draw cases.
- Mirrored the private runtime config change in `.config-history/config.yml`.
- No local engine analysis was run.

## Evidence

Before the block-list update, the active-control report showed these unblocked actionable clusters:

- `CloudNetBot | bullet | 120+1`: risk `3`, losses `1`, rating `-3`.
- `bot1e | bullet | 60+1`: risk `3`, losses `1`, rating `-3`.
- `AggressiveStockfish | bullet | 120+1`: risk `2`, rating-negative draws `1`, rating `-1`.
- `AggressiveStockfish | bullet | 90+1`: risk `2`, rating-negative draws `1`, rating `-1`.
- `DefenchessOfficial | bullet | 90+1`: risk `2`, rating-negative draws `1`, rating `-1`.

## Verification

- YAML parse check passed for `config.yml` and `.config-history/config.yml`.
- Re-ran `scripts/analyze_bot_games.py` with `--block-list-config config.yml`.
- The actionable watchlist no longer includes any risk `2` or risk `3` rows; only risk `1` marginal draw rows remain.
