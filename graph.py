from enum import Enum
import itertools
import heapq
from typing import List, TypedDict
from parser import (
    ConnectionValidator,
    HubValidator,
    StartOrEndHubValidator,
    ZoneEnum,
)


class Link:
    def __init__(self, capacity: int, node: list["Node"]) -> None:
        self.capacity = capacity
        self.nodes: list[Node] = node


class Node:
    def __init__(
        self,
        id: str,
        coords: tuple[int, int],
        color: str | None,
        capacity: float,
        start: bool = False,
        end: bool = False,
        zone: ZoneEnum = ZoneEnum.NORMAL,
    ) -> None:
        self.id = id
        self.coords = coords
        self.color = color
        self.zone = zone
        self.start = start
        self.end = end
        if capacity == -1:
            self.capacity = float("inf")
        else:
            self.capacity = capacity
        self._link: list[Link] = []

    def add_connection(self, link: Link) -> None:
        self._link.append(link)

    def remove_connection(self, link: Link) -> None:
        if self._link:
            self._link.remove(link)


class Graph:
    def __init__(self, name: str) -> None:
        self.name = name
        self.nodes: list[Node] = []
        self.links: list[Link] = []

    def convert_to_graph(
        self,
        hubs_list: list[HubValidator | StartOrEndHubValidator],
        connections: list[ConnectionValidator],
    ) -> None:
        for hub in hubs_list:
            self.nodes.append(
                Node(
                    id=hub.id,
                    coords=(hub.x, hub.y),
                    color=hub.color,
                    capacity=hub.max_drones
                    if hub.max_drones
                    else float("inf"),
                    zone=getattr(hub, "zone", ZoneEnum.NORMAL),
                    start=getattr(hub, "start", False),
                    end=getattr(hub, "end", False),
                )
            )
        for connection in connections:
            first_node = next(
                (
                    node
                    for node in self.nodes
                    if node.id == connection.connection.split("-")[0]
                ),
                None,
            )
            second_node = next(
                (
                    node
                    for node in self.nodes
                    if node.id == connection.connection.split("-")[1]
                ),
                None,
            )
            if first_node and second_node:
                link = Link(
                    connection.max_link_capacity, [first_node, second_node]
                )
                self.links.append(link)
                first_node.add_connection(link)
                second_node.add_connection(link)

    def remove(self, target: "Node") -> None:
        self.nodes.remove(target)
        for node in self.nodes:
            try:
                node.remove_connection(
                    [link for link in node._link if target in link.nodes][0]
                )
            except Exception:
                pass


class ZoneWeight(Enum):
    normal = 1
    priority = 10
    restricted = 20
    blocked = float("inf")


class Solver:
    def process(
        self, nodes: list[Node], start_node: Node, cost: dict[Node, float]
    ) -> dict[Node, float]:
        distances = {node: float("inf") for node in nodes}
        count = itertools.count()
        distances[start_node] = 0
        queue: List[tuple[float, int, "Node"]] = [(0, next(count), start_node)]
        heapq.heapify(queue)
        visited = []
        while queue:
            current = heapq.heappop(queue)
            if current[2] in visited:
                continue
            visited.append(current[2])
            if current[2]._link:
                for link in current[2]._link:
                    for neighbor in link.nodes:
                        if neighbor.zone and neighbor is not current[2]:
                            weight = (
                                distances[current[2]]
                                + ZoneWeight[neighbor.zone.value].value
                                + cost[neighbor]
                            )
                            if distances[neighbor] > weight:
                                distances[neighbor] = weight
                            heapq.heappush(
                                queue,
                                (distances[neighbor], next(count), neighbor),
                            )
        return distances

    def backtrack(
        self,
        end_node: Node,
        distances: dict[Node, float],
        cost: dict[Node, float],
    ) -> dict[Node, Node]:
        count = distances[end_node]
        path = {}
        current = end_node
        while count:
            found = False
            for link in current._link:
                for neighbor in link.nodes:
                    if neighbor != current:
                        if (
                            abs(
                                distances[current]
                                - (
                                    ZoneWeight[current.zone.value].value
                                    + cost[current]
                                )
                                - distances[neighbor]
                            )
                            < 1e-9
                        ):
                            path[neighbor] = current
                            current = neighbor
                            count = distances[neighbor]
                            found = True
                            break
                if found:
                    break
        return path

    def generate_drones_path(
        self, drone_nbr: int, nodes: list[Node]
    ) -> list[dict[Node, Node]]:
        drone_paths = []
        costs = {node: 0.0 for node in nodes}
        for i in range(drone_nbr):
            distances = self.process(nodes, nodes[0], costs)
            drone_paths.append(self.backtrack(nodes[-1], distances, costs))
            current = nodes[0]
            while current != nodes[-1]:
                if current.capacity != float("inf"):
                    costs[current] += 2 / current.capacity
                current = drone_paths[i][current]
        return drone_paths


class DronesDict(TypedDict):
    actions: list[str]
    current_node: Node
    path: dict[Node, Node]
    waited_turns: int


class DroneActions:
    def __init__(
        self,
        nodes: list[Node],
        connections: list[Link],
        nbr_drones: int,
        paths: list[dict[Node, Node]],
        goal: Node,
    ) -> None:
        self.nodes_status = {node: 0 for node in nodes}
        self.link_status = {link: 0 for link in connections}
        self.drones: list[DronesDict] = [
            {
                "actions": [nodes[0].id],
                "current_node": nodes[0],
                "path": paths[i],
                "waited_turns": 0,
            }
            for i in range(nbr_drones)
        ]
        self.goal = goal
        self.logs: list[list[str]] = []

    def finish(self) -> bool:
        for drone in self.drones:
            if drone["current_node"] != self.goal:
                return False
        return True

    def process(self) -> None:
        while not (self.finish()):
            step_log = []
            i = 0
            for drone in self.drones:
                i += 1
                if drone["current_node"] == self.goal:
                    continue
                next_node = drone["path"][drone["current_node"]]
                color = f"[{next_node.color}]"
                end = f"[/{next_node.color}]"
                link_to_next_node = next(
                    (
                        link
                        for link in drone["current_node"]._link
                        if next_node in link.nodes
                    ),
                    None,
                )
                if not (link_to_next_node):
                    raise ValueError("Error: Unexpected link")
                if next_node.capacity <= self.nodes_status[next_node]:
                    drone["waited_turns"] += 1
                    drone["actions"].append("wait")
                else:
                    if (
                        next_node.zone.value == "restricted"
                        and drone["actions"][-1] != "in_link"
                    ):
                        if (
                            link_to_next_node.capacity
                            <= self.link_status[link_to_next_node]
                        ):
                            drone["waited_turns"] += 1
                            drone["actions"].append("wait")
                        else:
                            self.link_status[link_to_next_node] += 1
                            step_log.append(
                                f"{color}D{i}-{drone['current_node'].id}"
                                f"-{next_node.id}{end}"
                            )
                            drone["actions"].append("in_link")
                            drone["waited_turns"] = 0
                    elif next_node.zone.value == "blocked":
                        pass
                    else:
                        if next_node.zone.value == "restricted":
                            self.link_status[link_to_next_node] -= 1
                        self.nodes_status[next_node] += 1
                        self.nodes_status[drone["current_node"]] -= 1
                        step_log.append(f"{color}D{i}-{next_node.id}{end}")
                        drone["current_node"] = next_node
                        drone["actions"].append(next_node.id)
                        drone["waited_turns"] = 0
            self.logs.append(step_log)
