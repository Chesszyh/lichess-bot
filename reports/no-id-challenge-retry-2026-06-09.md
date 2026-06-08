# No-ID Challenge Retry

Date: `2026-06-09 CST`

## Summary

- Treat challenge endpoint responses without an `id` as target-specific retryable failures.
- Keep the existing six-hour target cooldown for the failed opponent.
- Retry another suitable opponent in the same matchmaking cycle, bounded by the existing retry limit.
- No local engine analysis was run.

## Evidence

Recent logs show outgoing challenges that returned no usable challenge id and therefore consumed a matchmaking cycle without producing a game:

- `PiFishBob`: `Challenge id is None`.
- `Bot1nokk`: `Challenge id is None`.
- `Classic_BOT-v2`: `Challenge id is None`.
- `PZChessBot`: `Challenge id is None`.
- `stockfish1threadtest`: `Challenge id is None`.
- `stockfish2threadtest`: `Challenge id is None`.

The existing code already cooled down the target for six hours, but did not retry another candidate in the same cycle unless the response matched a known structured error. This delayed rated bullet/blitz game creation and reduced useful live-game sampling.

## Verification

- `pytest test_bot/test_matchmaking.py -q`: `44 passed`.
- `mypy --strict lib/matchmaking.py`: success.
- `py_compile lib/matchmaking.py test_bot/test_matchmaking.py`: success.
- `ruff check --config test_bot/ruff.toml --select RUF034 test_bot/test_matchmaking.py`: success.
- `ruff check --config test_bot/ruff.toml lib/matchmaking.py`: still fails on pre-existing `choose_opponent` complexity (`C901`, `PLR0912`), unrelated to this change.
