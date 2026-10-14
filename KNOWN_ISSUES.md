# Known issues

- `tests/test_zprocess.py` `HeartbeatTests` may still fail intermittently on macOS when the machine is idle: their `ScriptedHeartbeatServer` runs in the pytest process, which App Nap can throttle, while real parents now opt out of it (`HeartbeatServer`, b7fa8af). Suspected, not reproduced since the fix.
- A full suite run on 2026-10-13 once ended in a native crash dump with no test summary; an identical rerun passed. Cause unknown. A macOS crash report from 2026-10-11 shows a SIGSEGV in libzmq's own I/O thread (`zmq::io_thread_t::in_event`), possibly the same.
