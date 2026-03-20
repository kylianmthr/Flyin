import pygame
from graph import DronesDict, Link, Node, ZoneWeight


class Visualizer:
    def __init__(
        self,
        nodes: list[Node],
        connections: list[Link],
        drones: list[DronesDict],
    ) -> None:
        pygame.init()
        self.drones = drones
        self.nodes = nodes
        self.multiply = 1
        self.step = 0
        self.connections = connections
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = True
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        self.old_x = 0
        self.old_y = 0

    def _draw_map(self, multiplier: int) -> None:
        self.screen.fill("white")
        radius = 6 * multiplier
        offset = 15 * multiplier
        step = radius + offset
        min_x = min([node.coords[0] for node in self.nodes])
        max_x = max([node.coords[0] for node in self.nodes])
        min_y = min([node.coords[1] for node in self.nodes])
        max_y = max([node.coords[1] for node in self.nodes])
        self.node_width = (abs(max_x) - abs(min_x)) // 2
        self.node_height = (abs(max_y) - abs(min_y)) // 2
        offset_x = 400 - self.node_width * step
        offset_y = 300 - self.node_height * step
        for link in self.connections:
            pygame.draw.line(
                self.screen,
                "black",
                (
                    offset_x
                    + link.nodes[0].coords[0] * (offset + radius)
                    + self.mouse_offset_x,
                    offset_y
                    + link.nodes[0].coords[1] * (offset + radius)
                    + self.mouse_offset_y,
                ),
                (
                    offset_x
                    + link.nodes[1].coords[0] * (offset + radius)
                    + self.mouse_offset_x,
                    offset_y
                    + link.nodes[1].coords[1] * (offset + radius)
                    + self.mouse_offset_y,
                ),
                width=multiplier,
            )
        for node in self.nodes:
            try:
                pygame.draw.circle(
                    self.screen,
                    node.color if node.color else "white",
                    (
                        offset_x
                        + node.coords[0] * (offset + radius)
                        + self.mouse_offset_x,
                        offset_y
                        + node.coords[1] * (offset + radius)
                        + self.mouse_offset_y,
                    ),
                    radius,
                )
            except Exception:
                if node.color == "rainbow":
                    rainbow_circle = pygame.Surface(
                        (radius * 2, radius * 2), pygame.SRCALPHA
                    )
                    pygame.draw.circle(
                        rainbow_circle, "green", (radius, radius), radius
                    )
                    for r in range(radius, 0, -1):
                        alpha = int(255 * (r / radius))
                        color = (255, 0, 0, alpha)
                        pygame.draw.circle(
                            rainbow_circle, color, (radius, radius), r
                        )
                    self.screen.blit(
                        rainbow_circle,
                        (
                            offset_x
                            + node.coords[0] * (offset + radius)
                            - radius
                            + self.mouse_offset_x,
                            offset_y
                            + node.coords[1] * (offset + radius)
                            - radius
                            + self.mouse_offset_y,
                        ),
                    )
                else:
                    pygame.draw.circle(
                        self.screen,
                        "white",
                        (
                            offset_x
                            + node.coords[0] * (offset + radius)
                            + self.mouse_offset_x,
                            offset_y
                            + node.coords[1] * (offset + radius)
                            + self.mouse_offset_y,
                        ),
                        radius,
                    )

        pygame.display.flip()
        for drone in self.drones:
            if len(drone["actions"]) <= self.step:
                self._draw_drone(
                    next(
                        node
                        for node in self.nodes
                        if node.id == drone["actions"][-1]
                    )
                )
            elif drone["actions"][self.step] == "in_link":
                continue
            elif drone["actions"][self.step] == "wait":
                temp = drone["actions"]
                temp.remove("wait")
                if "in_link" in drone["actions"]:
                    temp.remove("in_link")
                self._draw_drone(
                    next(node for node in self.nodes if node.id == temp[-1])
                )
            else:
                self._draw_drone(
                    next(
                        node
                        for node in self.nodes
                        if node.id == drone["actions"][self.step]
                    )
                )

    def _get_node_coords(self, node: Node):
        radius = 6 * self.multiply
        offset = 15 * self.multiply
        step = radius + offset
        offset_x = 400 - self.node_width * step
        offset_y = 300 - self.node_height * step
        center_x = offset_x + node.coords[0] * step + self.mouse_offset_x
        center_y = offset_y + node.coords[1] * step + self.mouse_offset_y
        drone_size = 15 * self.multiply
        return (center_x - drone_size // 2, center_y - drone_size // 2)

    def _draw_drone(self, node):
        img = pygame.image.load("drone.png").convert_alpha()
        img = pygame.transform.scale(
            img, (15 * self.multiply, 15 * self.multiply)
        )
        coords = self._get_node_coords(node)
        self.screen.blit(img, coords)
        pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.multiply += 1
                    self._draw_map(
                        multiplier=self.multiply,
                    )
                if event.y < 0 and self.multiply != 1:
                    self.multiply -= 1
                    self._draw_map(multiplier=self.multiply)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.old_x = event.pos[0]
                self.old_y = event.pos[1]
                for node in self.nodes:
                    radius = 6 * self.multiply
                    x = node.coords[0]
                    y = node.coords[1]
                    offset = 15 * self.multiply
                    step = radius + offset
                    offset_x = 400 - self.node_width * step
                    offset_y = 300 - self.node_height * step
                    x = (
                        offset_x
                        + node.coords[0] * (offset + radius)
                        + self.mouse_offset_x
                    )
                    y = (
                        offset_y
                        + node.coords[1] * (offset + radius)
                        + self.mouse_offset_y
                    )
                    if (event.pos[0] - x) ** 2 + (
                        event.pos[1] - y
                    ) ** 2 <= radius**2:
                        print(node.id)
                        print("Weight:", ZoneWeight[node.zone.value].value)
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_offset_x += event.pos[0] - self.old_x
                self.mouse_offset_y += event.pos[1] - self.old_y
                self._draw_map(multiplier=self.multiply)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.step += 1
                    self._draw_map(multiplier=self.multiply)

    def run(self) -> None:
        self._draw_map(self.multiply)
        while self.running:
            self._handle_events()
            self.clock.tick(60)
        pygame.quit()
