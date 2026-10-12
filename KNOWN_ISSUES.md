# Known issues

- `tests/test_zprocess.py` `HeartbeatTests` fail intermittently on macOS only, after sleep or long idle and sometimes while awake: heartbeat timings stretch, so processes die or survive off schedule. Suspected macOS idle throttling (App Nap, timer coalescing); untested, try `caffeinate -i`.
