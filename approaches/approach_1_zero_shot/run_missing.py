"""
Run inference for the 3 missing Java/medium samples and append to results.json.
"""

import json
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "Qwen3.5-4B-Q6_K.gguf"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RESULTS_FILE = Path(__file__).parent / "results.json"

LANG_EXTENSIONS = {
    "java": [".java", ".Java"],
}

PROMPT_TEMPLATE = """\
You are an expert programmer. Below is a transcript of a {language} programming tutorial video.
Generate only the complete, runnable {language} source code shown or described in the transcript.
Output ONLY the code — no explanation, no markdown fences, no comments.

Transcript:
{transcript}

Code:
"""

MISSING_IDS = [
    "java/medium/medium_1",
    "java/medium/medium_2",
    "java/medium/medium_3",
]

N_CTX = 32768
MAX_OUTPUT_TOKENS = 2048
MAX_TRANSCRIPT_TOKENS = N_CTX - MAX_OUTPUT_TOKENS - 64


def collect_code(vid_dir: Path, language: str):
    exts = LANG_EXTENSIONS.get(language, [])
    code_files = sorted(f for f in vid_dir.iterdir() if f.suffix in exts)
    if not code_files:
        return None
    parts = []
    for f in code_files:
        parts.append(f"// === {f.name} ===")
        parts.append(f.read_text().strip())
    return "\n\n".join(parts) if len(code_files) > 1 else code_files[0].read_text().strip()


def main():
    # Load existing results
    existing = json.loads(RESULTS_FILE.read_text())
    existing_ids = {r["id"] for r in existing}
    print(f"Existing results: {len(existing)} samples")

    # Check which are actually missing
    to_run = [mid for mid in MISSING_IDS if mid not in existing_ids]
    if not to_run:
        print("All samples already present, nothing to do!")
        return
    print(f"Missing samples to generate: {to_run}")

    # Load model
    print("Loading model...")
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=N_CTX,
        n_gpu_layers=-1,
        verbose=False,
    )

    new_results = []
    for sample_id in to_run:
        parts = sample_id.split("/")
        language, tier, name = parts[0], parts[1], parts[2]
        vid_dir = DATA_DIR / language / tier / name

        transcript_file = vid_dir / "transcript.txt"
        if not transcript_file.exists():
            print(f"  [{sample_id}] SKIPPED — no transcript.txt")
            continue

        transcript = transcript_file.read_text().strip()
        reference_code = collect_code(vid_dir, language)
        if reference_code is None:
            print(f"  [{sample_id}] SKIPPED — no code files found")
            continue

        # Truncate transcript if needed
        tokens = llm.tokenize(transcript.encode())
        if len(tokens) > MAX_TRANSCRIPT_TOKENS:
            tokens = tokens[:MAX_TRANSCRIPT_TOKENS]
            transcript = llm.detokenize(tokens).decode(errors="replace")

        prompt = PROMPT_TEMPLATE.format(transcript=transcript, language=language)

        print(f"  [{sample_id}] generating ...", end=" ", flush=True)
        response = llm(
            prompt,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.0,
            stop=["Transcript:", "---"],
        )
        generated = response["choices"][0]["text"].strip()

        new_results.append({
            "id": sample_id,
            "language": language,
            "generated_code": generated,
            "reference_code": reference_code,
        })
        print("done")

    # Append to existing results and save
    existing.extend(new_results)
    RESULTS_FILE.write_text(json.dumps(existing, indent=2))
    print(f"\nAppended {len(new_results)} samples. Total now: {len(existing)}")


if __name__ == "__main__":
    main()
