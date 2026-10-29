# Known issues

- `tests/test_zprocess.py` `HeartbeatTests` may fail intermittently on macOS when the machine is idle: their `ScriptedHeartbeatServer` runs in the pytest process, which App Nap can throttle, while a real `HeartbeatServer` opts out of it.
- A full suite run has once ended in a native crash dump with no test summary, and an identical rerun passed. Cause unknown; a macOS crash report shows a SIGSEGV in libzmq's own I/O thread (`zmq::io_thread_t::in_event`), possibly the same.
- On Windows, heartbeat failure in `HeartbeatClient.mainloop()` (`process_tree.py`) terminates the child through `os.kill(pid, SIGTERM)` without running `KillLock`'s handler, even while the lock is held, so a child can be killed mid-write under `h5_lock`'s or NI_DAQmx's kill lock. Inherited from upstream; not run on Windows.
