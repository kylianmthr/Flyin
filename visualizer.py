import pygame
from graph import Link, Node


class Visualizer:
    def __init__(self, nodes: list[Node], connections: list[Link]) -> None:
        pygame.init()
        self.nodes = nodes
        self.multiply = 1
        self.connections = connections
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = True

    def _draw_map(self, multiplier):
        self.screen.fill("white")
        radius = 12 * multiplier
        offset = 40 * multiplier
        step = radius + offset
        min_x = min([node.coords[0] for node in self.nodes])
        max_x = max([node.coords[0] for node in self.nodes])
        min_y = min([node.coords[1] for node in self.nodes])
        max_y = max([node.coords[1] for node in self.nodes])
        print(min_x, max_x)
        self.node_width = (max_x - min_x) // 2
        self.node_height = (max_y - min_y) // 2
        offset_x = 400 - self.node_width * step
        offset_y = 300 - self.node_height * step
        for link in self.connections:
            pygame.draw.line(
                self.screen,
                "black",
                (
                    offset_x + link.nodes[0].coords[0] * (offset + radius),
                    offset_y + link.nodes[0].coords[1] * (offset + radius),
                ),
                (
                    offset_x + link.nodes[1].coords[0] * (offset + radius),
                    offset_y + link.nodes[1].coords[1] * (offset + radius),
                ),
                width=multiplier * 2,
            )
        for node in self.nodes:
            pygame.draw.circle(
                self.screen,
                "black",
                (
                    offset_x + node.coords[0] * (offset + radius),
                    offset_y + node.coords[1] * (offset + radius),
                ),
                radius * 1.2,
            )
            pygame.draw.circle(
                self.screen,
                node.color if node.color else "white",
                (
                    offset_x + node.coords[0] * (offset + radius),
                    offset_y + node.coords[1] * (offset + radius),
                ),
                radius,
            )

        pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.multiply += 1
                    self._draw_map(multiplier=self.multiply)
                if event.y < 0 and self.multiply != 1:
                    self.multiply -= 1
                    self._draw_map(multiplier=self.multiply)

    def run(self) -> None:
        self._draw_map(self.multiply)
        while self.running:
            self._handle_events()
            self.clock.tick(60)
        pygame.quit()
