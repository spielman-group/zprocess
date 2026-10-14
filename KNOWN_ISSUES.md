# Known issues

- `tests/test_zprocess.py` `HeartbeatTests` may still fail intermittently on macOS when the machine is idle: their `ScriptedHeartbeatServer` runs in the pytest process, which App Nap can throttle, while real parents now opt out of it (`HeartbeatServer`, b7fa8af). Suspected, not reproduced since the fix.
