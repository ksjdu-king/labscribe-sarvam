import streamlit as st
import pandas as pd
import requests
import sqlite3
import re
import base64
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="LabScribe Indic Agent",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SARVAM CONFIGURATION ---
SARVAM_API_KEY = "sk_dzfga3ek_lhUY8lqiVdUQt50BANGFiIr5"
STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
HEADERS = {"api-subscription-key": SARVAM_API_KEY}

SAFETY_RULES = {
    "temperature": {"max": 70.0, "unit": "°C"},
    "ph": {"min": 4.0, "max": 9.0, "unit": "pH"},
    "rpm": {"max": 10000, "unit": "RPM"},
    "absorbance": {"max": 2.5, "unit": "OD"}
}

DB_NAME = "lab_ledger.db"

# --- PERSISTENT SQLITE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            batch_tag TEXT,
            sample_id TEXT,
            metric TEXT,
            value REAL,
            unit TEXT,
            status TEXT,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_record(batch_tag, sample_id, metric, value, unit, status, notes):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now_str = datetime.now().strftime("%H:%M:%S")
    c.execute("""
        INSERT INTO observations (timestamp, batch_tag, sample_id, metric, value, unit, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_str, batch_tag, sample_id, metric, value, unit, status, notes))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT timestamp, batch_tag, sample_id, metric, value, unit, status FROM observations ORDER BY id DESC", conn)
    conn.close()
    return df

def clear_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM observations")
    conn.commit()
    conn.close()

init_db()

# --- STYLING (GLASSMORPHISM & ACCENTS) ---
st.markdown("""
<style>
    /* Metric Cards Styling */
    div[data-testid="stMetric"] {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px 14px;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-size: 0.85rem;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        color: #f8fafc;
    }
    
    /* Header Gradient */
    .title-banner {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 2px;
    }
    .badge {
        background-color: #1e3a8a;
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Agent Workbench")
    current_batch = st.text_input("Active Batch / Project", value="BATCH-01")
    
    st.divider()
    st.markdown("### 🗣️ Voice Persona")
    speaker_choice = st.selectbox("Speaker (Bulbul v3)", options=["kavya", "aditya", "priya", "rohan", "ritu"], index=0)
    target_lang = st.selectbox(
        "Response Dialect",
        options=["en-IN", "hi-IN", "ta-IN", "te-IN"],
        format_func=lambda x: {"en-IN": "English (India)", "hi-IN": "Hindi", "ta-IN": "Tamil", "te-IN": "Telugu"}.get(x, x)
    )
    
    st.divider()
    if st.button("🗑️ Reset Database & Logs", type="secondary", use_container_width=True):
        clear_db()
        st.session_state.messages = []
        st.rerun()

# --- HEADER & TELEMETRY KPIS ---
st.markdown('<div class="title-banner">🧪 LabScribe: Multilingual Indic Agent & Bench Copilot</div>', unsafe_allow_html=True)
st.markdown('<span class="badge">Sarvam AI Powered • Voice-to-Action • SQLite Ledger</span>', unsafe_allow_html=True)

df_all = load_data()
total_records = len(df_all)
critical_alerts = len(df_all[df_all["status"].str.contains("CRITICAL")]) if not df_all.empty else 0
active_batches = df_all["batch_tag"].nunique() if not df_all.empty else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Records", total_records)
k2.metric("Critical Alerts", critical_alerts, delta=f"{critical_alerts} Breaches", delta_color="inverse")
k3.metric("Active Batches", active_batches)
k4.metric("Storage Status", "Active 🟢", delta="SQLite")

st.write("")

# --- SARVAM API CALLS ---
def transcribe_audio(audio_bytes):
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {"model": "saaras:v3", "mode": "codemix", "language_code": "unknown"}
    res = requests.post(STT_URL, headers=HEADERS, files=files, data=data)
    if res.status_code == 200:
        return res.json().get("transcript", "")
    st.error(f"STT Error: {res.text}")
    return None

def generate_voice_feedback(text, speaker, lang):
    payload = {
        "inputs": [text],
        "target_language_code": lang,
        "speaker": speaker,
        "model": "bulbul:v3"
    }
    res = requests.post(TTS_URL, headers={**HEADERS, "Content-Type": "application/json"}, json=payload)
    if res.status_code == 200:
        audio_base64 = res.json()["audios"][0]
        return base64.b64decode(audio_base64)
    return None

# Mapping common Tamil and English spoken number words
WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
    "பத்து": 10, "இருபது": 20, "முப்பது": 30, "நாற்பது": 40, "ஐம்பது": 50,
    "அறுபது": 60, "எழுபது": 70, "எண்பது": 80, "தொண்ணூறு": 90, "நூறு": 100
}

def parse_spoken_number(text):
    """Finds numeric digits or converts spoken number words."""
    # 1. Direct digits (e.g., 75, 80.5)
    digit_match = re.search(r'[-+]?\d*\.?\d+', text)
    if digit_match and digit_match.group() != "":
        try:
            return float(digit_match.group())
        except ValueError:
            pass

    # 2. Spoken number words
    for word, val in WORD_TO_NUM.items():
        if word in text.lower():
            return float(val)
            
    return None

def execute_agent_intent(text, batch_tag):
    text_lower = text.lower()
    df = load_data()
    
    # --- 1. INTENT: ASKING A DIRECT QUESTION ABOUT THE DATABASE ---
    is_explicit_question = any(q in text_lower for q in [
        "what was", "what is", "how many", "which sample", "tell me the highest", 
        "show me", "எத்தனை", "என்ன", "எது"
    ])
    
    if is_explicit_question:
        if df.empty:
            return "The database is empty. No observations logged yet."
        if "highest" in text_lower or "அதிக" in text_lower or "max" in text_lower:
            row = df.loc[df["value"].idxmax()]
            return f"The highest value recorded is {row['value']} {row['unit']} for {row['sample_id']} ({row['metric']})."
        elif "critical" in text_lower or "alert" in text_lower:
            crit = df[df["status"].str.contains("CRITICAL")]
            if crit.empty:
                return "All parameters in the database are currently safe."
            return f"There are {len(crit)} critical violations logged in the system."
        elif "count" in text_lower or "total" in text_lower or "எத்தனை" in text_lower:
            return f"There are {len(df)} total observations logged in the ledger."

    # --- 2. INTENT: LOGGING BENCH DATA OR REPORTING A CRITICAL ALERT ---
    # Detect Metric
    metric = "General Observation"
    unit = ""
    if any(k in text_lower for k in ["temp", "celsius", "degree", "heat", "சூடு", "வெப்பநிலை"]):
        metric = "Temperature"
        unit = "°C"
    elif "ph" in text_lower:
        metric = "pH"
        unit = "pH"
    elif any(k in text_lower for k in ["absorbance", "optical density", "od", "density"]):
        metric = "Absorbance"
        unit = "OD"
    elif any(k in text_lower for k in ["rpm", "speed", "spin", "வேகம்"]):
        metric = "RPM"
        unit = "RPM"

    # Extract Value
    val = parse_spoken_number(text)
    
    # Check for qualitative crisis (e.g. "அதிகமா இருக்கு", "too high", "danger", "critical")
    is_qualitative_critical = any(w in text_lower for w in [
        "அதிகமா", "ரொம்ப அதிகம்", "critical", "reduce it", "danger", "too high", "exceed", "overheat"
    ])

    status = "Normal"
    alert_msg = ""

    if is_qualitative_critical:
        status = "CRITICAL: Manual Alert"
        alert_msg = f"Critical alert acknowledged for {metric}. Emergency cooling or regulation required."
        if val is None:
            val = 90.0  # Placeholder above standard threshold if no exact number was dictated

    elif val is not None:
        metric_key = metric.lower()
        if metric_key in SAFETY_RULES:
            rule = SAFETY_RULES[metric_key]
            if "max" in rule and val > rule["max"]:
                status = "CRITICAL: High Limit"
                alert_msg = f"Warning: {metric} reading of {val} exceeds safety limit of {rule['max']} {rule['unit']}."
            elif "min" in rule and val < rule["min"]:
                status = "CRITICAL: Low Limit"
                alert_msg = f"Warning: {metric} reading of {val} is below safe limit of {rule['min']} {rule['unit']}."
    else:
        val = 0.0

    # Extract Sample ID
    sample_match = re.search(r'(?:sample|batch|tube|சாம்பிள்)\s*([a-z0-9\-]+)', text_lower)
    sample_id = sample_match.group(0).upper() if sample_match else f"SPL-{len(df) + 1:02d}"

    # Commit to SQLite
    insert_record(batch_tag, sample_id, metric, val, unit, status, text)
    
    if alert_msg:
        return f"Logged {sample_id} with status {status}. {alert_msg}"
    return f"Recorded {sample_id}: {metric} at {val} {unit}."

# --- MAIN TWO-COLUMN WORKSPACE ---
col_voice, col_data = st.columns([1, 1.2], gap="large")

with col_voice:
    with st.container(border=True):
        st.subheader("🎙️ Voice Assistant & Bench Action")
        st.caption("Dictate observations (e.g. *'Sample B-2 temp 78 degrees'*) OR ask questions (e.g. *'What was the highest temperature?'*):")
        
        audio_input = st.audio_input("Speak to Agent")
        run_btn = st.button("⚡ Execute Voice Command", type="primary", use_container_width=True, disabled=audio_input is None)
        
        if run_btn and audio_input:
            with st.status("Transcribing and orchestrating with Sarvam...", expanded=True) as box:
                # 1. Voice in -> Text via Saaras v3
                raw_bytes = audio_input.read()
                transcript = transcribe_audio(raw_bytes)
                
                if transcript:
                    st.write(f"🗣️ **Heard:** *'{transcript}'*")
                    
                    # 2. Execute Action or Query
                    response_text = execute_agent_intent(transcript, current_batch)
                    st.write(f"🤖 **Action/Answer:** {response_text}")
                    
                    # 3. Text out -> Spoken Voice via Bulbul v3
                    voice_bytes = generate_voice_feedback(response_text, speaker_choice, target_lang)
                    box.update(label="Task Completed!", state="complete")
                    
                    # Add to history
                    st.session_state.messages.append({"user": transcript, "bot": response_text, "audio": voice_bytes})
                    st.rerun()

        # Voice Conversation History
        if st.session_state.messages:
            st.divider()
            st.markdown("##### 💬 Recent Spoken Interactions")
            for msg in reversed(st.session_state.messages[-3:]):
                with st.chat_message("user"):
                    st.write(msg["user"])
                with st.chat_message("assistant"):
                    st.write(msg["bot"])
                    if msg.get("audio"):
                        st.audio(msg["audio"], format="audio/wav", autoplay=False)

with col_data:
    with st.container(border=True):
        st.subheader("📊 Live Experiment Ledger & Telemetry")
        
        current_data = load_data()
        if not current_data.empty:
            def highlight_status(val):
                if 'CRITICAL' in str(val):
                    return 'background-color: rgba(239, 68, 68, 0.25); color: #f87171; font-weight: bold;'
                return 'background-color: rgba(34, 197, 94, 0.25); color: #4ade80; font-weight: bold;'

            st.dataframe(
                current_data.style.map(highlight_status, subset=['status']),
                use_container_width=True,
                height=220
            )
            
            st.markdown("##### 📈 Parameter Value Trends")
            st.line_chart(current_data, x="timestamp", y="value", height=200)

            csv = current_data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", data=csv, file_name="lab_measurements.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("Ledger is empty. Speak an observation on the left to log your first experiment.")