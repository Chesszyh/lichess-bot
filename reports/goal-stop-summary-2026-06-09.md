# Goal Stop Summary

## Scope

- Covers tracked work from `9124fdd` through `4779fe0`, plus this M8 follow-up pass.
- Goal state is not complete: bullet/blitz are not stable at `3080`.
- No heavy local engine experiments were run during an active game in this stop pass.
- Game `KZlP9dMr` was active during the first stop pass and was deliberately not waited on or analyzed, per stop request.
- Later continuation first did not wait for the active game; after it finished, a separate API check returned idle and the bot was safely restarted.
- This closeout pass did not wait on any game or make another runtime change.
- Game `M8ZpgJQe` was active or at least unresolved in local evidence during this pass and was deliberately not waited on or analyzed, per the latest continuation request.

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
- Later applied a local ignored config change to reduce `60+1` exposure, making incoming fast challenges `90+1` only and the default outgoing bullet pool `90+1` only.
- Later safely restarted LaunchAgent `org.chesszyh987.lichess-bot`; runtime PID changed from `78929` to `54477`.
- Later documented post-restart `blitz_probe` evidence: game `2ACAIGvE`, rated `300+2` blitz against `friendlybot_1700`, ended as a normal draw.
- Latest aggregate was refreshed from `71` to `72` rated fast games after `2ACAIGvE`.
- Latest observed unresolved game before this closeout was `M8ZpgJQe`, rated `180+3` blitz as black against `friendlybot_1700`, started from `blitz_probe`.
- Added `reports/bullet-90-plus-1-black-exposure-2026-06-09.md` to document the current reachable default bullet leak after `60+1` and `120+1` exposure reductions.
- Later `M8ZpgJQe` ended as a normal rated `180+3` blitz black loss by mate, rating `-5`.
- Added `reports/m8zpgjqe-blitz-black-ruy-loss-2026-06-09.md` and refreshed the aggregate from `72` to `73` rated fast games.
- Later narrowed the ignored local `blitz_probe` config to `300+2`/`300+3` only and restarted LaunchAgent from PID `54477` to `33763`.
- Confirmed commit `8218779` is present on both local `lc0+stockfish` and `origin/lc0+stockfish`.
- Confirmed commit `d67e3bf` is present on both local `lc0+stockfish` and `origin/lc0+stockfish`.
- This closeout pass only updates documentation; no runtime code, engine config, ignored local config, restart, or heavy local engine experiment was performed.

## Post-Pause Modification Summary

- Documentation was extended from the previous stop summary through the post-restart challenge-control verification.
- Ignored runtime config was changed to block `coda_bot`/`codabot` in incoming and outgoing paths.
- Ignored runtime config was changed to reduce `120+1` exposure by removing outgoing `120` bases and setting incoming `challenge.max_base` to `90`.
- Two safe idle LaunchAgent restarts loaded the blocklist and then the `120+1` exposure reduction; no restart was done while `D78oWQu6` was active.
- Fresh evidence added one `120+1` bullet loss sample, one `180+2` blitz draw sample, and two clean outgoing post-restart challenge-control checks.
- Fresh later evidence added the `60+1` exposure reduction, a safe restart into PID `54477`, and one `300+2` blitz draw sample.
- The later `M8ZpgJQe` result added one `180+3` blitz black loss and confirms black Open Ruy exposure is now visible in blitz as well as bullet.
- The latest reachable bullet slice is `90+1`, with black-side rating impact worse than the aggregate `90+1` slice; no behavior change was applied from this evidence alone.
- No tracked runtime code was changed in this post-pause interval; all committed changes are reports.

## Post-Closeout Modification Audit

- Baseline after the first stop summary (`1272542`) to current pre-pass head (`d67e3bf`) includes only tracked report updates.
- Files changed in that interval:
  - `reports/blitz-matchmaking-probe-2026-06-09.md`
  - `reports/bot-game-analysis-recent-fast-2026-06-09.md`
  - `reports/bullet-60-plus-1-exposure-reduction-2026-06-09.md`
  - `reports/coda-bot-bullet-blocklist-2026-06-09.md`
  - `reports/goal-stop-summary-2026-06-09.md`
  - `reports/ruy-lopez-open-1201-black-leak-2026-06-09.md`
- Commits in that interval:
  - `258bfa8` clarified that stopped/active games were excluded from conclusions.
  - `0d96dc5` documented the local `coda_bot`/`codabot` blocklist decision.
  - `d37c5d5` documented the blocklist restart and the Ruy Lopez `120+1` black leak.
  - `1ae59f3` documented pending `120+1` exposure reduction while a game was active.
  - `34fcc97` documented safe restart and aggregate refresh after `D78oWQu6`.
  - `8218779` documented post-restart challenge-control verification.
  - `2e0d220` documented the previous closeout state.
  - `a4eeadc` documented the `60+1` bullet exposure reduction and safe restart.
  - `d67e3bf` documented the post-change `300+2` blitz draw and aggregate refresh.
- Narrow baseline after the previous closeout commit (`2e0d220`) to current pre-pass head (`d67e3bf`) includes only three report files:
  - `reports/blitz-matchmaking-probe-2026-06-09.md`
  - `reports/bot-game-analysis-recent-fast-2026-06-09.md`
  - `reports/bullet-60-plus-1-exposure-reduction-2026-06-09.md`
- Runtime/config changes in the narrow interval were ignored local config only: default bullet exposure was reduced from `60+1`/`90+1` to `90+1` only, then loaded by safe idle restart.
- No tracked Python code, tests, engine binaries, opening books, or generated runtime artifact paths were intentionally changed.

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
- Matchmaking default pool is locally changed to `90+1` only; `120+1` entries were removed after the `PxsslsQe` loss and `60+1` entries were removed after the later exposure-reduction pass.
- `blitz_probe` override is now locally narrowed to `300` base with `+2/+3` increments.
- `coda_bot` and `codabot` are now present in local ignored challenge and matchmaking blocklists.
- Incoming challenge `min_base` and `max_base` are locally set to `90`.
- The current LaunchAgent process `33763` was started after these local config changes and the later `blitz_probe` narrowing.

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
- Performed a later safe idle LaunchAgent restart after the `60+1` exposure reduction.
- Runtime PID changed from `78929` to `54477`.
- Post-restart checks confirmed reconnect, loaded `challenge.min_base == 90`, loaded `challenge.max_base == 90`, and idle state.
- This closeout pass performed non-waiting local evidence checks only; latest local log evidence for `M8ZpgJQe` remained `status: started`.
- Performed a later restart after `M8ZpgJQe` ended and `blitz_probe` was narrowed to `300+2`/`300+3`.
- A later immediate pre-restart `/api/account/playing` check timed out; post-restart `/api/account/playing` returned `post_restart_active_count=0`.
- Runtime PID changed from `54477` to `33763`.
- Post-restart config log confirmed `blitz_probe.challenge_initial_time == [300]`.
- First outgoing challenge after PID `33763` used default rated bullet `90+1` against `Moment-That-Inspires`; it was canceled unanswered and produced no game.
- No additional restart was attempted.

## Closeout State

- Current tracked branch head before this documentation update: `4779fe0 Document 90 plus 1 black bullet exposure`.
- `4779fe0` was already aligned with `origin/lc0+stockfish`; the previous credential-store warnings did not leave the branch behind.
- Worktree had no tracked modifications before this closeout update.
- Only unrelated untracked local paths were present: `.DS_Store`, `.agents/`, `docs/api/`, `fastchess/`, `lc0/`, and `refs/`.
- The latest documented live process remains PID `33763`, started after the coda/codabot blocklist, `120+1` exposure reduction, `60+1` exposure reduction, and `blitz_probe` narrowing.
- The current stop/pass handoff should not be treated as goal completion; it is a documentation and state handoff.

## Evidence State

- Latest aggregate: `73` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact: `-72` over `55` scored games.
- Bullet is the clear leak: `-66` over `32` scored games.
- Blitz is now negative: `-6` over `23` scored games.
- Worst current opponent/control watchlist starts with `coda_bot | bullet | 120+1`: risk `9`, `3` losses, rating `-15`.
- Second actionable opponent/control watchlist item is `codabot | bullet | 60+1`: risk `5`, `1` loss, `1` lower-rated/rating-negative draw, rating `-8`.
- New repeated opening leak strengthened: Ruy Lopez Open structures as black, especially `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`.
- `Ruy Lopez: Open, Classical Defense | black | bullet | 120+1` is now W-D-L `0-0-3`, score `0.0%`.
- Previous white bullet `1.d4` Nimzo leak was mitigated by deterministic bot book selection, but fresh post-change bullet evidence still needs review.

## Stop Decision

- Do not mark the optimization goal complete.
- Before any future restart, re-check active games; do not wait on an active game just to complete documentation.
- `coda_bot` and `codabot` are blocked in the live ignored config; continue watching for any accepted/challenged leakage after PID `33763`.
- After the blocklist and exposure reductions, analyze whether bullet losses shift from `coda_bot/codabot` toward another repeated opponent/control/opening cluster.
- The `120+1` exposure reduction was applied locally by removing outgoing `120` matchmaking bases and lowering incoming `challenge.max_base` to `90`; that state was later superseded by the `60+1` reduction and remains loaded in PID `33763`.
- Incoming `120+1` rejection still remains to be observed directly.
- The later `60+1` exposure reduction is live in PID `33763`; outgoing default bullet verification should next confirm `90+1`, and incoming `60+1` rejection remains to be observed.
- `M8ZpgJQe` now confirms the black Open Ruy pattern in blitz; `blitz_probe` has been narrowed to longer `300+2`/`300+3` controls.
- Outgoing default bullet verification passed once after PID `33763`: default matchmaking used `90+1`, not `60+1` or `120+1`.
- The next `blitz_probe` verification target is an outgoing `300+2` or `300+3` challenge.
- If black Open Ruy losses recur at `300+2`/`300+3`, the next behavior candidate should be opening-specific design rather than another blind blocklist, book re-enable, or broad time-control filter.
- If a low-risk config change is needed next, prefer reducing exposure to leaking bullet controls/opponents over changing blitz, because blitz probe evidence is currently much less negative than bullet.
