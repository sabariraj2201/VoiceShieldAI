import os
import pickle
import sqlite3
import subprocess
from datetime import datetime

import librosa
import numpy as np
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file
)

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER


# =========================================================
# VOICESHIELD AI - FLASK APPLICATION
# =========================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
DATABASE = os.path.join(BASE_DIR, "voiceshield.db")
MODEL_FILE = os.path.join(BASE_DIR, "voice_model.pkl")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            detection TEXT,
            confidence REAL,
            risk TEXT,
            action TEXT,
            timestamp TEXT
        )
    """)

    connection.commit()
    connection.close()


init_database()


# =========================================================
# LOAD AI MODEL
# =========================================================

model = None

if os.path.exists(MODEL_FILE):

    try:

        with open(MODEL_FILE, "rb") as file:
            model = pickle.load(file)

        print("==========================================")
        print("✅ VoiceShield AI Model Loaded")
        print("==========================================")

    except Exception as error:

        print("❌ Model loading error:", error)

else:

    print("⚠️ voice_model.pkl not found.")


# =========================================================
# AUDIO FEATURE EXTRACTION
# MUST MATCH train_model.py
# =========================================================

def extract_features(file_path):

    y, sr = librosa.load(
        file_path,
        sr=None,
        mono=True
    )

    # -----------------------------------------------------
    # MFCC
    # -----------------------------------------------------

    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=20
    )

    mfcc_mean = np.mean(mfcc, axis=1)
    mfcc_std = np.std(mfcc, axis=1)

    # -----------------------------------------------------
    # MFCC DELTA
    # -----------------------------------------------------

    delta = librosa.feature.delta(mfcc)

    delta_mean = np.mean(delta, axis=1)
    delta_std = np.std(delta, axis=1)

    # -----------------------------------------------------
    # SPECTRAL CENTROID
    # -----------------------------------------------------

    spectral_centroid = librosa.feature.spectral_centroid(
        y=y,
        sr=sr
    )

    centroid_mean = np.mean(spectral_centroid)
    centroid_std = np.std(spectral_centroid)

    # -----------------------------------------------------
    # SPECTRAL BANDWIDTH
    # -----------------------------------------------------

    bandwidth = librosa.feature.spectral_bandwidth(
        y=y,
        sr=sr
    )

    bandwidth_mean = np.mean(bandwidth)
    bandwidth_std = np.std(bandwidth)

    # -----------------------------------------------------
    # SPECTRAL ROLLOFF
    # -----------------------------------------------------

    rolloff = librosa.feature.spectral_rolloff(
        y=y,
        sr=sr
    )

    rolloff_mean = np.mean(rolloff)
    rolloff_std = np.std(rolloff)

    # -----------------------------------------------------
    # ZERO CROSSING RATE
    # -----------------------------------------------------

    zcr = librosa.feature.zero_crossing_rate(y)

    zcr_mean = np.mean(zcr)
    zcr_std = np.std(zcr)

    # -----------------------------------------------------
    # RMS ENERGY
    # -----------------------------------------------------

    rms = librosa.feature.rms(y=y)

    rms_mean = np.mean(rms)
    rms_std = np.std(rms)

    # -----------------------------------------------------
    # CHROMA
    # -----------------------------------------------------

    chroma = librosa.feature.chroma_stft(
        y=y,
        sr=sr
    )

    chroma_mean = np.mean(chroma, axis=1)
    chroma_std = np.std(chroma, axis=1)

    # -----------------------------------------------------
    # COMBINE ALL FEATURES
    # -----------------------------------------------------

    features = np.concatenate([

        mfcc_mean,
        mfcc_std,

        delta_mean,
        delta_std,

        [centroid_mean],
        [centroid_std],

        [bandwidth_mean],
        [bandwidth_std],

        [rolloff_mean],
        [rolloff_std],

        [zcr_mean],
        [zcr_std],

        [rms_mean],
        [rms_std],

        chroma_mean,
        chroma_std

    ])

    return features


# =========================================================
# FFMPEG AUDIO CONVERSION
# =========================================================

AUDIO_CONVERSION_EXTENSIONS = {
    ".webm",
    ".m4a",
    ".mp4",
    ".ogg",
    ".oga",
    ".aac"
}


def convert_to_wav(input_path):

    base_name = os.path.splitext(input_path)[0]

    wav_path = base_name + "_converted.wav"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        wav_path
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

    except FileNotFoundError:

        raise RuntimeError(
            "FFmpeg is not installed or not available in PATH."
        )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg conversion failed:\n"
            + result.stderr[-1000:]
        )

    if not os.path.exists(wav_path):

        raise RuntimeError(
            "Converted WAV file was not created."
        )

    return wav_path


# =========================================================
# RISK CALCULATION
# =========================================================

def calculate_risk(detection, confidence):

    if detection == "AI-Cloned":

        if confidence >= 80:
            return "CRITICAL"

        elif confidence >= 60:
            return "HIGH"

        else:
            return "MEDIUM"

    else:

        if confidence >= 80:
            return "LOW"

        elif confidence >= 60:
            return "MEDIUM"

        else:
            return "HIGH"


# =========================================================
# ACTION DECISION
# =========================================================

def decide_action(detection, risk):

    if detection == "AI-Cloned":

        if risk in ["CRITICAL", "HIGH"]:
            return "BLOCKED"

        return "PENDING"

    return "ALLOWED"


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# ANALYZE AUDIO
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    if "audio" not in request.files:

        return jsonify({
            "success": False,
            "error": "No audio file received."
        }), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":

        return jsonify({
            "success": False,
            "error": "No audio file selected."
        }), 400

    original_filename = os.path.basename(
        audio_file.filename
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        original_filename
    )

    converted_path = None

    try:

        # -------------------------------------------------
        # SAVE ORIGINAL AUDIO
        # -------------------------------------------------

        audio_file.save(file_path)

        print()
        print("==========================================")
        print("🎵 ANALYZING AUDIO")
        print("==========================================")
        print("File:", original_filename)

        # -------------------------------------------------
        # CONVERT IF REQUIRED
        # -------------------------------------------------

        extension = os.path.splitext(
            original_filename
        )[1].lower()

        analysis_path = file_path

        if extension in AUDIO_CONVERSION_EXTENSIONS:

            print("🔄 Converting audio to WAV...")

            converted_path = convert_to_wav(
                file_path
            )

            analysis_path = converted_path

            print("✅ Conversion successful.")

        # -------------------------------------------------
        # EXTRACT FEATURES
        # -------------------------------------------------

        print("🔍 Extracting 114 audio features...")

        features = extract_features(
            analysis_path
        )

        print(
            "Feature count:",
            len(features)
        )

        # -------------------------------------------------
        # CHECK FEATURE COUNT
        # -------------------------------------------------

        if len(features) != 114:

            raise RuntimeError(
                f"Feature mismatch. "
                f"Expected 114 but got {len(features)}."
            )

        # -------------------------------------------------
        # MODEL CHECK
        # -------------------------------------------------

        if model is None:

            raise RuntimeError(
                "AI model is not loaded. "
                "Please train the model first."
            )

        # -------------------------------------------------
        # MODEL PREDICTION
        # -------------------------------------------------

        feature_array = np.array(
            features
        ).reshape(1, -1)

        prediction = model.predict(
            feature_array
        )[0]

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(
                feature_array
            )[0]

            confidence = float(
                max(probabilities) * 100
            )

        else:

            confidence = 50.0

        # -------------------------------------------------
        # DETECTION LABEL
        # -------------------------------------------------

        if int(prediction) == 1:

            detection = "AI-Cloned"

        else:

            detection = "Genuine"

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        risk = calculate_risk(
            detection,
            confidence
        )

        # -------------------------------------------------
        # ACTION
        # -------------------------------------------------

        action = decide_action(
            detection,
            risk
        )

        # -------------------------------------------------
        # SAVE HISTORY
        # -------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        connection = get_db_connection()

        cursor = connection.execute("""
            INSERT INTO history
            (
                filename,
                detection,
                confidence,
                risk,
                action,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            original_filename,
            detection,
            round(confidence, 2),
            risk,
            action,
            timestamp
        ))

        record_id = cursor.lastrowid

        connection.commit()
        connection.close()

        print()
        print("==========================================")
        print("🤖 VOICESHIELD AI RESULT")
        print("==========================================")
        print("Detection :", detection)
        print("Confidence:", round(confidence, 2), "%")
        print("Risk      :", risk)
        print("Action    :", action)
        print("==========================================")

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "id": record_id,

            "filename": original_filename,

            "detection": detection,

            "confidence": round(
                confidence,
                2
            ),

            "risk": risk,

            "action": action,

            "verified": detection == "Genuine",

            "message":
                "Voice verified successfully."
                if detection == "Genuine"
                else
                "AI voice cloning threat detected.",

            "timestamp": timestamp

        })

    except Exception as error:

        print()
        print("❌ ANALYSIS ERROR")
        print(error)

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500

    finally:

        # -------------------------------------------------
        # DELETE TEMPORARY WAV
        # -------------------------------------------------

        if converted_path:

            try:

                if os.path.exists(
                    converted_path
                ):

                    os.remove(
                        converted_path
                    )

            except Exception:

                pass


# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    connection = get_db_connection()

    rows = connection.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()

    connection.close()

    return jsonify([

        dict(row)

        for row in rows

    ])


# =========================================================
# DASHBOARD STATS
# =========================================================

@app.route("/stats")
def stats():

    connection = get_db_connection()

    total = connection.execute("""
        SELECT COUNT(*) AS count
        FROM history
    """).fetchone()["count"]

    genuine = connection.execute("""
        SELECT COUNT(*) AS count
        FROM history
        WHERE detection = 'Genuine'
    """).fetchone()["count"]

    threats = connection.execute("""
        SELECT COUNT(*) AS count
        FROM history
        WHERE detection = 'AI-Cloned'
    """).fetchone()["count"]

    blocked = connection.execute("""
        SELECT COUNT(*) AS count
        FROM history
        WHERE action = 'BLOCKED'
    """).fetchone()["count"]

    connection.close()

    return jsonify({

        "total": total,

        "genuine": genuine,

        "threats": threats,

        "blocked": blocked

    })


# =========================================================
# UPDATE ACTION
# =========================================================

@app.route("/update-action", methods=["POST"])
def update_action():

    data = request.get_json()

    record_id = data.get("id")

    action = data.get("action")

    if not record_id or not action:

        return jsonify({
            "success": False,
            "error": "Missing ID or action."
        }), 400

    connection = get_db_connection()

    connection.execute("""
        UPDATE history
        SET action = ?
        WHERE id = ?
    """, (
        action,
        record_id
    ))

    connection.commit()
    connection.close()

    return jsonify({

        "success": True,

        "message": "Action updated successfully."

    })


# =========================================================
# GENERATE PDF REPORT
# =========================================================

@app.route("/generate-report", methods=["POST"])
def generate_report():

    data = request.get_json()

    record_id = data.get("id")

    if not record_id:

        return jsonify({

            "success": False,

            "error": "Record ID missing."

        }), 400

    connection = get_db_connection()

    record = connection.execute("""
        SELECT *
        FROM history
        WHERE id = ?
    """, (
        record_id,
    )).fetchone()

    connection.close()

    if record is None:

        return jsonify({

            "success": False,

            "error": "Record not found."

        }), 404

    filename = (
        "VoiceShield_Report_"
        + str(record_id)
        + ".pdf"
    )

    report_path = os.path.join(
        REPORT_FOLDER,
        filename
    )

    # -----------------------------------------------------
    # PDF DOCUMENT
    # -----------------------------------------------------

    document = SimpleDocTemplate(
        report_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]

    title_style.alignment = TA_CENTER

    heading_style = styles["Heading2"]

    normal_style = styles["BodyText"]

    story = []

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "VoiceShield AI",
            title_style
        )
    )

    story.append(
        Paragraph(
            "AI Voice Authenticity & "
            "Impersonation Detection Report",
            heading_style
        )
    )

    story.append(
        Spacer(1, 20)
    )

    # -----------------------------------------------------
    # REPORT DATA
    # -----------------------------------------------------

    report_data = [

        ["Field", "Result"],

        ["Record ID", str(record["id"])],

        ["Audio File", record["filename"]],

        ["Detection", record["detection"]],

        [
            "Confidence",
            f'{record["confidence"]}%'
        ],

        ["Risk Level", record["risk"]],

        ["Action", record["action"]],

        ["Timestamp", record["timestamp"]]

    ]

    table = Table(
        report_data,
        colWidths=[160, 320]
    )

    table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.black
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])
    )

    story.append(table)

    story.append(
        Spacer(1, 25)
    )

    # -----------------------------------------------------
    # SECURITY SUMMARY
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Security Assessment",
            heading_style
        )
    )

    if record["detection"] == "AI-Cloned":

        summary = (
            "The analyzed audio was classified as an "
            "AI-cloned or synthetic voice. The system "
            "identified the recording as a potential "
            "voice impersonation attack. Appropriate "
            "security action should be taken."
        )

    else:

        summary = (
            "The analyzed audio was classified as a "
            "genuine voice sample. No AI voice-cloning "
            "indicators were detected by the current "
            "prototype model."
        )

    story.append(
        Paragraph(
            summary,
            normal_style
        )
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Generated by VoiceShield AI",
            normal_style
        )
    )

    # -----------------------------------------------------
    # BUILD PDF
    # -----------------------------------------------------

    document.build(story)

    return jsonify({

        "success": True,

        "filename": filename

    })


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.route("/download-report/<filename>")
def download_report(filename):

    safe_filename = os.path.basename(
        filename
    )

    report_path = os.path.join(
        REPORT_FOLDER,
        safe_filename
    )

    if not os.path.exists(report_path):

        return jsonify({

            "success": False,

            "error": "Report not found."

        }), 404

    return send_file(
        report_path,
        as_attachment=True
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print("🛡️ VOICESHIELD AI")
    print("==========================================")
    print("Server starting...")
    print("Open: http://127.0.0.1:5000")
    print("==========================================")

    app.run(
        debug=True
    )