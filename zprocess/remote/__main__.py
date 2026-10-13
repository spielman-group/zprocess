import sys
import locale
import os

if __package__ is None:
    sys.path.insert(0, os.path.abspath('../..'))


from zprocess.remote import DEFAULT_PORT
from zprocess.remote.server import RemoteProcessServer
from zprocess.utils import disable_quick_edit, server_argument_parser, server_kwargs


def main():
    parser = server_argument_parser('zprocess remote server', DEFAULT_PORT)

    parser.add_argument(
        '-tui',
        '--text-interface',
        action='store_true',
        help="""Run as a text-based interface showing subprocesses and clients""",
    )

    args = parser.parse_args()

    def run_curses(stdscr):
        import curses
        from zprocess.remote.curses_server import RemoteProcessServerCurses
    
        curses.curs_set(False)
        curses.halfdelay(1)
        stdscr.clear()
        stdscr.refresh()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        server = RemoteProcessServerCurses(stdscr, **server_kwargs(args))
        server.shutdown_on_interrupt()

    disable_quick_edit()

    if args.text_interface:
        import curses
    
        locale.setlocale(locale.LC_ALL, '')
        curses.wrapper(run_curses)
    else:
        server = RemoteProcessServer(**server_kwargs(args))
        server.shutdown_on_interrupt()


if __name__ == '__main__':
    main()
