# Active-Control Loss Clusters for 2026-06-08

Bot: `ilovecatgirl`
Scope: rated `60+1`, `90+1`, and `120+1` bullet games only

## Active-Only Baseline

- `reports/bot-game-analysis-active-controls-2026-06-08.md` now filters to the currently active rated controls instead of only highlighting them.
- Active-only sample: `259` games, W-D-L/unknown `109-120-20-10`.
- Rated-diff sample is positive: `+221` over `216` games.
- Exact active-control side splits are all rating-positive: `60+1 white +60`, `60+1 black +39`, `90+1 white +15`, `90+1 black +10`, `120+1 white +33`, `120+1 black +64`.

## Loss Timing

- `20` active-control rated losses were found.
- `17` of the `20` active-control losses are from April 2026, before the current June 8 config sequence.
- The largest active-only opening loss cluster is `Sicilian Defense: Najdorf Variation, English Attack` with `4` losses, but all four are historical and predate the current Black fast-book disable and active-control restrictions.
- The only June 8 active-control losses are:
  - `2QVD5cp2`: `60+1` White vs `abcd_engine`, `-10`, time forfeit, Nimzo-Indian.
  - `wUt40hrP`: `60+1` White vs `MEGA-NOOB-BOT`, `-6`, normal loss, Nimzo-Indian.
  - `87C7maRn`: `90+1` Black vs `MEGA-NOOB-BOT`, `-5`, high-clock normal loss, Ruy Lopez Open.

## Decision

- Do not act on the historical Najdorf active-control cluster yet; it is stale relative to the current Black book and active-control config.
- Keep `MEGA-NOOB-BOT` blocked. It accounts for two of the three June 8 active-control losses.
- Keep `abcd_engine` blocked as a narrow mitigation for the June 8 `60+1` time-forfeit loss, without removing `60+1`
  globally because the full active-only `60+1 white` pool remains strongly positive.
- Next actionable trigger: repeated post-block losses or rating-negative draws on the active controls, especially non-blocked
  `60+1` time losses or a fresh Black Najdorf loss after the current config.
