import pygame
from graph import Link, Node
from rich.console import Console


class Card:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
        description: str,
        bg_color: tuple[int, int, int] = (255, 255, 255),
        title_color: tuple[int, int, int] = (30, 41, 59),
        desc_color: tuple[int, int, int] = (71, 85, 105),
        shadow_color: tuple[int, int, int] = (210, 215, 220),
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.description = description
        self.bg_color = bg_color
        self.title_color = title_color
        self.desc_color = desc_color
        self.shadow_color = shadow_color
        self.title_font = pygame.font.SysFont("arial", 26, bold=True)
        self.desc_font = pygame.font.SysFont("arial", 18)
        self.padding = 20
        self.border_radius = 15
        self.shadow_offset = 6

    def _draw_text_wrapped(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
    ) -> None:
        words = text.split(" ")
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            width, _ = font.size(" ".join(current_line))
            if width > rect.width or "\n" in word:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word.replace("\n", "")]
        if current_line:
            lines.append(" ".join(current_line))
        y_offset = rect.y
        for line in lines:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (rect.x, y_offset))
            y_offset += font.get_linesize() + 4

    def draw(self, surface: pygame.Surface) -> None:
        shadow_rect = self.rect.copy()
        shadow_rect.x += self.shadow_offset
        shadow_rect.y += self.shadow_offset
        pygame.draw.rect(
            surface,
            self.shadow_color,
            shadow_rect,
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            surface, self.bg_color, self.rect, border_radius=self.border_radius
        )
        title_surf = self.title_font.render(self.title, True, self.title_color)
        surface.blit(
            title_surf,
            (self.rect.x + self.padding, self.rect.y + self.padding),
        )
        desc_y = (
            self.rect.y + self.padding + self.title_font.get_linesize() + 10
        )
        desc_rect = pygame.Rect(
            self.rect.x + self.padding,
            desc_y,
            self.rect.width - (self.padding * 2),
            self.rect.height - (desc_y - self.rect.y) - self.padding,
        )
        self._draw_text_wrapped(
            surface,
            self.description,
            self.desc_font,
            self.desc_color,
            desc_rect,
        )
        pygame.display.flip()


class Visualizer:
    def __init__(
        self,
        nodes: list[Node],
        connections: list[Link],
        paths: list[dict[int, Node]],
        logs: list[list[str]],
        max_turns: int,
    ) -> None:
        pygame.init()
        self.paths = paths
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
        self.max_step = max_turns
        self.is_visible = False
        self.info_card = Card(
            x=5,
            y=50,
            width=350,
            height=200,
            title="",
            description="",
        )
        self.capacities = {node.id: 0 for node in nodes}
        self.capacities[nodes[0].id] = len(paths)

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
                try:
                    pygame.draw.circle(
                        self.screen,
                        node.color if node.color else "white",
                        self._get_node_coords(node),
                        self.radius,
                    )
                except Exception:
                    pygame.draw.circle(
                        self.screen,
                        "white",
                        self._get_node_coords(node),
                        self.radius,
                    )

        pygame.display.flip()

    def _draw_drones(self) -> None:
        for node in self.nodes:
            self.capacities[node.id] = 0
        for path in self.paths:
            last_turn = max(path.keys())
            if self.step >= last_turn:
                current_node = path[last_turn]
                self.capacities[current_node.id] += 1
                self._draw_drone(current_node)
            elif self.step in path:
                current_node = path[self.step]
                self.capacities[current_node.id] += 1
                self._draw_drone(current_node)
            else:
                # prev_node = path[self.step - 1]
                # next_node = path[self.step + 1]
                pass

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
        font = pygame.font.SysFont("arial", 30)
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
                if event.button == 1:
                    self.old_x = event.pos[0]
                    self.old_y = event.pos[1]
                    for node in self.nodes:
                        x, y = self._get_node_coords(node)
                        if (event.pos[0] - x) ** 2 + (
                            event.pos[1] - y
                        ) ** 2 <= self.radius**2:
                            self.is_visible = True
                            self.info_card.title = node.id
                            self.info_card.description = node.zone.name
                            self.info_card.description += (
                                " \n"
                                f"{self.capacities[node.id]}/{node.capacity}"
                            )
                            break
                        self.is_visible = False
                    self._show_all()
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
        self._show_all()
        while self.running:
            self._handle_events()
            if self.is_visible:
                self.info_card.draw(self.screen)
            self.clock.tick(60)
        pygame.quit()
