import mne
import numpy as np
import joblib
from scipy.signal import welch
import glob

# -------------------------
# LOAD TRAINED MODEL
# -------------------------
clf = joblib.load("bandpower_3s_decoder.pkl")  # rename if needed

# -------------------------
# SETTINGS
# -------------------------
FILE_EDF=  r"C:\Users\loicf\Downloads\S002R04.edf"

SELECTED_CHANNELS = ["C3", "Cz", "C4"]

BANDS = {
    "alpha": (8, 12),
    "beta_low": (13, 20),
    "beta_mid": (20, 25),
    "beta_high": (25, 30),
}

WINDOW_SECONDS = 2.0
STEP_SECONDS = 2.0
SMOOTHING_ALPHA = 0.8

# Load raw EEG
raw = mne.io.read_raw_edf(FILE_EDF, preload=True, verbose=False)
raw.rename_channels(lambda x: x.replace(".", "").capitalize())
raw.pick_channels(["C3", "Cz", "C4"])

events, event_id = mne.events_from_annotations(raw)

print("Event dictionary:", event_id)
print("Unique events:", np.unique(events[:, 2]))

event_dict = {"T1": event_id["T1"], "T2": event_id["T2"]}

epochs = mne.Epochs(
    raw,
    events,
    event_id=event_dict,
    tmin=0.0,
    tmax=6.0,
    baseline=None,
    preload=True,
    verbose=False
)

trial = epochs.get_data()[0]
true_label = epochs.events[0, -1]
LEFT_CODE = event_id["T1"]
RIGHT_CODE = event_id["T2"]

true_side = "LEFT" if true_label == LEFT_CODE else "RIGHT"

print("True label:", true_label)

sfreq = raw.info['sfreq']
win_size = int(WINDOW_SECONDS * sfreq)
step_size = int(STEP_SECONDS * sfreq)

# -------------------------
# FEATURE EXTRACTION
# -------------------------
def extract_features(segment, sfreq):

    # Expect channel order: ["C3", "Cz", "C4"]
    C3 = segment[0]
    C4 = segment[2]

    win_size = len(segment[0])

    ALPHA = (8, 12)
    BETA_LOW = (13, 20)

    freqs, psd_C3 = welch(C3, sfreq, nperseg=win_size)
    _, psd_C4 = welch(C4, sfreq, nperseg=win_size)

    # --- Alpha ---
    alpha_mask = (freqs >= ALPHA[0]) & (freqs <= ALPHA[1])
    C3_alpha = np.mean(psd_C3[alpha_mask])
    C4_alpha = np.mean(psd_C4[alpha_mask])

    # --- Beta low ---
    beta_mask = (freqs >= BETA_LOW[0]) & (freqs <= BETA_LOW[1])
    C3_beta = np.mean(psd_C3[beta_mask])
    C4_beta = np.mean(psd_C4[beta_mask])

    # --- Lateralization ---
    alpha_diff = C3_alpha - C4_alpha
    beta_diff = C3_beta - C4_beta

    features = np.array([
        C3_alpha,
        C3_beta,
        C4_alpha,
        C4_beta,
        alpha_diff,
        beta_diff
    ])

    return features

# -------------------------
# SLIDING INFERENCE
# -------------------------
smoothed_prob = 0.5
window_index = 1

print("\n2-Second Sliding Inference")
print("--------------------------------")

for start in range(0, trial.shape[1] - win_size + 1, step_size):

    segment = trial[:, start:start+win_size]
    features = extract_features(segment, sfreq).reshape(1, -1)

    prob_right = clf.predict_proba(features)[0][1]

    smoothed_prob = (
        SMOOTHING_ALPHA * smoothed_prob +
        (1 - SMOOTHING_ALPHA) * prob_right
    )

    predicted_class = int(smoothed_prob > 0.5)
    predicted_side = "LEFT" if predicted_class == 1 else "RIGHT"

    print(
        f"Window {window_index} | "
        f"{start/sfreq:.1f}-{(start+win_size)/sfreq:.1f}s | "
        f"Raw: {prob_right:.3f} | "
        f"Smooth: {smoothed_prob:.3f} | "
        f"Pred: {predicted_side} | "
        f"True: {true_side} |"
    )
    print(features.shape)
    
    window_index += 1