import pygame
from graph import Link, Node


class Visualizer:
    def __init__(self, nodes: list[Node], connections: list[Link]) -> None:
        pygame.init()
        self.nodes = nodes
        self.multiply = 1
        self.connections = connections
        self.screen = pygame.display.set_mode((800, 600))
        self.screen.fill("white")
        self.clock = pygame.time.Clock()
        self.running = True

    def _draw_map(self, multiplier):
        self.radius = 3 * multiplier
        self.prev_y = []
        offset = 10 * multiplier
        self.node_width = (len(self.nodes)) * offset + (
            len(self.nodes) - 1
        ) * self.radius
        self.node_height = sum(
            [node.coords[1] * offset for node in self.nodes]
        )
        for node in self.nodes:
            if node.coords[1] not in self.prev_y:
                self.node_height = +self.radius
                self.prev_y.append(node.coords[1])
        i = 0
        offset_x = (800 - self.node_width) // 1.5
        offset_y = (400 - self.node_height) // 2
        for link in self.connections:
            pygame.draw.line(
                self.screen,
                "black",
                (
                    offset_x
                    + link.nodes[0].coords[0] * (offset + self.radius),
                    offset_y
                    + link.nodes[0].coords[1] * (offset + self.radius),
                ),
                (
                    offset_x
                    + link.nodes[1].coords[0] * (offset + self.radius),
                    offset_y
                    + link.nodes[1].coords[1] * (offset + self.radius),
                ),
            )
        for node in self.nodes:
            pygame.draw.circle(
                self.screen,
                "black",
                (
                    offset_x + node.coords[0] * (offset + self.radius),
                    offset_y + node.coords[1] * (offset + self.radius),
                ),
                self.radius * 1.2,
            )
            pygame.draw.circle(
                self.screen,
                node.color if node.color else "white",
                (
                    offset_x + node.coords[0] * (offset + self.radius),
                    offset_y + node.coords[1] * (offset + self.radius),
                ),
                self.radius,
            )
            print(i)
            i += 1

        pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.screen.fill("white")
                    self.multiply += 1
                    self._draw_map(multiplier=self.multiply)
                if event.y < 0:
                    self.screen.fill("white")
                    self.multiply -= 1
                    self._draw_map(multiplier=self.multiply)

    def run(self) -> None:
        self._draw_map(self.multiply)
        while self.running:
            self._handle_events()
            self.clock.tick(60)
        pygame.quit()
