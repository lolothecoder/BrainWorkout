import mne
import numpy as np
from mne.decoding import CSP
from sklearn.pipeline import Pipeline
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import joblib
import glob

# -------------------------
# CONFIGURATION
# -------------------------
DATA_PATH = r"C:/Users/ameer/OneDrive/Desktop/Job stuff/Extracullicular activities/London Neurotech Hackathon/data_Left_Right/*.edf"
SAMPLING_RATE = 160
TMIN = 0.0
TMAX = 3.0   # 3 seconds after cue
FMIN = 8
FMAX = 30

# Select channels similar to g.tec 8-channel motor setup

SELECTED_CHANNELS = [
    "C3", "C4", "Cz",
    "Fc3", "Fc4",
    "Cp3", "Cp4",
    "Pz"
]

# -------------------------
# LOAD DATA
# -------------------------
files = glob.glob(DATA_PATH)

all_epochs = []
all_labels = []

for file in files:
    raw = mne.io.read_raw_edf(file, preload=True, verbose=False)
    raw.rename_channels(lambda x: x.replace(".", "").capitalize())
    print(raw.ch_names)

    # Pick only motor channels
    raw.pick_channels(SELECTED_CHANNELS)

    # Bandpass filter
    raw.filter(FMIN, FMAX, fir_design='firwin')

    events, event_id = mne.events_from_annotations(raw)

    # Left = T1, Right = T2
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

    X = epochs.get_data()   # shape: (trials, channels, samples)
    y = epochs.events[:, -1]

    all_epochs.append(X)
    all_labels.append(y)

X = np.concatenate(all_epochs)
y = np.concatenate(all_labels)

# Convert labels to 0/1
y = (y == 2).astype(int)  # 0 = left, 1 = right

print("Data shape:", X.shape)

# -------------------------
# CLASSIFIER PIPELINE
# -------------------------
csp = CSP(n_components=4, log=True, norm_trace=False)

lda = LinearDiscriminantAnalysis()

clf = Pipeline([
    ('csp', csp),
    ('lda', lda)
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

# -------------------------
# SAVE MODEL
# -------------------------
joblib.dump(clf, "left_right_decoder.pkl")
print("Model saved as left_right_decoder.pkl")