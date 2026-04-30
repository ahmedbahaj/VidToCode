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

Some videos have programs that require user input at runtime (e.g. a number guessing game). These cannot be evaluated by simply running the code and diffing against `output.txt`.

Two options per interactive sample:
- **Pre-feed inputs via stdin** — pipe a fixed sequence of inputs and verify the output matches
- **Skip output matching** — fall back to CodeBLEU only, and mark the sample as `interactive` in the results table

All 36 samples should be tagged as `standard` or `interactive` before running the evaluation script.
