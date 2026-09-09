# 🛡️ VoiceShield AI

### AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks

VoiceShield AI is an AI-based voice security system designed to detect AI-generated or cloned voices and help prevent voice-cloning impersonation attacks.

## 🚀 Features

- 🎙️ Voice recording and audio upload
- 🤖 AI voice authenticity detection
- 📊 Confidence score
- ⚠️ Risk-level classification
- 🚫 Automatic threat blocking
- 🔐 Identity verification
- 📋 Analysis history
- 📄 Forensic PDF report generation
- 📈 Security dashboard
- 💾 Analysis history using SQLite

## 🔄 System Workflow

Voice / Call Input  
↓  
Audio Preprocessing  
↓  
AI Voice Authenticity Engine  
↓  
Genuine / AI-Cloned Detection  
↓  
Confidence Score & Risk Level  
↓  
Impersonation Detection  
↓  
Security Alert  
↓  
Verification / Block  
↓  
Forensic Report

## 🛠️ Technologies Used

- HTML
- CSS
- JavaScript
- Python
- Flask
- Librosa
- NumPy
- Scikit-learn
- SQLite
- ReportLab
- FFmpeg

## 📁 Project Structure

```text
VoiceShieldAI/
├── .gitignore
├── app.py
├── train_model.py
├── voice_model.pkl
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
