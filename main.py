import pygame
import random
import math

pygame.init()
width, height = 900, 600
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

# Brush state
x, y = width // 2, height // 2
angle = 0
speed = 2
brush_size = 3

screen.fill((255, 255, 255))  # white background
running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Free roaming motion (random walk)
    angle += random.uniform(-0.2, 0.2)
    x += math.cos(angle) * speed
    y += math.sin(angle) * speed

    # Wrap around screen
    x %= width
    y %= height

    pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), brush_size)

    pygame.display.flip()

pygame.quit()