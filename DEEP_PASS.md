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
- Marks: keep 76, rename 1, fix 0, cut 0. Ian: upstream's tests stay as they are;
  only the fork's may be renamed.

### The heartbeat tests

Four heartbeat tests fail intermittently on macOS. Ian: the failures are real;
workers are killed the same way in the labs. The tests stay as they are, as the
evidence, and the cause is studied under "Heartbeat study" below. Breaking the
miss counting in a scratch copy fails each of the four, so they do test it.

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
  socket in order. **keep**.

`ProcessTerminateTests`
- `test_terminate_ignores_local_wait_timeout`: `Process.terminate` does not leak
  `TimeoutExpired` when the child is slow to exit. **keep**.

`HeartbeatTests` (fork's)
- `test_subproc_lives_with_working_heartbeats`: a child whose heartbeats are
  answered keeps running. **keep**.
- `test_subproc_survives_missing_heartbeats_below_budget`: a child survives
  fewer unanswered heartbeats than allowed. **keep**: evidence of the heartbeat problem.
- `test_subproc_dies_after_1_to_5_missing_heartbeats`: a child exits once its
  allowance of unanswered heartbeats is used. **keep**: evidence of the heartbeat problem.
- `test_subproc_survives_malformed_heartbeats_below_budget`: as above, for wrong
  replies. **keep**: evidence of the heartbeat problem.
- `test_subproc_dies_after_1_to_5_malformed_heartbeats`: as above, for wrong
  replies. **keep**: evidence of the heartbeat problem.
- `test_successful_heartbeat_resets_miss_counter`: an answered heartbeat clears
  the misses so far. **keep**.
- `test_configured_heartbeat_interval_controls_request_cadence`: the
  `heartbeat_interval` argument sets how often heartbeats are sent. **keep**.
- `test_subproc_survives_until_kill_lock_released`: a child holding its kill
  lock is not killed until it releases it. **keep**.
- `test_parent_correctly_responds_to_heartbeats`: the real parent heartbeat
  server echoes a heartbeat. **keep**.

`EventTests`
- `test_events`: an event posted by a child reaches a waiter in the parent.
  **keep**.
- `test_external_broker`: the same, through an external event broker.
  **keep**.

`TaskTests`
- `test_cant_call_task_twice`: a task runs once. **keep**.
- `test_queue`: a task queue orders by due time, pops the earliest and cancels
  a task. **keep**.

`StartDaemonTests` (fork's)
- `test_start_daemon`: a daemon starts detached, in its own session, with tkinter
  loaded. **rename** → `test_start_daemon_detaches_even_with_tkinter_loaded`.

`ClientServerTests`
- `test_invalid_dtype_server_raises_valueerror`,
  `test_invalid_dtype_sender_raises_valueerror`: an unknown dtype is refused.
  **keep**.
- `test_rep_server`: a REP server replies, and a handler's exception reaches the
  client. **keep**.
- `test_raw_server`: the same for raw bytes, under every way of naming the
  dtype. **keep**.
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
- `test_timeout`: a held lock is released when its timeout expires. **keep**.
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
- `test_retry`: a client told to retry gets the lock once it is free. **keep**.
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
  **keep**.
- `test_bind_to_port`: the server binds a port it is given. **keep**. Its one-pass `for … else` loop is dead;
  that is for step 6.
- `test_stop_unstarted`: stopping a server that is not running raises. **keep**.

### tests/test_zlog_server.py

`ZLogServerTests`
- `test_hello`, `test_protocol`: the server answers hello and its protocol
  version. **keep**.
- `test_bad_request`: each malformed request gets its error, and the server
  keeps running. **keep**.
- `test_no_access`: `check_access` refuses a file it cannot write, with the OS
  error. **keep**.
- `test_cant_create_files`: `check_access` refuses a file whose directory cannot
  take a rotating handler's backups. **keep**.
- `test_access`: `check_access` accepts a writable file. **keep**.
- `test_log`: a logged message is written to the file. **keep**.

### tests/test_remote.py

`ZprocessRemoteTests`
- `test_hello`, `test_protocol`: the remote server answers hello and its protocol
  version. **keep**.
- `test_basic_process`: a process started through the remote server echoes
  data. **keep**.

## Heartbeat study

Findings and a proposal, for Ian's decision; nothing is built. There are two
problems.

### 1. macOS idle throttling

**Mechanism, reproduced.** A Qt parent, like BLACS, served heartbeats as
`HeartbeatServer` does (`zmq.proxy` on a REP socket in a thread), and a child ran
`HeartbeatClient`'s loop (sleep 1 s, send, poll 1 s), for 600 s. The parent's
window was minimized after 2 s. The scripts are in the session scratchpad, not
the repo.

| Parent | Heartbeats | Late (>100 ms) | Missed (>1 s) | Slowest reply |
| --- | --- | --- | --- | --- |
| App Nap allowed | 572 | 80, from 164 s on | 1 | 0.70 s |
| App Nap off (`appnope.nope()`) | 597 | 0 | 0 | 2.4 ms |

- It is the parent that is late. The child's `sleep(1)` stayed within 11 ms in
  both runs; only the replies slowed.
- Throttling by `taskpolicy -b` does not reproduce it (slowest reply 9 ms), so
  it is App Nap, which acts on GUI apps whose windows are hidden, not generic
  background priority.
- Ten minutes gave one miss. Ian's workers die after long idle or sleep, when App Nap
  holds a parent's timers for longer; macOS 27 appears to hold them longer
  still.

**What `PermissiveHeartBeat` does** (2f1192d, 5da28e4; upstream PR #26). It is
in `Production`, `Development` and `CodeHealth`. Upstream kills the child on
the first heartbeat not answered within 1 s. The branch allows 5 misses in a
row, counts a wrong reply as a miss, reconnects after each miss, and makes the
interval configurable.

**Where it falls short.** It still judges each heartbeat by a 1 s deadline.
After a miss it closes the socket, so a reply that comes 1.1 s late is thrown
away and counted as a miss. A parent held by App Nap for about 10 s (5 beats of
1 s sleep and 1 s wait) therefore kills every worker, however alive it is. It
helped by raising the limit from 1 s to about 10 s, but did not change the rule.

**Proposal**, building on the branch:
1. **At the cause:** keep zprocess parents out of App Nap. When a
   `HeartbeatServer` starts on macOS, call `appnope.nope()`, which asks
   `NSProcessInfo` for a latency-critical activity.
   - It is a new dependency, `appnope; sys_platform == 'darwin'`: pure Python
     with ctypes, from the Jupyter project, and already installed here through
     IPython. The alternative is about 15 lines of ctypes in zprocess.
   - It does nothing on Windows and Linux.
   - The cost: BLACS and other parents no longer nap, which saves a little
     energy on an idle lab machine but makes it no less responsive.
2. **Judge death by time since the parent was last heard from**, not by a count
   of 1 s deadlines. Keep waiting on the same socket, so a late reply still
   counts, and die when nothing has been heard for
   `allowed_missed_heartbeats * heartbeat_interval` plus the timeout (about 10 s
   by default, as now).
   - A truly dead parent is detected in the same time as today.
   - A late parent no longer kills its children.
   - It works the same on every platform.
   - The `HeartbeatTests` budgets would still hold.

Either one fixes the reproduction. Both together fix the cause and make the
child robust to any other stall, such as a debugger pause or a busy parent.

**Upstream:** the same problem, worse, because it kills on the first late
reply. The fix goes on `UpstreamBugFixes` too, perhaps with PR #26 brought up
to date rather than as a second pull request.

### 2. Port scans breaking the heartbeat port

**Mechanism, not reproduced.**
- `HeartbeatServer` binds `tcp://*` on a random port in every process that has
  children, so a network scanner can reach it.
- RobustPackets' docstring (2022) says corrupted messages "frequently occurs in
  networks with vulnerability testing", and its fix covers "every error we have
  ever seen".
- With a shared secret, as the labs' labconfig sets, CURVE refuses a scanner's
  connection before any message is read. So the failure was probably from a
  time or a machine without a secret, or the REP socket being left in a bad
  state. I have not shown which.

**What the branches did.**
- `RobustPackets` and `PortChanges` (2022): length-prefixed heartbeat messages
  (`ZEncode`/`ZDecode`), retries, and clearer failure messages.
- `PortChanges` and `PortChanges_MD` (2026, Michael D.): PAIR sockets in the
  queues, and explicit poll flags. They are not about the heartbeat.

**What is still broken.**
- `PermissiveHeartBeat` already treats a wrong reply as a miss and reconnects,
  which covers what the length prefix was for. So `RobustPackets` adds nothing
  over it for the heartbeat.
- Nothing recovers a parent whose heartbeat socket has itself failed: every
  child dies after its misses.
- The port is still open to the network for local children, which never need
  it.

**Proposal:**
- Bind `HeartbeatServer` to `127.0.0.1` unless the tree starts a remote child,
  when it binds as now. That removes the scanner's path for every local worker,
  which is every worker in the labs unless they use `zprocess.remote`.
- Proposal 2 above also means a briefly broken reply no longer kills anything.
- The dormant branches would then be retired, in step 4.

## Step 2.1: behaviour no one asked for

No candidates. Every change `CodeHealth` makes to `zprocess/` over `master`
traces to a request.

- **What the fork changed.** `git diff master CodeHealth`, two-dot, at
  `b7fa8af`: 16 non-merge commits, and in `zprocess/` 80 lines added and 40
  removed.
- **Request:**
  - Ian's `PermissiveHeartBeat` (2f1192d, 5da28e4; upstream PR #26). Its
    `heartbeat_interval` is used by hyde's kernel runtime.
  - The ServerHangs, LockLogFixes and `BaseException` fixes, from the master's
    and labscript-utils' requests on Ian's decisions.
  - The `start_daemon` launcher and the heartbeat fix, both Ian's.
  - The version scheme and the Python 3.10 floor, both Ian's.
- **Users considered:** labscript-utils' `ls_zprocess` and its zlock and zlog
  start-up, and every suite app's worker processes through `Process`. Also
  hyde's kernel runtime, and labs' own code using `zprocess` directly.
- The dormant branches (`PortChanges`, `RobustPackets`, `PortChanges_MD`) are
  not in `CodeHealth`. They are decided in step 4.

## Step 2.2: duplication

Candidates, for Ian's decision. All are upstream's own code. Merging any of them
widens the fork's difference from upstream, which costs something at every
upstream sync; that is weighed against the lines saved.

1. **The zlock and zlog servers' ROUTER skeleton.**
   - `ZMQLockServer` and `ZMQLogServer` each have `run`,
     `_win32_keyboardinterrupt`, `_mainloop`'s loop shape, `run_in_thread`,
     `stop` and `send`. The two `run` bodies differ in 23 of about 50 lines:
     the server's name, its logger and its handlers.
   - One base class in `zprocess` would hold them.
   - About 80 lines saved, across two modules.
2. **The zlock and zlog clients' socket and ping code.**
   - `ZLockClient` and `ZLogClient` each have `_new_socket`, `ping` and
     `get_protocol_version`, with near-identical bodies (24 of 42 lines differ in
     `_new_socket`).
   - One base class would hold them.
   - About 50 lines saved.
3. **The three command-line entry points.**
   - `zlock/__main__.py`, `zlog/__main__.py` and `remote/__main__.py` each build
     the same arguments (port, bind address, shared-secret file,
     allow-insecure, log directory, daemon) and read the secret.
   - One shared argument builder.
   - About 60 lines saved.
   - labscript-utils' `zlock.py` and `zlog.py` start these as subprocesses, so
     their command lines must stay as they are.
4. **`remote/__main__.py` reads the shared-secret file twice** (81-89), with
   identical code. Cut the second copy: 4 lines. This one has no cost.

Outcome (Ian approved all four):
- 1 is done as `aa6f0f8`: `ZMQRouterServer` in `zprocess.clientserver`.
- 3 is done as `8ebfbda`: `server_argument_parser()` and `server_kwargs()` in
  `zprocess.utils`.
  - Arguments are parsed as before.
  - The help lists the shared arguments first, and two descriptions are
    reworded.
- 4 is done as `cc8c24c`.
- 2 was not built. On a closer reading the clients are not duplicates:
  - `ZLockClient` repeats a REQ send-and-poll in each method, with a legacy
    reply for old servers in `get_protocol_version`.
  - `ZLogClient` uses a DEALER with shared `_send` and `_recv`.
  - They share only about six lines of `__init__`. Merging them would move zlock's
    client onto a different socket type, a behaviour change for no real saving.
- Checks:
  - The suite: 77 of 77.
  - Real zlock, zlog and remote servers started from the command line on scratch
    ports, with a secret file, a log directory and zlog's handler options. They
    answered and exited cleanly on SIGINT.
  - One independent review; its fixes are folded in.
- The librarian confirmed that neither new name duplicates anything.

Not candidates:
- `zlock.server.Lock` against `zlock.Lock`: these are a server's state and a
  client's lock, different jobs that share a name.
- `setup_logging` and `dedent`: different jobs from labscript-utils' functions
  of the same names.
- The compatibility redefinitions in `clientserver.py`, `process_tree.py`,
  `zlock` and `zlog`, and the legacy `connect` and `ping`, are step 4's.

## Later

- **Ian's upstream "simplify" PR**, to be made once the campaign is done. It uses
  `cc8c24c`, `8ebfbda` and `aa6f0f8`, in that order.
  - They touch only upstream's code. They apply cleanly to `UpstreamBugFixes`,
    where the suite passes with the heartbeat tests set aside.
  - `cc8c24c` and `8ebfbda` also apply to upstream `master`.
  - `aa6f0f8` needs the NaN-timeout fix (`8c84996` on `UpstreamBugFixes`) first,
    because its import block is beside that fix's `import math`.

## Step 2.3: root causes

Candidates, for Ian's decision.

**In zprocess: no candidates.** Every change the fork made to `zprocess/` is
itself the fix at the cause. That is the reply sent inside the request's `try`,
`XPUB_VERBOSER`, `math.isfinite`, the acquire outside the `assert`, the zlog
logger, `BaseException`, the `start_daemon` launcher, and `appnope` with late
replies counting. None of them is a guard over a symptom.

**Elsewhere, guards against zprocess faults that are now fixed.** Each is in
another owner's repository; zprocess changes nothing.

1. **runmanager `__main__.py:2942`** passes its own `Interruptor()` to
   `from_child.put()`. Its comment says the put waits for a subscription zmq never
   reports while the compile's `get()` holds the same one. That is the Interruptor
   deadlock fixed by `XPUB_VERBOSER` (zprocess `162afe7`, on `Development` and
   `Production`). The guard could go: 2 lines and its comment. Owner: runmanager.
2. **lyse `routines.py:638`**: the same guard and the same cause. Owner: lyse.
3. **hyde's kernel runtime** (`kernel_runtime/__init__.py:515`) sets
   `heartbeat_interval=10, allowed_missed_heartbeats=10`, which gives about 110 s
   before a kernel is taken for dead, against zprocess's 10 s.
   - Its comment says a busy kernel answers slowly. But the child sends the
     heartbeats and the parent answers them, so a slow answer means a slow parent,
     hyde's GUI. That is App Nap, which zprocess now prevents, with late replies
     counting.
   - The override may no longer be needed, and it slows detecting a dead hyde
     elevenfold.
   - Owner: hyde, Ian's call; it needs a trial with hyde idle.

`labscript_utils.ls_zprocess.ZMQServer.handler`'s `BaseException` guard is
labscript-utils' own entry 8, already settled there.

Outcome (Ian):
- 1 and 2: runmanager and lyse remove their `Interruptor` guards; the master has
  briefed them.
- 3: hyde's heartbeat override stays.

## Step 2.4: dead code, leftovers and branches

Candidates, for Ian's decision.
- A search across every repo, tests and hyde included, found who uses each name.
  It used `git grep -w`; the `\b` form missed hits, so it was rerun.
- "Upstream's" marks code that is also on `master`: removing it widens the gap
  with upstream, and labs' own scripts may use it ("Fork goes far from upstream":
  allowed on Ian's word, with what breaks stated).

### Dead code

1. **`utils.embed`** raises NotImplementedError ("no longer works with newer
   IPython"). Its only users are its definition and the re-export in
   `zprocess/__init__.py`. Remove both. Upstream's.
2. **`run_tests.py`**:
   - It lists a `tests.py` that does not exist.
   - `get_coverage_path` is never called.
   - Neither CI nor anyone else runs the file; `pytest.ini` drives the tests.
   - Remove the file, and `xmlrunner` from `requirements.txt`, which only it
     needed. Upstream's.
3. **`curses_server.LogLines`** ignores `maxlines` and hard-codes
   `deque(maxlen=100)`; its only caller passes 100. Use `maxlines`, a one-word
   fix. Upstream's.
4. **Demo `if __name__ == '__main__'` blocks in library modules:**
   - Blocks: `tasks.py:99`, `zlock/__init__.py:306`, `zlock/server.py:469`,
     `zlog/__init__.py:232`, `zlog/server.py:242`, `socks/server.py:475` (a
     three-hop demo), and a commented-out block at the end of
     `process_tree.py`.
   - Each is a hand test of its module, not a command. Remove them; the real
     entry points are the `__main__.py` files. Upstream's.
5. **`socks.server.RouteNotAllowed`**: defined, never raised or caught anywhere.
   Remove. Upstream's.

### Compatibility leftovers

6. **The `zprocess.locking` package**, marked "will be removed in zprocess 3",
   re-exports `zprocess.zlock`. Two users:
   - zprocess's own `process_tree.py:36`;
   - blacs `__main__.py:59`, an unused `import zprocess.locking`.
   - Move both to `zprocess.zlock`, then remove the package.
   - blacs's line is blacs's change, to be briefed to its owner. Upstream's.
7. **zlock's and zlog's module-level legacy API:**
   - zlock: `connect`, `ping`, `get_protocol_version`, `set_default_timeout`,
     `set_client_process_name` and `set_client_thread_name`.
   - zlog: `connect`, `ping`, `get_protocol_version` and `check_access`.
   - Also the compatibility `Lock` and `ZMQLoggingHandler` that need no client.
   - No suite repo uses any of them; labscript-utils makes its own clients. The
     only users are three of upstream's zlock tests.
   - Removing them breaks lab scripts written against the old API, and those
     three upstream tests go with them. Ian's call. Upstream's.
8. **`process_tree.setup_connection_with_parent` and
   `subprocess_with_queues`**, the "old way". No users anywhere. Remove both,
   with their `__all__` and `__init__` re-exports. Upstream's.
9. **`security.SecureSocket.send`** only calls `zmq.Socket.send`. It is a
   candidate to remove, but it needs a check that pyzmq's own `send_multipart`
   and the `send_pyobj` family behave the same without it. Upstream's.

**Kept, because they are used:**
- The compatibility `Event`, `Process` and `_default_process_tree`.
  labscript-devices calls `zprocess.Event(...)` (PrawnBlaster, PulseBlaster,
  CiceroOpalKellyXEM3001), and labscript-utils sets `_default_process_tree`.
- The compatibility `ZMQServer`: labscript-utils' `ls_zprocess.ZMQServer`
  subclasses it, and the suite's servers, labscript-devices' included, build on
  that.
- The module-level `zmq_get*` and `zmq_push*`. Only upstream's tests use them,
  but they are zprocess's documented public API.

### Branches

10. **`RobustPackets`** (2022, Ian; also on origin): length-prefixed heartbeat
    messages (`ZEncode`/`ZDecode`), `RETRIES`, retries in `HeartbeatClient`,
    and clearer failure messages. It was the port-scan fix of the time.
    - Its content is wholly in `PortChanges`. Two-dot, `PortChanges` differs
      from it only by 13 PAIR lines in `process_tree.py`.
    - `PermissiveHeartBeat` and the heartbeat fix supersede it: a wrong reply
      already counts as a miss, and late replies are read.
    - It is behind `master`. Merging it would undo upstream's later zlock fixes
      (`default_timeout`, the thread-name and process-name helpers, the bind
      address) and `Process.terminate`'s `TimeoutExpired` handling.
    - **Delete**, locally and on origin.
11. **`PortChanges`** (2022): `RobustPackets` plus the parent-child queues on
    PAIR sockets instead of PUSH/PULL. It is behind `master` in the same way.
    **Rename to `spielman_retired/PortChanges`**, as the record of the 2022
    port-scan work. Its PAIR change lives on in `PortChanges_MD`.
12. **`PortChanges_MD`** (origin only, `b14bd5f`): Michael D.'s pull request #1
    to the fork (April 2026), the same 13 PAIR lines on a current base, plus a
    whole-file line-ending rewrite of `process_tree.py`.
    - A PAIR socket accepts one peer, so a scanner cannot join a queue once the
      child has connected.
    - The labs' shared secret already rejects scanners through CURVE, before
      any message.
    - ZeroMQ documents PAIR as meant for inproc, and it does not reconnect as
      PUSH/PULL do.
    - **Rename to `spielman_retired/PortChanges_MD`**, unless Ian or Michael
      want PAIR. Then it would be redone cleanly, without the line-ending churn,
      and tested.

`PermissiveHeartBeat` stays as the head of upstream PR #26.
