Set-Content -Path README.md -Value @'
# LabScribe: Multilingual Indic Voice Agent & Bench Copilot

An autonomous, bidirectional voice-driven laboratory intelligence platform designed to eliminate manual data entry in sterile and hazardous wet-lab environments. Powered by Sarvam AI's speech intelligence infrastructure and persistent SQLite ledger storage.

---

## 🔬 Overview & Problem Statement

In contemporary biomedical, chemical, and physical research laboratories, scientists and technicians routinely operate under strict biosafety conditions—wearing personal protective equipment (PPE) such as nitrile gloves and handling sterile or hazardous reagents. 

Manual data entry presents two critical bottlenecks:
1. **Contamination Risk**: Touching keyboards, trackpads, or mobile devices compromises sterility and risks chemical or biological cross-contamination.
2. **Operational Friction**: Halting physical procedures to record rapid observations degrades workflow efficiency and increases the likelihood of unrecorded anomalies.

**LabScribe** solves this by providing a completely hands-free, code-mixed voice copilot. It allows researchers to log quantitative measurements and qualitative notes in regional and code-mixed speech (e.g., Tanglish, Hinglish, Indic English), performs automated threshold safety enforcement, commits data to a persistent SQL database, and delivers immediate verbal confirmations and safety alerts via low-latency text-to-speech.

---

## ✨ Key Architectural Capabilities

- **Bidirectional Voice Interface**: Complete hands-free cycle—speech input transcription followed by synthesized speech feedback for audible verification at the bench.
- **Indic Code-Switching STT**: Leverages Sarvam AI's `saaras:v3` model in `codemix` mode to transcribe complex mixed-language spoken observations across Indian dialects.
- **Deterministic Parameter & Safety Parsing**: Extracts metric types (Temperature, pH, Absorbance, RPM), numeric magnitudes, units, and sample IDs. Evaluates values against strict safety envelopes (e.g., $T_{\text{max}} = 70^\circ\text{C}$, $\text{pH} \in [4.0, 9.0]$) to generate real-time visual and auditory limit alerts.
- **Conversational Ledger Analytics**: Processes natural language queries regarding historical ledger telemetry (e.g., *"What was the highest temperature?"*, *"Are there any safety violations?"*) and vocalizes summarized database insights.
- **Persistent Data Store**: Utilizes an embedded SQLite database (`lab_ledger.db`) for transaction logging, preventing session loss and supporting one-click CSV telemetry export.

---

## 🛠️ Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit | Responsive, real-time command dashboard with KPI metrics and trend charts. |
| **Speech-to-Text (STT)** | Sarvam AI `saaras:v3` | Indic multilingual automatic speech recognition with code-mixing capabilities. |
| **Text-to-Speech (TTS)** | Sarvam AI `bulbul:v3` | High-fidelity Indian voice synthesis supporting selectable speakers and language codes. |
| **Data Persistence** | SQLite3 | Relational database schema indexing timestamp, batch tag, sample ID, metric, value, unit, and status. |
| **Data Analysis** | Pandas | Dynamic filtering, styling matrices, and tabular CSV compilation. |

---

## 📐 System Pipeline
