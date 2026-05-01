# Deployment Guide

This guide is for deploying this fork on a new machine with a new Lichess bot account.

Do not run the same bot account from two machines at the same time. The Bot API event stream is account-scoped; two live processes can race on challenge events, game streams, moves, and cancellations. Use one Lichess bot account per deployed bot.

## 1. Prepare The Account

Create a separate Lichess account for the new bot, then create an OAuth token for that account.

Required token scopes:

- `bot:play` for Bot API games
- `challenge:write` for outgoing challenges
- `team:write` for joining teams
- `tournament:write` for joining arena tournaments

Recommended scopes:

- `team:read` if the bot will inspect private team membership

Keep the token out of git. `config.yml` is ignored by this repository, but avoid pasting tokens into tracked docs, scripts, logs, or commits.

## 2. Clone And Install

```bash
git clone https://github.com/Chesszyh/lichess-bot.git
cd lichess-bot
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pytest
```

Run the test suite before editing runtime settings:

```bash
.venv/bin/python -m pytest -q
```

## 3. Build Or Install Stockfish

This bot expects a UCI engine. For best results, build Stockfish locally on the target machine.

Example:

```bash
git clone https://github.com/official-stockfish/Stockfish.git
cd Stockfish/src
make -j profile-build ARCH=apple-silicon
./stockfish bench
```

Use the correct `ARCH` for the new machine. On non-Apple hardware, check Stockfish's build docs and choose the best supported architecture.

## 4. Create `config.yml`

Start from the default config:

```bash
cp config.yml.default config.yml
```

Edit at least these fields:

```yaml
token: "<new bot token>"
url: "https://lichess.org/"

engine:
  dir: "/absolute/path/to/Stockfish/src"
  name: "stockfish"
  protocol: "uci"
  ponder: true
  uci_ponder: true
  uci_options:
    Threads: 3
    Hash: 768

challenge:
  concurrency: 3
  accept_bot: true
  only_bot: false
  min_rating: 2500
  max_rating: 4000

matchmaking:
  allow_matchmaking: true
  allow_during_games: true
  opponent_min_rating: 2500
  opponent_max_rating: 4000
  challenge_mode: "random"
  challenge_filter: "fine"

arena:
  enabled: true
  teams:
    - "1-bot-tournaments"
    - "lichess-bots"
  join_teams: true
```

Tune `Threads`, `Hash`, and `challenge.concurrency` for the machine:

- 10 CPU cores / 16 GB RAM: `concurrency: 3`, `Threads: 3`, `Hash: 768` is a reasonable baseline.
- Smaller machines: start with `concurrency: 1-2`, `Threads: 2-3`, `Hash: 512`.
- Larger machines: increase gradually and watch `resource_records/resource_usage.csv`.

Avoid setting `Threads * concurrency` far above physical CPU cores. It usually reduces move quality under load.

## 5. Optional Books And Tablebases

Opening books are configured under:

```yaml
engine:
  polyglot:
    enabled: true
    book:
      standard:
        - "/absolute/path/to/book.bin"
```

For this fork, bot-vs-bot play is usually strongest with a high-quality deterministic book, while human games can use more random book selection for variety.

Tablebases are optional. If endgame tablebase behavior looks suspicious, keep lichess-bot tablebase move selection disabled and let Stockfish search:

```yaml
engine:
  online_moves:
    online_egtb:
      enabled: false
  lichess_bot_tbs:
    syzygy:
      enabled: false
```

Stockfish can still use local Syzygy internally if configured through UCI options and the files are available.

## 6. First Run

Validate the engine and token:

```bash
.venv/bin/python lichess-bot.py --config config.yml -l lichess_bot_auto_logs/run.log
```

Expected startup log:

- `Checking engine configuration ...`
- `Engine configuration OK`
- `Welcome <bot username>!`
- `You're now connected to https://lichess.org/ and awaiting challenges.`

If the token check fails, verify the token belongs to the bot account and includes `bot:play`.

## 7. macOS LaunchAgent

For unattended operation on macOS, create:

`~/Library/LaunchAgents/org.<owner>.lichess-bot.plist`

Template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>org.example.lichess-bot</string>
  <key>WorkingDirectory</key>
  <string>/absolute/path/to/lichess-bot</string>
  <key>ProgramArguments</key>
  <array>
    <string>/absolute/path/to/lichess-bot/.venv/bin/python</string>
    <string>-u</string>
    <string>/absolute/path/to/lichess-bot/lichess-bot.py</string>
    <string>--config</string>
    <string>/absolute/path/to/lichess-bot/config.yml</string>
    <string>-l</string>
    <string>/absolute/path/to/lichess-bot/lichess_bot_auto_logs/run.log</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/absolute/path/to/lichess-bot/lichess_bot_auto_logs/launchd.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>/absolute/path/to/lichess-bot/lichess_bot_auto_logs/launchd.stderr.log</string>
</dict>
</plist>
```

Load and inspect:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/org.example.lichess-bot.plist
launchctl kickstart -k gui/$(id -u)/org.example.lichess-bot
launchctl print gui/$(id -u)/org.example.lichess-bot
tail -f lichess_bot_auto_logs/run.log
```

Before restarting, confirm no active game:

```bash
curl -fsS -H "Authorization: Bearer $LICHESS_BOT_TOKEN" \
  https://lichess.org/api/account/playing | python -m json.tool
```

Restart only when `nowPlaying` is empty unless you intentionally want to abandon games.

## 8. Runtime Checks

Check process state:

```bash
ps -o pid,ppid,%cpu,%mem,rss,command -ax | rg 'lichess-bot|stockfish'
tail -n 100 lichess_bot_auto_logs/run.log
```

Check resource usage:

```bash
tail -n 20 resource_records/resource_usage.csv
```

Check current games:

```bash
curl -fsS -H "Authorization: Bearer $LICHESS_BOT_TOKEN" \
  https://lichess.org/api/account/playing | python -m json.tool
```

Common healthy signs:

- Engine startup says `Using N threads` with the configured value.
- Main log periodically says `Next challenge will be created after ...`.
- Outgoing challenges are not repeated every few seconds when no opponent is available.
- Arena integration may log team join requests or arena join attempts when eligible arenas exist.

## 9. Two-Bot Research Setup

For agent-driven self-improvement, use separate bot accounts:

- Bot A: account, token, machine, repo checkout, config, logs.
- Bot B: separate account, token, machine, repo checkout, config, logs.

Do not share `runtime_state`, `resource_records`, `game_records`, or `config.yml` between bots.

A practical loop:

1. Each bot plays public high-rated bots and periodic private matches against the other research bot.
2. Export PGNs and resource records daily.
3. Classify losses: time management, opening, shallow search, disconnection, engine crash, or simply stronger opponent.
4. Let the assigned agent propose changes.
5. Run tests.
6. Restart only when `nowPlaying` is empty.
7. Record the change, result window, and rollback plan.

Avoid optimizing only for the other local bot. Keep public-pool games in the evaluation set to reduce overfitting.

## 10. Safety Notes

- Respect Lichess bot limits, including the daily bot-vs-bot cap.
- Do not spam challenges. Use cooldowns and backoff.
- Keep tokens private.
- Keep one running process per bot account.
- Commit code changes to git. Keep machine-specific `config.yml` private.
