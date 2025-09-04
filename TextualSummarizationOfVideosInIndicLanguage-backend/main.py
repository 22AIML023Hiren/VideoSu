# main.py
import os
import time
from pathlib import Path
from typing import Tuple, List
import json
import warnings
import numpy as np

import requests
import yt_dlp
from gtts import gTTS
from langdetect import detect
from deep_translator import GoogleTranslator

import torch
# New Import: Faster Whisper
import whisper

# ---------- CONFIG ----------
# Device selection: GPU if available otherwise CPU
# Set device explicitly for Faster Whisper
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🔁 Loading models... Using {DEVICE}")

# Models (small / fast defaults). You can override via env vars.
# We no longer need ASR_MODEL_ID for this new approach
SUMMARIZER_MODEL_ID = os.getenv("SUMMARIZER_MODEL_ID", "facebook/bart-large-cnn")

# Optional: local cache folder inside project to avoid re-downloads
LOCAL_HF_MODELS = Path(os.getenv("LOCAL_HF_MODELS", "hf_models"))

 
# Use faster-whisper model directly (small, medium, large, etc.)
WHISPER_MODEL_PATH = "small"
from transformers import pipeline
def _load_pipeline(task: str, model_id: str, device=0 if DEVICE == "cuda" else -1, **kwargs):
    # If LOCAL_HF_MODELS/<model_id_name> exists, load from there
    # sanitize name
    model_folder_name = model_id.replace("/", "__")
    local_path = LOCAL_HF_MODELS / model_folder_name
    if local_path.exists():
        print(f"✅ Loading {task} model from local: {local_path}")
        return pipeline(task, model=str(local_path), device=device, **kwargs)
    else:
        print(f"✅ Loading {task} model from HF: {model_id}")
        return pipeline(task, model=model_id, device=device, **kwargs)

# Build summarizer pipeline
summarizer_model = _load_pipeline("summarization", SUMMARIZER_MODEL_ID, device=0 if DEVICE == "cuda" else -1)

# Load Faster Whisper model directly from the local path
print(f"✅ Loading Faster Whisper model from local path...")
# The WhisperModel constructor can take a local path directly
whisper_model = whisper.load_model("medium", device=DEVICE)

print("✅ Models loaded successfully.")

# -----------------------------
# Bhashini settings
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "").strip()
# Try a couple of endpoints (some deployments vary). We'll try in order.
BHASHINI_URLS = [
    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
    # some deployments use mapmyindia host - include as fallback (payload/response formats may differ)
    "https://bhashini-api.mapmyindia.com/translation",
]

# -----------------------------
# Helpers
def chunk_text(text: str, max_chars: int = 3500) -> List[str]:
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"

# -----------------------------
# YouTube → WAV
def download_youtube_audio(url: str) -> str:
    try:
        download_dir = Path("downloads")
        download_dir.mkdir(exist_ok=True)

        # ENHANCED: Better yt-dlp options to avoid bot detection
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "quiet": False,
            "noplaylist": True,
            "extract_flat": False,
            "no_check_certificate": True,
            "ignoreerrors": False,
            "no_warnings": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
            },
            "extractor_args": {
                "youtube": {
                    "skip": ["dash", "hls"],
                    "player_client": ["android", "web"],
                }
            },
            "socket_timeout": 30,
            "retries": 5,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id")
            audio_path = download_dir / f"{video_id}.wav"
            
            # Store video info for later use if needed
            video_info = {
                "id": video_id,
                "title": info.get("title", ""),
                "description": info.get("description", ""),
                "duration": info.get("duration", 0),
            }
            
            # Save video info to a file for potential use
            info_path = download_dir / f"{video_id}_info.json"
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(video_info, f, ensure_ascii=False, indent=2)

        timeout = 30
        while timeout > 0 and not audio_path.exists():
            time.sleep(1)
            timeout -= 1

        if not audio_path.exists():
            raise Exception("Audio file not found after download")

        final_audio_dir = Path("audio_files")
        final_audio_dir.mkdir(exist_ok=True)
        final_audio_path = final_audio_dir / "audio.wav"

        if final_audio_path.exists():
            final_audio_path.unlink()

        os.replace(audio_path, final_audio_path)
        return str(final_audio_path)

    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg:
            raise Exception("YouTube bot detection triggered. Please try again in a few minutes or use a different video.")
        elif "Private video" in error_msg:
            raise Exception("This is a private video and cannot be downloaded.")
        elif "Video unavailable" in error_msg:
            raise Exception("Video is unavailable or has been removed.")
        else:
            raise Exception(f"YouTube download failed: {error_msg}")

def get_youtube_description(video_url: str) -> str:
    """Extract YouTube video description"""
    try:
        download_dir = Path("downloads")
        video_id = video_url.split("v=")[-1].split("&")[0]
        info_path = download_dir / f"{video_id}_info.json"
        
        if info_path.exists():
            with open(info_path, "r", encoding="utf-8") as f:
                video_info = json.load(f)
                return video_info.get("description", "")
        else:
            # If info file doesn't exist, try to get info without downloading
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "skip_download": True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get("description", "")
                
    except Exception as e:
        print(f"⚠️ Failed to get YouTube description: {e}")
        return ""

def clean_youtube_description(description: str) -> str:
    """Clean YouTube description by removing hashtags and keeping only useful content"""
    if not description:
        return ""
    
    # Split into lines and remove empty lines
    lines = [line.strip() for line in description.split('\n') if line.strip()]
    
    # Remove lines that are just hashtags or social media links
    cleaned_lines = []
    for line in lines:
        # Skip lines that are mostly hashtags or social media prompts
        if (line.startswith('#') or 
            'subscribe' in line.lower() or 
            'follow' in line.lower() or 
            'http' in line.lower() or
            'instagram' in line.lower() or
            'facebook' in line.lower() or
            'twitter' in line.lower()):
            continue
        
        # Remove any hashtags from the line but keep the text
        words = line.split()
        filtered_words = [word for word in words if not word.startswith('#')]
        cleaned_line = ' '.join(filtered_words)
        
        if cleaned_line and len(cleaned_line) > 10:  # Minimum length check
            cleaned_lines.append(cleaned_line)
    
    # Return first 75-100 words
    all_text = ' '.join(cleaned_lines)
    words = all_text.split()
    return ' '.join(words[:100])  # First 100 words

# -----------------------------
# Transcription (Updated for Faster Whisper)
def transcribe_audio(verbose: bool = False) -> str:
    try:
        audio_path = Path("audio_files") / "audio.wav"
        if not audio_path.exists():
            raise Exception("Audio file not found")
        
        # Using Faster Whisper for transcription
        print("🚀 Starting Faster Whisper transcription...")
        result = whisper_model.transcribe(str(audio_path), language="en")
        
        full_text = ""
        for segment in result["segments"]:
            full_text += segment["text"] + " "
        
        text = full_text.strip()
        
        if verbose:
            print(f"📄 Transcription language: en")
            print(f"📄 Transcription length: {len(text)} characters")
            print(f"📄 Transcription preview: {text[:200]}...")

        out_dir = Path("file")
        out_dir.mkdir(exist_ok=True)
        with open(out_dir / "transcript.txt", "w", encoding="utf-8") as f:
            f.write(text)

        return text
        
    except Exception as e:
        print(f"❌ Transcription error details: {str(e)}")
        raise Exception(f"Transcription failed: {str(e)}")

# -----------------------------
# Translation: Bhashini primary, GoogleTranslator fallback
def _try_bhashini_request(url: str, payload: dict, headers: dict, timeout: int = 60):
    # Single attempt wrapper
    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _parse_bhashini_response(data):
    # Try multiple possible response layouts
    try:
        if isinstance(data, dict):
            # Try different response formats
            if "pipelineResponse" in data:
                outputs = []
                for response in data["pipelineResponse"]:
                    if "output" in response:
                        for output in response["output"]:
                            if isinstance(output, dict):
                                if "target" in output:
                                    outputs.append(output["target"])
                                elif "translatedText" in output:
                                    outputs.append(output["translatedText"])
                if outputs:
                    return " ".join(outputs).strip()
            
            # Fallback to direct output
            if "output" in data and isinstance(data["output"], list):
                outputs = []
                for item in data["output"]:
                    if isinstance(item, dict):
                        if "target" in item:
                            outputs.append(item["target"])
                        elif "translatedText" in item:
                            outputs.append(item["translatedText"])
                if outputs:
                    return " ".join(outputs).strip()
            
            if "translatedText" in data:
                return data["translatedText"]
                
    except Exception as e:
        print(f"⚠️ Bhashini response parsing error: {e}")
    
    return ""

def _bhashini_translate(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Try Bhashini endpoints with retries and simple parsing.
    """
    if not BHASHINI_API_KEY:
        raise RuntimeError("Missing BHASHINI_API_KEY")

    headers = {
        "Authorization": BHASHINI_API_KEY,
        "Content-Type": "application/json",
    }

    chunks = chunk_text(text, max_chars=2000)  # Reduced chunk size for reliability
    all_translations = []

    for chunk in chunks:
        # payload matching Dhruva pipeline API
        payload_pipeline = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": src_lang,
                            "targetLanguage": tgt_lang,
                        }
                    },
                }
            ],
            "inputData": {"input": [{"source": chunk}]},
        }

        last_err = None
        translated = False
        
        for base_url in BHASHINI_URLS:
            for attempt in range(1, 4):  # 3 attempts per URL
                try:
                    print(f"➡️ Bhashini try: {base_url} attempt {attempt}")
                    resp = _try_bhashini_request(base_url, payload_pipeline, headers, timeout=30)
                    translated_text = _parse_bhashini_response(resp)
                    
                    if translated_text and len(translated_text) > 10:  # Minimum length check
                        all_translations.append(translated_text)
                        translated = True
                        break
                        
                except Exception as e:
                    last_err = e
                    time.sleep(1.5 * attempt)
            
            if translated:
                break
        
        if not translated:
            print(f"⚠️ Bhashini failed for chunk, using Google fallback")
            try:
                google_translation = GoogleTranslator(source=src_lang, target=tgt_lang).translate(chunk)
                all_translations.append(google_translation)
            except Exception:
                all_translations.append(chunk)  # Keep original if all fails

    return " ".join(all_translations).strip()

def translate_text(text: str, src_lang: str, tgt_lang: str) -> str:
    """
    Primary: Bhashini → Fallback: GoogleTranslator
    Always returns a string. If all fail, returns the original text.
    """
    try:
        print(f"🌐 Translating: {src_lang} → {tgt_lang} ({len(text)} chars)")
        return _bhashini_translate(text, src_lang, tgt_lang)
    except Exception as e:
        print(f"⚠️ Bhashini translation failed: {e}. Falling back to GoogleTranslator.")
        try:
            return GoogleTranslator(source=src_lang, target=tgt_lang).translate(text)
        except Exception as ge:
            print(f"❌ GoogleTranslator failed: {ge}. Returning original text.")
            return text

# -----------------------------
# Summarization flow (IMPROVED)
def summarize_pipeline(transcript: str, target_language: str = "en", video_url: str = None, device: str = "cpu") -> Tuple[str, str]:
    """
    Returns (english_summary, final_summary_in_target_lang)
    """
    txt = (transcript or "").strip()
    
    # Check if transcript is too short
    if len(txt) < 50:
        print("⚠️ Transcript too short for summarization, checking for YouTube description...")
        
        # Try to get YouTube description if video URL is provided
        if video_url:
            description = get_youtube_description(video_url)
            cleaned_description = clean_youtube_description(description)
            
            if cleaned_description and len(cleaned_description) > 50:
                print("✅ Using YouTube description as fallback")
                txt = cleaned_description
            else:
                # If description is not useful, return appropriate message
                noise_message = "This video contains primarily noise or non-speech content. A meaningful summary cannot be generated."
                return noise_message, translate_text(noise_message, "en", target_language)
        else:
            # For non-YouTube content or if no URL provided
            noise_message = "The audio content is too short or contains primarily noise. A meaningful summary cannot be generated."
            return noise_message, translate_text(noise_message, "en", target_language)

    src_lang = detect_language(txt)
    print(f"🌍 Detected transcript language: {src_lang}")

    # 1) Normalize to English for best summarization quality
    if src_lang != "en":
        print("🔁 Translating transcript → English for summarization...")
        txt = translate_text(ttxt, src_lang, "en")
        print(f"✅ Translated transcript length: {len(txt)} characters")

    # 2) Summarize in English with better chunking
    english_chunks = []
    text_chunks = chunk_text(txt, max_chars=2000)
    
    print(f"📊 Summarizing {len(text_chunks)} chunks...")
    
    for i, chunk in enumerate(text_chunks, 1):
        print(f"   Chunk {i}/{len(text_chunks)} ({len(chunk)} chars)")
        
        # Adaptive summary length
        word_count = len(chunk.split())
        max_len = min(250, max(80, int(word_count * 0.4)))
        min_len = max(30, int(max_len * 0.5))
        
        try:
            out = summarizer_model(
                chunk,
                max_length=max_len,
                min_length=min_len,
                do_sample=False,
            )
            summary_text = out[0]["summary_text"].strip()
            english_chunks.append(summary_text)
            print(f"   ✓ Summary: {summary_text[:100]}...")
        except Exception as e:
            print(f"   ⚠️ Chunk summarization failed: {e}")
            # Fallback: take first few sentences
            sentences = chunk.split('.')
            fallback_summary = '. '.join(sentences[:3]) + '.'
            english_chunks.append(fallback_summary)

    english_summary = " ".join(english_chunks).strip()
    print(f"✅ English summary length: {len(english_summary)} characters")

    # 3) Translate final summary to target language (if needed)
    if target_language and target_language.lower() != "en":
        print(f"🔁 Translating summary → {target_language}")
        final_summary = translate_text(english_summary, "en", target_language)
        print(f"✅ Final summary length: {len(final_summary)} characters")
    else:
        final_summary = english_summary

    return english_summary, final_summary

# -----------------------------
# TTS
def save_summary_as_audio(text_summary: str, language_code: str) -> str:
    out_dir = Path("file")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "summary.wav"

    try:
        # Clean text for TTS
        clean_text = ' '.join(text_summary.split()[:300])  # Limit length for TTS
        
        tts = gTTS(text=clean_text, lang=language_code, slow=False)
        tts.save(out_path)
        return str(out_path)
    except Exception as e:
        print(f"⚠️ gTTS failed for '{language_code}' → {e}. Falling back to English voice.")
        try:
            tts = gTTS(text=text_summary[:300], lang="en", slow=False)
            tts.save(out_path)
            return str(out_path)
        except Exception:
            # Final fallback: create empty audio file
            import wave
            with wave.open(str(out_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b'')
            return str(out_path)
