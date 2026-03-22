from pydantic import ValidationError
from graph import DroneActions, Graph, Solver
from parser import (
    ConnectionValidator,
    DroneCountValidator,
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
            solver = Solver()
            drone_nbr = next(
                (
                    validator["parsed_and_validated_data"].nbr
                    for validator in res
                    if isinstance(
                        validator["parsed_and_validated_data"],
                        DroneCountValidator,
                    )
                ),
                None,
            )
            if drone_nbr is None:
                raise ValueError("test")
            drone_paths = []
            costs = {node: 0.0 for node in graph.nodes}
            for i in range(drone_nbr):
                distances = solver.process(graph.nodes, graph.nodes[0], costs)
                drone_paths.append(
                    solver.backtrack(graph.nodes[-1], distances, costs)
                )
                current = graph.nodes[0]
                while current != graph.nodes[-1]:
                    if current.capacity != float("inf"):
                        costs[current] += 2 / current.capacity
                    current = drone_paths[i][current]
            drone_actions = DroneActions(
                graph.nodes,
                graph.links,
                drone_nbr,
                drone_paths,
                goal=graph.nodes[-1],
            )
            drone_actions.process()
            visualizer = Visualizer(
                graph.nodes,
                graph.links,
                drone_actions.drones,
                drone_actions.logs,
            )
            visualizer.run()
            print(
                len(
                    max(drone_actions.drones, key=lambda x: len(x["actions"]))[
                        "actions"
                    ]
                )
            )
        except (ValidationError, ValueError) as e:
            print("Error:", e)
    except (FileNotFoundError, PermissionError) as e:
        print("Error:", e)


if __name__ == "__main__":
    main(sys.argv)
