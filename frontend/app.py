# frontend/app.py
import streamlit as st
import requests
import base64
import re
import time

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
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: #ffffff;
    }
    
    /* Main content area */
    .main .block-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* ---------------- Header Section ---------------- */
    .header-container {
        background: linear-gradient(135deg, #1a2a3a 0%, #2d4a5f 100%);
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(76, 161, 175, 0.3);
    }
    .main-title {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: white;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    .sub-title {
        font-size: 1.4rem;
        color: #cce7ff;
        margin-bottom: 5px;
        font-weight: 400;
    }
    .tagline {
        font-size: 1.3rem;
        color: #4ca1af;
        font-weight: 500;
        margin-top: 15px;
        font-style: italic;
    }

    /* ---------------- Input widgets ---------------- */
    .stTextInput > div > div > input,
    .stRadio > div,
    .stFileUploader > div > div,
    .stTextArea > div > textarea {
        background-color: rgba(213, 245, 227, 0.1) !important;
        color: #ffffff !important;
        border: 2px solid #4ca1af !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 12px !important;
    }

    /* Backend URL input special styling */
    div[data-baseweb="input"] > div {
        background-color: rgba(209, 242, 235, 0.1) !important;
        border: 2px solid #4ca1af !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="input"] input {
        color: #ffffff !important;
    }

    /* ---------------- Fix Selectbox Visibility ---------------- */
    div[data-baseweb="select"] > div {
        background-color: rgba(213, 245, 227, 0.1) !important;
        color: #ffffff !important;
        font-weight: 500 !important;
        border-radius: 10px !important;
        border: 2px solid #4ca1af !important;
    }
    div[data-baseweb="select"] span {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* ---------------- Buttons ---------------- */
    .stButton > button {
        background: linear-gradient(135deg, #45b39d 0%, #52c5b8 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.8em 2em !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(69, 179, 157, 0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1abc9c 0%, #2dd4bf 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(26, 188, 156, 0.4) !important;
    }

    /* ---------------- Section cards ---------------- */
    .section-card {
        background: rgba(255, 255, 255, 0.08);
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        margin-bottom: 25px;
        border: 1px solid rgba(76, 161, 175, 0.3);
        backdrop-filter: blur(10px);
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #4ca1af;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(76, 161, 175, 0.3);
    }
    
    /* ---------------- Progress Bar ---------------- */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4ca1af 0%, #45b39d 100%) !important;
    }
    
    /* ---------------- Text colors ---------------- */
    .stMarkdown {
        color: #ffffff;
    }
    
    /* ---------------- Success/Error messages ---------------- */
    .stSuccess {
        background-color: rgba(69, 179, 157, 0.2) !important;
        border: 1px solid #45b39d !important;
    }
    .stError {
        background-color: rgba(231, 76, 60, 0.2) !important;
        border: 1px solid #e74c3c !important;
    }
    
    /* ---------------- Expander ---------------- */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    
    /* ---------------- Tabs ---------------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px 8px 0 0;
        padding: 12px 20px;
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(76, 161, 175, 0.3) !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Header Section
# ----------------------------
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">🎥 Textual Summarization of Videos in Indic Languages</h1>
        <p class="sub-title">Upload a video or paste a YouTube URL and get concise summaries with audio output</p>
        <p class="tagline">From hours to minutes: bridging video and language with intelligent summarization</p>
    </div>
""", unsafe_allow_html=True)

# ----------------------------
# Backend Connection
# ----------------------------
col1, col2 = st.columns([3, 1])
with col1:
    api_base = st.text_input("Backend URL", value="http://localhost:5000").strip()

with col2:
    st.write("")  # Spacer
    st.write("")  # Spacer
    if st.button("🔄 Check Connection", key="health_check"):
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
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>📥 Input Options</div>", unsafe_allow_html=True)

input_method = st.radio("Select Input Method", ["YouTube URL", "Upload Video"], horizontal=True)

video_file = None
video_url = None

if input_method == "YouTube URL":
    video_url = st.text_input("Enter YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...").strip()
    if video_url and "youtube.com/shorts/" in video_url:
        video_id = video_url.split("shorts/")[-1].split("?")[0]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
else:
    video_file = st.file_uploader(
        "Upload Video File", 
        type=["mp4", "mov", "avi", "mkv", "wav", "mp3"],
        help="Supported formats: MP4, MOV, AVI, MKV, WAV, MP3"
    )

col3, col4 = st.columns(2)
with col3:
    selected_lang = st.selectbox("Select Target Language for Summary", list(LANGUAGES.keys()))
    lang_code = LANGUAGES[selected_lang]

with col4:
    show_english = st.checkbox("Show English summary", value=True)
    show_stats = st.checkbox("Show video stats", value=True)

st.markdown("</div>", unsafe_allow_html=True)

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
if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
    if input_method == "YouTube URL" and not video_url:
        st.warning("⚠️ Please provide a valid YouTube URL.")
    elif input_method == "Upload Video" and not video_file:
        st.warning("⚠️ Please upload a video file.")
    else:
        with st.spinner("⏳ Processing video... This may take a few minutes depending on video length."):
            progress_bar = st.progress(0)
            
            try:
                # Simulate progress (you can replace this with actual progress updates if your backend supports it)
                for percent_complete in range(0, 101, 10):
                    progress_bar.progress(percent_complete)
                    time.sleep(0.1)
                
                if input_method == "Upload Video":
                    files = {"file": video_file}
                    data = {"language": lang_code}
                    response = requests.post(f"{api_base}/summarize", data=data, files=files, timeout=600)
                else:
                    files = {}
                    data = {"url": video_url, "language": lang_code}
                    response = requests.post(f"{api_base}/summarize", data=data, files=files, timeout=600)

                progress_bar.progress(100)
                result = response.json()

                if response.status_code == 200:
                    st.success("✅ Summary generated successfully!")
                    
                    # Display results in tabs for better organization
                    tab1, tab2, tab3, tab4 = st.tabs(["📄 Summary", "🌐 English Summary", "🔊 Audio", "📊 Details"])
                    
                    with tab1:
                        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                        st.markdown(f"### Summary in {selected_lang}")
                        st.write(result.get("summary", "—"))
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with tab2:
                        if show_english:
                            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                            st.markdown("### English Summary")
                            st.write(result.get("english_summary", "—"))
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.info("English summary display is disabled in settings")
                    
                    with tab3:
                        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                        st.markdown("### Audio Summary")
                        audio_b64 = result.get("summary_audio")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            st.audio(audio_bytes, format="audio/wav")
                            st.download_button(
                                "⬇️ Download Audio", 
                                audio_bytes, 
                                file_name=f"summary_{lang_code}.wav", 
                                mime="audio/wav"
                            )
                        else:
                            st.info("No audio generated.")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with tab4:
                        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
                        st.markdown("### Video Details")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("**Video Preview**")
                            if video_url:
                                st.video(video_url)
                            elif video_file:
                                # Reset file pointer to beginning
                                video_file.seek(0)
                                st.video(video_file)
                        
                        with col_b:
                            if show_stats:
                                metrics = result.get("metrics", {})
                                st.markdown("**Statistics**")
                                st.write(f"**Title:** {metrics.get('video_title', 'N/A')}")
                                st.write(f"**Duration:** {metrics.get('video_duration', 'N/A')}")
                                st.write(f"**Transcript Length:** {metrics.get('transcript_length', '—')} characters")
                                st.write(f"**Summary Length:** {metrics.get('final_summary_length', '—')} characters")
                                st.write(f"**Target Language:** {selected_lang}")
                                st.write(f"**Processing Time:** {metrics.get('processing_time', '—')} seconds")
                        
                        st.markdown("</div>", unsafe_allow_html=True)

                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. The video might be too long or the server is busy.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection error. Please check your internet connection and backend server.")
            except Exception as e:
                st.error(f"❌ Exception: {e}")

# ----------------------------
# Info Section
# ----------------------------
st.markdown("---")
with st.expander("ℹ️ About This Tool", expanded=False):
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("""
        **How It Works:**
        
        1. **Upload** a video or provide a YouTube URL
        2. **Select** your preferred language for the summary
        3. **Get** a concise text summary and audio version
        
        **Supported Languages:**
        - Hindi, Gujarati, Tamil, Telugu
        - Bengali, Punjabi, Kannada, Marathi
        - English
        
        **Technical Features:**
        - Automatic transcription with Whisper AI
        - Multi-language summarization
        - Text-to-speech audio generation
        """)
    
    with col_info2:
        st.markdown("""
        **Best Practices:**
        
        - For best results, use videos with clear audio
        - Ideal video length: 5-15 minutes
        - Supported formats: MP4, MOV, AVI, MKV
        
        **Limitations:**
        - Very long videos may take significant time to process
        - Heavy accents or background noise may affect accuracy
        - YouTube Shorts are converted to standard format
        
        **Need Help?**
        - Check the backend connection if experiencing issues
        - Ensure your video meets the format requirements
        """)

# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6c757d; padding: 20px;'>"
    "Video Summarization Tool • Powered by AI • From hours to minutes"
    "</div>",
    unsafe_allow_html=True
)
