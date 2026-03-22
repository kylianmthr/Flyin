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


class DroneSimulation:
    def __init__(self, filename) -> None:
        self.filename = filename
        self.parser = Parser()
        self.graph = Graph(filename)
        self.solver = Solver()
        self.hubs = []
        self.connections = []
        self.drone_nbr = 0

    def load_parser(self):
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

    def load_graph(self):
        self.graph.convert_to_graph(self.hubs, self.connections)

    def run(self):
        try:
            self.load_parser()
            self.load_graph()
            drone_paths = self.solver.generate_drones_path(
                self.drone_nbr, self.graph.nodes
            )
            drone_actions = DroneActions(
                self.graph.nodes,
                self.graph.links,
                self.drone_nbr,
                drone_paths,
                goal=self.graph.nodes[-1],
            )
            drone_actions.process()
            visualizer = Visualizer(
                self.graph.nodes,
                self.graph.links,
                drone_actions.drones,
                drone_actions.logs,
            )
            visualizer.run()
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        DroneSimulation(sys.argv[1]).run()
    else:
        print("Usage: python flyin.py <input_file>")
