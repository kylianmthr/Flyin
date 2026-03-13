from parser import DroneCountParser, HubParser, Parser, ParserManager, StartHubParser
import sys


def main(argv: list[str]) -> None:
    parser = Parser()
    try:
        parser = ParserManager()
        print(parser.process("hub: junction-test 1 0 [color=yellow max_drones=2]"))
    except (FileNotFoundError, PermissionError) as e:
        print("Error:", e)


if __name__ == "__main__":
    main(sys.argv)
