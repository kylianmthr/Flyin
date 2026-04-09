from typing import Any
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
        """Initializes an information card UI component.

        Args:
            x: Left position in pixels.
            y: Top position in pixels.
            width: Card width in pixels.
            height: Card height in pixels.
            title: Card title text.
            description: Card body text.
            bg_color: Card background color.
            title_color: Title text color.
            desc_color: Description text color.
            shadow_color: Shadow color.
        """
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
        surface: pygame.surface.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
    ) -> None:
        """Draws wrapped text within a bounding rectangle.

        Args:
            surface: Destination surface.
            text: Text to render.
            font: Font used for rendering.
            color: Text color.
            rect: Bounding rectangle for wrapped text.
        """
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

    def draw(self, surface: pygame.surface.Surface) -> None:
        """Renders the full card with title and wrapped description.

        Args:
            surface: Destination surface.
        """
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
        """Initializes pygame state for simulation playback.

        Args:
            nodes: Nodes to render.
            connections: Links to render.
            paths: Time-indexed drone paths.
            logs: Per-turn movement logs.
            max_turns: Total number of turns in the simulation.
        """
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
        self.link_capacities = {link: 0 for link in connections}
        self.capacities[nodes[0].id] = len(paths)
        self.raw_rainbow_image = pygame.image.load(
            "rainbow_circle.png"
        ).convert_alpha()
        diameter = self.radius * 2
        self.rainbow_image = pygame.transform.scale(
            self.raw_rainbow_image, (diameter, diameter)
        )

    def _zoom(self) -> None:
        """Recomputes drawing dimensions after zoom changes."""
        radius = 6
        offset = 10
        self.radius = radius * self.multiply
        self.offset = offset * self.multiply
        self.step_offset = self.radius + self.offset
        self.offset_x = 400 - self.node_width * self.step_offset
        self.offset_y = 300 - self.node_height * self.step_offset
        diameter = self.radius * 2
        self.rainbow_image = pygame.transform.scale(
            self.raw_rainbow_image, (diameter, diameter)
        )

    def _get_node_coords(self, node: Node) -> tuple[int, int]:
        """Converts a node position to screen coordinates.

        Args:
            node: Node to project.

        Returns:
            The node screen coordinates.
        """
        return (
            self.offset_x
            + node.coords[0] * (self.offset * self.multiply + self.radius)
            + self.mouse_offset_x,
            self.offset_y
            + node.coords[1] * (self.offset * self.multiply + self.radius)
            + self.mouse_offset_y,
        )

    def _draw_map(self) -> None:
        """Draws all links and nodes for the current viewport."""
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
                coords = self._get_node_coords(node)
                try:
                    pygame.draw.circle(
                        self.screen,
                        node.color if node.color else "white",
                        coords,
                        self.radius,
                    )
                except Exception:
                    img_rect = self.rainbow_image.get_rect(center=coords)
                    self.screen.blit(self.rainbow_image, img_rect)

        pygame.display.flip()

    def _draw_drones(self) -> None:
        """Draws drone sprites and updates node occupancy counters."""
        for node in self.nodes:
            self.capacities[node.id] = 0
        for link in self.connections:
            self.link_capacities[link] = 0
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
                prev_node = path[self.step - 1]
                next_node = path[self.step + 1]
                link = next(
                    (
                        link
                        for link in self.connections
                        if prev_node in link.nodes and next_node in link.nodes
                    )
                )
                self.link_capacities[link] += 1

    def _print_logs(self) -> None:
        """Prints logs for the current displayed simulation turn."""
        if self.step - 1 >= 0 and self.step <= len(self.logs):
            self.console.print(" ".join(self.logs[self.step - 1]))

    def _get_drone_coords(self, node: Node) -> tuple[int, int]:
        """Computes top-left sprite coordinates for a drone on a node.

        Args:
            node: Node where the drone is located.

        Returns:
            Top-left screen coordinates for the drone sprite.
        """
        center_x, center_y = self._get_node_coords(node)
        drone_size = 15 * self.multiply
        return (center_x - drone_size // 2, center_y - drone_size // 2)

    def _draw_drone(self, node: Node) -> None:
        """Draws a single drone sprite on the given node.

        Args:
            node: Node where the drone should be rendered.
        """
        img = pygame.transform.scale(
            self.img, (15 * self.multiply, 15 * self.multiply)
        )
        coords = self._get_drone_coords(node)
        self.screen.blit(img, coords)
        pygame.display.flip()

    def _show_step(self) -> None:
        """Displays the current turn indicator on the screen."""
        pygame.font.init()
        font = pygame.font.SysFont("arial", 30)
        surface = font.render(f"{self.step}/{self.max_step}", False, "black")
        self.screen.blit(surface, (3, 3))
        pygame.display.flip()

    def _show_all(self) -> None:
        """Renders map, drones, and turn indicator in one pass."""
        self._draw_map()
        self._draw_drones()
        self._show_step()

    def _point_to_line_dist(
        self, px: float, py: float, x1: float, y1: float, x2: float, y2: float
    ) -> Any:
        """
        Calculate the shortest distance from a point (px, py) to a line
        segment defined by (x1, y1) and (x2, y2).

        If the segment is a single point, returns the Euclidean distance from
        the point to (x1, y1).
        Otherwise, projects the point onto the segment and returns the distance
        to the closest point on the segment.

        Args:
            px (float): X coordinate of the point.
            py (float): Y coordinate of the point.
            x1 (float): X coordinate of the segment start.
            y1 (float): Y coordinate of the segment start.
            x2 (float): X coordinate of the segment end.
            y2 (float): Y coordinate of the segment end.

        Returns:
            float: The shortest distance from the point to the line segment.
        """
        dx = x2 - x1
        dy = y2 - y1
        length_squared = dx**2 + dy**2
        if length_squared == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_squared))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

    def _handle_events(self) -> None:
        """Handles input events for zoom, pan, selection, and stepping."""
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
                    click_handled = False
                    for node in self.nodes:
                        x, y = self._get_node_coords(node)
                        if (event.pos[0] - x) ** 2 + (
                            event.pos[1] - y
                        ) ** 2 <= self.radius**2:
                            self.is_visible = True
                            self.info_card.title = str(node.id)
                            self.info_card.description = node.zone.name
                            self.info_card.description += (
                                " \n"
                                f"{self.capacities[node.id]}/{node.capacity}"
                            )
                            click_handled = True
                            break
                    if not click_handled:
                        click_tolerance = max(5, self.multiply * 2)
                        for link in self.connections:
                            x1, y1 = self._get_node_coords(link.nodes[0])
                            x2, y2 = self._get_node_coords(link.nodes[1])
                            dist = self._point_to_line_dist(
                                event.pos[0], event.pos[1], x1, y1, x2, y2
                            )
                            if dist <= click_tolerance:
                                self.is_visible = True
                                self.info_card.title = (
                                    f"{link.nodes[0].id} ↔ {link.nodes[1].id}"
                                )
                                cap = getattr(link, "capacity", "N/A")
                                self.info_card.description = (
                                    f"{self.link_capacities[link]}/{cap}"
                                )
                                click_handled = True
                                break
                    if not click_handled:
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
        """Starts and maintains the interactive visualization loop."""
        self._show_all()
        while self.running:
            self._handle_events()
            if self.is_visible:
                self.info_card.draw(self.screen)
            self.clock.tick(60)
        pygame.quit()
