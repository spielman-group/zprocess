# zprocess deep pass

The code-health campaign's record for zprocess (`issues/code_health_campaign.md`
in the meta repo): the decisions that still hold, and what is deferred.

## Base

`CodeHealth` is upstream zprocess v3.0.1 (`7f188c9`) merged in, plus the fork's
own changes. Where upstream made a fork change its own way, upstream's is kept:
the daemon launcher, the Interruptor's `XPUB_VERBOSER`, late heartbeat replies,
App Nap (`appnope.nope()` once per `ProcessTree`) and the `test_no_access` fix.
With it come, by Ian's decision:
- PAIR sockets between parent and child, as upstream has them, negotiated with a
  remote server's protocol version;
- no default `ProcessTree` at import: `set_default_process_tree()` and
  `get_default_process_tree()`;
- Python 3.13 or newer;
- secure by default: servers and command lines need `allow_insecure` or
  `--allow-insecure` for insecure connections;
- `interrupt_main_thread()`, `KillLock.is_held()` and `exit_when_released()`,
  and a heartbeat failure that waits for the kill lock on every platform;
- `port_in_use()`, random ports in 49152-65535, and child sockets that do not
  reconnect to an exited parent's ports.

## Differences from upstream v3.0.1

The fork stays as close to upstream as it can (Ian). Every difference in
`git diff upstream/master CodeHealth` is one of these:

**Fix upstream lacks:**
- `ZMQServer` sends its reply inside the request's `try`, so a reply that cannot
  be pickled reaches the client as an error, and it catches `BaseException`, so a
  handler's `SystemExit` does too.
- `WriteQueue.put()` to a local child that has exited raises `ProcessExited`.
- zlock rejects a NaN timeout and acquires a reentrant lock outside the `assert`;
  zlog logs rollovers with its own logger.
- `curses_server.LogLines` honours `maxlines`.
- Text that is wrong upstream: the README's and docs' install lines, BitBucket
  link, Python 2.7 note and TODO placeholders; `_get_fileno`'s docstring;
  `OutputInterceptor`'s docstring, which sits after code and so is not one;
  `ProcessTree.subprocess`'s unfinished docstring; an orphaned "Disabled for
  now" comment in `security.py`; `tasks.py`'s module names.
- The code fixes but `maxlines` are on `UpstreamBugFixes`, for a pull request;
  `maxlines` and the text go with the "simplify" one.

**Fork design upstream lacks (Ian, step 2.2):**
- `ZMQRouterServer` in `zprocess.clientserver` holds the zlock and zlog servers'
  ROUTER loop, and `test_zlock_server.py` patches it there.
- `server_argument_parser()` and `server_kwargs()` in `zprocess.utils` hold the
  three servers' command-line arguments, with upstream's secure default and
  `--silent`. labscript-utils starts zlock and zlog as subprocesses, so their
  command lines stay as they are. Taking upstream's form is possible: three
  copies of the arguments again.

**Removal upstream lacks (Ian, step 2.4):**
- `zprocess.locking`, which upstream keeps, deprecated, until zprocess 4; nothing
  in the suite imports it. Taking upstream's form is possible: 22 lines back.
- `run_tests.py` and `xmlrunner`, `socks.server.RouteNotAllowed`,
  `SecureSocket.send`, and the demo `if __name__ == '__main__'` blocks in
  library modules.

**Ian's decision:** Python 3.13 or newer.

Logging calls pass their arguments lazily, as upstream's do.

`ZLockClient` and `ZLogClient` stay separate: one is a REQ client with a legacy
reply for old servers, the other a DEALER.

## Public interface kept

- `zprocess.Event` and `Process` without a `ProcessTree` use the default tree.
  labscript-utils' `ls_zprocess` sets it by assigning
  `process_tree._default_process_tree`; it is to call
  `set_default_process_tree()` instead.
- The compatibility `ZMQServer`: labscript-utils' `ls_zprocess.ZMQServer`
  subclasses it.
- The module-level `zmq_get*` and `zmq_push*`, deprecated upstream with a
  `FutureWarning`.

## Tests

- Upstream's tests stay as upstream wrote them; the fork adds one each for the
  unsendable reply, `SystemExit` and `ProcessExited`.
- `HeartbeatTests` are the evidence for the heartbeat behaviour. Breaking the
  miss counting fails each of them.
- hyde's kernel runtime keeps its `heartbeat_interval=10,
  allowed_missed_heartbeats=10` override (Ian).

## Branches

- `UpstreamBugFixes` holds the fork's fixes above that upstream lacks, rebased
  on v3.0.1, for a pull request.
- `spielman_retired/PortChanges` and `spielman_retired/PortChanges_MD` record the
  2022 port-scan work and its PAIR sockets: deferred until upstream took PAIR
  sockets; upstream now has them.

## Upstream

Ian's "simplify" pull request, once the campaign is done, offers the fork's
`ZMQRouterServer`, `server_argument_parser()` and the removals listed above that
upstream has not made.

## Style

Upstream's style wins for existing lines: long docstrings and comments on
internal code, `object` bases, `%` and `.format()`. The fork's own lines follow
labscript-style, wrapped at upstream's 88 columns.
