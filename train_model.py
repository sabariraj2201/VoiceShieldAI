import os
import pickle
import librosa
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


# ============================================================
# VOICESHIELD AI - MODEL TRAINING
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "dataset"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "voice_model.pkl"
)


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(file_path):

    print("🎵 Processing:", os.path.basename(file_path))

    y, sr = librosa.load(
        file_path,
        sr=16000,
        mono=True
    )

    # --------------------------------------------------------
    # MFCC
    # --------------------------------------------------------

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=20
    )

    mfcc_mean = np.mean(
        mfcc,
        axis=1
    )

    mfcc_std = np.std(
        mfcc,
        axis=1
    )


    # --------------------------------------------------------
    # Delta MFCC
    # --------------------------------------------------------

    mfcc_delta = librosa.feature.delta(
        mfcc
    )

    delta_mean = np.mean(
        mfcc_delta,
        axis=1
    )

    delta_std = np.std(
        mfcc_delta,
        axis=1
    )


    # --------------------------------------------------------
    # Spectral Centroid
    # --------------------------------------------------------

    spectral_centroid = librosa.feature.spectral_centroid(
        y=y,
        sr=sr
    )

    centroid_mean = np.mean(
        spectral_centroid
    )

    centroid_std = np.std(
        spectral_centroid
    )


    # --------------------------------------------------------
    # Spectral Bandwidth
    # --------------------------------------------------------

    bandwidth = librosa.feature.spectral_bandwidth(
        y=y,
        sr=sr
    )

    bandwidth_mean = np.mean(
        bandwidth
    )

    bandwidth_std = np.std(
        bandwidth
    )


    # --------------------------------------------------------
    # Spectral Rolloff
    # --------------------------------------------------------

    rolloff = librosa.feature.spectral_rolloff(
        y=y,
        sr=sr
    )

    rolloff_mean = np.mean(
        rolloff
    )

    rolloff_std = np.std(
        rolloff
    )


    # --------------------------------------------------------
    # Zero Crossing Rate
    # --------------------------------------------------------

    zero_crossing = librosa.feature.zero_crossing_rate(
        y
    )

    zcr_mean = np.mean(
        zero_crossing
    )

    zcr_std = np.std(
        zero_crossing
    )


    # --------------------------------------------------------
    # RMS ENERGY
    # --------------------------------------------------------

    rms = librosa.feature.rms(
        y=y
    )

    rms_mean = np.mean(
        rms
    )

    rms_std = np.std(
        rms
    )


    # --------------------------------------------------------
    # CHROMA
    # --------------------------------------------------------

    chroma = librosa.feature.chroma_stft(
        y=y,
        sr=sr
    )

    chroma_mean = np.mean(
        chroma,
        axis=1
    )

    chroma_std = np.std(
        chroma,
        axis=1
    )


    # --------------------------------------------------------
    # COMBINE ALL FEATURES
    # --------------------------------------------------------

    features = np.concatenate([

        mfcc_mean,
        mfcc_std,

        delta_mean,
        delta_std,

        [
            centroid_mean,
            centroid_std,

            bandwidth_mean,
            bandwidth_std,

            rolloff_mean,
            rolloff_std,

            zcr_mean,
            zcr_std,

            rms_mean,
            rms_std
        ],

        chroma_mean,
        chroma_std

    ])

    return features


# ============================================================
# LOAD DATASET
# ============================================================

X = []
y = []

genuine_folder = os.path.join(
    DATASET_PATH,
    "genuine"
)

cloned_folder = os.path.join(
    DATASET_PATH,
    "cloned"
)


# ============================================================
# GENUINE VOICES
# ============================================================

print()
print("==========================================")
print("🟢 Loading Genuine Voice Samples")
print("==========================================")

if os.path.exists(genuine_folder):

    for filename in os.listdir(
        genuine_folder
    ):

        if filename.lower().endswith(
            (
                ".wav",
                ".mp3",
                ".flac",
                ".m4a",
                ".webm"
            )
        ):

            file_path = os.path.join(
                genuine_folder,
                filename
            )

            try:

                features = extract_features(
                    file_path
                )

                X.append(
                    features
                )

                # Genuine = 0
                y.append(0)

                print(
                    "✅ Genuine:",
                    filename
                )

            except Exception as e:

                print(
                    "❌ Error:",
                    filename,
                    e
                )


# ============================================================
# CLONED VOICES
# ============================================================

print()
print("==========================================")
print("🔴 Loading AI-Cloned Voice Samples")
print("==========================================")

if os.path.exists(cloned_folder):

    for filename in os.listdir(
        cloned_folder
    ):

        if filename.lower().endswith(
            (
                ".wav",
                ".mp3",
                ".flac",
                ".m4a",
                ".webm"
            )
        ):

            file_path = os.path.join(
                cloned_folder,
                filename
            )

            try:

                features = extract_features(
                    file_path
                )

                X.append(
                    features
                )

                # AI-Cloned = 1
                y.append(1)

                print(
                    "🚨 Cloned:",
                    filename
                )

            except Exception as e:

                print(
                    "❌ Error:",
                    filename,
                    e
                )


# ============================================================
# CONVERT TO NUMPY
# ============================================================

X = np.array(
    X,
    dtype=np.float32
)

y = np.array(
    y,
    dtype=np.int32
)


# ============================================================
# DATASET SUMMARY
# ============================================================

genuine_samples = int(
    np.sum(y == 0)
)

cloned_samples = int(
    np.sum(y == 1)
)

total_samples = len(y)


print()
print("==========================================")
print("📊 DATASET SUMMARY")
print("==========================================")

print(
    "Total samples   :",
    total_samples
)

print(
    "Genuine samples :",
    genuine_samples
)

print(
    "Cloned samples  :",
    cloned_samples
)

print(
    "Feature count   :",
    X.shape[1]
    if len(X) > 0
    else 0
)

print("==========================================")


# ============================================================
# VALIDATE DATASET
# ============================================================

if total_samples < 2:

    print()
    print(
        "❌ Not enough audio samples."
    )

    print(
        "Please add more recordings."
    )

    exit()


if genuine_samples == 0:

    print(
        "❌ No genuine voice samples found."
    )

    exit()


if cloned_samples == 0:

    print(
        "❌ No cloned voice samples found."
    )

    exit()


# ============================================================
# WARNING FOR SMALL DATASET
# ============================================================

if genuine_samples < 5 or cloned_samples < 5:

    print()
    print(
        "⚠️ WARNING:"
    )

    print(
        "Dataset is currently very small."
    )

    print(
        "The trained model is suitable only"
    )

    print(
        "for prototype/demo purposes."
    )

    print(
        "Add more genuine and cloned samples"
    )

    print(
        "for reliable detection."
    )

    print()


# ============================================================
# RANDOM FOREST MODEL
# ============================================================

model = Pipeline([

    (
        "scaler",
        StandardScaler()
    ),

    (
        "classifier",
        RandomForestClassifier(

            n_estimators=200,

            max_depth=12,

            min_samples_split=2,

            random_state=42,

            class_weight="balanced"

        )
    )

])


# ============================================================
# TRAIN MODEL
# ============================================================

print()
print("==========================================")
print("🤖 TRAINING VOICESHIELD AI MODEL")
print("==========================================")

model.fit(
    X,
    y
)


# ============================================================
# TRAINING ACCURACY
# ============================================================

training_predictions = model.predict(
    X
)

training_accuracy = (
    np.mean(
        training_predictions == y
    )
    * 100
)


print()
print(
    "Training Accuracy:",
    round(
        training_accuracy,
        2
    ),
    "%"
)


# ============================================================
# SAVE MODEL
# ============================================================

with open(
    MODEL_FILE,
    "wb"
) as f:

    pickle.dump(
        model,
        f
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("==========================================")
print("✅ VOICESHIELD AI MODEL TRAINING COMPLETE")
print("==========================================")

print(
    "Model file:",
    MODEL_FILE
)

print(
    "Genuine samples:",
    genuine_samples
)

print(
    "Cloned samples:",
    cloned_samples
)

print(
    "Feature vector:",
    X.shape[1]
)

print(
    "Model saved successfully."
)

print("==========================================")