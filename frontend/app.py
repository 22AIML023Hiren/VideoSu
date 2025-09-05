# frontend/app.py
import streamlit as st
import requests
import base64
import re
import time
import json

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

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'api_base' not in st.session_state:
    st.session_state.api_base = "http://localhost:5000"

st.set_page_config(page_title="🎥 Video Summarizer", layout="wide")

# ----------------------------
# Custom CSS Styling - IMPROVED FOR VISIBILITY
# ----------------------------
st.markdown(
    """
    <style>
    /* ---------------- Background ---------------- */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* ---------------- Header Section ---------------- */
    .header-container {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        color: white;
    }
    .main-title {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        color: white;
        margin-bottom: 15px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    .sub-title {
        font-size: 1.4rem;
        color: #ecf0f1;
        margin-bottom: 10px;
        font-weight: 400;
    }
    .tagline {
        font-size: 1.3rem;
        color: #ecf0f1;
        font-weight: 500;
        margin-top: 20px;
        font-style: italic;
        background: rgba(255, 255, 255, 0.2);
        padding: 10px 20px;
        border-radius: 25px;
        display: inline-block;
    }

    /* ---------------- Input widgets ---------------- */
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        border: 2px solid #3498db !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        padding: 12px !important;
    }

    .stRadio > div {
        background-color: #ffffff !important;
        border: 2px solid #3498db !important;
        border-radius: 10px !important;
        padding: 15px !important;
    }

    .stFileUploader > div > div {
        background-color: #ffffff !important;
        border: 2px dashed #3498db !important;
        border-radius: 10px !important;
        padding: 20px !important;
    }

    /* Backend URL input special styling */
    div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        border: 2px solid #3498db !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="input"] input {
        color: #2c3e50 !important;
    }

    /* ---------------- Fix Selectbox Visibility ---------------- */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        font-weight: 500 !important;
        border-radius: 10px !important;
        border: 2px solid #3498db !important;
    }
    div[data-baseweb="select"] span {
        color: #2c3e50 !important;
        font-weight: 500 !important;
    }

    /* ---------------- Buttons ---------------- */
    .stButton > button {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.8em 2em !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
        font-size: 1.1rem;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #229954 0%, #27ae60 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4) !important;
    }

    /* ---------------- Section cards ---------------- */
    .section-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        border-left: 5px solid #3498db;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #ecf0f1;
    }
    
    /* ---------------- Progress Bar ---------------- */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%) !important;
    }
    
    /* ---------------- Feature Cards ---------------- */
    .feature-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 10px;
        border: 1px solid #e9ecef;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 15px;
        color: #3498db;
    }
    
    /* ---------------- Success/Error messages ---------------- */
    .stSuccess {
        background-color: rgba(46, 204, 113, 0.2) !important;
        border: 1px solid #27ae60 !important;
        color: #27ae60 !important;
    }
    .stError {
        background-color: rgba(231, 76, 60, 0.2) !important;
        border: 1px solid #e74c3c !important;
        color: #e74c3c !important;
    }
    
    /* ---------------- Expander ---------------- */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        border-radius: 10px !important;
        color: #2c3e50 !important;
        font-weight: 600 !important;
        border: 2px solid #3498db !important;
        margin-bottom: 10px;
    }
    
    /* ---------------- Tabs ---------------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #ecf0f1;
        border-radius: 10px 10px 0 0;
        padding: 12px 20px;
        color: #2c3e50;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #3498db !important;
        color: #ffffff !important;
    }
    
    /* ---------------- Dashboard specific styles ---------------- */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Dashboard Functions
# ----------------------------
def show_confidence_metrics():
    """Display confidence metrics in the dashboard"""
    st.markdown("### 🤖 Confidence Metrics")
    
    try:
        # Get confidence metrics from backend
        response = requests.post(
            f"{st.session_state.api_base}/confidence_metrics",
            json={"transcript": st.session_state.result.get("transcript", "")},
            timeout=10
        )
        
        if response.status_code == 200:
            metrics = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <h4>Word Count</h4>
                        <h2>{metrics.get("word_count", 0)}</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <h4>Unique Words</h4>
                        <h2>{metrics.get("unique_words", 0)}</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <h4>Lexical Diversity</h4>
                        <h2>{metrics.get('lexical_diversity', 0) * 100:.1f}%</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <h4>Confidence Score</h4>
                        <h2>{metrics.get('confidence_score', 0) * 100:.1f}%</h2>
                    </div>
                """, unsafe_allow_html=True)
            
            # Audio quality gauge
            audio_quality = metrics.get("audio_quality", 0.5)
            st.markdown("#### Audio Quality Score")
            st.progress(audio_quality, text=f"{audio_quality * 100:.1f}%")
            
        else:
            st.warning("Could not fetch confidence metrics")
            
    except Exception as e:
        st.error(f"Error fetching metrics: {str(e)}")

def show_processing_stats():
    """Display processing statistics"""
    st.markdown("### ⚡ Processing Statistics")
    
    processing_times = st.session_state.result.get("metrics", {}).get("processing_times", {})
    
    if processing_times:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Time per Processing Step:")
            for step, time_val in processing_times.items():
                if step != "total":
                    step_name = step.replace('_', ' ').title()
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4>{step_name}</h4>
                            <h3>{time_val}s</h3>
                        </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            # Create a simple bar chart
            steps = [step.replace('_', ' ').title() for step in processing_times.keys() if step != "total"]
            times = [processing_times[step] for step in processing_times if step != "total"]
            
            if steps and times:
                chart_data = {"Processing Step": steps, "Time (seconds)": times}
                st.bar_chart(chart_data, x="Processing Step", y="Time (seconds)")
    else:
        st.info("No processing time data available")

def show_user_feedback():
    """Display user feedback section"""
    st.markdown("### 💬 User Feedback")
    
    # Feedback form
    summary_id = st.session_state.result.get("summary_id", "")
    
    with st.form("feedback_form"):
        st.write("Rate this summary quality:")
        rating = st.slider("Rating", 1, 5, 4, help="1 = Poor, 5 = Excellent")
        feedback = st.text_area("Additional feedback (optional)", placeholder="What did you like or what can be improved?")
        
        if st.form_submit_button("Submit Feedback"):
            try:
                response = requests.post(
                    f"{st.session_state.api_base}/submit_feedback",
                    json={
                        "rating": rating,
                        "feedback": feedback,
                        "summary_id": summary_id
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Thank you for your feedback!")
                else:
                    st.error("Failed to submit feedback")
                    
            except Exception as e:
                st.error(f"Error submitting feedback: {str(e)}")
    
    # Show feedback statistics if available
    try:
        response = requests.get(f"{st.session_state.api_base}/get_feedback_stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            if stats["total_feedback"] > 0:
                st.markdown("---")
                st.markdown("#### 📊 Community Feedback Statistics")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4>Total Feedback</h4>
                            <h2>{stats["total_feedback"]}</h2>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4>Average Rating</h4>
                            <h2>{stats["average_rating"]}/5</h2>
                        </div>
                    """, unsafe_allow_html=True)
    except:
        pass  # Silently fail if feedback stats aren't available

def show_dashboard_tab():
    """Main dashboard tab content"""
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📊 Analytics Dashboard</div>", unsafe_allow_html=True)
    
    if st.session_state.result:
        tab1, tab2, tab3 = st.tabs(["Confidence Metrics", "Processing Stats", "User Feedback"])
        
        with tab1:
            show_confidence_metrics()
        
        with tab2:
            show_processing_stats()
        
        with tab3:
            show_user_feedback()
    else:
        st.info("Process a video first to see analytics dashboard")
    
    st.markdown("</div>", unsafe_allow_html=True)

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
# Feature Cards Section
# ----------------------------
st.markdown("### 🚀 Powerful Features for Video Analysis")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Multi-Language Support</h3>
            <p>Summarize videos in 9+ Indic languages with accurate translations</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔊</div>
            <h3>Audio Output</h3>
            <p>Listen to your summaries with natural text-to-speech technology</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3>Fast Processing</h3>
            <p>Get results quickly with our optimized AI pipeline</p>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>Analytics Dashboard</h3>
            <p>Get detailed metrics and confidence scores for your summaries</p>
        </div>
    """, unsafe_allow_html=True)

# ----------------------------
# Backend Connection
# ----------------------------
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>🔗 Backend Connection</div>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    api_base = st.text_input("Backend URL", value=st.session_state.api_base, help="Enter your backend server URL")
    st.session_state.api_base = api_base

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

st.markdown("</div>", unsafe_allow_html=True)

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
                    response = requests.post(f"{st.session_state.api_base}/summarize", data=data, files=files, timeout=600)
                else:
                    files = {}
                    data = {"url": video_url, "language": lang_code}
                    response = requests.post(f"{st.session_state.api_base}/summarize", data=data, files=files, timeout=600)

                progress_bar.progress(100)
                result = response.json()

                if response.status_code == 200:
                    st.session_state.result = result
                    st.success("✅ Summary generated successfully!")
                    
                    # Display results in tabs for better organization
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Summary", "🌐 English Summary", "🔊 Audio", "📊 Details", "📈 Dashboard"])
                    
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
                    
                    with tab5:
                        show_dashboard_tab()

                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. The video might be too long or the server is busy.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Connection error. Please check your internet connection and backend server.")
            except Exception as e:
                st.error(f"❌ Exception: {e}")

# Show dashboard tab if we already have results
if st.session_state.result:
    st.markdown("---")
    show_dashboard_tab()

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
        - Analytics dashboard with confidence metrics
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
