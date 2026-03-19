from pydantic import ValidationError
from graph import Graph, Solver
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
            print("Neighbors:", graph.nodes[0]._link)
            solver = Solver()
            path = solver.backtrack(
                graph.nodes[-1],
                solver.process(graph.nodes, graph.nodes[0]),
            )
            current = graph.nodes[0]
            path_str = f"{current.id}"
            while current != graph.nodes[-1]:
                current = path[current]
                path_str += f" -> {current.id}"
            print(path_str)
            print(
                "Path to first node to last node:",
            )
            print(graph.nodes[-1].end)
            visualizer = Visualizer(graph.nodes, graph.links)
            visualizer.run()
        except (ValidationError, ValueError) as e:
            print("Error:", e)
    except (FileNotFoundError, PermissionError) as e:
        print("Error:", e)


if __name__ == "__main__":
    main(sys.argv)
