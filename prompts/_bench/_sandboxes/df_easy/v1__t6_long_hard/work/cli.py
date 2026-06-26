"""linefilter: read lines from stdin, optionally transform, print them."""

import argparse
import sys


def transform(lines, upper=False):
    if upper:
        lines = [line.upper() for line in lines]
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="Filter and transform input lines.")
    parser.add_argument("--upper", action="store_true", help="uppercase each line")
    args = parser.parse_args(argv)

    lines = [line.rstrip("\n") for line in sys.stdin]
    for line in transform(lines, upper=args.upper):
        print(line)


if __name__ == "__main__":
    main()
