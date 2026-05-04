"""
Approach 2 — Structured: preprocessed annotations → code via Qwen3.5-4B-Q6_K (llama.cpp).

Instead of feeding the raw transcript, this approach uses the structured
annotations produced by preprocessing/preprocess.py. Each annotation is
a cleaned, intent-tagged narration segment.
"""

import json
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "Qwen3.5-27B-Q4_K_M.gguf"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ANNOTATIONS_DIR = Path(__file__).parent.parent.parent / "preprocessing" / "results"

LANG_EXTENSIONS = {
    "python": [".py"],
    "cpp": [".cpp", ".h"],
    "java": [".java", ".Java"],
    "javascript": [".js", ".html", ".css"],
}

PROMPT_TEMPLATE = """\
/no_think
You are an expert programmer. Below is a structured summary of a {language} programming tutorial video. \
Each step describes what the instructor coded, with an intent label.

Generate only the complete, runnable {language} source code that implements ALL the steps below. \
Follow the implementation steps precisely — use the exact variable names, function names, and logic described. \
Output ONLY the code — no explanation, no markdown fences, no comments.

Steps:
{steps}

Code:
"""


def format_steps(annotations: list[dict]) -> str:
    """Format structured annotations into a readable step list for the prompt."""
    lines = []
    for i, entry in enumerate(annotations, 1):
        intent = entry["intent"]
        narration = entry["narration"]
        lines.append(f"{i}. [{intent}] {narration}")
    return "\n".join(lines)


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
    """Walk data/{language}/{tier}/{video_id}/ and collect all valid samples with annotations."""
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

                # Check for structured annotations
                sample_id = f"{language}/{tier_dir.name}/{vid_dir.name}"
                annotation_file = ANNOTATIONS_DIR / sample_id / "structured_transcript.json"
                if not annotation_file.exists():
                    print(f"  [{sample_id}] no annotations, skipping")
                    continue

                reference_code = collect_code(vid_dir, language)
                if reference_code is None:
                    continue

                annotations = json.loads(annotation_file.read_text())
                samples.append({
                    "id": sample_id,
                    "annotations": annotations,
                    "reference_code": reference_code,
                    "language": language,
                })
    return samples


N_CTX = 32768
MAX_OUTPUT_TOKENS = 2048
# reserve tokens for prompt template overhead and output
MAX_STEPS_TOKENS = N_CTX - MAX_OUTPUT_TOKENS - 64


def run_inference(llm: Llama, annotations: list[dict], language: str) -> str:
    steps_text = format_steps(annotations)

    # truncate steps if they would overflow the context window
    tokens = llm.tokenize(steps_text.encode())
    if len(tokens) > MAX_STEPS_TOKENS:
        tokens = tokens[:MAX_STEPS_TOKENS]
        steps_text = llm.detokenize(tokens).decode(errors="replace")

    prompt = PROMPT_TEMPLATE.format(steps=steps_text, language=language)
    response = llm(
        prompt,
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=0.0,
        stop=["Steps:", "---"],
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
        n_steps = len(sample["annotations"])
        print(f"  [{sample['id']}] generating ({n_steps} steps) ...", end=" ", flush=True)
        generated = run_inference(llm, sample["annotations"], sample["language"])
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
