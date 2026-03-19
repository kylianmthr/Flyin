from enum import Enum
import itertools
import heapq
from typing import List
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
            if isinstance(hub, HubValidator):
                self.nodes.append(
                    Node(
                        id=hub.id,
                        coords=(hub.x, hub.y),
                        color=hub.color,
                        zone=hub.zone,
                    )
                )
            else:
                self.nodes.append(
                    Node(
                        id=hub.id,
                        coords=(hub.x, hub.y),
                        color=hub.color,
                        start=hub.start,
                        end=hub.end,
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
        self, nodes: list[Node], start_node: Node
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
            print(current)
            if current[2]._link:
                for link in current[2]._link:
                    for neighbor in link.nodes:
                        print(neighbor)
                        if neighbor.zone and neighbor is not current[2]:
                            if (
                                distances[neighbor]
                                > distances[current[2]]
                                + ZoneWeight[neighbor.zone.value].value
                            ):
                                if neighbor.zone.value == "priority":
                                    distances[neighbor] = 1
                                distances[neighbor] = (
                                    distances[current[2]]
                                    + ZoneWeight[neighbor.zone.value].value
                                )
                            print(neighbor)
                            heapq.heappush(
                                queue,
                                (distances[neighbor], next(count), neighbor),
                            )
        return distances

    def backtrack(
        self, end_node: Node, distances: dict[Node, float]
    ) -> dict[Node, Node]:
        count = distances[end_node]
        path = {}
        current = end_node
        while count:
            test = False
            for link in current._link:
                for neighbor in link.nodes:
                    if neighbor != current:
                        if (
                            distances[current]
                            - ZoneWeight[current.zone.value].value
                            == distances[neighbor]
                        ):
                            path[neighbor] = current
                            current = neighbor
                            count = distances[neighbor]
                            test = True
                            break
                if test:
                    break
        return path
