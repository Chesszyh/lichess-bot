# Bot White Book Best-Move Config

## Scope

- Runtime config changed: `config.yml`
- Private mirror changed: `.config-history/config.yml`
- Tracked evidence report: this file
- Target: rated bot-vs-bot bullet/blitz when the bot plays white

## Evidence Basis

- `reports/white-bullet-opening-leak-2026-06-09.md` identified a repeated white bullet leak:
  - `1.d4` in recent white `60+1` produced three losses and one draw.
  - `1.e4` in recent white `60+1` produced four draws and no losses.
  - The three losses were all Nimzo-Indian structures from the shared prefix `d4 Nf6 c4 e6 Nc3 Bb4 e3 O-O`.
- Current bot-vs-bot book is `engines/books/rodent.bin`.
- `rodent.bin` has equal top first-move weight for `e4` and `d4`, so `uniform_random` keeps re-entering the losing `1.d4` cluster.
- `chess.polyglot.Reader.find()` returns `e4` as the deterministic best first move from `rodent.bin`.

## Applied Config

The bot opponent-specific polyglot profile was changed from:

```yaml
selection: uniform_random
```

to:

```yaml
selection: best_move
```

The human opponent profile remains `uniform_random`.

The bot black profile remains unchanged and still disables local book for bullet/blitz:

```yaml
color_selection:
  black:
    max_depth_by_speed:
      bullet: 0
      blitz: 0
```

## Expected Effect

- Bot-vs-bot games as white should prefer `1.e4` instead of randomly choosing between equal top `e4` and `d4`.
- This reduces immediate recurrence risk for the known white `60+1` Nimzo loss cluster.
- This is intentionally config-only and reversible if future `1.e4` samples become a new leak.

## Verification

- Parsed both `config.yml` and `.config-history/config.yml`.
- Confirmed:
  - human selection: `uniform_random`
  - bot selection: `best_move`
  - bot black bullet book depth: `0`
  - `rodent.bin` deterministic best first move: `e4`

## Runtime Note

This change requires a safe idle restart before affecting new games.
