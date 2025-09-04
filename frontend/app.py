# frontend/app.py
import streamlit as st
import requests
import base64
import re

# ----------------------------
# Config & Language Options
# ----------------------------
LANGUAGES = {
    "Hindi": "hi",
    "Gujarati": "gu",
    "Tamil": "ta",
    "Telugu": "te",
    "Bengali": "bn",
    "Punjabi": "pa",
    "Kannada": "kn",
    "Marathi": "mr",
    "English": "en",
}

st.set_page_config(page_title="🎥 Video Summarizer", layout="wide")

# ----------------------------
# Custom CSS Styling
# ----------------------------
st.markdown(
    """
    <style>
    /* ---------------- Background ---------------- */
    body, .stApp {
        background-color: #eef5fb;  /* soft pastel blue */
    }

    /* ---------------- Title ---------------- */
    .main-title {
        text-align: center;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: #2c3e50;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        font-size: 1.15rem;
        color: #444;
        margin-bottom: 25px;
    }

    /* ---------------- Input widgets ---------------- */
    .stTextInput > div > div > input,
    .stRadio > div,
    .stFileUploader > div > div,
    .stTextArea > div > textarea {
        background-color: #d5f5e3 !important;  /* light green */
        color: #2c3e50 !important;
        border: 1px solid #a3e4d7 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px !important;
    }

    /* Backend URL input special styling */
    div[data-baseweb="input"] > div {
        background-color: #d1f2eb !important;  /* teal green shade */
        border: 1px solid #76d7c4 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="input"] input {
        color: #154360 !important;
    }

    /* ---------------- Fix Selectbox Visibility ---------------- */
    div[data-baseweb="select"] > div {
        background-color: #d5f5e3 !important;
        color: #2c3e50 !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] span {
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }

    /* ---------------- Buttons ---------------- */
    .stButton > button {
        background-color: #45b39d !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.6em 1.5em !important;
        font-weight: bold !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #1abc9c !important;
        color: white !important;
    }

    /* ---------------- Section cards ---------------- */
    .section-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a5276;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Title + Subtitle
# ----------------------------
st.markdown("<h1 class='main-title'>🎥 Textual Summarization of Videos in Indic Languages</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Upload a video or paste a YouTube URL and get concise summaries with audio output.</p>", unsafe_allow_html=True)

# ----------------------------
# Backend Connection
# ----------------------------
api_base = st.text_input("Backend URL", value="http://localhost:5000").strip()

try:
    health_response = requests.get(f"{api_base}/health", timeout=5)
    if health_response.status_code == 200:
        try:
            data = health_response.json()
            if data.get("status") == "healthy":
                st.success("✅ Backend connected successfully!")
            else:
                st.warning("⚠️ Backend responded but status not healthy")
        except Exception:
            st.success("✅ Backend reachable (non-JSON response)")
    else:
        st.error(f"❌ Backend returned status code {health_response.status_code}")
except requests.exceptions.ConnectionError:
    st.error("❌ Cannot connect to backend. Please check the URL.")
except Exception as e:
    st.error(f"❌ Health check failed: {e}")

# ----------------------------
# Input Section
# ----------------------------
input_method = st.radio("Select Input Method", ["YouTube URL", "Upload Video"], horizontal=True)

video_file = None
video_url = None

if input_method == "YouTube URL":
    video_url = st.text_input("Enter YouTube Video URL").strip()
    if video_url and "youtube.com/shorts/" in video_url:
        video_id = video_url.split("shorts/")[-1].split("?")[0]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
else:
    video_file = st.file_uploader("Upload Video File", type=["mp4", "mov", "avi", "mkv", "wav", "mp3"])

selected_lang = st.selectbox("Select Target Language for Summary", list(LANGUAGES.keys()))
lang_code = LANGUAGES[selected_lang]

show_english = st.checkbox("Show English summary", value=True)
show_stats = st.checkbox("Show video stats", value=True)

# ----------------------------
# Helper: Clean Transcript
# ----------------------------
def clean_transcript(text: str) -> str:
    if not text:
        return "—"
    cleaned = re.sub(r"\b(music|applause|laughs|background|noise)\b", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else "Transcript not available."

# ----------------------------
# Generate Summary
# ----------------------------
if st.button("🚀 Generate Summary", type="primary"):
    if input_method == "YouTube URL" and not video_url:
        st.warning("⚠️ Please provide a valid YouTube URL.")
    elif input_method == "Upload Video" and not video_file:
        st.warning("⚠️ Please upload a video file.")
    else:
        with st.spinner("⏳ Processing video..."):
            try:
                if input_method == "Upload Video":
                    files = {"file": video_file}
                    data = {"language": lang_code}
                    response = requests.post(f"{api_base}/summarize", data=data, files=files, timeout=600)
                else:
                    files = {}
                    data = {"url": video_url, "language": lang_code}
                    response = requests.post(f"{api_base}/summarize", data=data, files=files, timeout=600)

                result = response.json()

                if response.status_code == 200:
                    st.success("✅ Summary generated successfully!")

                    left, right = st.columns([2, 3])

                    with left:
                        st.markdown("<div class='section-card'><div class='section-header'>🎬 Video Preview</div>", unsafe_allow_html=True)
                        if video_url:
                            st.video(video_url)
                        elif video_file:
                            st.video(video_file)
                        st.markdown("</div>", unsafe_allow_html=True)

                        if show_stats:
                            st.markdown("<div class='section-card'><div class='section-header'>📊 Video Stats</div>", unsafe_allow_html=True)
                            metrics = result.get("metrics", {})
                            st.write(f"**Title:** {metrics.get('video_title', 'N/A')}")
                            st.write(f"**Duration:** {metrics.get('video_duration', 'N/A')} min")
                            st.write(f"**Transcript Length:** {metrics.get('transcript_length', '—')} chars")
                            st.write(f"**Summary Length:** {metrics.get('final_summary_length', '—')} chars")
                            st.write(f"**Target Language:** {metrics.get('target_language', '—')}")
                            st.markdown("</div>", unsafe_allow_html=True)

                    with right:
                        st.markdown("<div class='section-card'><div class='section-header'>📄 Summary</div>", unsafe_allow_html=True)
                        st.write(result.get("summary", "—"))
                        st.markdown("</div>", unsafe_allow_html=True)

                        if show_english:
                            st.markdown("<div class='section-card'><div class='section-header'>🌐 English Summary</div>", unsafe_allow_html=True)
                            st.write(result.get("english_summary", "—"))
                            st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("<div class='section-card'><div class='section-header'>🔊 Audio Summary</div>", unsafe_allow_html=True)
                        audio_b64 = result.get("summary_audio")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            st.audio(audio_bytes, format="audio/wav")
                            st.download_button("⬇️ Download Audio", audio_bytes, file_name="summary.wav", mime="audio/wav")
                        else:
                            st.info("No audio generated.")
                        st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

            except requests.exceptions.Timeout:
                st.error("❌ Request timed out.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection error.")
            except Exception as e:
                st.error(f"❌ Exception: {e}")

# ----------------------------
# Info Section
# ----------------------------
st.markdown("---")
with st.expander("ℹ️ About this website"):
    st.markdown("""
    This website processes YouTube videos and local uploads to provide summaries in Indic languages.

    **Features:**
    - YouTube URL & file upload support  
    - Automatic transcription with Whisper AI  
    - Multi-language summarization  
    - Audio summary generation  
    - Video stats (title, duration, lengths)  
    """)