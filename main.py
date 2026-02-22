import pygame
import math
import random
import socket
import threading

# --- UDP EEG setup ---
UDP_IP = ""
UDP_PORT = 1000
BUFFER_SIZE = 1024

# Shared variables for EEG bands
theta_value = 0.0
beta_low_value = 0.0
alpha_value = 0.0


# --- Alpha → Brush Size (2 → 20) ---
def alpha_to_brush_size(alpha):
    # Cap alpha between 0 and 30
    alpha = max(0, min(alpha, 30))

    # Linear mapping: 0 → 2  and  30 → 20
    min_size = 2
    max_size = 20
    size = min_size + (alpha / 30.0) * (max_size - min_size)

    return int(size)


# --- Smooth Red ↔ Blue Gradient ---
def alpha_to_color(alpha):
    # Cap alpha between 0 and 30
    alpha = max(0, min(alpha, 30))

    # Normalize 0 → 1
    t = alpha / 30.0

    # Interpolate:
    # Red (255,0,0) at alpha = 0
    # Blue (0,0,255) at alpha = 30
    red = int(255 * (1 - t))
    blue = int(255 * t)

    return (red, 0, blue)


def eeg_listener():
    global theta_value, beta_low_value, alpha_value
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(1.0)

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode('ascii').strip()
            values = [float(x) for x in message.split(',')]

            if len(values) >= 63:
                theta_value = values[57]
                alpha_value = values[58]
                beta_low_value = values[59]

        except socket.timeout:
            continue
        except Exception as e:
            print("EEG listener error:", e)


threading.Thread(target=eeg_listener, daemon=True).start()


# --- Pygame setup ---
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("EEG Red-Blue Alpha Brush")

clock = pygame.time.Clock()

x, y = width // 2, height // 2
angle = 0
screen.fill((255, 255, 255))

running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                pygame.image.save(screen, "eeg_brush_art.png")
                print("Image saved as eeg_brush_art.png")

    # --- Color & Brush Size from Alpha ---
    color = alpha_to_color(alpha_value)
    brush_size = alpha_to_brush_size(alpha_value)

    # Movement
    speed = 1
    angle += random.uniform(-0.2, 0.2)
    x += math.cos(angle) * speed
    y += math.sin(angle) * speed
    x %= width
    y %= height

    pygame.draw.circle(screen, color, (int(x), int(y)), brush_size)
    pygame.display.flip()

pygame.quit()