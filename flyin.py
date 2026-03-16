from parser import (
    Parser,
)
import sys


def main(argv: list[str]) -> None:
    parser = Parser()
    try:
        parser.open(argv[1])
        print(parser.process())
    except (FileNotFoundError, PermissionError) as e:
        print("Error:", e)


if __name__ == "__main__":
    main(sys.argv)
