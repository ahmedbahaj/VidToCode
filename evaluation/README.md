# Evaluation

Two metrics are used: **Compilation Score (CS)** from `output.txt` and **CodeBLEU** from the source code. CS is the primary metric — it directly answers whether the generated code works. CodeBLEU is secondary — it measures structural closeness to the reference even when execution fails.

---

## Compilation Score (CS)

A graduated 4-point scale per sample:

| Points | Condition |
|---|---|
| 0 | Fails to parse / compile — syntax error before anything runs |
| 1 | Parses / compiles, but crashes at runtime |
| 2 | Runs to completion, but output does not match `output.txt` |
| 3 | Runs to completion, output matches `output.txt` |

```
CS = (sum of points across all samples) / (3 × number of samples)
```

Result is 0 to 1. A score of 1.0 means every generated program ran and matched the expected output.

---

## CodeBLEU

Standard formula combining four equally weighted components:

```
CodeBLEU = 0.25 × BLEU
         + 0.25 × weighted n-gram match   (keywords weighted higher than identifiers)
         + 0.25 × AST subtree match       (structural similarity)
         + 0.25 × dataflow match          (variable usage patterns)
```

Result is 0 to 1. The reference is the ground truth source code from the dataset. In practice, scores above 0.35 are reasonable and above 0.5 are strong for code generation tasks.

---

## Comparison Table

Approaches 1 and 2 can be evaluated on all 36 samples. Approach 3 can only be evaluated on the 12 held-out test samples (evaluating on training data would be dishonest). To keep the cross-approach comparison fair, all three are compared on the same 12 test samples. Approaches 1 and 2 are additionally reported on the full 36 as a secondary result.

|  | All 36 samples | 12 test samples only |
|---|---|---|
| Approach 1 — Raw transcript → LLM | CS + CodeBLEU | CS + CodeBLEU |
| Approach 2 — Structured transcript → LLM | CS + CodeBLEU | CS + CodeBLEU |
| Approach 3 — Docstring → Fine-tuned CodeGen2 | — | CS + CodeBLEU |

The 12-sample column is the **primary comparison table**. The full-36 column shows how approaches 1 and 2 behave across the complete dataset.

---

## Dataset Split (Approach 3 only)

The dataset is a grid of 12 cells (4 languages × 3 length tiers), each containing 3 videos. A stratified split is applied inside each cell to ensure every language and every length tier is represented in both train and test:

```
from each cell of 3 videos → 2 train, 1 test
```

Result: **24 train, 12 test.** No validation set — 12 test samples is already small and splitting it further would produce unreliable tuning signal.

---

## Practical Issue: Interactive Outputs

Some videos have programs that require user input at runtime (e.g. a number guessing game, a calculator, a to-do list app). These cannot be evaluated by simply running the code and diffing against `output.txt`.

The evaluation script handles this in three tiers:

| Tier | Handling | Samples |
|---|---|---|
| **Deterministic stdin** | Pre-feed known inputs via stdin and compare output | `cpp/long/long_1`, `cpp/long/long_2`, `cpp/medium/medium_2`, `cpp/medium/medium_3`, `java/short/short_2`, `python/medium/medium_1` |
| **CLI arguments** | Pass argparse arguments instead of stdin | `python/long/long_1` |
| **Random-seeded** | Skipped — output depends on RNG, cannot match `output.txt` | `cpp/short/short_1`, `java/long/long_3`, `java/medium/medium_2`, `python/short/short_1`, `python/long/long_2` |
| **Browser-based** | Skipped — uses DOM APIs (`getElementById`, `prompt`, `alert`) | `javascript/long/long_1`, `javascript/medium/medium_2`, `javascript/short/short_1` |

---

## `results_evaluation.json` Format

Running `evaluate.py` on a `results.json` file produces a `results_evaluation.json` in the same directory. The file has the following structure:

### Top-level fields

```json
{
  "source_file": "approaches/approach_1_zero_shot/results.json",
  "total_samples": 36,
  "cs_scored": 28,
  "cs_overall": 0.2619,
  "codebleu_scored": 36,
  "codebleu_mean": 0.4308,
  "per_sample": [ ... ]
}
```

| Field | Type | Description |
|---|---|---|
| `source_file` | `string` | Path to the input `results.json` |
| `total_samples` | `int` | Total number of samples in the input |
| `cs_scored` | `int` | Number of samples that received a CS score (not skipped) |
| `cs_overall` | `float` | Aggregate CS: `sum(scores) / (3 × cs_scored)` — range 0 to 1 |
| `codebleu_scored` | `int` | Number of samples that received a CodeBLEU score |
| `codebleu_mean` | `float` | Mean CodeBLEU across scored samples — range 0 to 1 |

### Per-sample entry

Each element in the `per_sample` array has the following fields:

```json
{
  "id": "cpp/medium/medium_3",
  "language": "cpp",
  "is_skipped": false,
  "is_browser": false,
  "stdin_fed": true,
  "generated_code_length": 412,
  "reference_code_length": 824,
  "cs_score": 2,
  "cs_details": {
    "is_skipped": false,
    "is_browser": false,
    "stdin_fed": true,
    "status": "success",
    "stdout": "Enter an integer: Found at index: 5\n",
    "stderr": "",
    "output_match": false,
    "expected_preview": "Enter an integer: \n67\nThe number 67 was found...",
    "actual_preview": "Enter an integer: Found at index: 5"
  },
  "codebleu_score": 0.6829,
  "codebleu_details": {
    "codebleu": 0.6829,
    "ngram_match_score": 0.4928,
    "weighted_ngram_match_score": 0.5388,
    "syntax_match_score": 0.8000,
    "dataflow_match_score": 0.9000
  }
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Sample identifier (`{language}/{tier}/{name}`) |
| `language` | `string` | `python`, `cpp`, `java`, or `javascript` |
| `is_skipped` | `bool` | `true` if the sample was skipped for CS (random-seeded game) |
| `is_browser` | `bool` | `true` if the sample uses browser DOM APIs |
| `stdin_fed` | `bool` | `true` if stdin or CLI args were pre-fed for this sample |
| `generated_code_length` | `int` | Character count of the cleaned generated code |
| `reference_code_length` | `int` | Character count of the reference code |
| `cs_score` | `int\|null` | Compilation Score: 0–3, or `null` if skipped |
| `cs_details.status` | `string` | One of: `parse_error`, `runtime_error`, `timeout`, `success`, `skipped_random`, `skipped_browser`, `unavailable` |
| `cs_details.stdout` | `string` | Captured stdout (truncated to 1000 chars) |
| `cs_details.stderr` | `string` | Captured stderr (truncated to 1000 chars) |
| `cs_details.output_match` | `bool` | `true` if stdout exactly matches `output.txt` |
| `codebleu_score` | `float\|null` | CodeBLEU score (0–1), or `null` if computation failed |
| `codebleu_details` | `object` | Breakdown: `ngram_match_score`, `weighted_ngram_match_score`, `syntax_match_score`, `dataflow_match_score` |
