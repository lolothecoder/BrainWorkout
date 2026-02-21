import socket

# UDP configuration
UDP_IP = ""        # listen on all interfaces
UDP_PORT = 1000   # replace with your port
BUFFER_SIZE = 1024

# Frequency bands
bands = ['delta', 'theta', 'alpha', 'beta_low', 'beta_mid', 'beta_high', 'gamma']

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Set a timeout so Ctrl+C works
sock.settimeout(1.0)

print(f"Listening for Unicorn Bandpower UDP packets on port {UDP_PORT}...")

try:
    while True:
        try:
            # Receive UDP packet
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = data.decode('ascii').strip()
            
            # Convert all values to floats
            try:
                values = [float(x) for x in message.split(',')]
            except ValueError:
                print("Received malformed data:", message)
                continue
            
            # Check packet length
            if len(values) < 63:
                print("Not enough values in packet:", len(values))
                continue
            
            # Extract average bandpower (values 57–63 -> indices 56–62)
            average_bandpower = {bands[i]: values[56 + i] for i in range(7)}
            
            print("Average Bandpower:", average_bandpower)
        
        except socket.timeout:
            # Timeout reached, loop back to check for Ctrl+C
            continue

except KeyboardInterrupt:
    print("\nListener stopped by user.")

finally:
    sock.close()
    print("Socket closed.")