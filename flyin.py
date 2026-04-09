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


class DroneSimulation:
    def __init__(self, filename: str) -> None:
        """Initializes a simulation instance for a map file.

        Args:
            filename: Path to the input map file.
        """
        self.filename = filename
        self.parser = Parser()
        self.graph = Graph(filename)
        self.solver = Solver()
        self.hubs: list[HubValidator | StartOrEndHubValidator] = []
        self.connections: list[ConnectionValidator] = []
        self.drone_nbr = 0

    def load_parser(self) -> None:
        """Parses and validates drones, hubs, and connections from input."""
        self.parser.open(self.filename)
        res = self.parser.process()
        self.hubs = [
            node["parsed_and_validated_data"]
            for node in res
            if isinstance(
                node["parsed_and_validated_data"],
                StartOrEndHubValidator,
            )
            or isinstance(node["parsed_and_validated_data"], HubValidator)
        ]
        specials_hub = [
            node
            for node in self.hubs
            if isinstance(node, StartOrEndHubValidator)
        ]
        if len(specials_hub) != 2:
            raise ValueError(
                "Error: Map must contains exactly one start and one end hub"
            )
        self.connections = [
            node["parsed_and_validated_data"]
            for node in res
            if isinstance(
                node["parsed_and_validated_data"], ConnectionValidator
            )
        ]
        self.drone_nbr = next(
            (
                validator["parsed_and_validated_data"].nbr
                for validator in res
                if isinstance(
                    validator["parsed_and_validated_data"],
                    DroneCountValidator,
                )
            )
        )

    def load_graph(self) -> None:
        """Builds the in-memory graph from parsed hubs and connections."""
        self.graph.convert_to_graph(self.hubs, self.connections)
        for node in self.graph.nodes:
            if not len(node._link):
                raise ValueError(
                    "Error: All hubs must have at least one connection"
                )

    def run(self) -> None:
        """Runs parsing, solving, logging, and visualization for the map."""
        try:
            self.load_parser()
            self.load_graph()
            drone_paths = self.solver.generate_drones_path(
                self.drone_nbr,
                self.graph.nodes,
                [node for node in self.graph.nodes if node.end][0],
            )
            drone_actions = DroneActions(
                self.drone_nbr,
                drone_paths,
                goal=[node for node in self.graph.nodes if node.end][0],
            )
            drone_actions.process()
            visualizer = Visualizer(
                self.graph.nodes,
                self.graph.links,
                drone_actions.paths,
                drone_actions.logs,
                drone_actions.max_turn,
            )
            visualizer.run()
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        DroneSimulation(sys.argv[1]).run()
    else:
        print("Usage: python flyin.py <input_file>")
