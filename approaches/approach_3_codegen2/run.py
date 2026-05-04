#!/usr/bin/env python3
"""
Approach 3: Zero-Shot Code Generation from Raw Transcripts using CodeGen2.5.
Reads raw_transcript.txt for each sample and generates code using Salesforce/codegen25-7b-instruct via HuggingFace Transformers.
"""

import json
import os
import re
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "preprocessing" / "results"
OUTPUT_FILE = Path(__file__).resolve().parent / "results.json"

MODEL_ID = "Salesforce/codegen25-7b-instruct"

def get_prompt(transcript, language):
    """
    Constructs a strict few-shot prompt to force CodeGen2.5 to output only code.
    CodeGen2.5-instruct uses custom prompt formatting if trained for it, but standard few-shot works best for strict code extraction.
    """
    return f"""You are an expert programmer. Read the following YouTube video transcript which contains a coding tutorial.
Your task is to write ONLY the exact, complete, runnable {language} source code that implements the final outcome of the tutorial.
Do not output any markdown formatting, code fences, or explanations. Just output the raw code.

--- Transcript ---
{transcript}

--- Generated {language} Code ---
"""

def discover_samples():
    samples = []
    if not DATA_DIR.exists():
        print(f"Warning: {DATA_DIR} does not exist. Run preprocessing first.")
        return samples

    for lang_dir in DATA_DIR.iterdir():
        if not lang_dir.is_dir(): continue
        lang = lang_dir.name
        for length_dir in lang_dir.iterdir():
            if not length_dir.is_dir(): continue
            for sample_dir in length_dir.iterdir():
                if not sample_dir.is_dir(): continue
                
                raw_path = sample_dir / "raw_transcript.txt"
                if raw_path.exists():
                    samples.append({
                        "id": f"{lang}/{length_dir.name}/{sample_dir.name}",
                        "language": lang,
                        "raw_transcript_path": raw_path
                    })
    
    # Sort for deterministic processing
    return sorted(samples, key=lambda x: x["id"])

def safe_load_tokenizer(model_id):
    try:
        return AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    except Exception as e:
        # The Salesforce tokenizer has known bugs on modern transformers.
        # It's already been downloaded to the huggingface cache at this point,
        # so we can dynamically patch the broken python file and retry.
        import os, glob, sys
        home = os.path.expanduser("~")
        pattern = os.path.join(home, ".cache", "huggingface", "modules", "transformers_modules", "Salesforce", "codegen25*", "*", "tokenization_codegen25.py")
        matches = glob.glob(pattern)
        
        if not matches:
            raise e # If we can't find the file, raise original error
            
        print("Patching broken Salesforce tokenizer cache...")
        for path in matches:
            with open(path, "r") as f:
                content = f.read()
            
            # Fix 1: Add missing @property decorator to vocab_size
            if "def vocab_size(self):" in content and "@property" not in content.split("def vocab_size(self):")[0][-20:]:
                content = content.replace("    def vocab_size(self):", "    @property\n    def vocab_size(self):")
            
            # Fix 2: Remove conflicting kwarg from super().__init__
            if "add_special_tokens=add_special_tokens," in content:
                content = content.replace("add_special_tokens=add_special_tokens,", "")
                
            with open(path, "w") as f:
                f.write(content)
                
        # Remove broken module from sys.modules so it's reloaded
        for k in list(sys.modules.keys()):
            if "tokenization_codegen25" in k:
                del sys.modules[k]
                
        return AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

def main():
    print(f"Loading {MODEL_ID}...")
    
    # Check device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Safely load and patch tokenizer
    tokenizer = safe_load_tokenizer(MODEL_ID)
    
    # Use float16 if on CUDA to save memory, otherwise float32
    dtype = torch.float16 if device == "cuda" else torch.float32
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )

    samples = discover_samples()
    print(f"Found {len(samples)} samples to process.")
    
    results = []
    
    # Create approach directory if it doesn't exist
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    for i, sample in enumerate(samples):
        print(f"Processing {i+1}/{len(samples)}: {sample['id']}")
        
        with open(sample["raw_transcript_path"], "r") as f:
            transcript = f.read()
            
        prompt = get_prompt(transcript, sample["language"])
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        input_len = inputs.input_ids.shape[1]
        
        # CodeGen2.5 handles up to ~8192 context, depending on exact config
        if input_len > 6000:
            print(f"  Warning: Long prompt ({input_len} tokens). Might be truncated.")
            
        # Generate code (sampling with low temperature to match Approach 1 constraints)
        outputs = model.generate(
            **inputs,
            max_new_tokens=1500,
            temperature=0.2,
            do_sample=True,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Decode only the newly generated tokens
        generated_tokens = outputs[0][input_len:]
        generated_code = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        
        # Cleanup extra markdown fences if the model still generated them
        cleaned_code = re.sub(r'^```\w*\n?', '', generated_code)
        cleaned_code = re.sub(r'\n?```$', '', cleaned_code)
        cleaned_code = cleaned_code.strip()
        
        results.append({
            "id": sample["id"],
            "language": sample["language"],
            "generated_code": cleaned_code
        })
        
        # Save incrementally
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)

    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
