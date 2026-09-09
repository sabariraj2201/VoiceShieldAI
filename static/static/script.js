// ============================================================
// VOICESHIELD AI - FRONTEND JAVASCRIPT
// ============================================================


// ------------------------------------------------------------
// RECORDING VARIABLES
// ------------------------------------------------------------

let mediaRecorder = null;
let audioChunks = [];
let recordedAudioBlob = null;

let recordingTimerInterval = null;
let recordingSeconds = 0;


// ------------------------------------------------------------
// CURRENT ANALYSIS
// ------------------------------------------------------------

let currentAnalysisId = null;


// ------------------------------------------------------------
// DOM READY
// ------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {

    loadStats();
    loadHistory();

});


// ============================================================
// LIVE VOICE RECORDING
// ============================================================

async function startRecording() {

    try {

        const stream =
            await navigator.mediaDevices.getUserMedia({
                audio: true
            });

        audioChunks = [];

        mediaRecorder =
            new MediaRecorder(stream);

        mediaRecorder.ondataavailable =
            function (event) {

                if (event.data.size > 0) {

                    audioChunks.push(
                        event.data
                    );

                }

            };


        mediaRecorder.onstop =
            function () {

                recordedAudioBlob =
                    new Blob(
                        audioChunks,
                        {
                            type:
                                mediaRecorder.mimeType
                                || "audio/webm"
                        }
                    );


                const audioURL =
                    URL.createObjectURL(
                        recordedAudioBlob
                    );


                const audioPlayer =
                    document.createElement(
                        "audio"
                    );

                audioPlayer.controls = true;

                audioPlayer.src =
                    audioURL;


                const container =
                    document.getElementById(
                        "recordedAudioContainer"
                    );


                if (container) {

                    container.innerHTML = "";

                    container.appendChild(
                        audioPlayer
                    );


                    const text =
                        document.createElement(
                            "p"
                        );

                    text.innerText =
                        "Recording ready for AI analysis.";

                    container.appendChild(
                        text
                    );

                }


                const analyzeButton =
                    document.getElementById(
                        "analyzeRecordingBtn"
                    );


                if (analyzeButton) {

                    analyzeButton.disabled =
                        false;

                }


                const status =
                    document.getElementById(
                        "recordingStatus"
                    );


                if (status) {

                    status.innerText =
                        "🟢 Recording completed";

                }


                stream
                    .getTracks()
                    .forEach(
                        track =>
                            track.stop()
                    );

            };


        mediaRecorder.start();


        recordingSeconds = 0;

        updateRecordingTimer();


        recordingTimerInterval =
            setInterval(
                updateRecordingTimer,
                1000
            );


        const startButton =
            document.getElementById(
                "startRecordingBtn"
            );


        const stopButton =
            document.getElementById(
                "stopRecordingBtn"
            );


        if (startButton) {

            startButton.disabled =
                true;

        }


        if (stopButton) {

            stopButton.disabled =
                false;

        }


        const status =
            document.getElementById(
                "recordingStatus"
            );


        if (status) {

            status.innerText =
                "🔴 Recording in progress...";

        }

    }

    catch (error) {

        console.error(error);

        alert(
            "Microphone access failed. Please allow microphone permission."
        );

    }

}


// ============================================================
// STOP RECORDING
// ============================================================

function stopRecording() {

    if (
        mediaRecorder &&
        mediaRecorder.state !== "inactive"
    ) {

        mediaRecorder.stop();

    }


    clearInterval(
        recordingTimerInterval
    );


    const startButton =
        document.getElementById(
            "startRecordingBtn"
        );


    const stopButton =
        document.getElementById(
            "stopRecordingBtn"
        );


    if (startButton) {

        startButton.disabled =
            false;

    }


    if (stopButton) {

        stopButton.disabled =
            true;

    }

}


// ============================================================
// RECORDING TIMER
// ============================================================

function updateRecordingTimer() {

    const timer =
        document.getElementById(
            "recordingTimer"
        );


    if (!timer) {

        return;

    }


    const minutes =
        Math.floor(
            recordingSeconds / 60
        );


    const seconds =
        recordingSeconds % 60;


    timer.innerText =
        String(minutes).padStart(2, "0")
        + ":"
        + String(seconds).padStart(2, "0");


    recordingSeconds++;

}


// ============================================================
// ANALYZE RECORDED VOICE
// ============================================================

async function analyzeRecordedAudio() {

    if (!recordedAudioBlob) {

        alert(
            "Please record a voice first."
        );

        return;

    }


    const formData =
        new FormData();


    formData.append(
        "audio",
        recordedAudioBlob,
        "Live_Voice_Recording.webm"
    );


    showAnalyzingState();


    try {

        const response =
            await fetch(
                "/analyze",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Voice analysis failed."
            );

        }


        displayAnalysisResult(
            data
        );


        loadStats();

        loadHistory();

    }

    catch (error) {

        console.error(error);

        alert(
            "❌ Analysis failed: "
            + error.message
        );


        hideAnalyzingState();

    }

}


// ============================================================
// UPLOAD AUDIO ANALYSIS
// ============================================================

async function analyzeAudio() {

    const fileInput =
        document.getElementById(
            "audioFile"
        );


    if (
        !fileInput ||
        !fileInput.files.length
    ) {

        alert(
            "Please select an audio file."
        );

        return;

    }


    const file =
        fileInput.files[0];


    const formData =
        new FormData();


    formData.append(
        "audio",
        file
    );


    showAnalyzingState();


    try {

        const response =
            await fetch(
                "/analyze",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Voice analysis failed."
            );

        }


        displayAnalysisResult(
            data
        );


        loadStats();

        loadHistory();

    }

    catch (error) {

        console.error(error);

        alert(
            "❌ Analysis failed: "
            + error.message
        );


        hideAnalyzingState();

    }

}


// ============================================================
// ANALYSIS LOADING STATE
// ============================================================

function showAnalyzingState() {

    const result =
        document.getElementById(
            "result"
        );


    if (!result) {

        return;

    }


    result.innerHTML = `

        <div class="analysis-loading">

            <div class="loading-icon">
                🤖
            </div>

            <h3>
                AI Voice Authenticity Engine
            </h3>

            <p>
                Analyzing acoustic characteristics...
            </p>

            <div class="loading-bar">

                <div class="loading-progress"></div>

            </div>

            <small>
                Extracting audio features •
                Running ML classification •
                Calculating confidence •
                Assessing risk
            </small>

        </div>

    `;

}


// ============================================================
// HIDE LOADING STATE
// ============================================================

function hideAnalyzingState() {

    const result =
        document.getElementById(
            "result"
        );


    if (result) {

        result.innerHTML = "";

    }

}


// ============================================================
// DISPLAY ANALYSIS RESULT
// ============================================================

function displayAnalysisResult(data) {

    const result =
        document.getElementById(
            "result"
        );


    if (!result) {

        return;

    }


    // IMPORTANT:
    // Backend sends "detection", NOT "status"

    const detection =
        data.detection || "Unknown";


    const confidence =
        Number(
            data.confidence || 0
        );


    const risk =
        data.risk || "UNKNOWN";


    const action =
        data.action || "UNKNOWN";


    const filename =
        data.filename || "Audio File";


    const recordId =
        data.id || null;


    // Save current analysis ID

    currentAnalysisId =
        recordId;


    // Threat detection

    const isThreat =
        detection === "AI-Cloned";


    let resultClass =
        "genuine-result";


    let icon =
        "🟢";


    let title =
        "VOICE VERIFIED";


    let subtitle =
        "Genuine Voice Detected";


    if (isThreat) {

        resultClass =
            "threat-result";


        icon =
            "🚨";


        title =
            "AI-CLONED VOICE DETECTED";


        subtitle =
            "Potential Voice Impersonation Attack";

    }


    // --------------------------------------------------------
    // RISK ICON
    // --------------------------------------------------------

    let riskIcon =
        "🟢";


    if (
        risk === "CRITICAL"
    ) {

        riskIcon =
            "🔴";

    }

    else if (
        risk === "HIGH"
    ) {

        riskIcon =
            "🔴";

    }

    else if (
        risk === "MEDIUM"
    ) {

        riskIcon =
            "🟠";

    }


    // --------------------------------------------------------
    // ACTION ICON
    // --------------------------------------------------------

    let actionIcon =
        "✅";


    if (
        action === "BLOCKED"
    ) {

        actionIcon =
            "🚫";

    }

    else if (
        action === "PENDING"
    ) {

        actionIcon =
            "⏳";

    }


    // --------------------------------------------------------
    // RESULT HTML
    // --------------------------------------------------------

    result.innerHTML = `

        <div class="voice-result-card ${resultClass}">

            <div class="result-icon">
                ${icon}
            </div>


            <h2>
                ${title}
            </h2>


            <p class="result-subtitle">
                ${subtitle}
            </p>


            <div class="result-details">


                <div class="result-row">

                    <span>
                        🎧 Audio File
                    </span>

                    <strong>
                        ${filename}
                    </strong>

                </div>


                <div class="result-row">

                    <span>
                        🔍 Detection Result
                    </span>

                    <strong>
                        ${detection}
                    </strong>

                </div>


                <div class="result-row">

                    <span>
                        📊 Confidence
                    </span>

                    <strong>
                        ${confidence.toFixed(0)}%
                    </strong>

                </div>


                <div class="confidence-container">

                    <div
                        class="confidence-bar"
                        style="width:${Math.min(
                            Math.max(
                                confidence,
                                0
                            ),
                            100
                        )}%"
                    ></div>

                </div>


                <div class="result-row">

                    <span>
                        ${riskIcon}
                        Risk Level
                    </span>

                    <strong>
                        ${risk}
                    </strong>

                </div>


                <div class="result-row">

                    <span>
                        ${actionIcon}
                        Security Action
                    </span>

                    <strong>
                        ${action}
                    </strong>

                </div>


            </div>


            <div class="security-message">

                ${
                    isThreat
                    ?
                    `

                    <strong>
                        🚨 SECURITY ALERT
                    </strong>

                    <p>
                        Suspicious AI-generated voice detected.
                        This recording may represent a
                        voice impersonation attack.
                    </p>


                    <button
                        class="danger-action"
                        onclick="showThreatResponse()"
                    >
                        🚫 View Threat Response
                    </button>

                    `
                    :
                    `

                    <strong>
                        🟢 VOICE VERIFIED
                    </strong>

                    <p>
                        The analyzed voice appears genuine.
                        No immediate cloning threat detected.
                    </p>


                    <button
                        class="safe-action"
                        onclick="verifyIdentity(${recordId})"
                    >
                        🔐 Verify Identity
                    </button>

                    `
                }

            </div>


            <div class="result-action-buttons">

                ${
                    recordId
                    ?
                    `

                    <button
                        onclick="generateReport(${recordId})"
                    >
                        📄 Generate Forensic Report
                    </button>

                    `
                    :
                    ""
                }

            </div>


        </div>

    `;


    result.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


// ============================================================
// THREAT RESPONSE
// ============================================================

function showThreatResponse() {

    const alertBox =
        document.getElementById(
            "securityAlert"
        );


    if (!alertBox) {

        alert(
            "🚨 HIGH-RISK VOICE THREAT DETECTED"
        );

        return;

    }


    alertBox.innerHTML = `

        <div class="threat-alert-box">

            <h3>
                🚨 Voice Impersonation Threat
            </h3>


            <p>
                VoiceShield AI detected characteristics
                associated with an AI-cloned or spoofed voice.
            </p>


            <ul>

                <li>
                    🚫 Suspicious call should be blocked
                </li>

                <li>
                    🔐 Identity verification recommended
                </li>

                <li>
                    📄 Forensic report can be generated
                </li>

            </ul>


            <button
                onclick="verifyIdentity(${currentAnalysisId})"
            >
                🔐 Start Verification
            </button>


            ${
                currentAnalysisId
                ?
                `

                <button
                    onclick="blockAnalysis(${currentAnalysisId})"
                >
                    🚫 Block This Analysis
                </button>

                `
                :
                ""
            }

        </div>

    `;


    alertBox.style.display =
        "block";


    alertBox.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


// ============================================================
// LOAD DASHBOARD STATS
// ============================================================

async function loadStats() {

    try {

        const response =
            await fetch(
                "/stats"
            );


        const data =
            await response.json();


        const total =
            document.getElementById(
                "totalAnalyses"
            );


        const genuine =
            document.getElementById(
                "genuineCount"
            );


        const threats =
            document.getElementById(
                "threatCount"
            );


        const blocked =
            document.getElementById(
                "blockedCount"
            );


        if (total) {

            total.innerText =
                data.total || 0;

        }


        if (genuine) {

            genuine.innerText =
                data.genuine || 0;

        }


        if (threats) {

            threats.innerText =
                data.threats || 0;

        }


        if (blocked) {

            blocked.innerText =
                data.blocked || 0;

        }


        // Analytics

        const analyticsGenuine =
            document.getElementById(
                "analyticsGenuine"
            );


        const analyticsThreats =
            document.getElementById(
                "analyticsThreats"
            );


        const analyticsBlocked =
            document.getElementById(
                "analyticsBlocked"
            );


        if (analyticsGenuine) {

            analyticsGenuine.innerText =
                data.genuine || 0;

        }


        if (analyticsThreats) {

            analyticsThreats.innerText =
                data.threats || 0;

        }


        if (analyticsBlocked) {

            analyticsBlocked.innerText =
                data.blocked || 0;

        }

    }

    catch (error) {

        console.error(
            "Stats loading failed:",
            error
        );

    }

}


// ============================================================
// LOAD HISTORY
// ============================================================

async function loadHistory() {

    try {

        const response =
            await fetch(
                "/history"
            );


        const data =
            await response.json();


        const historyBody =
            document.getElementById(
                "historyBody"
            );


        if (!historyBody) {

            return;

        }


        historyBody.innerHTML = "";


        if (!data.length) {

            historyBody.innerHTML = `

                <tr>

                    <td colspan="7">
                        No analysis history available.
                    </td>

                </tr>

            `;

            return;

        }


        data.forEach(
            function (record) {

                // Backend field = detection

                const detection =
                    record.detection ||
                    "Unknown";


                const statusClass =
                    detection === "AI-Cloned"
                    ? "status-threat"
                    : "status-genuine";


                let riskClass =
                    "risk-low";


                if (
                    record.risk === "CRITICAL"
                ) {

                    riskClass =
                        "risk-high";

                }

                else if (
                    record.risk === "HIGH"
                ) {

                    riskClass =
                        "risk-high";

                }

                else if (
                    record.risk === "MEDIUM"
                ) {

                    riskClass =
                        "risk-medium";

                }


                let actionClass =
                    "action-allowed";


                if (
                    record.action === "BLOCKED"
                ) {

                    actionClass =
                        "action-blocked";

                }


                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `

                    <td>
                        ${record.id}
                    </td>


                    <td>
                        ${record.timestamp}
                    </td>


                    <td>
                        ${record.filename}
                    </td>


                    <td class="${statusClass}">

                        ${detection}

                    </td>


                    <td>

                        ${Number(
                            record.confidence || 0
                        ).toFixed(0)}%

                    </td>


                    <td class="${riskClass}">

                        ${record.risk}

                    </td>


                    <td class="${actionClass}">

                        ${record.action}

                        <br>


                        <button
                            onclick="blockAnalysis(${record.id})"
                        >
                            🚫 Block
                        </button>


                        <button
                            onclick="verifyIdentity(${record.id})"
                        >
                            🔐 Verify
                        </button>


                        <button
                            onclick="generateReport(${record.id})"
                        >
                            📄 Report
                        </button>

                    </td>

                `;


                historyBody.appendChild(
                    row
                );

            }
        );

    }

    catch (error) {

        console.error(
            "History loading failed:",
            error
        );

    }

}


// ============================================================
// BLOCK ANALYSIS
// ============================================================

async function blockAnalysis(id) {

    if (!id) {

        alert(
            "Analysis ID is missing."
        );

        return;

    }


    try {

        const response =
            await fetch(
                "/update-action",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        id: id,

                        action: "BLOCKED"

                    })

                }
            );


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.error ||
                "Unable to block."
            );

        }


        alert(
            "🚫 Security action updated: BLOCKED"
        );


        loadStats();

        loadHistory();

    }

    catch (error) {

        alert(
            "❌ "
            + error.message
        );

    }

}


// ============================================================
// VERIFY IDENTITY
// ============================================================

function verifyIdentity(id = null) {

    if (id) {

        currentAnalysisId =
            id;

    }


    const verification =
        document.getElementById(
            "verification"
        );


    if (!verification) {

        alert(
            "🔐 Identity verification initiated."
        );

        return;

    }


    verification.innerHTML = `

        <div class="verification-box">

            <h3>
                🔐 Identity Verification
            </h3>


            <p>
                Additional verification is required
                before trusting this voice identity.
            </p>


            <div class="verification-steps">

                <div>
                    1️⃣ Voice identity check
                </div>

                <div>
                    2️⃣ Multi-factor authentication
                </div>

                <div>
                    3️⃣ Security confirmation
                </div>

            </div>


            <button
                onclick="completeVerification()"
            >
                ✅ Confirm Verification
            </button>

        </div>

    `;


    verification.style.display =
        "block";


    verification.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


// ============================================================
// COMPLETE VERIFICATION
// ============================================================

function completeVerification() {

    alert(
        "✅ Identity verification completed successfully."
    );

}


// ============================================================
// GENERATE REPORT
// ============================================================

async function generateReport(id = null) {

    const reportId =
        id || currentAnalysisId;


    if (!reportId) {

        alert(
            "❌ No analysis selected for report generation."
        );

        return;

    }


    try {

        const response =
            await fetch(
                "/generate-report",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        id: reportId

                    })

                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.success
        ) {

            throw new Error(
                data.error ||
                "Report generation failed."
            );

        }


        alert(
            "📄 Security report generated successfully."
        );


        const downloadURL =
            "/download-report/"
            + encodeURIComponent(
                data.filename
            );


        window.open(
            downloadURL,
            "_blank"
        );

    }

    catch (error) {

        alert(
            "❌ Report error: "
            + error.message
        );

    }

}
