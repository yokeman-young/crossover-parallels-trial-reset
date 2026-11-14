from .base import AppSpec

SPEC = AppSpec(
    key="crossover",
    name="CrossOver",
    bundle_id="com.codeweavers.CrossOver",
    app_paths=["~/Applications/CrossOver.app", "/Applications/CrossOver.app"],
    procs=["CrossOver.app/Contents/MacOS/CrossOver"],
    domain="com.codeweavers.CrossOver",
    # Trial is a timestamp: shifting the start date back makes the trial look fresh.
    shift_datetime_keys={"FirstRunDate": 3, "SULastCheckTime": 3},
    watch_paths=[
        "~/Library/Preferences/com.codeweavers.CrossOver.plist",
    ],
    notes="Timestamp-based trial. No account/server component observed.",
)
