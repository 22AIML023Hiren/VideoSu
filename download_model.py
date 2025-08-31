# Save this code as a temporary Python file, e.g., download_model.py

from huggingface_hub import snapshot_download

# This function will download all files in the repository
# It will save the files to the default Hugging Face cache location
# If the files already exist, it will skip the download
# The 'allow_patterns' will ensure only the model.bin file is downloaded, saving time and space.
snapshot_download(
    repo_id="openai/whisper-small",
    allow_patterns=["*.bin"]
)

print("Model download complete. The model is now in your Hugging Face cache.")