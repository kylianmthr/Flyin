from parser import (
    ConnectionValidator,
    HubValidator,
    StartOrEndHubValidator,
    ZoneEnum,
)


class Link:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.nodes: list[Node] = []


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
        self._link: Link | None = None

    def add_connection(self, node: "Node"):
        if self._link:
            self._link.nodes.append(node)

    def remove_connection(self, node: "Node"):
        if self._link:
            self._link.nodes.remove(node)

    def add_link(self, link: Link):
        self._link = link


class Graph:
    def __init__(self, name: str) -> None:
        self.name = name
        self.nodes: list[Node] = []
        self.links: list[Link] = []

    def convert_to_graph(
        self,
        hubs_list: list[HubValidator | StartOrEndHubValidator],
        connections: list[ConnectionValidator],
    ):
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
            link = Link(connection.max_link_capacity)
            self.links.append(link)
            if first_node and second_node:
                first_node.add_link(link)
                second_node.add_link(link)
                first_node.add_connection(second_node)
                second_node.add_connection(first_node)

    def remove(self, target: "Node"):
        self.nodes.remove(target)
        for node in self.nodes:
            try:
                node.remove_connection(target)
            except Exception:
                pass
