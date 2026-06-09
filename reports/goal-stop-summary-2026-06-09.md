# Goal Stop Summary

## Scope

- Covers tracked work from `9124fdd` through `258bfa8`, plus the continuation pass after the stop summary was written.
- Goal state is not complete: bullet/blitz are not stable at `3080`.
- No heavy local engine experiments were run during an active game in this stop pass.
- Game `KZlP9dMr` was active during the first stop pass and was deliberately not waited on or analyzed, per stop request.
- Later continuation did not wait for the next active game and did not restart the bot process.

## Tracked Changes

- Added `reports/white-bullet-opening-leak-2026-06-09.md` and initial `reports/bot-game-analysis-recent-fast-2026-06-09.md` in `9124fdd`.
- Added `reports/hefydfeq-coda-bot-loss-review-2026-06-09.md` and refreshed the aggregate in `a97f0f5`.
- Added `reports/bot-white-book-best-move-config-2026-06-09.md` in `07a5067`.
- Added restart verification and post-restart aborted-game follow-up in `ed8c1b5` and `2ccf4b0`.
- Refreshed the aggregate after the `Void_Bot` abort in `b52e8fe`.
- Documented the first `180+2` blitz probe draw against `CupchessBot` in `9a5e7b5`.
- Added and clarified this stop summary in `1272542` and `258bfa8`.
- Continuation refresh extends the aggregate from `63` to `69` rated fast games.
- Added `reports/coda-bot-bullet-blocklist-2026-06-09.md` to document the local `coda_bot`/`codabot` blocklist decision.

## Continuation After Stop Summary

- Updated `reports/bot-game-analysis-recent-fast-2026-06-09.md` from `63` to `69` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- New aggregate result state is `44` draws, `20` losses, `4` unknown, and `1` win.
- Overall scored rating impact changed from `-61` over `48` games to `-63` over `52` games.
- Bullet remains unchanged as the main leak at `-61` over `31` scored games.
- Blitz moved from neutral to slightly negative at `-2` over `21` scored games.
- The actionable watchlist still starts with `coda_bot | bullet | 120+1` and `codabot | bullet | 60+1`.
- Locally added `coda_bot` and `codabot` to both incoming challenge and outgoing matchmaking blocklists in ignored config mirrors.
- No tracked runtime code was changed after the stop summary; the continuation is documentation plus ignored local config only.

## Local Runtime Config

- Ignored `config.yml` and `.config-history/config.yml` remain aligned.
- Bot-vs-bot polyglot selection is `best_move`; human selection remains `uniform_random`.
- Bot black bullet/blitz book depth remains disabled at `0`.
- Matchmaking default pool still probes `60+1`, `90+1`, and `120+1` bullet-style controls.
- `blitz_probe` override remains active for `180/240/300` base with `+2/+3` increments.
- `coda_bot` and `codabot` are now present in local ignored challenge and matchmaking blocklists.

## Runtime Actions

- Performed one safe idle LaunchAgent restart after `/api/account/playing` returned `active_count=0`.
- Runtime PID changed from `91127` to `39567`.
- Post-restart checks confirmed reconnect and idle state.
- No later restart was performed, so the coda blocklist change requires a future safe idle restart to take effect.

## Evidence State

- Latest aggregate: `69` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact: `-63` over `52` scored games.
- Bullet is the clear leak: `-61` over `31` scored games.
- Blitz is slightly negative: `-2` over `21` scored games.
- Worst current opponent/control watchlist starts with `coda_bot | bullet | 120+1`: risk `9`, `3` losses, rating `-15`.
- Second actionable opponent/control watchlist item is `codabot | bullet | 60+1`: risk `5`, `1` loss, `1` lower-rated/rating-negative draw, rating `-8`.
- New repeated opening leak: Ruy Lopez Open structures as black, especially `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`.
- Previous white bullet `1.d4` Nimzo leak was mitigated by deterministic bot book selection, but fresh post-change bullet evidence still needs review.

## Stop Decision

- Do not mark the optimization goal complete.
- Before any future restart, re-check active games; do not wait on an active game just to complete documentation.
- Next useful work should restart only at a safe idle point, then confirm `coda_bot` and `codabot` are not accepted/challenged.
- After the restart evidence is available, analyze whether bullet losses shift from `coda_bot/codabot` toward another repeated opponent/control/opening cluster.
- If a low-risk config change is needed next, prefer reducing exposure to leaking bullet controls/opponents over changing blitz, because blitz probe evidence is currently neutral-to-positive.
