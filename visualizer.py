import pygame
from graph import DronesDict, Link, Node, ZoneWeight
from rich.console import Console


class Visualizer:
    def __init__(
        self,
        nodes: list[Node],
        connections: list[Link],
        drones: list[DronesDict],
        logs: list[list[str]],
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
        self.logs = logs
        self.console = Console(highlight=False)
        self.radius = 3
        self.offset = 5
        self.step_offset = self.radius + self.offset
        min_x = min([node.coords[0] for node in self.nodes])
        max_x = max([node.coords[0] for node in self.nodes])
        min_y = min([node.coords[1] for node in self.nodes])
        max_y = max([node.coords[1] for node in self.nodes])
        self.node_width = (abs(max_x) - abs(min_x)) // 2
        self.node_height = (abs(max_y) - abs(min_y)) // 2
        self.offset_x = 400 - self.node_width * self.step_offset
        self.offset_y = 300 - self.node_height * self.step_offset
        self.img = pygame.image.load("drone.png").convert_alpha()
        self.max_step = len(
            max(drones, key=lambda x: len(x["actions"]))["actions"]
        )

    def _zoom(self) -> None:
        radius = 6
        offset = 10
        self.radius = radius * self.multiply
        self.offset = offset * self.multiply
        self.step_offset = self.radius + self.offset
        self.offset_x = 400 - self.node_width * self.step_offset
        self.offset_y = 300 - self.node_height * self.step_offset

    def _get_node_coords(self, node: Node) -> tuple[int, int]:
        return (
            self.offset_x
            + node.coords[0] * (self.offset * self.multiply + self.radius)
            + self.mouse_offset_x,
            self.offset_y
            + node.coords[1] * (self.offset * self.multiply + self.radius)
            + self.mouse_offset_y,
        )

    def _draw_map(self) -> None:
        self.screen.fill("white")
        for link in self.connections:
            pygame.draw.line(
                self.screen,
                "black",
                self._get_node_coords(link.nodes[0]),
                self._get_node_coords(link.nodes[1]),
                width=self.multiply,
            )
        for node in self.nodes:
            pygame.draw.circle(
                self.screen,
                node.color if node.color else "white",
                self._get_node_coords(node),
                self.radius,
            )

        pygame.display.flip()

    def _draw_drones(self) -> None:
        for drone in self.drones:
            if len(drone["actions"]) <= self.step:
                drone["current_node"] = next(
                    node
                    for node in self.nodes
                    if node.id == drone["actions"][-1]
                )
                self._draw_drone(drone["current_node"])
            elif drone["actions"][self.step] == "in_link":
                continue
            elif drone["actions"][self.step] == "wait":
                self._draw_drone(drone["current_node"])
            else:
                drone["current_node"] = next(
                    node
                    for node in self.nodes
                    if node.id == drone["actions"][self.step]
                )
                self._draw_drone(drone["current_node"])

    def _print_logs(self) -> None:
        if self.step - 1 >= 0 and self.step <= len(self.logs):
            self.console.print(" ".join(self.logs[self.step - 1]))

    def _get_drone_coords(self, node: Node) -> tuple[int, int]:
        center_x, center_y = self._get_node_coords(node)
        drone_size = 15 * self.multiply
        return (center_x - drone_size // 2, center_y - drone_size // 2)

    def _draw_drone(self, node: Node) -> None:
        img = pygame.transform.scale(
            self.img, (15 * self.multiply, 15 * self.multiply)
        )
        coords = self._get_drone_coords(node)
        self.screen.blit(img, coords)
        pygame.display.flip()

    def _show_step(self) -> None:
        pygame.font.init()
        font = pygame.font.SysFont("Arial", 30)
        surface = font.render(f"{self.step}/{self.max_step}", False, "black")
        self.screen.blit(surface, (3, 3))
        pygame.display.flip()

    def _show_all(self) -> None:
        self._draw_map()
        self._draw_drones()
        self._show_step()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.multiply += 1
                elif event.y < 0 and self.multiply != 1:
                    self.multiply -= 1
                self._zoom()
                self._show_all()
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:
                    dx, dy = event.rel
                    self.mouse_offset_x += dx
                    self.mouse_offset_y += dy
                    self._show_all()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.old_x = event.pos[0]
                self.old_y = event.pos[1]
                for node in self.nodes:
                    x, y = self._get_node_coords(node)
                    if (event.pos[0] - x) ** 2 + (
                        event.pos[1] - y
                    ) ** 2 <= self.radius**2:
                        print(node.id)
                        print("Weight:", ZoneWeight[node.zone.value].value)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    if self.step < self.max_step:
                        self.step += 1
                        self._show_all()
                        self._print_logs()
                if event.key == pygame.K_LEFT:
                    if self.step > 0:
                        self.step -= 1
                        self._show_all()
                        self._print_logs()

    def run(self) -> None:
        self._draw_map()
        self._draw_drones()
        self._show_step()
        while self.running:
            self._handle_events()
            self.clock.tick(60)
        pygame.quit()
