if __debug__:
    # Non-interactive backend for file output
    import matplotlib
    matplotlib.use('agg')

import argparse
import asyncio

from .interactive import async_shell_main, async_widish_main, async_command_main
from .watch import run_with_watcher


def main():
    parser = argparse.ArgumentParser(
        description="Widip: an interactive environment for computing with wiring diagrams"
    )
    parser.add_argument(
        "-c",
        dest="command_string",
        help="read commands from the first non-option argument"
    )
    parser.add_argument(
        "operands",
        nargs=argparse.REMAINDER,
        help="[command_string | file] [arguments...]"
    )

    args = parser.parse_args()

    try:
        if args.command_string is not None:
            asyncio.run(async_command_main(args.command_string, *args.operands))
        elif args.operands:
            file_name = args.operands[0]
            file_args = args.operands[1:]
            asyncio.run(async_widish_main(file_name, *file_args))
        else:
            async_shell_runner = async_shell_main("bin/yaml/shell.yaml")
            interactive_shell = run_with_watcher(async_shell_runner)
            asyncio.run(interactive_shell)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
