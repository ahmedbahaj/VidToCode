"""
Approach 1 — Zero-shot: raw transcript → code via Qwen3.5-4B-Q6_K (llama.cpp).
"""

import json
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "Qwen3.5-4B-Q6_K.gguf"
DATA_DIR = Path(__file__).parent.parent.parent / "data"

LANG_EXTENSIONS = {
    "python": [".py"],
    "cpp": [".cpp", ".h"],
    "java": [".java"],
    "javascript": [".js", ".html", ".css"],
}

PROMPT_TEMPLATE = """\
You are an expert programmer. Below is a transcript of a {language} programming tutorial video.
Generate only the complete, runnable {language} source code shown or described in the transcript.
Output ONLY the code — no explanation, no markdown fences, no comments.

Transcript:
{transcript}

Code:
"""


def collect_code(vid_dir: Path, language: str) -> str | None:
    """Return concatenated source code for all files matching the language's extensions."""
    exts = LANG_EXTENSIONS.get(language, [])
    code_files = sorted(f for f in vid_dir.iterdir() if f.suffix in exts)
    if not code_files:
        return None
    parts = []
    for f in code_files:
        parts.append(f"// === {f.name} ===" if language != "python" else f"# === {f.name} ===")
        parts.append(f.read_text().strip())
    return "\n\n".join(parts) if len(code_files) > 1 else code_files[0].read_text().strip()


def discover_samples() -> list[dict]:
    """Walk data/{language}/{tier}/{video_id}/ and collect all valid samples."""
    samples = []
    for lang_dir in sorted(DATA_DIR.iterdir()):
        if not lang_dir.is_dir() or lang_dir.name not in LANG_EXTENSIONS:
            continue
        language = lang_dir.name
        for tier_dir in sorted(lang_dir.iterdir()):
            if not tier_dir.is_dir():
                continue
            for vid_dir in sorted(tier_dir.iterdir()):
                if not vid_dir.is_dir():
                    continue
                transcript_file = vid_dir / "transcript.txt"
                if not transcript_file.exists():
                    continue
                reference_code = collect_code(vid_dir, language)
                if reference_code is None:
                    continue
                meta_file = vid_dir / "metadata.json"
                meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
                samples.append({
                    "id": f"{language}/{tier_dir.name}/{vid_dir.name}",
                    "transcript": transcript_file.read_text().strip(),
                    "reference_code": reference_code,
                    "language": language,
                    "tier": tier_dir.name,
                    "title": meta.get("title", ""),
                })
    return samples


N_CTX = 32768
MAX_OUTPUT_TOKENS = 2048
# reserve tokens for prompt template overhead and output
MAX_TRANSCRIPT_TOKENS = N_CTX - MAX_OUTPUT_TOKENS - 64


def run_inference(llm: Llama, transcript: str, language: str) -> str:
    # truncate transcript if it would overflow the context window
    tokens = llm.tokenize(transcript.encode())
    if len(tokens) > MAX_TRANSCRIPT_TOKENS:
        tokens = tokens[:MAX_TRANSCRIPT_TOKENS]
        transcript = llm.detokenize(tokens).decode(errors="replace")

    prompt = PROMPT_TEMPLATE.format(transcript=transcript, language=language)
    response = llm(
        prompt,
        max_tokens=MAX_OUTPUT_TOKENS,
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
        n_ctx=N_CTX,
        n_gpu_layers=-1,  # offload all layers to Metal GPU
        verbose=False,
    )

    samples = discover_samples()
    print(f"Loaded {len(samples)} samples")

    results = []
    for sample in samples:
        print(f"  [{sample['id']}] generating ...", end=" ", flush=True)
        generated = run_inference(llm, sample["transcript"], sample["language"])
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
