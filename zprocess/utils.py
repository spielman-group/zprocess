import sys
import os
import threading
import logging
import logging.handlers
from binascii import hexlify
import socket
import tempfile
from pathlib import Path
import io
import subprocess
import argparse

import zmq

class TimeoutError(zmq.ZMQError, TimeoutError):
    pass


class Interrupted(RuntimeError):
    pass


class Interruptor(object):
    """An object that can be passed to the put() and get() methods of ReadQueue and
    WriteQueue objects, and the get() methods ZMQClient objects, in order to be able to
    interrupt these potentially blocking methods from another thread. Upon calling
    Interruptor.set(), all currently blocking threads calling the aforementioned
    put()/get() methods will raise Interrupted, and all subsequent calls to put()/get()
    with this interruptor will raise Interrupted immediately, until the clear() method
    is called.

    This class may be used to interrupt other blocking zmq operations in user code as
    well, it is not specific to ZMQClient, ReadQueue and WriteQueue. The semantics are
    the following. A thread about to do blocking IO should call Interruptor.subscribe(),
    which will return a socket. The caller can then poll that socket for an interruption
    message. If a message arrives, it will contain the reason, if any, for interruption.
    zprocess classes then raise zprocess.Interrupted(reason), but calling code may do
    with the interruption what they like. The caller must call Interruptor.unsubscribe()
    once blocking zmq operations have completed, regardless of whether an interruption
    was received or not. Calling code should also unregister the interruption socket
    from the zmq.Poller() used to poll. """

    def __init__(self):
        # make a send socket
        self._ctx = zmq.Context.instance()
        self._xpub = self._ctx.socket(zmq.XPUB)
        # Report every subscription and unsubscription, not only the first and last
        # for a topic, since subscribe() and unsubscribe() wait for one each:
        self._xpub.setsockopt(zmq.XPUB_VERBOSER, 1)
        self._endpoint = 'inproc://zpInterruptor' + hexlify(os.urandom(8)).decode()
        self._xpub.bind(self._endpoint)
        self._local = threading.local()
        self._lock = threading.Lock()
        self.reason = ''
        self.is_set = False

    def subscribe(self):
        """Called by put()/get() methods. Return a thread-local inproc socket subscribed
        to interrupt messages."""
        with self._lock:
            if not hasattr(self._local, 'sub'):
                self._local.sub = self._ctx.socket(zmq.SUB)
                self._local.sub.connect(self._endpoint)
                self._local.subscribed = False
            if self._local.subscribed:
                msg = "Thread already subscribed. Did you forget to call unsubscribe()?"
                raise RuntimeError(msg)
            self._local.sub.subscribe(b'')
            # Ensure subscription is processed:
            self._xpub.recv()
            self._local.subscribed = True
            # If we're already set, send an interruption message immediately:
            if self.is_set:
                self._xpub.send(self.reason.encode('utf8'))
        return self._local.sub

    def unsubscribe(self):
        """Called by put()/get() upon interruption or end of blocking IO to ubsubscribe
        from interrupt messages. This is somewhat important so that messages do not pile
        up"""
        with self._lock:
            if not hasattr(self._local, 'sub') or not self._local.subscribed:
                raise RuntimeError('not subscribed')
            self._local.sub.unsubscribe(b'')
            # Ensure unsubscription is processed:
            self._xpub.recv()
            self._local.subscribed = False

    def set(self, reason=None):
        """Send an interrupt message containing the given reason to all present and
        future subscribed threads, until clear() is called."""
        if reason is None:
            reason = ''
        with self._lock:
            if self.is_set:
                raise RuntimeError('Already set. Did you forget to call clear()?')
            self.is_set = True
            self.reason = reason
            self._xpub.send(reason.encode('utf8'))

    def clear(self):
        """Cease sending interrupt messages to newly subscribed threads."""
        with self._lock:
            if not self.is_set:
                raise RuntimeError('Not set')
            self.is_set = False
            self.reason = ''


def _reraise(exc_info):
    exctype, value, traceback = exc_info
    raise value.with_traceback(traceback)


def raise_exception_in_thread(exc_info):
    """Raises an exception in a thread"""
    threading.Thread(target=_reraise, args=(exc_info,)).start()


def start_daemon(cmd_args):
    """calls subprocess.Popen configured to detach the subprocess from the parent, such
    that it keeps running even if the parent exits. Returns None. Note that the child
    process will have its current working directory set to the value of
    tempfile.gettempdir(), rather than remaining in the parent's working directory. In
    Windows this prevents it holding a lock on the current directory, which would
    prevent it from being deleted, and the behaviour is the same on unix for
    consistency."""
    kwargs = {}
    if os.name == 'nt':
        kwargs['creationflags'] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        # Start it from a short-lived Python process, in a new session, so that it is
        # not our child and has no controlling terminal. Forking here and calling
        # Popen in the child instead is killed on macOS when a library such as Tcl has
        # registered fork handlers.
        launcher = (
            'import subprocess, sys; '
            + 'subprocess.Popen(sys.argv[1:], start_new_session=True)'
        )
        cmd_args = [sys.executable, '-c', launcher] + list(cmd_args)
    process = subprocess.Popen(
        cmd_args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        cwd=tempfile.gettempdir(),
        **kwargs
    )
    if os.name == 'posix':
        process.wait()


def _get_fileno(stream):
    """Return stream.fileno(), or -1 if the call raises io.UnsupportedOperation"""
    try:
        return stream.fileno()
    except io.UnsupportedOperation:
        # IDLE or Jupyter. Return an invalid fileno
        return -1


def disable_quick_edit():
    """Disable the 'quick-edit' misfeature of Windows' cmd.exe, in which a single click
    on the console puts it in 'select' mode indefinitely, causing writes to stdout from
    the program to block, freezing the program. The program remains paused like this
    even if the window is no longer focused, until the user sends a keypress to the
    console. This breaks so many things and is easy to do without realising it. This
    function disables the feature, and and adds an atexit() hook to set it back back to
    its initial configuration when Python exits.
    """
    if os.name == 'nt' and all(
        [
            a is not None and a.isatty() and _get_fileno(a) >= 0
            for a in (sys.stdin, sys.stdout, sys.stderr)
        ]
    ):
        import win32console
        import atexit
        import pywintypes

        ENABLE_QUICK_EDIT = 0x0040
        ENABLE_EXTENDED_FLAGS = 0x0080
        console = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)
        try:
            orig_mode = console.GetConsoleMode()
        except pywintypes.error:
            # Probably there is no console after all.
            # Don't know why, but don't worry about it:
            return
        if (orig_mode & ENABLE_EXTENDED_FLAGS) and not (orig_mode & ENABLE_QUICK_EDIT):
            # Already disabled, nothing for us to do.
            return
        new_mode = (orig_mode | ENABLE_EXTENDED_FLAGS) & ~ENABLE_QUICK_EDIT
        console.SetConsoleMode(new_mode)
        atexit.register(console.SetConsoleMode, orig_mode)

        
def setup_logging(name, silent=False, directory=None):
    """Basic logging setup used by zprocess servers. silent=True will configure logging
    calls to be no-ops. directory must be specified for logging to file, otherwise only
    terminal logging will be produced. Directory will be created if it doesn't exist,
    but its parent directories must already exist"""
    LOGLEVEL = logging.DEBUG
    if directory is not None:
        logpath = os.path.join(directory, '%s.log' % name)
        if not os.path.exists(directory):
            os.mkdir(directory)
    else:
        logpath = None
    logger = logging.Logger(name)
    logger.setLevel(LOGLEVEL)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s')
    file_handler_success = False
    if not silent:
        if logpath is not None:
            try:
                handler = logging.handlers.RotatingFileHandler(
                    logpath, maxBytes=50 * 1024 ** 2, backupCount=1
                )
                handler.setLevel(LOGLEVEL)
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                file_handler_success = True
            except (OSError, IOError):
                file_handler_success = False
        if sys.stdout is not None and sys.stdout.isatty():
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(LOGLEVEL)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
    if silent:
        logger.addHandler(logging.NullHandler())
    if not silent and not file_handler_success and logpath is not None:
        msg = 'Can\'t open or do not have permission to write to log file '
        msg += logpath + '. Only terminal logging will be output.'
        logger.warning(msg)
    elif file_handler_success:
        logger.info('logging to %s', logpath)
    return logger


def server_argument_parser(name, default_port):
    """Return an ArgumentParser for a zprocess server, with the arguments that every
    server takes. name is the server's name, such as 'zlock server'. Pass the parsed
    arguments to server_kwargs() to get the arguments of the server's constructor."""
    parser = argparse.ArgumentParser(description=name + '.')

    parser.add_argument('-p', '--port', type=int, default=default_port,
                        help='The port to listen on. Default: %d' % default_port)

    parser.add_argument(
        '-a',
        '--bind-address',
        type=str,
        default='*',
        help="""Interface to listen on. Set to '*' (default) for all interfaces, or
            '127.0.0.1' or '::1' for loopback ipv4 or ipv6 interfaces only""",
    )

    parser.add_argument(
        '-s',
        '--shared-secret-file',
        type=str,
        default=None,
        help="""Filepath to the shared secret used for secure communication.""",
    )

    parser.add_argument(
        '-l',
        '--server-log-dir',
        type=str,
        default=None,
        help="""Directory for the (optional) log file of the %s.""" % name,
    )

    exclusive_grp = parser.add_mutually_exclusive_group()

    exclusive_grp.add_argument(
        '-i',
        '--allow-insecure',
        action='store_true',
        dest='allow_insecure',
        default=True,
        help="""Must be set to acknowledge that communication will be insecure if not
        using a shared secret, otherwise connections to hosts other than localhost will
        raise an exception. Is by default set on zprocess 2 for backward compatibility,
        but will be unset by default in zprocess 3.""",
    )

    exclusive_grp.add_argument(
        '-ni',
        '--no-allow-insecure',
        action='store_false',
        dest='allow_insecure',
        help="""Set to explicitly disallow insecure connections. This will be
        unnecessary on zprocess 3.0, when requiring secure connections will be the
        default behaviour.""",
    )
    return parser


def server_kwargs(args):
    """Return the server constructor's keyword arguments from arguments parsed by a
    parser from server_argument_parser()."""
    if args.shared_secret_file is None:
        shared_secret = None
    else:
        shared_secret = open(args.shared_secret_file).read().strip()
    return dict(
        port=args.port,
        bind_address='tcp://' + args.bind_address,
        shared_secret=shared_secret,
        allow_insecure=args.allow_insecure,
        server_log_dir=args.server_log_dir,
    )


def gethostbyname(host, prefer_ipv4=True, require_ipv4=False):
    """Like socket.gethostbyname, but may return an IPv6 address."""
    if require_ipv4:
        family = socket.AF_INET
    else:
        family = 0
    results = socket.getaddrinfo(
        host, None, family, socket.SOCK_STREAM, socket.IPPROTO_TCP
    )
    if prefer_ipv4:
        for family, _, _, _, sockaddr in results:
            if family == socket.AF_INET:
                return sockaddr[0]
    family, _, _, _, sockaddr = results[0]
    return sockaddr[0]


def get_venv_executable_and_env(env=None):
    """If we are running in a venv on Windows or MacOS such that sys.executable is a
    shim to sys._base_executable, then return sys._base_executable, as well as the
    environment that should be passed to sys._base_executable in order for it to know to
    configure itself for the virtual environment instead of the base environment. This
    allows us to skip the shim and thus have fewer layers in our process hierarchy. If
    we are not in a venv, return sys.executable and the env as passed in. If env passed
    in is None, and needs to be modified for the subprocess, a copy of os.environ(),
    appropriately modified, will be returned."""
    base_executable = getattr(sys, '_base_executable', sys.executable)
    if Path(base_executable) != Path(sys.executable):
        if env is None:
            env = os.environ.copy()
        env["__PYVENV_LAUNCHER__"] = str(sys.executable)
        return base_executable, env
    return sys.executable, env

