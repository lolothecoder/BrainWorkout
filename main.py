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


# --- EEG → 3 Color Mapping ---
def eeg_to_color(theta, alpha):
    """
    Only returns:
    Red     = strong theta (deep relaxation)
    Blue    = strong alpha (eyes closed)
    Orange  = mixed state
    """

    # ---- Adjust these thresholds to your signal range ----
    alpha_threshold = 15
    theta_threshold = 15

    # Blue → strong alpha (close eyes)
    if alpha > alpha_threshold and theta < theta_threshold:
        return (0, 0, 255)

    # Red → strong theta
    elif theta > theta_threshold and alpha < alpha_threshold:
        return (255, 0, 0)

    # Orange → everything else (blend state)
    else:
        return (255, 140, 0)


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
width, height = 900, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("EEG Color Brush Art")

clock = pygame.time.Clock()

x, y = width // 2, height // 2
angle = 0
brush_size = 8
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

    # --- Get restricted EEG color ---
    color = eeg_to_color(theta_value, alpha_value)

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