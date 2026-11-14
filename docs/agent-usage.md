# Agent recipes

```bash
# environment
trialreset --json doctor | jq '.apps'

# plan → apply → verify
trialreset --json reset parallels --dry-run | jq '{delete_keys, kill, caches}'
trialreset --json reset parallels | jq '.actions'
trialreset --json check parallels | jq '.prefs.delete_keys'   # []

# launch flow (reset only when not running)
trialreset --json launch parallels | jq '{ok, opened, actions}'

# watcher
trialreset --json watch install parallels | jq '{ok, paths}'
trialreset --json watch status parallels | jq '{installed, loaded}'

# network layer (needs root; the CLI prints the command when it does not have it)
trialreset block parallels
sudo $(trialreset --json block parallels | jq -r '.command' | sed 's/^sudo //')
```

Waiting for a state change instead of sleeping:

```bash
before=$(trialreset --json check parallels | jq '.prefs.delete_keys | length')
for _ in $(seq 1 60); do
  now=$(trialreset --json check parallels | jq '.prefs.delete_keys | length')
  [ "$now" -lt "$before" ] && break
  sleep 2
done
```
