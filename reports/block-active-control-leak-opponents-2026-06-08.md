# Block Active-Control Leak Opponents

## Scope

- Date: `2026-06-08`
- Bot: `ilovecatgirl`
- Target controls: rated `60+1`, `90+1`, `120+1`
- Method: PGN/report evidence only; no local engine experiment was run.

## Evidence

`reports/bot-game-analysis-active-controls-2026-06-08.md` still has an opening/opponent risk gate failure and identifies repeated rating leaks:

- `duchessAI | bullet | 60+1`: risk `10`, lower-rated draws `5`, rating-negative draws `5`, rating `-10`.
- `MDBOT | bullet | 60+1`: risk `9`, losses `3`, rating `-8`.
- `ToromBot | bullet | 90+1`: risk `6`, losses `2`, rating `-10`.
- `BorkaTower | bullet | 60+1`: risk `4`, losses `1`, lower-rated draws `1`, rating `-3`.
- `Valhalla-Bot | bullet | 120+1`: risk `4`, rating-negative draws `2`, rating `-2`.
- `grail-bot | bullet | 120+1`: risk `3`, losses `1`, rating `-10`.
- `abhisun_bot | bullet | 120+1`: risk `3`, losses `1`, rating `-9`.
- `RockingSuperstars | bullet | 60+1`: risk `3`, losses `1`, rating `-8`.

The fresh post-`2026-06-08T13:20:00Z` report only shows `Fischer_Bot` as a new leak, and that opponent was already blocked. This update addresses the remaining historical active-control leak clusters that were still eligible for matchmaking.

## Change

Added the listed opponents to both incoming challenge and outgoing matchmaking block lists in runtime `config.yml`, mirrored in `.config-history/config.yml`.

Private config history commit:

- `140bd0a Block active-control leak opponents`

## Deployment

- Confirmed `/api/account/playing` returned `active_count=0` before restart.
- Restarted bot process from PID `18602` to PID `21952`.
- Startup log confirms connection as `ilovecatgirl` and preserved cadence: next challenge after `Mon Jun 8 23:32:41 2026`.

## Verification

- YAML parsed for `config.yml` and `.config-history/config.yml`.
- All eight new opponents are present in both `challenge.block_list` and `matchmaking.block_list`.
- `pytest test_bot/test_config.py -q`: `15 passed`.
