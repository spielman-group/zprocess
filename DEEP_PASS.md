# zprocess deep pass

The code-health campaign's record for zprocess (`issues/code_health_campaign.md`
in the meta repo): the decisions that still hold, and what is deferred.

## Tests

- Upstream's tests stay as upstream wrote them; only the fork's may change.
- `HeartbeatTests` are the evidence for the heartbeat problem and stay as they
  are. Breaking the miss counting fails each of them.
- Deferred: rename `StartDaemonTests.test_start_daemon` to
  `test_start_daemon_detaches_even_with_tkinter_loaded`.

## Heartbeats

- A child is taken for dead after `allowed_missed_heartbeats` heartbeats with no
  reply, and a late reply still counts, so a slow parent does not kill its
  children.
- `HeartbeatServer` calls `appnope.nope()` on macOS, so an idle GUI parent is not
  throttled by App Nap; `appnope` is a darwin-only dependency.
- The fallback for parents older than `allowed_missed_heartbeats` stays: such
  parents, remote ones included, still exist.
- Proposed, not decided: bind `HeartbeatServer` to `127.0.0.1` unless the tree starts a remote
  child, so a network scanner cannot reach a local worker's heartbeat port. With
  the labs' shared secret, CURVE already refuses a scanner.
- hyde's kernel runtime keeps its `heartbeat_interval=10,
  allowed_missed_heartbeats=10` override (Ian).

## Shared code

- `ZMQRouterServer` in `zprocess.clientserver` holds the zlock and zlog servers'
  ROUTER loop; `server_argument_parser()` and `server_kwargs()` in
  `zprocess.utils` hold the three servers' command-line arguments.
  labscript-utils starts zlock and zlog as subprocesses, so their command lines
  stay as they are.
- `ZLockClient` and `ZLogClient` stay separate: one is a REQ client with a legacy
  reply for old servers, the other a DEALER. Merging them would change zlock's
  socket type for about six shared lines.

## Public interface kept

These compatibility names stay, because suite code uses them or they are
documented:
- `zprocess.Event`, `Process` and `_default_process_tree`: labscript-devices
  calls `zprocess.Event(...)`, and labscript-utils sets `_default_process_tree`.
- The compatibility `ZMQServer`: labscript-utils' `ls_zprocess.ZMQServer`
  subclasses it.
- The module-level `zmq_get*` and `zmq_push*`, zprocess's documented API.

zlock's and zlog's module-level legacy API, `zprocess.locking`,
`setup_connection_with_parent`, `subprocess_with_queues` and `utils.embed` are
gone; lab scripts written against them must make their own clients.

## Branches

- `spielman_retired/PortChanges` and `spielman_retired/PortChanges_MD` record the
  PAIR-socket queue work. If PAIR is wanted, it is redone on a current base,
  without `PortChanges_MD`'s line-ending rewrite of `process_tree.py`.

## Upstream

Ian's "simplify" pull request, once the campaign is done, is this ordered series,
which applies to `UpstreamBugFixes`: `cc8c24c`, `8ebfbda`, `aa6f0f8`, `283e9eb`,
`473002d`, `ec5f353`, `f520c41`, `a48d658`, `2bbe98b`, `6cb4297`, `463c014`,
`df32fce`. On upstream `master`, `aa6f0f8` needs the NaN-timeout fix (`8c84996`)
first. `2bbe98b`, `6cb4297` and `df32fce` remove legacy API.

## Style

Upstream's style wins for existing lines: long docstrings and comments on
internal code, `object` bases, `%` and `.format()`. The fork's own lines follow
labscript-style, wrapped at upstream's 88 columns.
