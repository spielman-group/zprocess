import sys
import os
import traceback
import logging
import logging.handlers
import uuid

from zprocess.tasks import Task
from zprocess.clientserver import ZMQRouterServer
from zprocess.clientserver import ERR_INVALID_COMMAND  # Re-exported

# If no client writes to a file in this time, we close it:
FILE_CLOSE_TIMEOUT = 5

ERR_WRONG_NUM_ARGS = b'error: wrong number of arguments'
ERR_BAD_ENCODING = b'error: filepath not UTF8 encoded or contains nulls'
PROTOCOL_VERSION = '1.0.0'


def _format_exc():
    """Format just the last line of the current exception, not the whole traceback"""
    exc_type, exc_value, _ = sys.exc_info()
    return traceback.format_exception_only(exc_type, exc_value)[0].strip()


class FileHandler(logging.FileHandler):
    instances = {}

    def __init__(self, filepath, **kwargs):
        # Don't open the file until logging is requested:
        kwargs['delay'] = True
        super(FileHandler, self).__init__(filepath, **kwargs)
        self.clients = set()

    @classmethod
    def instance(cls, filepath, **kwargs):
        if filepath not in cls.instances:
            cls.instances[filepath] = cls(filepath, **kwargs)
            logger.info("Opening %s", filepath)
        return cls.instances[filepath]

    def log(self, client_id, message):
        if client_id not in self.clients:
            self.clients.add(client_id)
            msg = "New client (total: %d) for %s"
            logger.info(msg, len(self.clients), self.baseFilename)
        if hasattr(self, 'shouldRollover'):
            try:
                if self.shouldRollover(message):
                    logger.info("Rolling over %s", self.baseFilename)
                    self.doRollover()
            except (OSError, IOError):
                logger.warning(
                    "Failed to check/rollover %s:\n    %s",
                    self.baseFilename,
                    _format_exc(),
                )
                return
        if self.stream is None:
            try:
                self.stream = self._open()
            except (OSError, IOError):
                logger.warning(
                    "Failed to open %s:\n    %s", self.baseFilename, _format_exc()
                )
                return
        try:
            self.stream.write(message + '\n')
            self.flush()
        except (OSError, IOError):
            # Nothing to be done.
            return

    def format(self, record):
        return record

    def client_done(self, client_id, ip=None):
        if client_id in self.clients:
            self.clients.remove(client_id)
            msg = "Client done (remaining: %d) with %s"
            if ip is not None:
                msg = '[%s] ' % ip + msg
            logger.info(msg, len(self.clients), self.baseFilename)
        if not self.clients:
            del self.instances[self.baseFilename]
            if self.stream is not None:
                logger.info("No more clients, closing %s", self.baseFilename)
                self.close()


class RotatingFileHandler(FileHandler, logging.handlers.RotatingFileHandler):
    pass


class TimedRotatingFileHandler(FileHandler, logging.handlers.TimedRotatingFileHandler):
    pass


class ZMQLogServer(ZMQRouterServer):
    name = 'zlog'
    protocol_version = PROTOCOL_VERSION

    def __init__(
        self,
        port=None,
        bind_address='tcp://*',
        silent=False,
        handler_class=FileHandler,
        handler_kwargs=None,
        shared_secret=None,
        allow_insecure=False,
        server_log_dir=None
    ):
        ZMQRouterServer.__init__(
            self,
            port=port,
            bind_address=bind_address,
            silent=silent,
            shared_secret=shared_secret,
            allow_insecure=allow_insecure,
            server_log_dir=server_log_dir,
        )
        self.handler_class = handler_class
        self.handler_kwargs = handler_kwargs if handler_kwargs is not None else {}
        self.timeout_tasks = {}

    def log(self, args):
        # Validate arguments, but we can't reply if they are invalid. We just do nothing
        # in that case.
        if len(args) != 3:
            return
        client_id, filepath, message = args
        filepath = self._check_filepath(filepath)
        if filepath is None:
            return
        try:
            message = message.decode('utf8')
        except UnicodeDecodeError:
            return
        filepath = os.path.abspath(filepath)
        handler = self.handler_class.instance(filepath, **self.handler_kwargs)
        handler.log(client_id, message)
        self.cancel_timeout(client_id)
        self.set_timeout(client_id, filepath)

    def _check_filepath(self, filepath):
        """UTF8-decode a filepath, convert it to an absolute filepath, check it has no
        nulls, and return the result. If the filepath is invalid (can't be decoded or
        has nulls), returns None."""
        if b'\0' in filepath:
            return
        try:
            filepath = filepath.decode('utf8')
        except UnicodeDecodeError:
            return
        return os.path.abspath(filepath)

    def check_access(self, routing_id, ip, args):
        if len(args) != 1:
            self.send(routing_id, ERR_WRONG_NUM_ARGS)
            return
        filepath = self._check_filepath(args[0])
        if filepath is None:
            self.send(routing_id, ERR_BAD_ENCODING)
            return
        dirname = os.path.dirname(filepath)
        try:
            # Check we can open the file in append mode:
            with open(filepath, 'a') as _:
                pass
            if self.handler_class in [RotatingFileHandler, TimedRotatingFileHandler]:
                # Check we can create files in the directory, so that we can make backup
                # log files in the directory (not a guarantee obviously, but pretty
                # good):
                test_filename = 'test_can_create_file-' + uuid.uuid4().hex
                test_filepath = os.path.join(dirname, test_filename)
                try:
                    with open(test_filepath, 'w'):
                        pass
                finally:
                    try:
                        os.unlink(test_filepath)
                    except (OSError, IOError):
                        pass
        except (OSError, IOError):
            message = _format_exc()
            self.send(routing_id, message.encode('utf8'))
            msg = '[%s] Access denied for %s: \n    %s'
            logger.warning(msg, ip, filepath, message)
        else:
            self.send(routing_id, b'ok')
            logger.info('[%s] Access confirmed for %s', ip, filepath)

    def done(self, routing_id, ip, args):
        if len(args) != 2:
            self.send(routing_id, ERR_WRONG_NUM_ARGS)
            return
        client_id, filepath = args
        filepath = self._check_filepath(filepath)
        if filepath is None:
            self.send(routing_id, ERR_BAD_ENCODING)
            return
        self.cancel_timeout(client_id)
        handler = self.handler_class.instance(filepath, **self.handler_kwargs)
        handler.client_done(client_id, ip=ip)
        self.send(routing_id, b'ok')

    def set_timeout(self, client_id, filepath):
        """Add a task to say the client is done with the file after a timeout"""
        task = Task(FILE_CLOSE_TIMEOUT, self.do_timeout, client_id, filepath)
        self.tasks.add(task)
        self.timeout_tasks[client_id] = task

    def cancel_timeout(self, client_id):
        """Cancel the scheduled auto-closing of the file for the client"""
        task = self.timeout_tasks.pop(client_id, None)
        if task is not None:
            self.tasks.cancel(task)

    def do_timeout(self, client_id, filepath):
        logger.info("Client timed out for %s", filepath)
        handler = self.handler_class.instance(filepath, **self.handler_kwargs)
        handler.client_done(client_id)
        del self.timeout_tasks[client_id]

    def _setup_logging(self):
        global logger
        logger = ZMQRouterServer._setup_logging(self)
        return logger

    def handle(self, routing_id, ip, command, args):
        if command == b'log':
            self.log(args)
        elif command == b'check_access':
            self.check_access(routing_id, ip, args)
        elif command == b'done':
            self.done(routing_id, ip, args)
        else:
            ZMQRouterServer.handle(self, routing_id, ip, command, args)


if __name__ == '__main__':
    port = 7340
    server = ZMQLogServer(
        port,
        handler_class=RotatingFileHandler,
        handler_kwargs={'maxBytes': 256, 'backupCount': 3},
    )
    server.run()
