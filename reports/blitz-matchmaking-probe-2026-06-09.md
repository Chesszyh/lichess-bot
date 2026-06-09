# Blitz Matchmaking Probe

## Scope

- Objective: keep improving both bullet and blitz bot-vs-bot performance toward `3080`.
- Runtime config files changed locally:
  - `config.yml`
  - `.config-history/config.yml`
- Tracked code changed: none.

## Evidence

- The active local matchmaking config was only selecting bullet-style controls:
  - `challenge_initial_time`: repeated `60`, `90`, and `120`
  - `challenge_increment`: only `1`
- Recent post-threshold evidence contained one fresh rated bullet game:
  - `oi6DonOy` vs `Cheszter`, rated bullet `90+1`, draw, `+2`
- No fresh post-threshold blitz games existed, so the current setup could not produce the blitz evidence required by the objective.
- `engine.blitz_time_management.enabled` is already `true`, so blitz-specific time-management config is available once matchmaking creates blitz games.

## Change

Added one local matchmaking override:

```yaml
matchmaking:
  overrides:
    blitz_probe:
      challenge_initial_time:
      - 180
      - 240
      - 300
      challenge_increment:
      - 2
      - 3
      challenge_days:
      - null
```

The existing default bullet pool remains unchanged. With one override plus the default path, the matcher can now sample blitz controls while still preserving bullet coverage.

## Validation

- Parsed both local runtime config files successfully.
- Confirmed `blitz_probe.challenge_initial_time == [180, 240, 300]`.
- Confirmed `blitz_probe.challenge_increment == [2, 3]`.
- Confirmed `blitz_probe.challenge_days == [None]`.

## Deployment Note

Because `config.yml` is ignored and read at startup, the LaunchAgent must be restarted while idle before the new override affects matchmaking. Restart must only happen after checking:

- no active game in `/api/account/playing`,
- no mid-game log tail,
- LaunchAgent process is running and idle.

## Post-Restart Samples

- `04:15:54`: `blitz_probe` selected rated `240+3` as black against `BlueMoonBot`; the outgoing challenge was not accepted and was canceled.
- `04:26:30`: `blitz_probe` selected rated `240+3` as black against `Void_Bot`; the game was aborted before any move because White was inactive, so it gives no playing-strength evidence.
- `04:36:56`: `blitz_probe` selected rated `180+2` as white against `CupchessBot` (`3025`); game `Q3bzjLhX` ended as a normal draw by agreement with bot rating diff `+1`.
- `12:50:42`: `blitz_probe` selected rated `180+2` as white against `Cheszter` (`3026`); game `vcfAgx1S` ended as a normal draw by repetition with bot rating diff `+1`.
- `08:24:54`: `blitz_probe` selected rated `180+2` as white against `Bot1nokk` (`3041`); game `D78oWQu6` ended as a normal draw by agreement with bot rating diff `+1`.
- `16:54:37`: `blitz_probe` selected rated `240+2` as black against `Bot1nokk` (`3040`); the outgoing challenge was unanswered and canceled.
- `17:05:12`: `blitz_probe` selected rated `240+2` as white against `styx_reckless` (`3025`); the outgoing challenge was declined.
- `17:06:15`: `blitz_probe` selected rated `300+2` as white against `friendlybot_1700` (`3005`); game `2ACAIGvE` ended as a normal draw.
- The refreshed fast aggregate now covers `72` games and has blitz at `-1` rating over `22` scored games, while bullet is `-66` over `32` scored games.

## Current Decision

- No runtime config change from these samples.
- The `180+2` and `300+2` draws are positive evidence for keeping the blitz probe active.
- The weaker current evidence is bullet-side, especially black `120+1`/`90+1` losses and repeated Ruy Lopez Open structures, so the next investigation should focus there rather than further changing blitz matchmaking.
