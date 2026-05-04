"""
Temp script: reprocess specific samples that had too few segments.
Retries up to 10 times, keeping only results with >= min_segments.
"""

import json
import re
import sys
from pathlib import Path
from llama_cpp import Llama

sys.path.insert(0, str(Path(__file__).parent))
from preprocess import PROMPT_TEMPLATE, parse_json_response, N_CTX, MAX_OUTPUT_TOKENS, MAX_TRANSCRIPT_TOKENS

MODEL_PATH = Path(__file__).parent.parent / "models" / "Qwen3.5-4B-Q6_K.gguf"
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent / "results"

TARGETS = {
    "java/long/long_1": 15,   # 300-line transcript, expect at least 15 segments
}

def main():
    llm = Llama(model_path=str(MODEL_PATH), n_ctx=N_CTX, n_gpu_layers=-1, verbose=False)

    for sample_id, min_segments in TARGETS.items():
        parts = sample_id.split("/")
        language = parts[0]
        transcript_path = DATA_DIR / sample_id / "transcript.txt"
        transcript = transcript_path.read_text().strip()

        tokens = llm.tokenize(transcript.encode())
        if len(tokens) > MAX_TRANSCRIPT_TOKENS:
            tokens = tokens[:MAX_TRANSCRIPT_TOKENS]
            transcript = llm.detokenize(tokens).decode(errors="replace")

        prompt = PROMPT_TEMPLATE.format(transcript=transcript, language=language)
        out_dir = OUTPUT_DIR / sample_id
        out_file = out_dir / "structured_transcript.json"

        print(f"[{sample_id}] target: >= {min_segments} segments")

        best = None
        for attempt in range(10):
            temp = 0.1 + (attempt * 0.1)
            print(f"  attempt {attempt+1}/10 (temp={temp:.1f}) ...", end=" ", flush=True)

            response = llm(
                prompt,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=temp,
                stop=["Transcript:", "---", "]"],
            )
            raw = "[" + response["choices"][0]["text"].strip() + "]"

            try:
                parsed = parse_json_response(raw)
                valid_intents = {"implementation", "explanation", "debugging", "refactoring"}
                structured = []
                for entry in parsed:
                    if not isinstance(entry, dict):
                        continue
                    if "narration" not in entry:
                        narr_key = next((k for k in entry if k.startswith("narr")), None)
                        if narr_key:
                            entry["narration"] = entry.pop(narr_key)
                    if "narration" not in entry or "intent" not in entry:
                        continue
                    if entry["intent"] not in valid_intents:
                        entry["intent"] = "explanation"
                    structured.append({"narration": entry["narration"], "intent": entry["intent"]})

                print(f"{len(structured)} segments", end="")

                if best is None or len(structured) > len(best):
                    best = structured
                    print(" ★ (new best)", end="")

                if len(structured) >= min_segments:
                    print(" ✓ GOOD ENOUGH")
                    break
                else:
                    print(f" (need {min_segments})")

            except Exception as e:
                print(f"FAILED ({e})")

        if best and len(best) >= min_segments:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(best, indent=2))
            print(f"  → Saved {len(best)} segments to {out_file}")
        elif best:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(best, indent=2))
            print(f"  → Saved best effort: {len(best)} segments (below target {min_segments})")
        else:
            print(f"  → All attempts failed!")


if __name__ == "__main__":
    main()
