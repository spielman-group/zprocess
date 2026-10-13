# zprocess deep pass

A planning document for the code-health campaign (`issues/code_health_campaign.md`
in the meta repo). It lists candidates for Ian's review, one section per step, and
is deleted when the pass is done. Nothing is changed until Ian has reviewed each
entry.

## Step 1: contract

What each existing test protects, for Ian's review. Marks:

- **keep**: protects a real behaviour, and fails when that behaviour breaks.
- **rename**: keep, under a name that states the behaviour.
- **fix**: the behaviour is real, but the test cannot be trusted to fail only
  when it breaks.
- **cut**: protects nothing worth keeping; the reason is given.

Upstream (chrisjbillington/zprocess) wrote 66 of the tests. The fork added 11:
the heartbeat tests from `PermissiveHeartBeat`, and one each for the
`ServerHangs`, `BaseException` and `start_daemon` fixes. All 77 are collected.

### Totals

- Test files: 4. `tests/output_redirection.py` and
  `tests/GUI_output_redirection.py` are manual demo scripts, not tests; they are
  for step 4.
- Tests: 77, and 18 subtests. Lines: 2127 in `tests/`.
- Marks: keep 58, rename 15, fix 4, cut 0.

### The heartbeat tests

Four heartbeat tests fail intermittently on macOS since the 27.0.1 update. The
suite passed in full on 2026-10-11 before the update, which the crash reports
date to that evening, and has failed on and off since. Run again with the machine in use, they passed three
times out of three: plain, under `caffeinate -i`, and under
`taskpolicy -t 0 -l 0`.

- **Verdict: the platform, exposed by the tests.** The heartbeat code is right;
  breaking it makes the tests fail as they should (below). macOS throttles
  timers in idle background processes, and on 27 it does so harder. These tests
  allow a fixed wall-clock budget of 2-3 s per heartbeat and an exit within 2-3 s,
  so a delayed timer reads as a missed or extra heartbeat.
- Checked in a scratch copy of `HeartbeatClient.mainloop`:
  - Dying on the first miss fails all four, and the reset test.
  - Never dying fails both "dies" tests and the kill-lock test.
  - Never resetting the count fails the missing-heartbeat "survives" test, the
    reset test and the kill-lock test.
  - So each fix-marked test does fail when its behaviour breaks; the trouble is
    only false failures.
- **Fix**: give the deadlines slack, and measure misses by count, not time. That
  is a test change only.
- `KNOWN_ISSUES.md` records the symptom until then.

### tests/test_zprocess.py

`RaiseExceptionInThreadTest`
- `test_can_raise_exception_in_thread`: an exception handed to
  `raise_exception_in_thread` is re-raised in another thread. **keep**.

`TypeCheckConvertTests`: what each message type a client or server may send. All
**keep**; together they protect the type rules users meet on every `zmq_get*`.
- `test_turns_None_into_empty_bytestring_raw`, `_multipart`: `None` is sent as
  empty bytes.
- `test_wraps_bytestring_into_list_multipart`: one bytestring is one frame.
- `test_accepts_bytes_raw`, `test_accepts_list_of_bytes_multipart`,
  `test_accepts_string_string`, `test_accepts_pyobj_pyobj`: valid data passes
  unchanged.
- `test_rejects_string_raw`, `test_rejects_string_multipart`,
  `test_rejects_pyobj_string`: the wrong type raises TypeError.
- `test_rejects_invalid_send_type`: an unknown dtype raises ValueError.

`ProcessClassTests`
- `test_process`: a child process echoes data to its parent, and its stdout,
  stderr, shell output, log records and rich prints reach the parent's output
  socket in order. **rename** →
  `test_a_child_echoes_data_and_its_output_reaches_the_parent`.

`ProcessTerminateTests`
- `test_terminate_ignores_local_wait_timeout`: `Process.terminate` does not leak
  `TimeoutExpired` when the child is slow to exit. **keep**.

`HeartbeatTests` (fork's)
- `test_subproc_lives_with_working_heartbeats`: a child whose heartbeats are
  answered keeps running. **keep**.
- `test_subproc_survives_missing_heartbeats_below_budget`: a child survives
  fewer unanswered heartbeats than allowed. **fix**: timing, as above.
- `test_subproc_dies_after_1_to_5_missing_heartbeats`: a child exits once its
  allowance of unanswered heartbeats is used. **fix**: timing.
- `test_subproc_survives_malformed_heartbeats_below_budget`: as above, for wrong
  replies. **fix**: timing.
- `test_subproc_dies_after_1_to_5_malformed_heartbeats`: as above, for wrong
  replies. **fix**: timing.
- `test_successful_heartbeat_resets_miss_counter`: an answered heartbeat clears
  the misses so far. **keep**.
- `test_configured_heartbeat_interval_controls_request_cadence`: the
  `heartbeat_interval` argument sets how often heartbeats are sent. **keep**.
- `test_subproc_survives_until_kill_lock_released`: a child holding its kill
  lock is not killed until it releases it. **keep**.
- `test_parent_correctly_responds_to_heartbeats`: the real parent heartbeat
  server echoes a heartbeat. **rename** →
  `test_the_parent_answers_a_childs_heartbeat`.

`EventTests`
- `test_events`: an event posted by a child reaches a waiter in the parent.
  **rename** → `test_an_event_posted_by_a_child_reaches_the_parent`.
- `test_external_broker`: the same, through an external event broker.
  **rename** → `test_events_pass_through_an_external_broker`.

`TaskTests`
- `test_cant_call_task_twice`: a task runs once. **keep**.
- `test_queue`: a task queue orders by due time, pops the earliest and cancels
  a task. **rename** → `test_task_queue_orders_pops_and_cancels_by_due_time`.

`StartDaemonTests` (fork's)
- `test_start_daemon`: a daemon starts detached, in its own session, with tkinter
  loaded. **rename** → `test_start_daemon_detaches_even_with_tkinter_loaded`.

`ClientServerTests`
- `test_invalid_dtype_server_raises_valueerror`,
  `test_invalid_dtype_sender_raises_valueerror`: an unknown dtype is refused.
  **keep**.
- `test_rep_server`: a REP server replies, and a handler's exception reaches the
  client. **rename** → `test_a_server_replies_and_returns_handler_exceptions`.
- `test_raw_server`: the same for raw bytes, under every way of naming the
  dtype. **rename** → `test_a_raw_server_replies_and_returns_handler_exceptions`.
- `test_pull_server`: a pull-only server takes data, refuses a reply and keeps
  running. **keep**.
- `test_customauth_backcompat`: a server that overrides `setup_auth` gets no
  `SecureContext`. **keep**.
- `test_unpicklable_response` (fork's): a reply that cannot be pickled reaches
  the client as an error, and the server keeps running. **keep**.
- `test_handler_raises_systemexit` (fork's): the same for a `SystemExit`.
  **keep**.
- `test_overlapping_requests_one_client` (fork's): two threads on one client do
  not deadlock. **keep**.

### tests/test_zlock_server.py

`ZLockServerTests`: the lock server's protocol, through a real server.
- `test_hello`, `test_protocol`: the server answers hello and its protocol
  version. **keep**.
- `test_uncontested_reader`, `test_uncontested_writer`: one client acquires and
  releases. **keep**.
- `test_multiple_readers`: readers share a lock. **keep**.
- `test_reader_then_writer`: a writer waits for a reader. **keep**.
- `test_waiting_writer_blocks_new_readers`: a waiting writer goes before later
  readers. **keep**.
- `test_concurrent_error`: two requests at once from one client are refused.
  **keep**.
- `test_change_mind`: a client told to retry may retry as a reader. **keep**.
- `test_absentee_acquire_release`: releasing a lock granted in absentia, before
  retrying, is refused. **keep**.
- `test_absentee_acquire_timeout`: a lock granted in absentia times out if the
  client never retries. **keep**.
- `test_timeout`: a held lock is released when its timeout expires. **rename** →
  `test_a_lock_is_released_when_its_timeout_expires`.
- `test_reentry`: a client may re-acquire its own lock, and must release it as
  often. **keep**.
- `test_reentrant_contending_writers`,
  `test_reentrant_reader_with_waiting_writer`: re-entry does not let a waiting
  writer in early. **keep**.
- `test_invalid_reentry`: a reader cannot re-enter as a writer. **keep**.
- `test_malformed_requests`: each malformed request gets its error, and NaN
  timeouts are refused. **keep**.
- `test_absentee_acquire`: a lock released while a client waits to retry is its
  on retrying. **keep**.
- `test_retry`: a client told to retry gets the lock once it is free. **rename**
  → `test_a_retrying_client_gets_the_lock_once_free`.
- `test_absent_give_up`: a client that does not retry in time loses its place.
  **keep**.
- `test_give_up_triggers`: a waiter giving up lets in exactly the waiters it
  should. **keep**.
- `test_locks_independent`: different keys are different locks. **keep**.

`ImplementationUnitTests`
- `test_lock_errors`: the server's `Lock` refuses invalid transitions. **keep**.
- `test_zlock_client_uses_instance_default_timeout`: a client's default timeout
  is sent with each acquire. **keep**.
- `test_set_client_thread_name_requires_default_client`,
  `test_set_client_thread_name_delegates_to_default_client`,
  `test_set_client_process_name_avoids_double_separator`: the module-level name
  helpers act on the default client. **keep**.

`OtherTests`
- `test_default_bind_address`: the server binds all interfaces by default.
  **rename** → `test_the_server_binds_all_interfaces_by_default`.
- `test_bind_to_port`: the server binds a port it is given. **rename** →
  `test_the_server_binds_a_given_port`. Its one-pass `for … else` loop is dead;
  that is for step 6.
- `test_stop_unstarted`: stopping a server that is not running raises. **keep**.

### tests/test_zlog_server.py

`ZLogServerTests`
- `test_hello`, `test_protocol`: the server answers hello and its protocol
  version. **keep**.
- `test_bad_request`: each malformed request gets its error, and the server
  keeps running. **keep**.
- `test_no_access`: `check_access` refuses a file it cannot write, with the OS
  error. **rename** → `test_check_access_refuses_an_unwritable_file`.
- `test_cant_create_files`: `check_access` refuses a file whose directory cannot
  take a rotating handler's backups. **rename** →
  `test_check_access_refuses_a_directory_without_room_for_backups`.
- `test_access`: `check_access` accepts a writable file. **keep**.
- `test_log`: a logged message is written to the file. **keep**.

### tests/test_remote.py

`ZprocessRemoteTests`
- `test_hello`, `test_protocol`: the remote server answers hello and its protocol
  version. **keep**.
- `test_basic_process`: a process started through the remote server echoes
  data. **rename** → `test_a_remote_process_echoes_data`.
