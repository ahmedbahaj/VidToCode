#!/usr/bin/env python3
"""
Evaluation script for VidToCode project.
Computes Compilation Score (CS) and CodeBLEU for generated code vs ground truth.

Usage:
    python evaluate.py ../approaches/approach_1_zero_shot/results.json
    python evaluate.py ../approaches/approach_1_zero_shot/results.json --skip-codebleu
    python evaluate.py ../approaches/approach_1_zero_shot/results.json -o results_eval.json
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TIMEOUT = 30  # seconds per compile/run step

# Samples that are truly unskippable — depend on randomness or browser APIs.
# Only these remain skipped for CS.
SKIPPED_SAMPLES = {
    # Random-seeded games: output depends on RNG, can't match output.txt
    "cpp/short/short_1",           # Number guessing game (rand())
    "java/long/long_3",            # Rock-paper-scissors (Random)
    "java/medium/medium_2",        # Number guessing game (Random)
    "python/short/short_1",        # Number guessing game (random)
    "python/long/long_2",          # Hangman (random word)
}

# Browser-based JavaScript samples that use DOM APIs (can't run in Node.js)
BROWSER_SAMPLES = {
    "javascript/long/long_1",      # DOM-based to-do app (getElementById, etc.)
    "javascript/medium/medium_2",  # Number guessing game (window.prompt)
    "javascript/short/short_1",    # Dice roll (prompt / alert)
}

# Pre-defined stdin inputs for interactive samples.
# Extracted from the ground-truth output.txt files.
STDIN_INPUTS = {
    # C++
    "cpp/long/long_1":       "0 0\n0 1\n1 1\n1 2\n2 2\n",         # Tic-tac-toe moves
    "cpp/long/long_2":       "3\n17\n81\n3\n",                     # QuickSort: size=3, elements
    "cpp/medium/medium_2":   "2\n100\n3\n50\n1\n4\n",             # Banking: deposit 100, withdraw 50, show, exit
    "cpp/medium/medium_3":   "67\n",                               # Binary search: search for 67
    # Java
    "java/short/short_2":    "4\n10\n3\n",                         # Calculator: divide 10 / 3
    # Python
    "python/medium/medium_1": "4\n",                               # To-do list: quit immediately
    "python/long/long_1":    None,                                  # Argparse — uses CLI args, see below
}

# CLI arguments for samples that use argparse instead of stdin.
CLI_ARGS = {
    "python/long/long_1":    ["m", "thin", "-t", "olives", "--extra-cheese"],
}

# ---------------------------------------------------------------------------
# Code cleaning utilities
# ---------------------------------------------------------------------------

def clean_generated_code(raw_text, language):
    """
    Extract clean, runnable code from generated text that may contain
    markdown fences, <think> blocks, duplicate code blocks, and junk text.
    """
    # 1. Remove <think>...</think> blocks
    text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)

    # 2. Try to extract the first substantial code block from markdown fences
    lang_aliases = {
        'python': r'(?:python|py)',
        'cpp': r'(?:cpp|c\+\+|c)',
        'java': r'(?:java)',
        'javascript': r'(?:javascript|js|html)',
    }
    alias_pattern = lang_aliases.get(language, re.escape(language))

    # Match ```lang\n...\n``` blocks
    pattern = r'```(?:' + alias_pattern + r')?\s*\n(.*?)```'
    blocks = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    if blocks:
        # Return the first code block that has meaningful content
        for block in blocks:
            block = block.strip()
            if len(block) > 20:
                return block

    # 3. Fallback: if there are no markdown fences, strip leftover ``` lines
    text = re.sub(r'^```\w*\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    return text


def strip_rtf(rtf_text):
    """
    Convert RTF-formatted text to plain text.
    Handles the RTF format found in some Java ground-truth files.
    """
    if not rtf_text.strip().startswith('{\\rtf'):
        return rtf_text

    text = rtf_text

    # Remove RTF groups that carry no code content
    text = re.sub(r'\{\\fonttbl[^}]*\}', '', text)
    text = re.sub(r'\{\\colortbl[^}]*\}', '', text)
    text = re.sub(r'\{\\\*\\expandedcolortbl[^}]*\}', '', text)

    # Remove the RTF header preamble (everything before \f0\fs...)
    text = re.sub(r'^.*?\\f0\\fs\d+\s*\\cf0\s*', '', text, flags=re.DOTALL)

    # RTF uses  \  at end of line as a newline
    text = text.replace('\\\r\n', '\n')
    text = text.replace('\\\n', '\n')
    text = text.replace('\\\r', '\n')

    # Handle escaped braces and backslash
    text = text.replace('\\{', '{')
    text = text.replace('\\}', '}')
    text = text.replace('\\\\', '\\')

    # Remove remaining RTF control words like \pard, \tx566, etc.
    text = re.sub(r'\\[a-zA-Z]+\d*\s?', '', text)

    # Remove remaining unmatched braces (outermost RTF wrapper)
    # Count and remove only unbalanced trailing }
    text = text.strip()
    while text.endswith('}'):
        text = text[:-1].strip()

    text = text.strip()
    return text


# ---------------------------------------------------------------------------
# Ground truth loading
# ---------------------------------------------------------------------------

def find_output_file(sample_dir):
    """Find the output file, handling inconsistent naming (output.txt, Output.txt, Output.text)."""
    candidates = ['output.txt', 'Output.txt', 'Output.text']
    for name in candidates:
        path = sample_dir / name
        if path.exists():
            return path
    return None


def find_code_file(sample_dir, language):
    """Find the ground-truth source code file, handling inconsistent naming."""
    extensions = {
        'python': ['.py'],
        'cpp': ['.cpp'],
        'java': ['.java', '.Java'],
        'javascript': ['.js'],
    }
    exts = extensions.get(language, [])

    # Preferred names first
    preferred = {
        'python': ['main.py'],
        'cpp': ['main.cpp'],
        'java': ['Code.java', 'Code.Java'],
        'javascript': ['index.js', 'script.js', 'main.js', 'server.js'],
    }

    for name in preferred.get(language, []):
        path = sample_dir / name
        if path.exists():
            return path

    # Fallback: any file with the right extension
    for f in sample_dir.iterdir():
        if f.suffix.lower() in [e.lower() for e in exts]:
            return f
    return None


def get_ground_truth(sample_id):
    """
    Load the ground-truth source code and expected output for a sample.
    Returns (ground_truth_code: str, expected_output: str).
    """
    parts = sample_id.split('/')
    language, length_tier, name = parts[0], parts[1], parts[2]
    sample_dir = DATA_DIR / language / length_tier / name

    # Expected output
    expected_output = ""
    output_file = find_output_file(sample_dir)
    if output_file:
        expected_output = output_file.read_text(errors='replace').strip()

    # Ground truth code
    ground_truth_code = ""
    code_file = find_code_file(sample_dir, language)
    if code_file:
        ground_truth_code = code_file.read_text(errors='replace')
        # Strip RTF if needed
        if ground_truth_code.strip().startswith('{\\rtf'):
            ground_truth_code = strip_rtf(ground_truth_code)

    return ground_truth_code, expected_output


# ---------------------------------------------------------------------------
# Compilation & execution
# ---------------------------------------------------------------------------

def compile_and_run(code, language, stdin_input=None, timeout=TIMEOUT, cli_args=None):
    """
    Compile and run code in the given language.

    Returns (status, stdout, stderr) where status is one of:
        'parse_error'    - Failed to parse / compile
        'runtime_error'  - Parsed but crashed at runtime
        'timeout'        - Ran but didn't finish in time
        'success'        - Ran to completion
        'unavailable'    - Required toolchain not found
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        try:
            if language == 'python':
                return _run_python(code, tmpdir, stdin_input, timeout, cli_args=cli_args)
            elif language == 'cpp':
                return _run_cpp(code, tmpdir, stdin_input, timeout)
            elif language == 'java':
                return _run_java(code, tmpdir, stdin_input, timeout)
            elif language == 'javascript':
                return _run_javascript(code, tmpdir, stdin_input, timeout)
            else:
                return 'unavailable', '', f'Unsupported language: {language}'
        except FileNotFoundError as e:
            return 'unavailable', '', f'Toolchain not found: {e}'
        except subprocess.TimeoutExpired:
            return 'timeout', '', 'Process timed out'
        except Exception as e:
            return 'parse_error', '', f'Unexpected error: {e}'


def _run_python(code, tmpdir, stdin_input, timeout, cli_args=None):
    code_file = tmpdir / "main.py"
    code_file.write_text(code)

    # Syntax check
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(code_file)],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        return 'parse_error', '', result.stderr

    # Run (with optional CLI args for argparse-based scripts)
    cmd = [sys.executable, str(code_file)] + (cli_args or [])
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, timeout=timeout,
        input=stdin_input
    )
    if result.returncode != 0:
        return 'runtime_error', result.stdout, result.stderr
    return 'success', result.stdout, result.stderr


def _run_cpp(code, tmpdir, stdin_input, timeout):
    code_file = tmpdir / "main.cpp"
    code_file.write_text(code)
    out_file = tmpdir / "main"

    # Compile
    result = subprocess.run(
        ['g++', '-o', str(out_file), str(code_file), '-std=c++17'],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        return 'parse_error', '', result.stderr

    # Run
    result = subprocess.run(
        [str(out_file)],
        capture_output=True, text=True, timeout=timeout,
        input=stdin_input
    )
    if result.returncode != 0:
        return 'runtime_error', result.stdout, result.stderr
    return 'success', result.stdout, result.stderr


def _run_java(code, tmpdir, stdin_input, timeout):
    # Extract class name from code
    match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = match.group(1) if match else 'Main'

    code_file = tmpdir / f"{class_name}.java"
    code_file.write_text(code)

    # Compile
    result = subprocess.run(
        ['javac', str(code_file)],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        return 'parse_error', '', result.stderr

    # Run
    result = subprocess.run(
        ['java', '-cp', str(tmpdir), class_name],
        capture_output=True, text=True, timeout=timeout,
        input=stdin_input
    )
    if result.returncode != 0:
        return 'runtime_error', result.stdout, result.stderr
    return 'success', result.stdout, result.stderr


def _run_javascript(code, tmpdir, stdin_input, timeout):
    code_file = tmpdir / "main.js"
    code_file.write_text(code)

    # Syntax check
    result = subprocess.run(
        ['node', '--check', str(code_file)],
        capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        return 'parse_error', '', result.stderr

    # Run
    result = subprocess.run(
        ['node', str(code_file)],
        capture_output=True, text=True, timeout=timeout,
        input=stdin_input
    )
    if result.returncode != 0:
        return 'runtime_error', result.stdout, result.stderr
    return 'success', result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Compilation Score (CS)
# ---------------------------------------------------------------------------

def compute_cs(code, language, expected_output, is_skipped=False, is_browser=False,
               stdin_input=None, cli_args=None):
    """
    Compute the Compilation Score (0–3) for a single sample.

    Returns (score: int | None, details: dict).
    Score is None when the sample is skipped (random-seeded / browser / unavailable).
    """
    details = {
        'is_skipped': is_skipped,
        'is_browser': is_browser,
        'stdin_fed': stdin_input is not None or cli_args is not None,
        'status': None,
        'stdout': '',
        'stderr': '',
        'output_match': False,
    }

    if is_browser:
        details['status'] = 'skipped_browser'
        details['note'] = 'Browser-based JavaScript — cannot run with Node.js'
        return None, details

    if is_skipped:
        details['status'] = 'skipped_random'
        details['note'] = 'Random-seeded program — output is non-deterministic'
        return None, details

    status, stdout, stderr = compile_and_run(
        code, language, stdin_input=stdin_input, cli_args=cli_args,
    )
    details['status'] = status
    details['stdout'] = stdout[:1000]
    details['stderr'] = stderr[:1000]

    if status == 'unavailable':
        details['note'] = f'Toolchain unavailable: {stderr[:200]}'
        return None, details

    if status == 'parse_error':
        return 0, details

    if status in ('runtime_error', 'timeout'):
        return 1, details

    # status == 'success' — compare output
    actual = stdout.strip()
    expected = expected_output.strip()

    if actual == expected:
        details['output_match'] = True
        return 3, details
    else:
        details['expected_preview'] = expected[:300]
        details['actual_preview'] = actual[:300]
        return 2, details


# ---------------------------------------------------------------------------
# CodeBLEU
# ---------------------------------------------------------------------------

def compute_codebleu_score(generated, reference, language):
    """
    Compute CodeBLEU between generated and reference code.
    Returns (score: float | None, details: dict).
    """
    if not generated or not reference or len(generated.strip()) < 5 or len(reference.strip()) < 5:
        return None, {'error': 'generated or reference code is too short'}

    try:
        from codebleu import calc_codebleu

        lang_map = {
            'python': 'python',
            'cpp': 'cpp',
            'java': 'java',
            'javascript': 'javascript',
        }

        result = calc_codebleu(
            references=[[reference]],
            predictions=[generated],
            lang=lang_map.get(language, language),
            weights=(0.25, 0.25, 0.25, 0.25),
        )

        return result['codebleu'], {
            'codebleu': result['codebleu'],
            'ngram_match_score': result.get('ngram_match_score'),
            'weighted_ngram_match_score': result.get('weighted_ngram_match_score'),
            'syntax_match_score': result.get('syntax_match_score'),
            'dataflow_match_score': result.get('dataflow_match_score'),
        }

    except ImportError:
        return None, {'error': 'codebleu package not installed — pip install codebleu'}
    except Exception as e:
        return None, {'error': str(e)}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Evaluate VidToCode generated code against ground truth.'
    )
    parser.add_argument(
        'results_file',
        help='Path to a results.json file (e.g. approaches/approach_1_zero_shot/results.json)',
    )
    parser.add_argument(
        '--output', '-o', default=None,
        help='Output path for evaluation results JSON (default: <results_file>_evaluation.json)',
    )
    parser.add_argument('--skip-cs', action='store_true', help='Skip Compilation Score')
    parser.add_argument('--skip-codebleu', action='store_true', help='Skip CodeBLEU')
    args = parser.parse_args()

    # ---- Load results ----
    with open(args.results_file) as f:
        samples = json.load(f)
    print(f"Loaded {len(samples)} samples from {args.results_file}")
    print("=" * 80)

    evaluation_results = []
    cs_scores = []
    codebleu_scores = []

    for sample in samples:
        sample_id = sample['id']
        language = sample['language']
        generated_raw = sample['generated_code']
        reference_raw = sample.get('reference_code', '')

        print(f"\n--- {sample_id} ({language}) ---")

        # Clean generated code
        generated_clean = clean_generated_code(generated_raw, language)

        # Clean reference code (may be RTF)
        if reference_raw.strip().startswith('{\\rtf') or '\\rtf1\\' in reference_raw:
            reference_clean = strip_rtf(reference_raw)
        else:
            reference_clean = reference_raw

        # Also load ground truth from data/ directory
        gt_code, expected_output = get_ground_truth(sample_id)

        # Prefer the ground-truth file if the reference_code field is too short or empty
        if not reference_clean or len(reference_clean.strip()) < 10:
            reference_clean = gt_code

        is_skipped = sample_id in SKIPPED_SAMPLES
        is_browser = sample_id in BROWSER_SAMPLES
        stdin_input = STDIN_INPUTS.get(sample_id)
        cli_args = CLI_ARGS.get(sample_id)

        eval_entry = {
            'id': sample_id,
            'language': language,
            'is_skipped': is_skipped,
            'is_browser': is_browser,
            'stdin_fed': stdin_input is not None or cli_args is not None,
            'generated_code_length': len(generated_clean),
            'reference_code_length': len(reference_clean),
            'cs_score': None,
            'cs_details': {},
            'codebleu_score': None,
            'codebleu_details': {},
        }

        # ---- Compilation Score ----
        if not args.skip_cs:
            cs, cs_details = compute_cs(
                generated_clean, language, expected_output,
                is_skipped=is_skipped, is_browser=is_browser,
                stdin_input=stdin_input, cli_args=cli_args,
            )
            eval_entry['cs_score'] = cs
            eval_entry['cs_details'] = cs_details
            if cs is not None:
                cs_scores.append(cs)

            status = cs_details.get('status', '?')
            fed = ' [stdin fed]' if (stdin_input or cli_args) and cs is not None else ''
            if cs is not None:
                print(f"  CS: {cs}/3  ({status}){fed}")
                if cs == 2:
                    print(f"    Expected: {cs_details.get('expected_preview', '')[:80]}")
                    print(f"    Actual:   {cs_details.get('actual_preview', '')[:80]}")
            else:
                print(f"  CS: SKIPPED  ({status})")

        # ---- CodeBLEU ----
        if not args.skip_codebleu:
            cb_score, cb_details = compute_codebleu_score(
                generated_clean, reference_clean, language,
            )
            eval_entry['codebleu_score'] = cb_score
            eval_entry['codebleu_details'] = cb_details
            if cb_score is not None:
                codebleu_scores.append(cb_score)
                print(f"  CodeBLEU: {cb_score:.4f}")
            else:
                err = cb_details.get('error', 'unknown')
                print(f"  CodeBLEU: N/A ({err})")

        evaluation_results.append(eval_entry)

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # -- CS summary --
    if cs_scores:
        cs_overall = sum(cs_scores) / (3 * len(cs_scores))
        print(f"\nCompilation Score (CS):")
        print(f"  Scored samples : {len(cs_scores)} / {len(samples)}")
        print(f"  CS overall     : {cs_overall:.4f}  ({sum(cs_scores)} / {3 * len(cs_scores)})")
        print(f"  Distribution   :")
        for s in range(4):
            count = cs_scores.count(s)
            bar = '█' * count
            print(f"    {s}/3 : {count:>2}  {bar}")
    else:
        print("\nCompilation Score: not computed")

    # -- CodeBLEU summary --
    if codebleu_scores:
        avg_cb = sum(codebleu_scores) / len(codebleu_scores)
        print(f"\nCodeBLEU:")
        print(f"  Scored samples : {len(codebleu_scores)} / {len(samples)}")
        print(f"  Mean CodeBLEU  : {avg_cb:.4f}")
    else:
        print("\nCodeBLEU: not computed")

    # -- Per-language breakdown --
    print(f"\n{'Language':<14} {'CS':>8} {'CodeBLEU':>10} {'Samples':>8}")
    print("-" * 44)
    for lang in ['python', 'cpp', 'java', 'javascript']:
        lang_results = [r for r in evaluation_results if r['language'] == lang]
        lang_cs = [r['cs_score'] for r in lang_results if r['cs_score'] is not None]
        lang_cb = [r['codebleu_score'] for r in lang_results if r['codebleu_score'] is not None]

        cs_str = f"{sum(lang_cs) / (3 * len(lang_cs)):.4f}" if lang_cs else "  N/A "
        cb_str = f"{sum(lang_cb) / len(lang_cb):.4f}" if lang_cb else "  N/A "
        print(f"  {lang:<12} {cs_str:>8} {cb_str:>10} {len(lang_results):>8}")

    # -- Per-length-tier breakdown --
    print(f"\n{'Length Tier':<14} {'CS':>8} {'CodeBLEU':>10} {'Samples':>8}")
    print("-" * 44)
    for tier in ['short', 'medium', 'long']:
        tier_results = [r for r in evaluation_results if f'/{tier}/' in r['id']]
        tier_cs = [r['cs_score'] for r in tier_results if r['cs_score'] is not None]
        tier_cb = [r['codebleu_score'] for r in tier_results if r['codebleu_score'] is not None]

        cs_str = f"{sum(tier_cs) / (3 * len(tier_cs)):.4f}" if tier_cs else "  N/A "
        cb_str = f"{sum(tier_cb) / len(tier_cb):.4f}" if tier_cb else "  N/A "
        print(f"  {tier:<12} {cs_str:>8} {cb_str:>10} {len(tier_results):>8}")

    # ---- Save results ----
    output_path = args.output
    if not output_path:
        base = Path(args.results_file)
        output_path = str(base.parent / (base.stem + '_evaluation.json'))

    output_data = {
        'source_file': str(args.results_file),
        'total_samples': len(samples),
        'cs_scored': len(cs_scores),
        'cs_overall': sum(cs_scores) / (3 * len(cs_scores)) if cs_scores else None,
        'codebleu_scored': len(codebleu_scores),
        'codebleu_mean': sum(codebleu_scores) / len(codebleu_scores) if codebleu_scores else None,
        'per_sample': evaluation_results,
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\nResults saved to: {output_path}")


if __name__ == '__main__':
    main()
