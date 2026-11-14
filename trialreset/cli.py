"""trialreset — generic macOS trial/state reset toolkit.

Every subcommand accepts --json and prints exactly one JSON document:
stable exit codes (0 ok, 1 verification failed, 2 unsupported / not installed).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
import plistlib
import shutil
import subprocess
import sys

from . import core
from .adapters import SPECS, get as get_spec

EXIT_OK, EXIT_FAIL, EXIT_UNSUPPORTED = 0, 1, 2


# --------------------------------------------------------------------- helpers

def emit(payload: dict, as_json: bool, human: str = "") -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif human:
        print(human)


def prefs_path(spec) -> str | None:
    if not spec.domain:
        return None
    return os.path.expanduser(f"~/Library/Preferences/{spec.domain}.plist")


def snapshot(spec) -> dict:
    return core.read_defaults(spec.domain) if spec.domain else {}


def running(spec) -> list[str]:
    pids = []
    for pattern in spec.procs:
        code, out = core.run(["pgrep", "-f", pattern])
        if code == 0:
            pids.extend(out.split())
    return sorted(set(pids))


def do_reset(spec, force: bool = False, dry_run: bool = False) -> dict:
    plan = core.plan_reset(spec, snapshot(spec))
    actions: list[str] = []
    if not plan.app:
        return {"ok": False, "error": "app not installed", "actions": []}
    if not plan.delete_keys and not plan.set_dates:
        return {"ok": False, "error": "no matching keys", "actions": [], "warnings": plan.warnings}

    if dry_run:
        return {"ok": True, "dry_run": True, **plan.to_dict(), "actions": []}

    backup = core.backup_prefs(prefs_path(spec) or "", os.path.expanduser(f"~/.trialreset/{spec.key}/backup"))
    if backup:
        actions.append(f"backup: {backup}")

    killed = core.kill_processes(spec.procs)
    actions += [f"killed: {p}" for p in killed]
    if killed:
        _dt.time.sleep(1)

    for key in plan.delete_keys:
        if core.delete_key(spec.domain, key):
            actions.append(f"deleted: {key}")
    for key, iso in plan.set_dates.items():
        if core.write_datetime(spec.domain, key, _dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")):
            actions.append(f"shifted: {key} -> {iso}")

    for cache in core.expand_caches(spec.caches):
        try:
            if os.path.isdir(cache):
                shutil.rmtree(cache)
            else:
                os.remove(cache)
            actions.append(f"cleared: {cache}")
        except OSError as exc:
            actions.append(f"failed to clear {cache}: {exc}")

    after = snapshot(spec)
    remaining = [k for k in after if spec.delete_key_prefixes and any(k.startswith(p) for p in spec.delete_key_prefixes)]
    if remaining:
        actions.append(f"WARN: keys still present after reset: {remaining}")

    _dt.datetime.utcnow()
    state_dir = os.path.expanduser(f"~/.trialreset/{spec.key}")
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "last-reset"), "w") as fh:
        fh.write(str(int(_dt.datetime.now().timestamp())))
    with open(os.path.join(state_dir, "version"), "w") as fh:
        fh.write(str(core.app_version(plan.app) or "unknown"))
    return {"ok": True, **plan.to_dict(), "actions": actions}


# ------------------------------------------------------------------ subcommands

def cmd_list(args):
    rows = []
    for key, spec in sorted(SPECS.items()):
        rows.append({
            "key": key,
            "name": spec.name,
            "installed": bool(core.locate_app(spec)),
            "version": core.app_version(core.locate_app(spec)),
            "running": bool(running(spec)),
        })
    emit({"apps": rows}, args.json, "\n".join(
        f"{r['key']:<10} {r['name']:<18} {'installed' if r['installed'] else 'missing':<9} {r['version'] or '':<10} {'running' if r['running'] else ''}"
        for r in rows))
    return EXIT_OK


def cmd_check(args):
    spec = get_spec(args.app)
    app = core.locate_app(spec)
    data = {
        "app": spec.key,
        "path": app,
        "version": core.app_version(app),
        "running": running(spec),
        "prefs": {
            "domain": spec.domain,
            "delete_keys": sorted(k for k in snapshot(spec) if spec.delete_key_prefixes and any(k.startswith(p) for p in spec.delete_key_prefixes)),
            "shift_keys": {k: str(snapshot(spec).get(k)) for k in spec.shift_datetime_keys},
        },
    }
    emit(data, args.json, json.dumps(data, ensure_ascii=False, indent=2) if not args.json else "")
    return EXIT_OK if app else EXIT_UNSUPPORTED


def cmd_reset(args):
    spec = get_spec(args.app)
    result = do_reset(spec, force=args.force, dry_run=args.dry_run)
    emit(result, args.json, json.dumps(result, ensure_ascii=False, indent=2) if not args.json else "")
    return EXIT_OK if result.get("ok") else EXIT_FAIL


def cmd_launch(args):
    """Reset (only when the app is not running), then open it."""
    spec = get_spec(args.app)
    app = core.locate_app(spec)
    if not app:
        emit({"ok": False, "error": "app not installed"}, args.json, f"{spec.name} not installed")
        return EXIT_UNSUPPORTED
    if running(spec):
        core.run(["open", "-a", app])
        emit({"ok": True, "action": "activated", "app": app}, args.json, f"{spec.name} already running; activated")
        return EXIT_OK
    result = do_reset(spec)
    core.run(["open", "-a", app])
    result.update({"opened": app})
    emit(result, args.json, json.dumps(result, ensure_ascii=False, indent=2) if not args.json else "")
    return EXIT_OK if result.get("ok") else EXIT_FAIL


def watch_paths(spec) -> list[str]:
    paths = [os.path.expanduser(p) for p in spec.watch_paths]
    app = core.locate_app(spec)
    if app:
        paths.append(os.path.join(app, "Contents", "Info.plist"))
    return [p for p in dict.fromkeys(paths) if os.path.exists(p)]


def agent_plist_path(spec) -> str:
    return os.path.expanduser(f"~/Library/LaunchAgents/local.trialreset.{spec.key}.plist")


def cmd_watch(args):
    spec = get_spec(args.app)
    label = f"local.trialreset.{spec.key}"
    plist_path = agent_plist_path(spec)

    if args.action == "status":
        code, _ = core.run(["launchctl", "print", f"gui/{os.getuid()}/{label}"])
        data = {"app": spec.key, "installed": os.path.exists(plist_path), "loaded": code == 0,
                "paths": watch_paths(spec)}
        emit(data, args.json, json.dumps(data, indent=2))
        return EXIT_OK

    if args.action == "uninstall":
        core.run(["launchctl", "bootout", f"gui/{os.getuid()}/{label}"])
        if os.path.exists(plist_path):
            os.remove(plist_path)
        emit({"ok": True, "removed": plist_path}, args.json, f"removed {label}")
        return EXIT_OK

    paths = watch_paths(spec)
    if not paths:
        emit({"ok": False, "error": "no watch paths exist"}, args.json, "nothing to watch")
        return EXIT_FAIL
    payload = {
        "Label": label,
        "ProgramArguments": [sys.executable, "-m", "trialreset.cli", "reset", spec.key, "--quiet"],
        "WatchPaths": paths,
        "RunAtLoad": True,
        "StandardOutPath": os.path.expanduser(f"~/.trialreset/{spec.key}/agent.log"),
        "StandardErrorPath": os.path.expanduser(f"~/.trialreset/{spec.key}/agent.log"),
    }
    os.makedirs(os.path.dirname(os.path.expanduser(f"~/.trialreset/{spec.key}/agent.log")), exist_ok=True)
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)
    with open(plist_path, "wb") as fh:
        plistlib.dump(payload, fh)
    core.run(["launchctl", "bootout", f"gui/{os.getuid()}/{label}"])
    core.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", plist_path])
    emit({"ok": True, "plist": plist_path, "paths": paths}, args.json, f"installed {label} watching {len(paths)} paths")
    return EXIT_OK


def cmd_block(args):
    spec = get_spec(args.app)
    if not spec.domains:
        emit({"ok": True, "domains": [], "note": "adapter declares no endpoints"}, args.json, "nothing to block")
        return EXIT_OK
    if os.geteuid() != 0:
        cmd = f"sudo {' '.join([sys.executable, '-m', 'trialreset.cli'] + sys.argv[1:])}"
        emit({"ok": False, "needs_root": True, "domains": spec.domains, "command": cmd},
             args.json, f"run with sudo:\n  {cmd}")
        return EXIT_FAIL
    marker = f"# trialreset:{spec.key}"
    hosts = "/etc/hosts"
    shutil.copy2(hosts, f"/etc/hosts.trialreset.{int(_dt.datetime.now().timestamp())}")
    lines = [l for l in open(hosts).read().splitlines() if marker not in l]
    if not args.unblock:
        host_list = list(spec.domains) + (["update.parallels.com"] if args.with_updates else [])
        lines += [f"0.0.0.0 {d} {marker}" for d in host_list]
    open(hosts, "w").write("\n".join(lines) + "\n")
    core.run(["dscacheutil", "-flushcache"])
    core.run(["killall", "-HUP", "mDNSResponder"])
    emit({"ok": True, "blocked": [] if args.unblock else spec.domains}, args.json,
         "unblocked" if args.unblock else f"blocked {len(spec.domains)} domains")
    return EXIT_OK


def cmd_doctor(args):
    facts = {"platform": sys.platform, "python": sys.version.split()[0], "apps": {}}
    for key, spec in SPECS.items():
        app = core.locate_app(spec)
        facts["apps"][key] = {
            "installed": bool(app),
            "version": core.app_version(app),
            "prefs_keys": len(snapshot(spec)),
            "agent_loaded": core.run(["launchctl", "print",
                                      f"gui/{os.getuid()}/local.trialreset.{key}"])[0] == 0,
        }
    emit(facts, args.json, json.dumps(facts, indent=2))
    return EXIT_OK


# ------------------------------------------------------------------------ main

def build():
    p = argparse.ArgumentParser(prog="trialreset", description="macOS trial/state reset toolkit")
    p.add_argument("--json", action="store_true", help="machine readable output")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("list", parents=[common], help="show adapters and install state")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("check", parents=[common], help="inspect one app")
    s.add_argument("app", choices=sorted(SPECS))
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("reset", parents=[common], help="clear or shift trial state")
    s.add_argument("app", choices=sorted(SPECS))
    s.add_argument("--force", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_reset)

    s = sub.add_parser("launch", parents=[common], help="reset if needed, then open the app")
    s.add_argument("app", choices=sorted(SPECS))
    s.set_defaults(func=cmd_launch)

    s = sub.add_parser("watch", parents=[common], help="install/uninstall the launchd watcher")
    s.add_argument("action", choices=["install", "uninstall", "status"])
    s.add_argument("app", choices=sorted(SPECS))
    s.set_defaults(func=cmd_watch)

    s = sub.add_parser("block", parents=[common], help="block account/licence endpoints (root)")
    s.add_argument("app", choices=sorted(SPECS))
    s.add_argument("--unblock", action="store_true")
    s.add_argument("--with-updates", action="store_true")
    s.set_defaults(func=cmd_block)

    s = sub.add_parser("doctor", parents=[common], help="environment + adapter status")
    s.set_defaults(func=cmd_doctor)
    return p


def main(argv=None) -> int:
    args = build().parse_args(argv)
    if getattr(args, "quiet", False):
        args.json = True
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
