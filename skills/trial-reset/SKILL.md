---
name: trial-reset
description: Reset the local trial state of CrossOver or Parallels Desktop on macOS before launch, install a launchd watcher and optional endpoint blocking, then verify. Use when asked to reset/extend a trial, make an app "fresh" each launch, or wire a pre-launch reset hook.
---

# Trial reset (macOS)

Operate this repository: https://github.com/yokeman-young/crossover-parallels-trial-reset

## When to use

- "reset CrossOver/Parallels trial", "每次启动都重置", "make it think it's a fresh install"
- user wants a launch hook or watcher for trial state
- user wants to know why a reset "didn't take"

Not for: patching vendor binaries, licence key generation, server-side trial re-issuing.

## Prerequisites

```bash
python3 --version            # >= 3.9
python3 -m trialreset.cli --json doctor
```

If `trialreset` is not importable, run from the repo root with `python3 -m trialreset.cli`.

## Procedure

1. **Inventory** — confirm the app and adapter exist:

   ```bash
   python3 -m trialreset.cli --json list
   ```

   Assert `apps[].installed == true` for the target key (`crossover` or `parallels`).

2. **Plan** — never apply blind:

   ```bash
   python3 -m trialreset.cli --json reset <key> --dry-run
   ```

   Assert `delete_keys` (blob model) or `set_dates` (timestamp model) is non-empty.
   Empty plan = preference schema changed: stop and report the snapshot from `check`.

3. **Apply**:

   ```bash
   python3 -m trialreset.cli --json reset <key>
   ```

   Assert `ok == true` and `actions` contains a `backup:` entry, then `deleted:` / `shifted:`.

4. **Verify**:

   ```bash
   python3 -m trialreset.cli --json check <key>
   ```

   Blob model → `prefs.delete_keys == []`; timestamp model → `prefs.shift_keys` timestamps are
   within the last few minutes.

5. **Launch flow** (optional launcher app that resets before opening):

   ```bash
   ./scripts/build-launcher.sh <key>
   open "$HOME/Applications/<Name> (Trial Reset).app"
   ```

6. **Watcher** (safety net; skips while the app is running):

   ```bash
   python3 -m trialreset.cli --json watch install <key>
   python3 -m trialreset.cli --json watch status <key>
   ```

7. **Network layer** (only if the vendor checks licence server-side):

   ```bash
   python3 -m trialreset.cli block <key>        # prints the sudo command when unprivileged
   sudo python3 -m trialreset.cli block <key>
   ```

## Assertions

| check | expected |
| --- | --- |
| `list` | `apps[<key>].installed` is true |
| `reset --dry-run` | `delete_keys` or `set_dates` non-empty |
| `reset` | `ok` true, `actions` has `backup:` |
| `check` | `prefs.delete_keys` empty / shift keys recent |
| `watch status` | `installed` and `loaded` true |

## Failure handling

| symptom | meaning | do |
| --- | --- | --- |
| exit 2 `app not installed` | wrong key or not installed | run `list`, report |
| keys reappear right after reset | background service wrote them | add the helper process to `procs` in the adapter |
| reset works but trial still expired | vendor tracks it server-side | report; blocking only hides the verdict |
| `block` prints a sudo command | not root | hand the command to the operator |
| watcher fired, nothing changed | app was running (by design) | expected; applies next launch |

## Safety

- Backups land in `~/.trialreset/<key>/backup/` (10 kept) — restore from there.
- Never patch inside an app bundle; only user prefs, caches and declared processes.
- If `~/.trialreset/<key>/disabled` exists, the operator bought a licence — leave it alone.
