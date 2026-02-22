import mne
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib
import glob
from scipy.signal import welch

# -------------------------
# CONFIGURATION
# -------------------------
DATA_PATH = r"C:/Users/ameer/OneDrive/Desktop/Job stuff/Extracullicular activities/London Neurotech Hackathon/data_Left_Right/*.edf"

TMIN = 0.0
TMAX = 2.0   # 2 seconds after cue

SELECTED_CHANNELS = [
    "C3",
    "Cz",
    "C4"
]

"""
SELECTED_CHANNELS = [
    "Fz",
    "C3",
    "Cz",
    "C4",
    "Pz",
    "Po7",
    "Oz",
    "Po8"
]
"""

# Unicorn-like frequency bands
BANDS = {
    "alpha": (8, 12),
    "beta_low": (13, 20),
    "beta_mid": (20, 25),
    "beta_high": (25, 30),
}

# -------------------------
# FEATURE EXTRACTION
# -------------------------
def extract_unicorn_style_features(epochs):

    X = epochs.get_data()  # trials × channels × samples
    sfreq = epochs.info['sfreq']

    win_size = int(sfreq * 1.0)     # 1 second window
    step_size = int(sfreq * 0.04)   # 40 ms step

    # Define only the bands we care about
    ALPHA = (8, 12)
    BETA_LOW = (13, 20)

    all_features = []

    for trial in X:
        trial_windows = []

        for start in range(0, trial.shape[1] - win_size + 1, step_size):

            segment = trial[:, start:start + win_size]

            # Expect channels ordered as ["C3", "Cz", "C4"]
            C3 = segment[0]
            C4 = segment[2]

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

            window_features = [
                C3_alpha,
                C3_beta,
                C4_alpha,
                C4_beta,
                alpha_diff,
                beta_diff
            ]

            trial_windows.append(window_features)

        trial_windows = np.array(trial_windows)

        # Average across trial duration (2s or 3s depending on TMAX)
        trial_mean = trial_windows.mean(axis=0)

        all_features.append(trial_mean)

    return np.array(all_features)

# -------------------------
# LOAD DATA
# -------------------------
files = glob.glob(DATA_PATH)

all_epochs = []
all_labels = []

for file in files:
    raw = mne.io.read_raw_edf(file, preload=True, verbose=False)
    raw.rename_channels(lambda x: x.replace(".", "").capitalize())

    raw.pick_channels(SELECTED_CHANNELS)

    events, event_id = mne.events_from_annotations(raw)

    event_dict = {"T1": 1, "T2": 2}

    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_dict,
        tmin=TMIN,
        tmax=TMAX,
        baseline=None,
        preload=True,
        verbose=False
    )

    X_features = extract_unicorn_style_features(epochs)
    y = epochs.events[:, -1]

    all_epochs.append(X_features)
    all_labels.append(y)

X = np.concatenate(all_epochs)
y = np.concatenate(all_labels)

y = (y == 2).astype(int)
print("Label mapping clarification:")
print("0 = T1 (LEFT hand)")
print("1 = T2 (RIGHT hand)")
print("Unique labels in dataset:", np.unique(y))

print("Feature shape:", X.shape)

# -------------------------
# CLASSIFIER PIPELINE
# -------------------------
clf = Pipeline([
    ('scaler', StandardScaler()),
    ('lda', LinearDiscriminantAnalysis())
])

# -------------------------
# CROSS-VALIDATION
# -------------------------
scores = cross_val_score(clf, X, y, cv=5)
print("CV Accuracy: %.2f ± %.2f" % (np.mean(scores), np.std(scores)))

# -------------------------
# TRAIN FINAL MODEL
# -------------------------
clf.fit(X, y)
print(clf.named_steps['lda'].coef_)
print("Training feature shape:", X.shape)

# -------------------------
# SAVE MODEL
# -------------------------
joblib.dump(clf, "bandpower_3s_decoder.pkl")
print("Model saved as bandpower_3s_decoder.pkl")