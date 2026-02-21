import pygame
import random
import socket
import threading

# --- UDP EEG setup ---
UDP_IP = ""        # listen on all interfaces
UDP_PORT = 12345   # replace with your port
BUFFER_SIZE = 1024

bands = ['delta', 'theta', 'alpha', 'beta_low', 'beta_mid', 'beta_high', 'gamma']

# Shared variables for EEG bands
theta_value = 0.0
beta_low_value = 0.0
alpha_value = 0.0

# Map EEG band (0-30) to 0-255 for RGB
def map_band_to_color(value, min_val=0, max_val=30):
    value = max(min_val, min(max_val, value))
    return int((value - min_val) / (max_val - min_val) * 255)

def eeg_listener():
    """Background thread to listen for EEG UDP packets."""
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
                # Extract average bands: indices 57-63 in 70-value payload
                # 57→delta, 58→theta, 59→alpha, 60→beta_low, 61→beta_mid, 62→beta_high, 63→gamma
                theta_value = values[57]      # index 57 = theta
                alpha_value = values[58]      # index 58 = alpha
                beta_low_value = values[59]   # index 59 = beta_low
        except socket.timeout:
            continue
        except Exception as e:
            print("EEG listener error:", e)

# Start EEG listener in a background thread
threading.Thread(target=eeg_listener, daemon=True).start()

# --- Pygame setup ---
pygame.init()
width, height = 900, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("EEG Color Brush Art")

clock = pygame.time.Clock()

# Brush state
x, y = width // 2, height // 2
angle = 0
brush_size = 8  # constant size

# White background
screen.fill((255, 255, 255))

running = True
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Map EEG bands to RGB color ---
    r = map_band_to_color(theta_value)
    g = map_band_to_color(beta_low_value)
    b = map_band_to_color(alpha_value)
    color = (r, g, b)

    # --- Optional movement ---
    speed = 4
    angle += random.uniform(-0.2, 0.2)
    x += random.cos(angle) * speed
    y += random.sin(angle) * speed
    x %= width
    y %= height

    # --- Draw brush ---
    pygame.draw.circle(screen, color, (int(x), int(y)), brush_size)

    pygame.display.flip()

pygame.quit()