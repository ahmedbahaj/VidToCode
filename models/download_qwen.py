"""
Download Qwen3.5-4B-Q6_K.gguf from HuggingFace into this models/ directory.
Run once; subsequent runs skip if file already exists.
"""

import os
os.environ["HF_HUB_DISABLE_XET"] = "1"  # use standard HTTP; xet CDN has DNS issues
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "unsloth/Qwen3.5-4B-GGUF"
FILENAME = "Qwen3.5-4B-Q6_K.gguf"
DEST_DIR = Path(__file__).parent


def main():
    dest = DEST_DIR / FILENAME
    if dest.exists():
        print(f"Already downloaded: {dest}")
        return

    print(f"Downloading {FILENAME} from {REPO_ID} ...")
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=str(DEST_DIR),
    )
    print(f"Saved to: {path}")


if __name__ == "__main__":
    main()
