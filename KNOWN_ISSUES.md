# Known issues

- A full suite run has once ended in a native crash dump with no test summary, and an identical rerun passed. Cause unknown; a macOS crash report shows a SIGSEGV in libzmq's own I/O thread (`zmq::io_thread_t::in_event`), possibly the same.
