# HANDSOFF

This is the handoff state for the ThinkPad Stockfish `lichess-bot` tuning goal as of 2026-06-09 UTC.

## Current Runtime State

- Main repo branch: `only-stockfish`.
- Main repo latest pushed handoff before this final documentation update: `21dc400 Keep avoid-exited book lines under engine control`.
- Private config mirror latest committed handoff before the Polyglot lockout update: `.config-history` `45ea95a Mirror the Breyer book exit privately`.
- `.config-history` has no remote configured; private mirror commits are local only.
- Last checked service state after the Polyglot lockout update: `lichess-bot.service` active under PID `3063380`, started at `2026-06-09 09:47:04 UTC`.
- Restart safety check before the Polyglot lockout update showed no active `Stockfish/src/stockfish` game child. The service was restarted safely at `2026-06-09 09:47:05 UTC`; startup logs showed `Engine configuration OK`, `Welcome NeuroSoCute!`, connected to Lichess, and awaiting challenges.
- The running process has loaded `offer_draw_clock_advantage_accept_min_score_cp: 1`, `dynamic_nobot_cooldown_max_minutes: 360`, the full Ruy Lopez `...h3` book-exit avoid list, and bot-specific `book_exit_lockout_plies: 6` from `config.yml`.
- State-load verification after restart showed `maia3-79m_2600` source `nobot` capped from a 2036 expiry to `2026-06-09T15:04:32Z`.
- Final snapshot at `2026-06-09 09:56 UTC` showed post-deploy game `VRq462VD` ended by draw agreement at `09:55:20`, logs showed `Process Freed. Count: 0`, no `Stockfish/src/stockfish` child remained, and the next challenge was scheduled after `2026-06-09 09:58:20 UTC`. This is only a snapshot; recheck before any future restart.
- After committing this handoff, the main worktree should be clean except expected untracked local assets such as `Stockfish/`.

Do not restart while a game is active or while a Stockfish child process exists. Check first:

```bash
ps -eo pid,ppid,lstart,cmd | rg 'lichess-bot.py|Stockfish/src/stockfish|stockfish|tail -n 0 -F lichess_bot_auto_logs/run.log|timeout .*tail'
tail -n 160 lichess_bot_auto_logs/run.log
systemctl --user status lichess-bot.service --no-pager -l
```

## Current Live Policy

- Accept only `bullet` and `blitz`; rapid is no longer accepted.
- Prefer bullet first, then try the configured blitz fallback when the bullet pool is empty.
- Keep rated target-band games at `3080+`:
  - `challenge.min_rating: 3080`
  - `matchmaking.opponent_min_rating: 3080`
  - `matchmaking.preferred_opponent_min_rating: 3080`
  - `matchmaking.blitz_fallback.preferred_opponent_min_rating: 3080`
- Keep `config.yml` ignored/private. Mirror every private runtime config change in `.config-history/config.yml` and commit inside `.config-history`.

## Changes Made During This Tuning Pass

### Matchmaking And Pool Control

- Stopped accepting rapid after the active game completed; live policy is bullet/blitz only.
- Raised incoming and outgoing opponent floors to the 3080 target band.
- Preferred bullet for outgoing challenges while allowing blitz fallback when no bullet candidate is available.
- Added `try_overrides_on_empty_pool` so a failed bullet pool can try the blitz fallback in the same cycle.
- Shortened ordinary decline and unanswered outgoing challenge cooldowns to reduce sparse-pool dead time.
- Added source-aware matchmaking cooldown metadata and target-band blocker logs.
- Added `legacy_unknown_cooldown_max_minutes: 360` to cap stale source-unknown cooldowns without deleting configured long blocks.
- Added `dynamic_nobot_cooldown_max_minutes: 360` to cap dynamic `nobot` cooldowns without changing configured blocklists. This followed the `2026-06-09 08:57 UTC` sparse-pool log where `maia3-79m_2600` was a 3101 blitz target-band blocker with source `nobot` and about 10 years remaining.
- Added `draw_cooldown_minutes: 30` for repeated drawn fast bot pairings.
- Added retry timing that waits until soon-expiring target-band cooldowns clear instead of always sleeping the full no-candidate interval.

### Draw And Repetition Handling

- Added `draw_or_resign.offer_draw_min_rating` and set the live floor to `3080`, so normal draw offers do not lock in below-target results.
- Added clock-edge draw-offer guards for bullet/blitz:
  - Current live `offer_draw_clock_advantage_opponent_ms: 45000`
  - Current live `offer_draw_clock_advantage_min_ms: 30000`
  - Current live `offer_draw_clock_advantage_accept_min_score_cp: 1`
- Extended the same clock-edge guard to zero-WDL Lichess EGTB draw offers. This closes the path where tablebase equality could still offer a draw while the opponent was under practical bullet clock pressure.
- Added repetition guard clock-edge override so the bot can avoid repetition even against higher-rated opponents when the opponent is low on clock:
  - `repetition_guard.clock_advantage_override_opponent_ms: 40000`
  - `repetition_guard.clock_advantage_override_min_ms: 30000`
- Added `repetition_guard.avoid_opponent_immediate_claim: true` to filter moves that let the opponent immediately claim threefold, while preserving the score-loss cap.
- Enforced repetition root-move filters after engine search, so a returned move outside the allowed root set is replaced before play.
- Kept repetition avoidance score-bounded with `repetition_guard.max_score_loss_cp: 150`.

### Opening And Book Control

- Stopped relying on deep online opening explorer guidance for bot games. The live private config keeps Lichess opening explorer as a shallow `max_depth: 2` fallback, then uses local Polyglot or Stockfish search.
- Fixed weighted-random book selection so `min_weight` filtering happens before sampling.
- Bot-vs-bot Polyglot profile currently uses `weighted_random`, `min_weight: 50`, `normalization: max`, `max_depth: 12`.
- Added `engine.polyglot.book_exit_lockout_plies` with default `0`; the live bot-specific profile uses `6`, so after `avoid_moves` exhausts every current book move, Polyglot is skipped for the next six plies before book use can resume.
- Added bot-specific `avoid_moves` for repeated or losing book branches:
  - Skip `Bb5` after `e4 e5 Nf3 Nc6` to avoid repeated Berlin Wall draw channels.
  - Skip all current book moves after `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3` (`Na5`, `Nb8`, `Bb7`, `h6`, `Re8`, `Nd7`, `Be6`). This stops forcing the repeated Breyer path and intentionally exits the book at that exact position instead of falling through to lower-weight book moves.
  - Skip `Ng5` after `e4 e5 Nf3 Nc6 Bc4 Nf6` to leave the Two Knights repetition channel.
  - Skip `b4` after `e4 e5 Nf3 Nc6 Bc4 Bc5` after `ezGWI9wS`; the live book then selects `c3`.

## Key Evidence From Recent Games

- `ezGWI9wS`: high-signal loss. White stayed in book through `e4 e5 Nf3 Nc6 Bc4 Bc5 b4 ... Bg5`; first engine search after book was about `-0.88` and `31.0%` winrate, and the bot lost `-5`. This led to the `b4` bot-book filter.
- `IBkQluUF` and `ol8VgVif`: repeated Two Knights `Ng5` family draws; led to the bot-book `Ng5` filter.
- `VT7zOio9` and related Ruy Lopez Chigorin draws: led to the Chigorin `Na5` sidestep.
- `Q1poOSgG`, `Wp8SbY5A`, `nSLk3U9v`: repeated Berlin Wall draw channels; led to the `Bb5` filter.
- `J7nJYTTZ` and `xzMGfX4n`: draw agreements/offers despite large clock edge; led to clock-aware draw-offer guards.
- `iCfhUIsj`: target-band bullet draw against `Cheszter` after Lichess EGTB returned `wdl: 0`; the bot offered a draw with about 52s vs 16s, showing EGTB-zero draw offers bypassed the normal draw clock guard. This led to the EGTB guard and the live 30s minimum clock-edge threshold.
- `UJlBX5Z5`: target-band bullet loss against `TakticproChess`. The book left the bot around `-0.51` / 43.6% after a Breyer line and later stayed around `-0.3` to `-0.5`; later repeated Breyer-family draws made this part of the signal for the full `...h3` book-exit avoid list.
- `8K19ZtZc`: target-band bullet loss against `Cheszter`. The bot declined a draw offer around 65s vs 33s with repeated exact `0.0` evaluations, then drifted into a losing endgame and resigned at EGTB `wdl: -2`. This led to `offer_draw_clock_advantage_accept_min_score_cp: 1`, so exact `0.0` opponent draw offers are no longer rejected solely on clock edge.
- `i6JbiFiR`: another target-band bullet loss against `Cheszter` from the English Opening: Agincourt Defense after the same unpatched clock-policy window. Treat it as evidence that Cheszter/English black games need continued watch, but do not stack a second speculative opening change on top of the draw-policy fix yet.
- `CFFJyFaz`: live validation of the `8K19ZtZc` draw-refusal fix. The bot first skipped proactive normal draw offers while holding a huge clock edge, then accepted Black's draw offer because the latest bot score was exactly `0 cp`, below the live `1 cp` acceptance threshold.
- `VRq462VD`: additional post-lockout-deploy validation of the clock-edge draw policy against `Cheszter`. The bot skipped proactive normal draw offers while White had about 13-16s and the bot had about 124-127s, filtered a move that allowed an immediate threefold claim, then accepted White's draw offer because the latest bot score was exactly `0 cp`, below the live `1 cp` acceptance threshold. This game did not validate the Ruy Lopez `...h3` lockout path.
- `N1AY97NU`, `h1EjQzfE`, `2R78e4KP`, `Yl9L44Tx`, and `dums3X5c`: repeated target-band draws from the same Ruy Lopez Closed Breyer book path after `...h3 Nb8 d4 Nbd7 ...`; `UJlBX5Z5` was a target-band loss from the same family. This led to filtering all current book moves at the `...h3` tabiya so the bot exits book and lets Stockfish search.
- `yiF82zTL`: validated that the full `...h3` avoid list forces the first no-book exit; at the tabiya, Stockfish searched and chose `9...Bb7` with about `-0.41`, `45.5%`, depth 24. It also exposed an adjacent failure mode: after engine-chosen `...Bb7`, Polyglot immediately re-entered for `...Re8` and `...Bf8`, reaching another drawish Ruy Lopez Closed/Flohr path. This led to the six-ply `book_exit_lockout_plies` follow-up.
- `nSLk3U9v` and `xUcwqJsv`: repetition with large clock edge; led to repetition clock override and opponent immediate-claim filtering.
- `o1u2AXZc`: showed hard repetition avoidance can choose losing alternatives; keep the score-loss cap.
- `KvLfR0la`: showed root-move filtering had to be enforced after search.

## Verification Already Run

Fresh verification from the EGTB-zero draw guard and 30s live draw-clock threshold:

```text
git diff --check: exit 0
19 passed in 0.46s
config.yml offer_draw_clock_advantage_opponent_ms=45000
config.yml offer_draw_clock_advantage_min_ms=30000
.config-history/config.yml offer_draw_clock_advantage_opponent_ms=45000
.config-history/config.yml offer_draw_clock_advantage_min_ms=30000
```

Fresh verification from the 8K19ZtZc draw-refusal fix and report tool:

```text
6 passed in 0.44s
ruff touched files: All checks passed!
git diff --check: exit 0
config.yml offer_draw_clock_advantage_accept_min_score_cp=1
.config-history/config.yml offer_draw_clock_advantage_accept_min_score_cp=1
recent_bot_game_report.py flags i6JbiFiR, 8K19ZtZc, and UJlBX5Z5 as priority losses
service restarted at 2026-06-09 08:49:03 UTC, PID 2531217
startup logs showed Engine configuration OK, Welcome NeuroSoCute!, and awaiting challenges
live game CFFJyFaz accepted Black's draw offer at exact 0 cp despite clock edge because 0 cp < 1 cp
```

Fresh verification from the dynamic `nobot` cooldown cap:

```text
69 passed in 0.42s
ruff touched files: All checks passed!
git diff --check: exit 0
config.yml dynamic_nobot_cooldown_max_minutes=360
.config-history/config.yml dynamic_nobot_cooldown_max_minutes=360
service restarted at 2026-06-09 09:04:29 UTC, PID 2680528
runtime_state maia3-79m_2600 source=nobot expires_at=2026-06-09T15:04:32.203579+00:00
09:07 matchmaking log shows maia3-79m_2600 source=nobot remaining=357m
```

Fresh verification from the Ruy Lopez `...h3` Breyer book-exit sidestep:

```text
config.yml avoid list=Na5,Nb8,Bb7,h6,Re8,Nd7,Be6
.config-history/config.yml avoid list=Na5,Nb8,Bb7,h6,Re8,Nd7,Be6
real book moves at the tabiya=Na5,Nb8,Nd7,h6,Be6,Bb7,Re8
get_book_move=None after filtering all current book moves
service restarted at 2026-06-09 09:21:07 UTC, PID 2807672
startup logs showed Engine configuration OK, Welcome NeuroSoCute!, and awaiting challenges
```

Fresh verification from the Polyglot avoid-exhausted lockout:

```text
6 passed in 0.34s
28 passed, 1 xfailed in 6.81s
ruff touched files: All checks passed!
git diff --check: exit 0
config.yml book_exit_lockout_plies=6
.config-history/config.yml book_exit_lockout_plies=6
real config/book check: first_get_book_move=None, lockout_until=23, follow_up_get_book_move=None
service restarted at 2026-06-09 09:47:05 UTC, PID 3063380
startup logs showed Engine configuration OK, Welcome NeuroSoCute!, and awaiting challenges
```

Targeted draw-refusal/report test command:

```bash
.venv/bin/python -m pytest \
  test_bot/test_engine_time_management.py::test_search__does_not_accept_normal_draw_when_opponent_is_near_flagging \
  test_bot/test_engine_time_management.py::test_search__accepts_zero_score_draw_offer_despite_clock_edge_when_configured \
  test_bot/test_engine_time_management.py::test_search__does_not_offer_normal_draw_when_opponent_is_near_flagging \
  test_bot/test_external_moves.py::test_get_online_move__egtb_zero_respects_clock_edge \
  test_bot/test_config.py::test_insert_default_values__draw_clock_guard_defaults \
  test_bot/test_recent_bot_game_report.py -q
```

Targeted EGTB test command:

```bash
.venv/bin/python -m pytest \
  test_bot/test_external_moves.py::test_get_online_move__egtb_zero_respects_clock_edge \
  test_bot/test_engine_time_management.py::test_search__does_not_accept_normal_draw_when_opponent_is_near_flagging \
  test_bot/test_engine_time_management.py::test_search__does_not_offer_normal_draw_when_opponent_is_near_flagging \
  test_bot/test_config.py \
  test_bot/test_external_moves.py::test_get_book_move__avoid_moves_filters_configured_san_line -q
```

Fresh verification from the final Evans branch change:

```text
config.yml avoided=b2b4 book_move=c2c3
.config-history/config.yml avoided=b2b4 book_move=c2c3
17 passed in 0.34s
git diff --check: exit 0
```

Targeted test command:

```bash
.venv/bin/python -m pytest test_bot/test_config.py \
  test_bot/test_external_moves.py::test_get_book_move__avoid_moves_filters_configured_san_line \
  test_bot/test_external_moves.py::test_get_book_move__weighted_random_respects_min_weight -q
```

Known verification debt is unchanged:

- Full `ruff` and `mypy` are still blocked by pre-existing complexity and typing failures documented in `docs/BOT_OPTIMIZATION_HISTORY.md`.
- No completed live game has yet validated the latest `b4 -> c3` replacement after the service restart.
- No completed live game has yet validated the six-ply Ruy Lopez `...h3` book-exit lockout after the latest service restart. `yiF82zTL` validated the first no-book exit but exposed immediate adjacent book re-entry before the lockout existed.
- No completed live game has yet validated the EGTB-zero draw-offer guard. `VRq462VD` is additional validation of the normal draw-offer clock edge and exact-0-cp acceptance path.
- Avoid heavy local Stockfish experiments while the live bot is running.

## Next Best Work

- Watch the next `e4 e5 Nf3 Nc6 Bc4 Bc5 c3` bot game. If the first engine search is still materially negative, prefer a narrower branch change such as moving toward `O-O` or lowering bot book depth in that branch before changing global book randomness.
- Watch the next Ruy Lopez `...h3` bot game. The bot should have no book move at that exact position, then skip Polyglot for the next two bot turns under the live six-ply lockout before book use can resume.
- Watch the next target-band equal EGTB ending. The bot should not offer a draw if the opponent is below 45s and the bot has at least a 30s clock edge.
- Keep watching target-band opponent draw offers in repeated exact `0.0` endings. `CFFJyFaz` validated the current rule once; future games should continue accepting only when the latest bot score is below the live 1 cp threshold.
- Keep `UJlBX5Z5` as evidence for possible Breyer/opening-depth tuning if the new `...h3` book exit still produces early negative first-search positions.
- Watch Cheszter English Opening: Agincourt Defense games (`8K19ZtZc`, `i6JbiFiR`). If another early negative or losing endgame appears, prefer a narrow black-side `1.c4 e6 2.g3 d5` book/explorer adjustment over broad book randomization.
- Track whether the 3080 floor makes volume too sparse. If it does, prefer a temporary, explicitly logged `3060-3079` fallback window over permanently reopening 3000-3079.
- Keep using the target-band blocker logs to separate real pool scarcity from stale cooldowns, rate limits, and mode declines.
- Watch whether `maia3-79m_2600` or other dynamic `nobot` target-band blockers become retryable after the 360-minute cap; configured blocklists should still remain long-lived.
- Keep prioritizing losses and low-signal draws against bots over broad engine tuning.
- Clean up `engine_wrapper.py` complexity and fake-engine test typing before larger strategy changes.

## Useful Commands

Recent rated bullet/blitz games:

```bash
curl -fsSL -H 'Accept: application/x-ndjson' \
  'https://lichess.org/api/games/user/NeuroSoCute?max=30&rated=true&perfType=bullet,blitz&moves=true&pgnInJson=false&tags=true&clocks=true&evals=false&opening=true&sort=dateDesc' \
  | jq -r '[.id,.createdAt,.lastMoveAt,.speed,.status,(if .players.white.user.name=="NeuroSoCute" then "white" else "black" end),(.players.white.user.name),(.players.white.rating|tostring),(.players.white.ratingDiff|tostring),(.players.black.user.name),(.players.black.rating|tostring),(.players.black.ratingDiff|tostring),(.opening.name // ""),(.moves|split(" ")[0:60]|join(" "))] | @tsv'
```

Book check for the latest Evans sidestep:

```bash
.venv/bin/python - <<'PY'
import chess, chess.polyglot
from lib.config import load_config

cfg = load_config('config.yml')
book = cfg.engine.polyglot.book.standard[0]
board = chess.Board()
for san in 'e4 e5 Nf3 Nc6 Bc4 Bc5'.split():
    board.push_san(san)

with chess.polyglot.open_reader(book) as reader:
    print(sorted([(board.san(e.move), e.move.uci(), e.weight) for e in reader.find_all(board)], key=lambda x: x[2], reverse=True))
PY
```

Before restart:

```bash
ps -eo pid,ppid,lstart,cmd | rg 'lichess-bot.py|Stockfish/src/stockfish|stockfish'
tail -n 160 lichess_bot_auto_logs/run.log
```
