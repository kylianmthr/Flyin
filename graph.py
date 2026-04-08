from enum import Enum
import itertools
import heapq
from typing import TypedDict
from parser import (
    ConnectionValidator,
    HubValidator,
    StartOrEndHubValidator,
    ZoneEnum,
)
from collections import defaultdict


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
    priority = 1
    restricted = 2
    blocked = float("inf")


class Solver:
    def __init__(self) -> None:
        self.node_reservations: dict[tuple[Node, float | int], int] = (
            defaultdict(int)
        )
        self.link_reservations: dict[tuple[Link, int], int] = defaultdict(int)

    def process(
        self,
        start_node: Node,
        end_node: Node,
        start_turn: int,
    ) -> dict[tuple[Node, int], float]:
        distances: dict[tuple[Node, int], float] = defaultdict(
            lambda: float("inf")
        )
        distances[(start_node, start_turn)] = 0
        count = itertools.count()
        queue = [(start_turn, next(count), start_node)]
        heapq.heapify(queue)
        visited = []
        while queue:
            current_turn, _, current_node = heapq.heappop(queue)
            if (current_node, current_turn) in visited:
                continue
            visited.append((current_node, current_turn))
            if current_node == end_node:
                break
            next_turn = current_turn + 1
            if (
                self.node_reservations[(current_node, next_turn)]
                < current_node.capacity
                or current_node.start
                or current_node.end
            ):
                if distances[(current_node, next_turn)] > next_turn:
                    distances[(current_node, next_turn)] = next_turn
                    heapq.heappush(
                        queue, (next_turn, next(count), current_node)
                    )
                for link in current_node._link:
                    for neighbor in link.nodes:
                        if (
                            neighbor == current_node
                            or neighbor.zone.value == "blocked"
                        ):
                            continue
                        cost = ZoneWeight[neighbor.zone.value].value
                        arrival_turn = current_turn + cost
                        if (
                            self.node_reservations[(neighbor, arrival_turn)]
                            >= neighbor.capacity
                            and not neighbor.end
                        ):
                            continue
                        if (
                            cost == 2
                            and self.link_reservations[
                                (link, current_turn + 1)
                            ]
                            >= link.capacity
                        ):
                            continue
                        if (
                            distances[(neighbor, int(arrival_turn))]
                            > arrival_turn
                        ):
                            distances[(neighbor, int(arrival_turn))] = (
                                arrival_turn
                            )
                            heapq.heappush(
                                queue, (arrival_turn, next(count), neighbor)
                            )
        return distances

    def backtrack(
        self,
        end_node: Node,
        arrival_turn: int,
        distances: dict[tuple[Node, int], float],
    ) -> dict[int, Node]:
        path: dict[int, Node] = {}
        current_node = end_node
        current_turn = arrival_turn
        path[current_turn] = current_node
        while current_turn > 0:
            found_predecessor = False
            prev_turn_wait = current_turn - 1
            if (
                distances.get((current_node, prev_turn_wait), float("inf"))
                == prev_turn_wait
            ):
                current_turn = prev_turn_wait
                path[current_turn] = current_node
                continue
            cost = 2 if current_node.zone.value == "restricted" else 1
            prev_turn_move = current_turn - cost
            for link in current_node._link:
                for neighbor in link.nodes:
                    if neighbor != current_node:
                        if (
                            distances.get(
                                (neighbor, prev_turn_move), float("inf")
                            )
                            == prev_turn_move
                        ):
                            current_node = neighbor
                            current_turn = prev_turn_move
                            path[current_turn] = current_node
                            found_predecessor = True
                            break
                if found_predecessor:
                    break
            if not found_predecessor:
                raise ValueError(
                    f"Can't backtrack {current_node.id} (turn: {current_turn})"
                )

        return path

    def generate_drones_path(
        self, drone_nbr: int, nodes: list[Node], end_node: Node
    ) -> list[dict[int, Node]]:
        drone_paths = []
        for i in range(drone_nbr):
            distances = self.process(nodes[0], end_node, 0)
            possible_arrivals = [
                turn for (node, turn) in distances.keys() if node == end_node
            ]
            if not possible_arrivals:
                raise ValueError(f"Can't find valid path for drone {i + 1}")
            arrival_turn = min(possible_arrivals)
            time_path = self.backtrack(end_node, arrival_turn, distances)
            sorted_turns = sorted(time_path.keys())
            for index in range(len(sorted_turns)):
                current_turn = sorted_turns[index]
                current_node = time_path[current_turn]
                self.node_reservations[(current_node, current_turn)] += 1
                if index < len(sorted_turns) - 1:
                    next_turn = sorted_turns[index + 1]
                    next_node = time_path[next_turn]
                    if current_node != next_node:
                        used_link = next(
                            (
                                link
                                for link in current_node._link
                                if next_node in link.nodes
                            ),
                            None,
                        )
                        if used_link and (next_turn - current_turn == 2):
                            transit_turn = current_turn + 1
                            self.link_reservations[
                                (used_link, transit_turn)
                            ] += 1
            drone_paths.append(time_path)

        return drone_paths


class DronesDict(TypedDict):
    actions: list[str]
    current_node: Node
    path: dict[Node, Node]
    waited_turns: int


class DroneActions:
    def __init__(
        self,
        nbr_drones: int,
        paths: list[dict[int, "Node"]],
        goal: "Node",
    ) -> None:
        self.nbr_drones = nbr_drones
        self.paths = paths
        self.goal = goal
        self.logs: list[list[str]] = []
        self.max_turn = max(max(path.keys()) for path in paths) if paths else 0

    def process(self) -> None:
        for current_turn in range(1, self.max_turn + 1):
            step_log = []
            for i in range(self.nbr_drones):
                drone_id = i + 1
                path = self.paths[i]
                if current_turn > max(path.keys()):
                    continue
                prev_node = path.get(current_turn - 1)
                current_node = path.get(current_turn)
                if current_node is None:
                    next_node = path.get(current_turn + 1)
                    if prev_node and next_node:
                        step_log.append(
                            f"D{drone_id}-{prev_node.id}-{next_node.id}"
                        )
                elif prev_node is None:
                    color = (
                        f"[{current_node.color}]" if current_node.color else ""
                    )
                    end = (
                        f"[/{current_node.color}]"
                        if current_node.color
                        else ""
                    )
                    step_log.append(
                        f"{color}D{drone_id}-{current_node.id}{end}"
                    )
                elif current_node != prev_node:
                    color = (
                        f"[{current_node.color}]" if current_node.color else ""
                    )
                    end = (
                        f"[/{current_node.color}]"
                        if current_node.color
                        else ""
                    )
                    step_log.append(
                        f"{color}D{drone_id}-{current_node.id}{end}"
                    )
                else:
                    pass
            if step_log:
                self.logs.append(step_log)
