import json

notebook = {
    "cells": [],
    "metadata": {},
    "nbformat": 4,
    "nbformat_minor": 5
}

def add_markdown(source):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": source
    })

def add_code(source):
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source
    })

add_markdown([
    "# VidToCode Evaluation Analysis\n",
    "\n",
    "This notebook analyzes the evaluation results across three different approaches:\n",
    "1. **4B Zeroshot** (`4B_zeroshot_results_evaluation.json`)\n",
    "2. **27B Zeroshot** (`27B_zeroshot_results_evaluation.json`)\n",
    "3. **27B Structured** (`27B_structured_results_evaluation.json`)\n",
    "\n",
    "We compare their Code Synthesis (CS) scores, CodeBLEU metrics, and specific status transitions."
])

add_code([
    "import json\n",
    "import matplotlib.pyplot as plt\n",
    "import numpy as np\n",
    "\n",
    "def load_data(file_path):\n",
    "    with open(file_path, 'r') as f:\n",
    "        return json.load(f)\n",
    "\n",
    "d1 = load_data('results/4B_zeroshot_results_evaluation.json')\n",
    "d2 = load_data('results/27B_zeroshot_results_evaluation.json')\n",
    "d3 = load_data('results/27B_structured_results_evaluation.json')"
])

add_markdown([
    "## 1. Overall Metrics\n",
    "Let's look at the overall CS scores and CodeBLEU means across the three runs."
])

add_code([
    "models = ['4B Zeroshot', '27B Zeroshot', '27B Structured']\n",
    "cs_overall = [d1['cs_overall'], d2['cs_overall'], d3['cs_overall']]\n",
    "cb_mean = [d1['codebleu_mean'], d2['codebleu_mean'], d3['codebleu_mean']]\n",
    "\n",
    "print(f\"4B Zeroshot CS: {cs_overall[0]:.3f}, CodeBLEU: {cb_mean[0]:.3f}\")\n",
    "print(f\"27B Zeroshot CS: {cs_overall[1]:.3f}, CodeBLEU: {cb_mean[1]:.3f}\")\n",
    "print(f\"27B Structured CS: {cs_overall[2]:.3f}, CodeBLEU: {cb_mean[2]:.3f}\")\n",
    "\n",
    "fig, ax1 = plt.subplots(figsize=(8, 5))\n",
    "x = np.arange(len(models))\n",
    "width = 0.35\n",
    "\n",
    "rects1 = ax1.bar(x - width/2, cs_overall, width, label='CS Score')\n",
    "rects2 = ax1.bar(x + width/2, cb_mean, width, label='CodeBLEU Mean')\n",
    "\n",
    "ax1.set_ylabel('Scores')\n",
    "ax1.set_title('Overall Metrics Comparison')\n",
    "ax1.set_xticks(x)\n",
    "ax1.set_xticklabels(models)\n",
    "ax1.legend()\n",
    "\n",
    "plt.show()"
])

add_markdown([
    "**Observation:**\n",
    "The 27B Zeroshot model dramatically improves over the 4B model, increasing the CS score from 19.0% to 51.2%. Interestingly, the **27B Structured** approach actually **regresses**, dropping the CS score back to 38.1%."
])

add_markdown([
    "## 2. Model vs Model Comparisons\n",
    "### 4B Zeroshot vs 27B Zeroshot\n",
    "Let's see which specific samples improved or regressed."
])

add_code([
    "def extract_samples(d):\n",
    "    return {s['id']: s for s in d['per_sample']}\n",
    "\n",
    "s1 = extract_samples(d1)\n",
    "s2 = extract_samples(d2)\n",
    "s3 = extract_samples(d3)\n",
    "ids = list(s1.keys())\n",
    "\n",
    "def compare(name_a, s_a, name_b, s_b):\n",
    "    cs_up = 0\n",
    "    cs_down = 0\n",
    "    cb_diff = 0\n",
    "    status_changes = {}\n",
    "    \n",
    "    for id_ in ids:\n",
    "        if s_a[id_].get('cs_score') is not None and s_b[id_].get('cs_score') is not None:\n",
    "            score_a = s_a[id_]['cs_score']\n",
    "            score_b = s_b[id_]['cs_score']\n",
    "            if score_b > score_a: cs_up += 1\n",
    "            elif score_b < score_a: cs_down += 1\n",
    "        \n",
    "        cb_a = s_a[id_].get('codebleu_score', 0) or 0\n",
    "        cb_b = s_b[id_].get('codebleu_score', 0) or 0\n",
    "        cb_diff += (cb_b - cb_a)\n",
    "        \n",
    "        stat_a = s_a[id_].get('cs_details', {}).get('status', 'unknown')\n",
    "        stat_b = s_b[id_].get('cs_details', {}).get('status', 'unknown')\n",
    "        if stat_a != stat_b:\n",
    "            change = f'{stat_a} -> {stat_b}'\n",
    "            status_changes[change] = status_changes.get(change, 0) + 1\n",
    "            \n",
    "    print(f\"Improvements ({name_b} > {name_a}): {cs_up}\")\n",
    "    print(f\"Regressions ({name_b} < {name_a}): {cs_down}\")\n",
    "    print(f\"Avg CodeBLEU Change: {cb_diff / len(ids):.4f}\")\n",
    "    print(\"Status Changes:\")\n",
    "    for k, v in sorted(status_changes.items(), key=lambda x: -x[1]):\n",
    "        print(f\"  {k}: {v}\")\n",
    "\n",
    "print(\"--- 4B Zeroshot vs 27B Zeroshot ---\")\n",
    "compare('4B_zero', s1, '27B_zero', s2)"
])

add_markdown([
    "**Observation:**\n",
    "Going from 4B to 27B resulted in **15 improvements** and only **1 regression**. Notably, 13 samples went from a `parse_error` to `success`, showing the 27B model outputs much more syntactically valid code."
])

add_markdown([
    "### 27B Zeroshot vs 27B Structured\n",
    "Now let's examine why the structured approach performed worse."
])

add_code([
    "print(\"--- 27B Zeroshot vs 27B Structured ---\")\n",
    "compare('27B_zero', s2, '27B_struct', s3)"
])

add_markdown([
    "**Observation:**\n",
    "The Structured approach caused **10 regressions** against only 3 improvements. 7 of the successful zero-shot generations turned into `parse_error`s! This indicates that the structured formatting constraint or prompt might be confusing the model into generating invalid syntax."
])

add_markdown([
    "## 3. Best Model per Sample\n",
    "How often is each model the absolute best for a given sample?"
])

add_code([
    "best_counts = {'4B_zero': 0, '27B_zero': 0, '27B_struct': 0, 'tie': 0}\n",
    "for id_ in ids:\n",
    "    v1 = s1[id_].get('cs_score')\n",
    "    v2 = s2[id_].get('cs_score')\n",
    "    v3 = s3[id_].get('cs_score')\n",
    "    if v1 is None: continue\n",
    "    m = max(v1, v2, v3)\n",
    "    winners = []\n",
    "    if v1 == m: winners.append('4B_zero')\n",
    "    if v2 == m: winners.append('27B_zero')\n",
    "    if v3 == m: winners.append('27B_struct')\n",
    "    \n",
    "    if len(winners) == 1:\n",
    "        best_counts[winners[0]] += 1\n",
    "    elif len(winners) > 1 and m > 0:\n",
    "        best_counts['tie'] += 1\n",
    "\n",
    "labels = list(best_counts.keys())\n",
    "sizes = list(best_counts.values())\n",
    "\n",
    "plt.figure(figsize=(6,6))\n",
    "plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)\n",
    "plt.title('Which model achieved the highest CS Score? (Solo wins vs Ties)')\n",
    "plt.show()\n",
    "\n",
    "print(best_counts)"
])

add_markdown([
    "## Conclusion\n",
    "- **27B Zeroshot** is clearly the superior model in this evaluation, dominating the CS Score.\n",
    "- The **Structured** constraint hurts the 27B model, leading to many `parse_error`s that were otherwise successful in the zeroshot approach. This might require debugging the prompt or post-processing pipeline for the structured approach."
])

with open('results/evaluation_analysis.ipynb', 'w') as f:\n",
    "    json.dump(notebook, f, indent=2)\n",
    "print('Notebook created successfully.')\n"
