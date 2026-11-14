from .base import AppSpec

SPEC = AppSpec(
    key="parallels",
    name="Parallels Desktop",
    bundle_id="com.parallels.desktop.console",
    app_paths=["/Applications/Parallels Desktop.app", "~/Applications/Parallels Desktop.app"],
    procs=[
        "Parallels Desktop.app/Contents/MacOS/prl_client_app",
        "prl_disp_service",
    ],
    domain="com.parallels.Parallels Desktop",
    # Licence blob lives in prefixed keys; deleting them returns the client to first-run.
    delete_key_prefixes=["License.", "WiConfig"],
    caches=["~/Library/Preferences/Parallels/*"],
    domains=[
        "account.parallels.com",
        "my.parallels.com",
        "licensing.parallels.com",
        "activation.parallels.com",
        "pcs.parallels.com",
    ],
    watch_paths=[
        "~/Library/Preferences/com.parallels.Parallels Desktop.plist",
        "/Applications/Parallels Desktop.app/Contents/Info.plist",
    ],
    notes="Licence-key based. Trial may also be tracked server-side; see docs/how-it-works.md.",
)
