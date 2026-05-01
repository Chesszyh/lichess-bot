# Repository Guidelines

## Project Structure & Module Organization

This is a Python lichess-bot repository. The entry point is `lichess-bot.py`, which delegates most behavior to modules in `lib/`. Tests live in `test_bot/` and follow the same behavioral areas as the runtime code, for example `test_engine_time_management.py`, `test_matchmaking.py`, and `test_config.py`. Default configuration is documented in `config.yml.default`; local `config.yml` is ignored and may contain secrets. Runtime artifacts are written to `lichess_bot_auto_logs/`, `game_records/`, `resource_records/`, and `runtime_state/`. Engine assets are under `engines/` (`books/`, `syzygy/`, `lc0/networks/`), while external references and local engine source trees such as `Stockfish/`, `lc0/`, and `refs/` should not be treated as core app modules.

## Build, Test, and Development Commands

Create and activate a virtual environment before development:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r test_bot/test-requirements.txt
```

Run the bot locally with:

```bash
python lichess-bot.py --config config.yml -l lichess_bot_auto_logs/run.log
```

Run checks used by CI:

```bash
pytest --log-cli-level=10
ruff check --config test_bot/ruff.toml
mypy --strict .
```

Use targeted tests while iterating, for example `pytest test_bot/test_engine_time_management.py -q`.

## Coding Style & Naming Conventions

Use Python 3.10+ syntax and keep lines at or below 127 characters, matching `test_bot/ruff.toml`. Prefer typed functions and explicit data flow; CI runs `mypy --strict`. Runtime modules use snake_case filenames and functions. Test functions should be named `test_<unit>__<behavior>` when useful for clarity. Keep comments short and reserve them for non-obvious logic.

## Testing Guidelines

Add or update tests for behavior changes, especially in matchmaking, challenge handling, time management, config defaults, and Lichess API stream handling. Prefer focused unit tests with small fake objects over live network tests. Do not require real bot tokens in automated tests; use environment-provided test tokens only where the existing suite already does.

## Commit & Pull Request Guidelines

Recent commits use concise imperative messages such as `Add exact movetime caps for fast games` and `Back off empty matchmaking pools`. Keep commits scoped and avoid mixing runtime behavior, config changes, and generated artifacts. Pull requests should explain the user-visible change, list verification commands run, link relevant issues or games/logs when debugging bot behavior, and call out any configuration or deployment impact.

## Security & Configuration Tips

Never commit real Lichess tokens. Keep secrets in `config.yml` or environment variables. If local bot config changes need private tracking, mirror them in `.config-history/` rather than the main repository.
