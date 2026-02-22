import socket
import numpy as np
import joblib

# -------------------------
# LOAD MODEL
# -------------------------
clf = joblib.load("bandpower_3s_decoder.pkl")

# -------------------------
# UDP SETUP
# -------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 1000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Listening for Unicorn bandpower stream...")

# -------------------------
# SMOOTHING
# -------------------------
SMOOTHING_ALPHA = 0.8
smoothed_prob = 0.5

# -------------------------
# ONLINE LOOP
# -------------------------
while True:

    data, _ = sock.recvfrom(4096)
    payload = data.decode("ascii").strip()

    values = np.array(payload.split(","), dtype=float)

    if len(values) != 70:
        continue

    # --- Extract Alpha ---
    alpha_start = 16   # 17th value (0-index)
    beta_start = 24    # 25th value

    # Channel indices (0-based)
    C3_idx = 1
    C4_idx = 3

    C3_alpha = values[alpha_start + C3_idx]
    C4_alpha = values[alpha_start + C4_idx]

    C3_beta = values[beta_start + C3_idx]
    C4_beta = values[beta_start + C4_idx]

    # --- Lateralization ---
    alpha_diff = C3_alpha - 2*C4_alpha
    beta_diff  = C3_beta - 2*C4_beta

    features = np.array([
        C3_alpha,
        C3_beta,
        C4_alpha,
        C4_beta,
        alpha_diff,
        beta_diff
    ]).reshape(1, -1)

    # --- Predict ---
    prob_left = clf.predict_proba(features)[0][1]

    """
    smoothed_prob = (
        SMOOTHING_ALPHA * smoothed_prob +
        (1 - SMOOTHING_ALPHA) * prob_left
    )
    """

    predicted_class = int(prob_left > 0.8)
    predicted_side = "LEFT" if predicted_class == 1 else "RIGHT"

    print(
        f"P(LEFT): {prob_left:.3f} | "
        f"Pred: {predicted_side}"
    )
