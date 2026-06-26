"""linefilter: read lines from stdin, optionally transform, print them."""

import argparse
import sys


def transform(lines, upper=False, reverse=False):
    if upper:
        lines = [line.upper() for line in lines]
    if reverse:
        lines = list(reversed(lines))
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="Filter and transform input lines.")
    parser.add_argument("--upper", action="store_true", help="uppercase each line")
    parser.add_argument("--reverse", action="store_true", help="reverse order of output lines")
    args = parser.parse_args(argv)

    lines = [line.rstrip("\n") for line in sys.stdin]
    for line in transform(lines, upper=args.upper, reverse=args.reverse):
        print(line)


if __name__ == "__main__":
    main()
