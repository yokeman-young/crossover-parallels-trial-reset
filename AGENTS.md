# AGENTS.md — contract for automated use

`trialreset` is designed to be driven by an agent with no human in the loop.

## Contract

- **Platform**: macOS. Bundle resolution via `CFBundleIdentifier`, launchd for watching.
- **Never interactive**: `block` without root prints the sudo command and exits 1; it does not prompt.
- **JSON surface**: add `--json` to any subcommand; exactly one JSON document on stdout.
- **Exit codes**: `0` ok, `1` verification failed / needs root, `2` app missing.
- **Idempotent**: `reset` is safe to repeat; `watch install` replaces the agent; `block` rewrites
  only its own marked lines.
- **Non-destructive by default**: `reset` backs up prefs to `~/.trialreset/<app>/backup/` (10 kept).

## Sequence

```bash
trialreset --json doctor
# assert apps.<key>.installed == true

trialreset --json reset <app> --dry-run
# assert delete_keys/set_dates non-empty; empty means schema changed → stop

trialreset --json reset <app>
# assert ok == true and actions contains backup + delete/shift

trialreset --json launch <app>
# assert opened != null

trialreset --json check <app>
# assert prefs.delete_keys empty (blob trial) or shift dates are recent (timestamp trial)

trialreset --json watch install <app>
# assert ok == true and plist exists
```

## Assertion table

| Step | Assert | Meaning |
| --- | --- | --- |
| doctor | `apps.<key>.installed` | app present |
| reset --dry-run | `delete_keys` or `set_dates` non-empty | schema still recognised |
| reset | `actions[]` has `backup:` | prefs backed up |
| reset | no `WARN: keys still present` | reset took effect |
| check | `prefs.delete_keys == []` | licence blob cleared |
| watch install | `paths` covers prefs + Info.plist | watcher won't miss updates |

## Failure modes

| Symptom | Cause | Action |
| --- | --- | --- |
| exit 2, `app not installed` | wrong bundle id / not installed | run `list`; report |
| reset ok but keys return immediately | service wrote them back | add the helper process to `procs` |
| `needs_root: true` | running `block` unprivileged | report the printed command to the operator |
| watcher fired but nothing changed | app was running (by design) | expected; reset applies at next launch |
| trial still expired after reset | vendor tracks server-side | report; blocking only hides the verdict |

## Safety

- Only touch `~/Library/Preferences`, `~/Library/Caches`, declared caches and processes.
- Never patch inside an app bundle.
- Never delete a preference domain wholesale; only declared keys/prefixes.
- Respect `~/.trialreset/<app>/disabled` — it means the operator bought a licence.
