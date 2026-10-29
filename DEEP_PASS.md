# zprocess deep pass

The code-health campaign's record for zprocess (`issues/code_health_campaign.md`
in the meta repo): the decisions that still hold, and what is deferred.

## Base

`CodeHealth` is upstream zprocess v3.0.1 (`7f188c9`) merged in, plus the fork's
own changes. Where upstream made a fork change its own way, upstream's is kept:
the daemon launcher, the Interruptor's `XPUB_VERBOSER`, late heartbeat replies,
App Nap (`appnope.nope()` once per `ProcessTree`) and the `test_no_access` fix.
With it come, by Ian's decision:
- PAIR sockets between parent and child, negotiated with a remote server's
  protocol version;
- no default `ProcessTree` at import: `set_default_process_tree()` and
  `get_default_process_tree()`;
- Python 3.11 or newer;
- secure by default: servers and command lines need `allow_insecure` or
  `--allow-insecure` for insecure connections;
- `interrupt_main_thread()`, `KillLock.is_held()` and `exit_when_released()`,
  and a heartbeat failure that waits for the kill lock on every platform;
- `port_in_use()`, random ports in 49152-65535, and child sockets that do not
  reconnect to an exited parent's ports.

## Fork changes upstream lacks

- `ZMQServer` sends its reply inside the request's `try`, so a reply that cannot
  be pickled reaches the client as an error, and it catches `BaseException`, so a
  handler's `SystemExit` does too.
- `WriteQueue.put()` to a local child that has exited raises `ProcessExited`.
- zlock rejects a NaN timeout, acquires a reentrant lock outside the `assert`,
  and zlog logs rollovers with its own logger.
- `ZMQRouterServer` in `zprocess.clientserver` holds the zlock and zlog servers'
  ROUTER loop. `server_argument_parser()` and `server_kwargs()` in
  `zprocess.utils` hold the three servers' command-line arguments, `--silent`
  included. labscript-utils starts zlock and zlog as subprocesses, so their
  command lines stay as they are.
- `ZLockClient` and `ZLogClient` stay separate: one is a REQ client with a legacy
  reply for old servers, the other a DEALER.
- Removed: `zprocess.locking`, `utils.embed`, `run_tests.py`,
  `socks.server.RouteNotAllowed`, `SecureSocket.send`, and the demo
  `if __name__ == '__main__'` blocks in library modules. `curses_server.LogLines`
  honours `maxlines`.

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
  2022 port-scan work, which upstream's PAIR sockets now cover.

## Upstream

Ian's "simplify" pull request, once the campaign is done, offers the fork's
`ZMQRouterServer`, `server_argument_parser()` and the removals listed above that
upstream has not made.

## Style

Upstream's style wins for existing lines: long docstrings and comments on
internal code, `object` bases, `%` and `.format()`. The fork's own lines follow
labscript-style, wrapped at upstream's 88 columns.
