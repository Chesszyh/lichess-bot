# Bullet 60+1 Exposure Reduction

## Scope

- Objective: reduce the strongest remaining bullet exposure after `120+1` was removed from the live default pool.
- Evidence source: local PGNs, refreshed aggregate report, Lichess API state checks, and runtime logs.
- No local engine analysis was run.
- No tracked runtime code was changed.

## Current Evidence

- Refreshed `reports/bot-game-analysis-recent-fast-2026-06-09.md`; no new PGNs were added after `D78oWQu6`.
- Aggregate remains `71` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact remains `-67` over `54` scored games.
- Bullet remains the clear leak at `-66` over `32` scored games.
- Blitz remains near neutral at `-1` over `22` scored games.
- Public rating snapshot during this pass:
  - Bullet: `2991`, progress `-29`, games `2406`, RD `45`.
  - Blitz: `2946`, progress `+1`, games `1999`, RD `45`.

## Root Cause Slice

- The previous live config already removed outgoing `120+1` and reduced incoming challenge `max_base` to `90`.
- After that change, the remaining default bullet pool was `60+1` and `90+1`.
- Historical focused impact still shows `60+1` as the worst currently reachable default bullet control:
  - `60+1`: rating `-30` over `11` games, W-D-L `0-7-5`, score `29.2%`.
  - `90+1`: rating `-9` over `8` games, W-D-L `0-5-3`, score `31.2%`.
- Side/context impact also points at `60+1`:
  - `60+1 white`: `-25` over `10` games.
  - `Nimzo-Indian Defense: Normal Variation, Classical Defense | white | bullet | 60+1`: `-21` over `3` games.

## Local Config Change

Applied the low-risk exposure reduction in ignored config mirrors:

- `challenge.min_base`: `60` -> `90`
- `challenge.max_base`: kept at `90`
- `matchmaking.challenge_initial_time`: removed all `60` entries
- `matchmaking.challenge_increment`: kept at `[1]`
- `matchmaking.overrides.blitz_probe`: unchanged at `180/240/300` with `+2/+3`

This makes the default bullet pool `90+1` only while preserving the blitz probe.

## Deployment

- Pre-restart config parse passed for both `config.yml` and `.config-history/config.yml`.
- Pre-restart `/api/account/playing` returned `active_count=0`.
- LaunchAgent `org.chesszyh987.lichess-bot` was safely restarted.
- Runtime PID changed from `78929` to `54477`.
- Startup log confirmed `Engine configuration OK`, `Welcome ilovecatgirl!`, and connection to Lichess.
- Post-restart `/api/account/playing` returned `active_count=0`.
- `lichess_bot_auto_logs/config.log` confirmed loaded challenge bounds:
  - `challenge.max_base: 90`
  - `challenge.min_base: 90`

## Post-Restart Verification

- First outgoing challenge after restart used the unchanged blitz probe:
  - `16:54:37`: `blitz_probe` selected rated `240+2` against `Bot1nokk`.
  - Challenge `tKTROxdG` was unanswered and canceled.
  - Post-cancel `/api/account/playing` returned `active_count=0`.
- This verifies the restart did not break matchmaking.
- It does not yet verify the default bullet path because the first sampled path was `blitz_probe`.

## Next Verification Target

- The next default matchmaking challenge should be rated `90+1`, not `60+1`.
- Incoming `60+1` challenges should be declined by the challenge filter because `min_base == max_base == 90`.
- If a fresh post-change `90+1` bullet game is completed, refresh the aggregate and compare it against the old `60+1` leak.
