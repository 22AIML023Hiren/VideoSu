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
import json
from datetime import datetime

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

@app.route("/confidence_metrics", methods=["POST"])
def confidence_metrics():
    """Calculate confidence metrics for transcription"""
    try:
        data = request.json
        transcript = data.get("transcript", "")
        
        # Simple confidence metrics (safe calculations)
        words = transcript.split()
        word_count = len(words)
        unique_words = len(set(words))
        lexical_diversity = unique_words / word_count if word_count > 0 else 0
        
        # Calculate average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Simple audio quality estimation based on transcript length and diversity
        audio_quality_score = min(lexical_diversity * 3, 1.0) if word_count > 20 else 0.5
        
        return jsonify({
            "word_count": word_count,
            "unique_words": unique_words,
            "lexical_diversity": round(lexical_diversity, 3),
            "avg_word_length": round(avg_word_length, 2),
            "confidence_score": round(min(lexical_diversity * 5, 1.0), 2),
            "audio_quality": round(audio_quality_score, 2)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    """Store user feedback about summary quality"""
    try:
        data = request.json
        rating = data.get("rating")
        feedback = data.get("feedback", "")
        summary_id = data.get("summary_id", "unknown")
        
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "rating": rating,
            "feedback": feedback,
            "summary_id": summary_id
        }
        
        # Append to feedback file
        feedback_file = Path("feedback.json")
        if not feedback_file.exists():
            with open(feedback_file, "w") as f:
                json.dump([], f)
        
        with open(feedback_file, "r+") as f:
            feedback_list = json.load(f)
            feedback_list.append(feedback_data)
            f.seek(0)
            json.dump(feedback_list, f, indent=2)
        
        return jsonify({"status": "success", "message": "Feedback saved"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_feedback_stats", methods=["GET"])
def get_feedback_stats():
    """Get feedback statistics"""
    try:
        feedback_file = Path("feedback.json")
        if not feedback_file.exists():
            return jsonify({
                "total_feedback": 0,
                "average_rating": 0,
                "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            })
        
        with open(feedback_file, "r") as f:
            feedback_list = json.load(f)
        
        if not feedback_list:
            return jsonify({
                "total_feedback": 0,
                "average_rating": 0,
                "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
            })
        
        total = len(feedback_list)
        ratings = [item["rating"] for item in feedback_list if "rating" in item]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        rating_dist = {str(i): 0 for i in range(1, 6)}
        for rating in ratings:
            rating_dist[str(rating)] = rating_dist.get(str(rating), 0) + 1
        
        return jsonify({
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_dist
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/summarize", methods=["POST"])
def summarize():
    start_time = time.time()
    processing_steps = {}
    
    try:
        processing_steps["start"] = time.time()
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
        processing_steps["audio_start"] = time.time()
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
        processing_steps["audio_end"] = time.time()

        # Step 2: Transcription
        processing_steps["transcription_start"] = time.time()
        transcript = transcribe_audio(verbose=True)
        processing_steps["transcription_end"] = time.time()

        # Step 3: Summarization
        processing_steps["summarization_start"] = time.time()
        english_summary, final_summary = summarize_pipeline(transcript, target_language, video_url, DEVICE)
        processing_steps["summarization_end"] = time.time()

        # Step 4: Audio Generation
        processing_steps["audio_gen_start"] = time.time()
        try:
            audio_path = save_summary_as_audio(final_summary, target_language)
        except:
            audio_path = None
        processing_steps["audio_gen_end"] = time.time()

        # Calculate step timings
        processing_times = {
            "audio_download": round(processing_steps["audio_end"] - processing_steps["audio_start"], 2),
            "transcription": round(processing_steps["transcription_end"] - processing_steps["transcription_start"], 2),
            "summarization": round(processing_steps["summarization_end"] - processing_steps["summarization_start"], 2),
            "audio_generation": round(processing_steps["audio_gen_end"] - processing_steps["audio_gen_start"], 2),
            "total": round(time.time() - start_time, 2)
        }

        # Generate a unique ID for this summary
        import hashlib
        summary_id = hashlib.md5(f"{video_title}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]

        # Step 5: Response
        response_data = {
            "transcript": transcript,
            "english_summary": english_summary,
            "summary": final_summary,
            "summary_audio": None,
            "summary_id": summary_id,
            "status": "success",
            "metrics": {
                "video_title": video_title,
                "video_duration": video_duration,
                "transcript_length": len(transcript),
                "english_summary_length": len(english_summary),
                "final_summary_length": len(final_summary),
                "target_language": target_language,
                "processing_time": processing_times["total"],
                "processing_times": processing_times
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
