"""
Download Qwen3.5-27B GGUF from HuggingFace into this models/ directory.
Run once; subsequent runs skip if file already exists.

Available quants (pick one by setting FILENAME):
  Q4_K_M  (~17 GB) — good balance of quality and size
  Q6_K    (~22 GB) — higher quality, matches 4B quant level
  Q8_0    (~29 GB) — near-lossless
"""

import os
os.environ["HF_HUB_DISABLE_XET"] = "1"  # use standard HTTP; xet CDN has DNS issues
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "unsloth/Qwen3.5-27B-GGUF"
FILENAME = "Qwen3.5-27B-Q4_K_M.gguf"
DEST_DIR = Path(__file__).parent


def main():
    dest = DEST_DIR / FILENAME
    if dest.exists():
        print(f"Already downloaded: {dest}")
        return

    print(f"Downloading {FILENAME} from {REPO_ID} ...")
    print(f"This is a large file (~17 GB), it may take a while.")
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=str(DEST_DIR),
    )
    print(f"Saved to: {path}")


if __name__ == "__main__":
    main()
