if __debug__:
    # Non-interactive backend for file output
    import matplotlib
    matplotlib.use('agg')

import argparse
import asyncio
import sys
import importlib.resources
from importlib.metadata import version, PackageNotFoundError

from .interactive import async_shell_main, async_titi_main, async_command_main
from .watch import run_with_watcher


def get_version():
    try:
        return version("titi")
    except PackageNotFoundError:
        return "unknown"

def list_executables():
    """Lists available YAML executables in titi/bin."""
    try:
        bin_path = importlib.resources.files("titi") / "bin"
        if bin_path.exists():
            print("\nAvailable executables in titi/bin:")
            for item in bin_path.rglob("*.yaml"):
                 # Calculate relative path from bin_path for cleaner output if desired, or just name
                 print(f"  {item.name} ({item.parent.name})")
    except Exception:
        pass


class CustomFormatter(argparse.HelpFormatter):
    def format_help(self):
        help_text = super().format_help()
        # Capture stdout to append our custom list (not ideal but simple)
        # Actually, let's just print it after or inject it.
        return help_text

def main():
    parser = argparse.ArgumentParser(
        description="Titi is Terminal Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use 'titi [executable.yaml]' to run a diagram."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}"
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

    # Intercept --help to add our listing
    if "-h" in sys.argv or "--help" in sys.argv:
        parser.print_help()
        list_executables()
        sys.exit(0)

    args = parser.parse_args()

    try:
        if args.command_string is not None:
            asyncio.run(async_command_main(args.command_string, *args.operands))
        elif args.operands:
            file_name = args.operands[0]
            file_args = args.operands[1:]
            asyncio.run(async_titi_main(file_name, *file_args))
        else:
            # Default fallback if no args provided.
            async_shell_runner = async_shell_main("yaml/shell.yaml")
            interactive_shell = run_with_watcher(async_shell_runner)
            asyncio.run(interactive_shell)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
