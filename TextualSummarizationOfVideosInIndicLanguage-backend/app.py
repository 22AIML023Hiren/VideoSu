# app.py BACKEND 
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
from pathlib import Path
import logging
import yt_dlp
import random
import time

# Universal device detection - works for both CPU and GPU
def get_device():
    if torch.cuda.is_available():
        device = "cuda"
        print(f"🚀 GPU detected: Using {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        print("🔧 Using CPU mode - GPU not available")
    return device

DEVICE = get_device()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BHASHINI_API_KEY = "iDb3Qb49PnN-1F647c-IRU3AMt15BgVaaQqA7naIMmDcCsZWo8SWjioSDWLvBPTy"
os.environ["BHASHINI_API_KEY"] = BHASHINI_API_KEY

# Import functions from main
from main import (
    download_youtube_audio,
    transcribe_audio,
    detect_language,
    summarize_pipeline,
    save_summary_as_audio,
)

app = Flask(__name__)
CORS(app)

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Backend is running"
    })

def format_duration(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes == 0:
        return f"{remaining_seconds} seconds"
    elif remaining_seconds == 0:
        return f"{minutes} minutes"
    else:
        return f"{minutes} minutes {remaining_seconds} seconds"

def get_youtube_metadata(video_url: str):
    """Fetch title and duration using yt_dlp."""
    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get("title", "Unknown Title")
            duration_seconds = info.get("duration", 0)
            formatted_duration = format_duration(duration_seconds)
            return title, formatted_duration
    except Exception as e:
        logger.error(f"❌ Metadata fetch failed: {e}")
        return "Unknown Title", "N/A"

@app.route("/summarize", methods=["POST"])
def summarize():
    start_time = time.time()
    try:
        video_url = request.form.get("url") or request.form.get("video_url")
        # Simple check for direct video URLs
        if video_url and not ("youtube.com" in video_url or "youtu.be" in video_url):
            return jsonify({"error": "Only YouTube URLs supported. Use YouTube links or file upload.", "status": "error"}), 400
        
        target_language = (request.form.get("language") or "en").strip().lower()
        uploaded_file = request.files.get("file")

        if not video_url and not uploaded_file:
            return jsonify({"error": "No video URL or file provided", "status": "error"}), 400

        video_title, video_duration = "N/A", "N/A"

        # Step 1: Audio Source
        if video_url:
            try:
                audio_path = download_youtube_audio(video_url)
                video_title, video_duration = get_youtube_metadata(video_url)
                logger.info(f"✅ Audio downloaded: {audio_path}")
                logger.info(f"🎞️ Title: {video_title}, ⏱ Duration: {video_duration}")
            except Exception as e:
                return jsonify({"error": f"YouTube download failed: {str(e)}", "status": "error"}), 400
        else:
            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            audio_path = audio_dir / "audio.wav"
            uploaded_file.save(audio_path)
            video_title = "Uploaded File"

        # Step 2: Transcription
        transcript = transcribe_audio(verbose=True)

        # Step 3: Summarization
        english_summary, final_summary = summarize_pipeline(transcript, target_language, video_url, DEVICE)

        # Step 4: Audio Generation
        try:
            audio_path = save_summary_as_audio(final_summary, target_language)
        except:
            audio_path = None

        # Step 5: Response
        response_data = {
            "transcript": transcript,
            "english_summary": english_summary,
            "summary": final_summary,
            "summary_audio": None,
            "status": "success",
            "metrics": {
                "video_title": video_title,
                "video_duration": video_duration,
                "transcript_length": len(transcript),
                "english_summary_length": len(english_summary),
                "final_summary_length": len(final_summary),
                "target_language": target_language,
                "processing_time": round(time.time() - start_time, 2)
            }
        }

        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                response_data["summary_audio"] = base64.b64encode(f.read()).decode("utf-8")
        
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}", "status": "error"}), 500

if __name__ == "__main__":
    for d in ["downloads", "audio_files", "file", "hf_models"]:
        Path(d).mkdir(exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
