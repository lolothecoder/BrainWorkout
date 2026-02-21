import pygame
import random
import math

# Initialize pygame
pygame.init()

width, height = 900, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("EEG Art Simulation")

clock = pygame.time.Clock()

# Brush state
x, y = width // 2, height // 2
angle = 0

# Time variable for simulated brain waves
t = 0

# White background
screen.fill((255, 255, 255))

running = True
while running:
    clock.tick(60)  # 60 FPS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Simulated EEG waves using sine ---
    t += 0.02

    alpha = math.sin(t)           # calm wave
    beta = math.sin(t + 2)        # focus wave
    theta = math.sin(t + 4)       # dream wave

    # Map waves to brush behavior
    speed = 1 + (beta + 1) * 4
    brush_size = int(2 + (alpha + 1) * 8)

    color = (
        int((theta + 1) * 127),          # red channel
        50,                              
        200 - int((theta + 1) * 100)     # blue channel
    )

    # --- Movement ---
    angle += random.uniform(-0.2, 0.2)
    x += math.cos(angle) * speed
    y += math.sin(angle) * speed

    # Wrap around screen edges
    x %= width
    y %= height

    # --- Draw ---
    pygame.draw.circle(screen, color, (int(x), int(y)), brush_size)

    pygame.display.flip()

pygame.quit()