# Block Actionable DarkOnBot Leak

Date: `2026-06-09 CST`

## Summary

- Added block-list-aware PGN analysis via `--block-list-config`.
- Added `Actionable Opponent Leak Watchlist` to reports when a block list is supplied.
- Added `DarkOnBot` to private runtime `challenge.block_list` and `matchmaking.block_list`.
- Mirrored the private config change in `.config-history/config.yml`.
- No local engine analysis was run.

## Evidence

After filtering the already-blocked opponents from the active-control leak watchlist, `DarkOnBot` was the strongest remaining repeated opponent leak:

- `DarkOnBot | bullet | 120+1`: risk `3`, losses `1`, rating `-6`, latest `2026-04-14T10:06:52+00:00`.
- `DarkOnBot | bullet | 90+1`: risk `3`, losses `1`, rating `-5`, latest `2026-04-26T10:25:22+00:00`.
- `DarkOnBot | bullet | 60+1`: risk `3`, losses `1`, rating `-3`, latest `2026-04-16T07:11:58+00:00`.

## Rationale

The earlier leak watchlist mixed already-blocked opponents with still-actionable ones. The new analyzer option reads only `challenge.block_list` and `matchmaking.block_list` names from private config, then renders unblocked rows separately. That made `DarkOnBot` stand out as a repeated active-control loss leak across all three deployed bullet controls. Blocking it reduces avoidable downside while leaving one-off or high-rated draw cases available for more evidence.

## Verification

- `pytest test_bot/test_analyze_bot_games.py -q`
- `ruff check --config test_bot/ruff.toml scripts/analyze_bot_games.py test_bot/test_analyze_bot_games.py`
- `mypy --strict --explicit-package-bases scripts/analyze_bot_games.py test_bot/test_analyze_bot_games.py`
- Parsed both `config.yml` and `.config-history/config.yml` with PyYAML.
- Regenerated active-control reports with `--block-list-config config.yml`.
