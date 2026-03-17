from pydantic import ValidationError
from graph import Graph
from parser import (
    ConnectionValidator,
    HubValidator,
    Parser,
    StartOrEndHubValidator,
)
import sys

from visualizer import Visualizer


def main(argv: list[str]) -> None:
    parser = Parser()
    try:
        parser.open(argv[1])
        try:
            res = parser.process()
            print(res)
            graph = Graph("test")
            graph.convert_to_graph(
                [
                    node["parsed_and_validated_data"]
                    for node in res
                    if isinstance(
                        node["parsed_and_validated_data"],
                        StartOrEndHubValidator,
                    )
                    or isinstance(
                        node["parsed_and_validated_data"], HubValidator
                    )
                ],
                [
                    node["parsed_and_validated_data"]
                    for node in res
                    if isinstance(
                        node["parsed_and_validated_data"], ConnectionValidator
                    )
                ],
            )
            visualizer = Visualizer(graph.nodes, graph.links)
            visualizer.run()
        except (ValidationError, ValueError) as e:
            print("Error:", e)
    except (FileNotFoundError, PermissionError) as e:
        print("Error:", e)


if __name__ == "__main__":
    main(sys.argv)
