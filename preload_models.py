# preload_models.py
from huggingface_hub import snapshot_download
from pathlib import Path

target = Path("hf_models")
target.mkdir(exist_ok=True)

models = {
    "openai/whisper-small": "openai__whisper-small",
    "sshleifer/distilbart-cnn-12-6": "sshleifer__distilbart-cnn-12-6",
}

for repo, local_name in models.items():
    print(f"⬇️ Downloading {repo} ...")
    local_dir = target / local_name
    snapshot_download(repo_id=repo, local_dir=local_dir, local_dir_use_symlinks=False)
    print(f"✅ Saved to {local_dir}")
