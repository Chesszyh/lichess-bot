# Opponent Rate-Limit Retry for 2026-06-08

Bot: `ilovecatgirl`

## Evidence

- At 2026-06-08 22:39:33 CST, outgoing matchmaking triggered on schedule after the configured 15-minute cadence.
- It found `308` online bots, `62` suitable opponents, and preferred `20` opponents rated at least `3000`.
- The selected opponent was `Moment-That-Inspires`.
- Lichess rejected the challenge because that opponent had already played `100` bot-vs-bot games today, returning
  `opponent_is_rate_limited: True` and a timeout until 2026-06-09 06:52:24 UTC.
- The bot did not have an active game and `/api/account/playing` returned `0` ongoing games.

## Change

Outgoing matchmaking now treats opponent-side bot-vs-bot daily limits as retryable inside the same matchmaking cycle:

- Cool down the rate-limited opponent for the Lichess-provided timeout.
- Retry up to `3` total opponent candidates in the same cycle.
- Preserve the existing global cadence and bot-side rate-limit backoff.

This increases useful outgoing attempts without shortening `matchmaking.challenge_timeout` or increasing pressure on the
Lichess challenge endpoint.

## Verification

- `pytest test_bot/test_matchmaking.py::test_challenge__retries_next_candidate_when_opponent_is_rate_limited -q`
- `pytest test_bot/test_matchmaking.py -q`
- `mypy --strict lib/matchmaking.py`
- `ruff check --config test_bot/ruff.toml lib/matchmaking.py --select B007,ARG005,ANN001`
- `git diff --check -- lib/matchmaking.py test_bot/test_matchmaking.py`
