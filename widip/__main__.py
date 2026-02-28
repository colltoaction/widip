import sys
import argparse
import logging

# Stop starting a Matplotlib GUI
import matplotlib
matplotlib.use('agg')

from .watch import shell_main, widish_main

def build_arguments(args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-n", "--no-draw",
        action="store_true",
        help="Skips jpg drawing, just run the program"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "file_name",
        nargs="?",
        help="The yaml file to run, if not provided it will start a shell"
    )
    args = parser.parse_args(args)
    return args


def main(argv):
    args = build_arguments(argv[1:])
    draw = not args.no_draw

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    logging.debug(f"running \"{args.file_name}\" file with no-draw={args.no_draw}")

    if args.file_name is None:
        logging.debug("Starting shell")
        shell_main("bin/yaml/shell.yaml", draw)
    else:
        widish_main(args.file_name, draw)

if __name__ == "__main__":
    main(sys.argv)