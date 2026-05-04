"""
Preprocessing: raw transcript → structured annotation via Qwen3.5-4B.

Reads each transcript.txt from data/, sends it through Qwen with a structured
prompt, and saves the result as structured_transcript.json in preprocessed/.

Usage:
    uv run preprocessing/preprocess.py
"""

import json
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).parent.parent / "models" / "Qwen3.5-4B-Q6_K.gguf"
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent / "results"

LANGUAGES = ["python", "cpp", "java", "javascript"]

PROMPT_TEMPLATE = """\
/no_think
You are a transcript preprocessor for programming tutorials. Below is a raw \
transcript from a {language} programming tutorial video. Each line is formatted \
as [timestamp] spoken text.

Your task:

1. REMOVE all filler: introductions ("hi I'm..."), outros ("thanks for \
watching"), sponsor segments, subscribe/like requests, music tags, \
and any off-topic chatter that is not about the code.

2. SEGMENT the remaining content into logical chunks. Each chunk should \
be one coherent action — a single coding step, one concept, or one \
debugging action. Do not combine multiple unrelated steps.

3. CLASSIFY each chunk with exactly one intent:
   - "implementation" — the narrator describes code to write \
(defining functions, variables, loops, conditions, classes, etc.)
   - "explanation" — the narrator explains a concept, algorithm behavior, \
or why something works (without dictating specific code)
   - "debugging" — the narrator is finding or fixing a bug
   - "refactoring" — the narrator restructures or improves existing code

4. CLEAN each narration: convert spoken language to concise written \
instructions. Fix grammar, remove hesitations ("um", "uh", "so"), \
and be precise about code elements (variable names, operators, types).

Output ONLY a valid JSON array. Each element is an object with exactly \
two keys: "narration" (string) and "intent" (string). \
Do not wrap in markdown fences. Do not add any explanation. Do not think.

Transcript:
{transcript}

JSON:
[
"""

N_CTX = 32768
MAX_OUTPUT_TOKENS = 8192
MAX_TRANSCRIPT_TOKENS = N_CTX - MAX_OUTPUT_TOKENS - 128


def discover_samples():
    """Walk data/{language}/{tier}/{video_id}/ and collect all valid samples."""
    samples = []
    for lang_dir in sorted(DATA_DIR.iterdir()):
        if not lang_dir.is_dir() or lang_dir.name not in LANGUAGES:
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
                samples.append({
                    "id": f"{language}/{tier_dir.name}/{vid_dir.name}",
                    "language": language,
                    "transcript_path": transcript_file,
                })
    return samples


def parse_json_response(text):
    """
    Try to extract a valid JSON array from the LLM response.
    Handles <think> blocks, markdown fences, and other junk.
    """
    import re
    text = text.strip()

    # Strip <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Find the JSON array boundaries
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return json.loads(text)


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            "Run models/download_qwen.py first."
        )

    print("Loading model...")
    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=N_CTX,
        n_gpu_layers=-1,
        verbose=False,
    )

    samples = discover_samples()
    print(f"Found {len(samples)} samples\n")

    success = 0
    failed = []

    for sample in samples:
        sample_id = sample["id"]
        language = sample["language"]
        transcript = sample["transcript_path"].read_text().strip()

        # Determine output path: preprocessed/{lang}/{tier}/{name}/structured_transcript.json
        out_dir = OUTPUT_DIR / sample_id
        out_file = out_dir / "structured_transcript.json"

        # Skip if already processed
        if out_file.exists():
            print(f"  [{sample_id}] already exists, skipping")
            success += 1
            continue

        print(f"  [{sample_id}] preprocessing ...", end=" ", flush=True)

        # Truncate transcript if needed
        tokens = llm.tokenize(transcript.encode())
        if len(tokens) > MAX_TRANSCRIPT_TOKENS:
            tokens = tokens[:MAX_TRANSCRIPT_TOKENS]
            transcript = llm.detokenize(tokens).decode(errors="replace")

        prompt = PROMPT_TEMPLATE.format(transcript=transcript, language=language)
        response = llm(
            prompt,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.0,
            stop=["Transcript:", "---", "]"],
        )
        # Prepend '[' since we primed the prompt with it, and append ']' since it's a stop token
        raw_output = "[" + response["choices"][0]["text"].strip() + "]"

        # Parse and validate
        try:
            parsed = parse_json_response(raw_output)
            if not isinstance(parsed, list):
                raise ValueError("Response is not a JSON array")

            # Auto-fix and filter entries
            structured = []
            valid_intents = {"implementation", "explanation", "debugging", "refactoring"}
            for entry in parsed:
                if not isinstance(entry, dict):
                    continue

                # Fix typo'd narration keys (e.g. "narruse", "narrar")
                if "narration" not in entry:
                    narr_key = next((k for k in entry if k.startswith("narr")), None)
                    if narr_key:
                        entry["narration"] = entry.pop(narr_key)

                # Skip entries missing required keys
                if "narration" not in entry or "intent" not in entry:
                    continue

                # Fix invalid intents — default to "explanation"
                if entry["intent"] not in valid_intents:
                    entry["intent"] = "explanation"

                # Keep only the two required keys
                structured.append({
                    "narration": entry["narration"],
                    "intent": entry["intent"],
                })

            if not structured:
                raise ValueError("No valid entries after filtering")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"FAILED ({e})")
            failed.append({"id": sample_id, "error": str(e), "raw_output": raw_output[:500]})
            # Save raw output for debugging
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "raw_output.txt").write_text(raw_output)
            continue

        # Save
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(structured, indent=2))

        n_impl = sum(1 for e in structured if e["intent"] == "implementation")
        n_expl = sum(1 for e in structured if e["intent"] == "explanation")
        n_other = len(structured) - n_impl - n_expl
        print(f"done ({len(structured)} segments: {n_impl} impl, {n_expl} expl, {n_other} other)")
        success += 1

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Done: {success}/{len(samples)} succeeded, {len(failed)} failed")
    if failed:
        print("\nFailed samples:")
        for f in failed:
            print(f"  {f['id']}: {f['error']}")


if __name__ == "__main__":
    main()
