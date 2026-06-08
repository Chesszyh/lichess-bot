# Block Lower-Rated Draw Leaks

Date: `2026-06-09 CST`

## Summary

- Added `Worst-ai` and `odonata-bot` to private runtime `challenge.block_list` and `matchmaking.block_list`.
- Mirrored the change in `.config-history/config.yml`.
- No public default config changed.
- No local engine analysis was run.

## Evidence

- `Worst-ai` produced the largest unblocked rating-negative draw:
  - `Worst-ai vs ilovecatgirl - ml4y9CRN.pgn`
  - opponent rating `2764`
  - rating impact `-3`
  - lower-rated draw gap `138`
  - opening: Nimzowitsch Defense: Declined Variation
- `odonata-bot` produced the next largest unblocked lower-rated draw leak:
  - `ilovecatgirl vs odonata-bot - pMrpQbqB.pgn`
  - opponent rating `2758`
  - rating impact `-2`
  - lower-rated draw gap `157`
  - opening: Hungarian Opening

## Rationale

The top historical active-control risk cluster opponents were already blocked. These two opponents are lower-rated one-off draw leaks with direct negative rating impact and no current evidence that rematches are useful for improving expected bullet/blitz rating. Blocking them reduces avoidable downside while preserving the higher-rated matchmaking pool.

## Verification

- Parsed both `config.yml` and `.config-history/config.yml` with PyYAML.
- Confirmed both names are present in `challenge.block_list`.
- Confirmed both names are present in `matchmaking.block_list`.
