# M8ZpgJQe Blitz Black Ruy Loss

## Scope

- Objective: document the first finished `180+3` blitz loss after the `60+1` bullet exposure reduction.
- Evidence source: local PGN, refreshed aggregate report, runtime logs, and ignored local config.
- No local engine search was run.
- No tracked runtime code was changed.

## Game

- Game: `friendlybot_1700 vs ilovecatgirl - M8ZpgJQe.pgn`
- Site: `https://lichess.org/M8ZpgJQe`
- Start: `2026-06-09T09:28:12Z`
- Result: black loss by mate, rating `-5`
- Control: rated blitz `180+3`
- Opening: `Ruy Lopez: Open, Classical Defense`
- Prefix: `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5 Bb3 d5 dxe5 Be6`

## Aggregate Delta

- Refreshed aggregate moved from `72` to `73` rated fast games.
- Results moved from `46` draws, `21` losses, `4` unknown, `1` win to `46` draws, `22` losses, `4` unknown, `1` win.
- Overall scored impact moved from `-67` over `54` games to `-72` over `55` games.
- Bullet stayed at `-66` over `32` games.
- Blitz moved from `-1` over `22` games to `-6` over `23` games.
- `180+3 black` worsened to `-9` over `3` games.
- `Ruy Lopez: Open, Classical Defense | black | blitz` is now `-9` over `2` games.

## Interpretation

- This loss confirms that the black Open Ruy issue is not isolated to bullet `120+1` or `90+1`.
- The loss came from `blitz_probe`, not from the default bullet path.
- The `300+2` and `300+3` samples remain the strongest blitz-probe slice: combined rating `+6` over `6` scored games with no losses in the current aggregate.
- The old `blitz_probe` pool could produce `180+3`, the newly confirmed negative slice.

## Local Config Change

Applied a low-risk ignored config change in both `config.yml` and `.config-history/config.yml`:

- `matchmaking.overrides.blitz_probe.challenge_initial_time`: `[180, 240, 300]` -> `[300]`
- `matchmaking.overrides.blitz_probe.challenge_increment`: unchanged at `[2, 3]`
- Default bullet path remains `90+1` only.

This narrows `blitz_probe` to `300+2` and `300+3`, preserving the best current blitz evidence while avoiding the newly confirmed `180+3` black loss slice.

## Deployment

- Config smoke validation passed for both ignored config files.
- A post-game `/api/account/playing` check returned `active_count=0`.
- A later immediate pre-restart `/api/account/playing` check timed out; the shell command still executed the LaunchAgent restart.
- LaunchAgent `org.chesszyh987.lichess-bot` restarted from PID `54477` to PID `33763`.
- Post-restart `/api/account/playing` returned `post_restart_active_count=0`.
- Post-restart log confirmed `Engine configuration OK` and account login.
- `lichess_bot_auto_logs/config.log` confirmed the loaded `blitz_probe.challenge_initial_time` is now `[300]`.

## Next Verification Target

- The next `blitz_probe` outgoing challenge should be `300+2` or `300+3`, not `180+2`, `180+3`, `240+2`, or `240+3`.
- The next default bullet outgoing challenge should still be `90+1`.
- If another black Open Ruy loss appears at `300+2` or `300+3`, stop treating longer blitz as safer and move to an opening-specific design rather than more time-control filtering.
