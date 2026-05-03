"""
Approach 1 — Zero-shot: raw transcript → code via Qwen3.5-4B-Q6_K (llama.cpp).
"""

import json
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "Qwen3.5-4B-Q6_K.gguf"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

PROMPT_TEMPLATE = """\
You are an expert programmer. Below is a transcript of a programming tutorial video.
Generate only the complete, runnable source code shown or described in the transcript.
Output ONLY the code — no explanation, no markdown fences.

Transcript:
{transcript}

Code:
"""


def discover_samples() -> list[dict]:
    """Walk data/{language}/{tier}/{video_id}/ and collect all valid samples."""
    samples = []
    for lang_dir in sorted(DATA_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        language = lang_dir.name
        for tier_dir in sorted(lang_dir.iterdir()):
            if not tier_dir.is_dir():
                continue
            for vid_dir in sorted(tier_dir.iterdir()):
                if not vid_dir.is_dir():
                    continue
                transcript_file = vid_dir / "transcript.txt"
                code_file = vid_dir / "main.py"
                meta_file = vid_dir / "metadata.json"
                if not (transcript_file.exists() and code_file.exists()):
                    continue
                meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
                samples.append({
                    "id": f"{language}/{tier_dir.name}/{vid_dir.name}",
                    "transcript": transcript_file.read_text().strip(),
                    "reference_code": code_file.read_text().strip(),
                    "language": language,
                    "tier": tier_dir.name,
                    "title": meta.get("title", ""),
                })
    return samples


def run_inference(llm: Llama, transcript: str) -> str:
    prompt = PROMPT_TEMPLATE.format(transcript=transcript)
    response = llm(
        prompt,
        max_tokens=2048,
        temperature=0.0,
        stop=["Transcript:", "---"],
    )
    return response["choices"][0]["text"].strip()


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run models/download_qwen.py first."
        )

    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=8192,
        n_gpu_layers=-1,  # offload all layers to Metal GPU
        verbose=False,
    )

    samples = discover_samples()
    print(f"Loaded {len(samples)} samples")

    results = []
    for sample in samples:
        print(f"  [{sample['id']}] generating ...", end=" ", flush=True)
        generated = run_inference(llm, sample["transcript"])
        results.append({
            "id": sample["id"],
            "language": sample["language"],
            "generated_code": generated,
            "reference_code": sample["reference_code"],
        })
        print("done")

    out_path = Path(__file__).parent / "results.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
