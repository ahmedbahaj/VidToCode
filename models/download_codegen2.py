#!/usr/bin/env python3
"""
Downloads the Salesforce/codegen25-7b-instruct model for Approach 3.
Downloads the model to the Hugging Face cache so it can be easily loaded via transformers.
"""

from huggingface_hub import snapshot_download

MODEL_ID = "Salesforce/codegen25-7b-instruct"

def main():
    print(f"Downloading {MODEL_ID} from HuggingFace...")
    print("This is a ~14GB model, so it may take a while depending on your connection.")
    
    # We download it to the default cache directory
    snapshot_download(
        repo_id=MODEL_ID,
        ignore_patterns=["*.safetensors.index.json", "*.msgpack"]
    )
    print("Download complete! Model is ready for use in Approach 3.")

if __name__ == "__main__":
    main()
