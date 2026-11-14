# Pitfalls

1. **`osascript … quit` hangs on Automation permission.** First run shows a TCC prompt; in a
   headless/agent context the call blocks forever. Use `pkill -f` instead (the kit does).
2. **An agent that resets must never kill a live session.** `watch install` runs with `--quiet`
   and the reset path skips when the app is running.
3. **cfprefsd caches — `plutil` is not enough.** Editing the plist on disk with `plutil -replace`
   is silently overwritten by the preference daemon on the next app launch (observed: expired date
   reverted to the cached value). Use `defaults write <domain> <key> -date …`, or kill cfprefsd.
   This is also how to *demo* an expired state: pause the watcher, `defaults write` an old date,
   launch the original icon.
4. **Dotted keys are not key paths.** `License.Flags` must be passed as one literal key name to
   `defaults`, not as nested `PlistBuddy` paths.
5. **IPv6 name cache.** `dig` bypasses `/etc/hosts`; verify blocking with `ping`/`curl`, and
   remember some apps resolve AAAA separately.
6. **Restart the service, not just the GUI.** Parallels keeps licence state in
   `prl_disp_service`; the GUI quitting is not enough.
7. **A reset wipes purchased activations too.** Set `~/.trialreset/<app>/disabled` after buying.
8. **Bundle IDs beat paths after updates.** Resolve by `CFBundleIdentifier`; app bundles move.
9. **launchd `WatchPaths` fires on mtime changes**, including writes made by the reset itself.
   Keep a short guard (the CLI's `last-reset` + launchd's own throttle) to avoid loops.
10. **App Management TCC** may block writes inside another app's bundle. Never patch inside the
    bundle; only touch user prefs and caches.
