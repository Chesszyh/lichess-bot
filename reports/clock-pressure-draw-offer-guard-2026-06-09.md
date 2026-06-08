# Clock-Pressure Draw Offer Guard

Date: `2026-06-09 CST`

## Summary

- Added an optional guard for the high-rated draw-offer acceptance rule.
- When enabled, the bot will not accept a high-rated opponent's draw offer if our clock is safe and the opponent is near flagging.
- Enabled locally with `own_clock >= 30000 ms` and `opponent_clock <= 15000 ms`.
- Mirrored the private config change in `.config-history/config.yml`.
- No local engine analysis was run.

## Evidence

The active-control report now identifies clock-pressure draw leaks where the bot had a large clock edge but the game still ended drawn:

- `Worst-ai vs ilovecatgirl - ml4y9CRN.pgn`: bot `122s`, opponent `4s`, rating `-3`.
- `AggressiveStockfish vs ilovecatgirl - CFYHfwEL.pgn`: bot `93s`, opponent `13s`, rating `-1`.
- `DefenchessOfficial vs ilovecatgirl - mmJFwmO6.pgn`: bot `88s`, opponent `11s`, rating `-1`.
- `friendlybot_1700 vs ilovecatgirl - nX47W72Z.pgn`: bot `96s`, opponent `10s`, rating `+0`.

Several listed opponents are already blocked, but the pattern indicates that accepting stable-equal draw offers while the opponent is under severe clock pressure can leave rating on the table.

## Verification

- Watched `test_search__does_not_accept_high_rated_draw_offer_when_opponent_is_in_clock_pressure` fail before implementation.
- `pytest test_bot/test_engine_time_management.py::test_search__accepts_high_rated_draw_offer_in_stable_equal_endgame test_bot/test_engine_time_management.py::test_search__does_not_accept_high_rated_draw_offer_when_opponent_is_in_clock_pressure test_bot/test_engine_time_management.py::test_search__does_not_accept_high_rated_draw_rule_for_lower_rated_opponent test_bot/test_engine_time_management.py::test_search__does_not_accept_incoming_draw_via_generic_offer_rule -q` -> `4 passed`.
- `pytest test_bot/test_engine_time_management.py -q` -> `33 passed`.
- YAML parse check passed for `config.yml.default`, `config.yml`, and `.config-history/config.yml`.
- `mypy --strict lib/engine_wrapper.py` still reports existing union/override errors in `lib/engine_wrapper.py`, `homemade.py`, and `test_bot/homemade.py`; the clock-pressure helper has no remaining strict-type error.
- `ruff check --config test_bot/ruff.toml lib/engine_wrapper.py test_bot/test_engine_time_management.py` still reports existing complexity and test fake docstring/unused-argument findings.
