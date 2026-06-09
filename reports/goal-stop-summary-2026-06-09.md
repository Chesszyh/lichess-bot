# Goal Stop Summary

## Scope

- Covers tracked work from `9124fdd` through `8218779`, plus this closeout pass.
- Goal state is not complete: bullet/blitz are not stable at `3080`.
- No heavy local engine experiments were run during an active game in this stop pass.
- Game `KZlP9dMr` was active during the first stop pass and was deliberately not waited on or analyzed, per stop request.
- Later continuation first did not wait for the active game; after it finished, a separate API check returned idle and the bot was safely restarted.
- This closeout pass did not wait on any game or make another runtime change.

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
- Later refreshed the aggregate from `69` to `70` rated fast games, adding the `PxsslsQe` `CCI-6` bullet loss.
- Later safely restarted LaunchAgent `org.chesszyh987.lichess-bot` so the coda/codabot blocklist config is loaded by the current process.
- Later applied a local ignored config change to reduce `120+1` exposure, but did not restart because game `D78oWQu6` was active.
- Later `D78oWQu6` ended as a rated `180+2` blitz draw, then a safe idle restart loaded the `120+1` exposure reduction.
- Later refreshed the aggregate from `70` to `71` rated fast games.
- Later verified the first two outgoing challenges after PID `78929` startup avoided `120+1`.
- Confirmed commit `8218779` is present on both local `lc0+stockfish` and `origin/lc0+stockfish`.
- This closeout pass only updates documentation; no runtime code, engine config, or ignored local config was changed.

## Post-Pause Modification Summary

- Documentation was extended from the previous stop summary through the post-restart challenge-control verification.
- Ignored runtime config was changed to block `coda_bot`/`codabot` in incoming and outgoing paths.
- Ignored runtime config was changed to reduce `120+1` exposure by removing outgoing `120` bases and setting incoming `challenge.max_base` to `90`.
- Two safe idle LaunchAgent restarts loaded the blocklist and then the `120+1` exposure reduction; no restart was done while `D78oWQu6` was active.
- Fresh evidence added one `120+1` bullet loss sample, one `180+2` blitz draw sample, and two clean outgoing post-restart challenge-control checks.
- No tracked runtime code was changed in this post-pause interval; all committed changes are reports.

## Continuation After Stop Summary

- Updated `reports/bot-game-analysis-recent-fast-2026-06-09.md` from `63` to `69` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- New aggregate result state is `44` draws, `20` losses, `4` unknown, and `1` win.
- Overall scored rating impact changed from `-61` over `48` games to `-63` over `52` games.
- Bullet remains unchanged as the main leak at `-61` over `31` scored games.
- Blitz moved from neutral to slightly negative at `-2` over `21` scored games.
- The actionable watchlist still starts with `coda_bot | bullet | 120+1` and `codabot | bullet | 60+1`.
- Locally added `coda_bot` and `codabot` to both incoming challenge and outgoing matchmaking blocklists in ignored config mirrors.
- No tracked runtime code was changed after the stop summary; the continuation is documentation plus ignored local config only.

## Restart and Fresh Evidence

- Pre-restart `/api/account/playing` check returned `active_count=0`.
- LaunchAgent PID changed from `39567` to `28441`.
- Post-restart log confirmed startup, engine configuration check, account login, and Lichess connection.
- Post-restart `/api/account/playing` check returned `active_count=0`.
- Refreshed aggregate now includes `CCI-6 vs ilovecatgirl - PxsslsQe.pgn`.
- Latest aggregate result state is `44` draws, `21` losses, `4` unknown, and `1` win.
- Overall scored rating impact is now `-68` over `53` games.
- Bullet is now `-66` over `32` scored games; blitz remains `-2` over `21` scored games.
- The newest loss is another `120+1` black-side Ruy Lopez Open Classical sample, not a coda/codabot sample.

## Config Load and D78 Evidence

- `D78oWQu6` ended as a normal rated `180+2` blitz draw by agreement against `Bot1nokk`, rating diff `+1`.
- Pre-restart `/api/account/playing` check returned `active_count=0`.
- LaunchAgent PID changed from `28441` to `78929`.
- Post-restart log confirmed startup, engine configuration check, account login, and Lichess connection.
- Post-restart `/api/account/playing` check returned `active_count=0`.
- Latest aggregate result state is `45` draws, `21` losses, `4` unknown, and `1` win.
- Overall scored rating impact is now `-67` over `54` games.
- Bullet remains `-66` over `32` scored games; blitz improves to `-1` over `22` scored games.
- Initial outgoing challenge verification after PID `78929` startup:
  - `16:42:01`: `blitz_probe` used `180+2` (`3+2`) against `cinder-bot`; declined.
  - `16:43:10`: default matchmaking used `60+1` (`1+1`) against `SF_Bot1nok`; canceled.
  - Log scan found no outgoing `120+1`/`2+1` challenge after PID `78929` startup.

## Local Runtime Config

- Ignored `config.yml` and `.config-history/config.yml` remain aligned.
- Bot-vs-bot polyglot selection is `best_move`; human selection remains `uniform_random`.
- Bot black bullet/blitz book depth remains disabled at `0`.
- Matchmaking default pool is locally changed to probe `60+1` and `90+1`; `120+1` entries were removed after the `PxsslsQe` loss.
- `blitz_probe` override remains active for `180/240/300` base with `+2/+3` increments.
- `coda_bot` and `codabot` are now present in local ignored challenge and matchmaking blocklists.
- Incoming challenge `max_base` is locally changed from `120` to `90`.
- The current LaunchAgent process `78929` was started after these local config changes.

## Runtime Actions

- Performed one safe idle LaunchAgent restart after `/api/account/playing` returned `active_count=0`.
- Runtime PID changed from `91127` to `39567`.
- Post-restart checks confirmed reconnect and idle state.
- Performed a later safe idle LaunchAgent restart after `/api/account/playing` again returned `active_count=0`.
- Runtime PID changed from `39567` to `28441`.
- Post-restart checks confirmed reconnect and idle state.
- No restart was performed after the `120+1` exposure reduction because `/api/account/playing` returned `active_count=1` for `D78oWQu6`.
- Performed a later safe idle LaunchAgent restart after `D78oWQu6` ended and `/api/account/playing` returned `active_count=0`.
- Runtime PID changed from `28441` to `78929`.
- Post-restart checks confirmed reconnect and idle state.
- This closeout pass performed one non-waiting `/api/account/playing` check and got `active_count=0`.
- No additional restart was attempted.

## Closeout State

- Current tracked branch head before this documentation update: `8218779 Verify post-restart challenge controls`.
- `8218779` was already aligned with `origin/lc0+stockfish`; the previous credential-store warnings did not leave the branch behind.
- Worktree had no tracked modifications before this closeout update.
- Only unrelated untracked local paths were present: `.DS_Store`, `.agents/`, `docs/api/`, `fastchess/`, `lc0/`, and `refs/`.
- The latest documented live process remains PID `78929`, started after the coda/codabot blocklist and `120+1` exposure reduction.
- The current stop/pass handoff should not be treated as goal completion; it is a documentation and state handoff.

## Evidence State

- Latest aggregate: `71` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact: `-67` over `54` scored games.
- Bullet is the clear leak: `-66` over `32` scored games.
- Blitz is slightly negative: `-1` over `22` scored games.
- Worst current opponent/control watchlist starts with `coda_bot | bullet | 120+1`: risk `9`, `3` losses, rating `-15`.
- Second actionable opponent/control watchlist item is `codabot | bullet | 60+1`: risk `5`, `1` loss, `1` lower-rated/rating-negative draw, rating `-8`.
- New repeated opening leak strengthened: Ruy Lopez Open structures as black, especially `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`.
- `Ruy Lopez: Open, Classical Defense | black | bullet | 120+1` is now W-D-L `0-0-3`, score `0.0%`.
- Previous white bullet `1.d4` Nimzo leak was mitigated by deterministic bot book selection, but fresh post-change bullet evidence still needs review.

## Stop Decision

- Do not mark the optimization goal complete.
- Before any future restart, re-check active games; do not wait on an active game just to complete documentation.
- Confirm `coda_bot` and `codabot` are not accepted/challenged after the PID `28441` restart.
- After the restart evidence is available, analyze whether bullet losses shift from `coda_bot/codabot` toward another repeated opponent/control/opening cluster.
- The next non-blind behavior change candidate was applied locally: reduce exposure to `120+1` black-side Ruy Lopez Open by removing outgoing `120` matchmaking bases and lowering incoming `challenge.max_base` to `90`.
- This latest config change is live in PID `78929`; outgoing challenge verification has started cleanly, and incoming `120+1` challenge rejection remains to be observed.
- If a low-risk config change is needed next, prefer reducing exposure to leaking bullet controls/opponents over changing blitz, because blitz probe evidence is currently much less negative than bullet.
