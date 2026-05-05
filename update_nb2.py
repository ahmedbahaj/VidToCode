import json

with open('results/evaluation_analysis.ipynb', 'r') as f:
    nb = json.load(f)

# Cell 3: Update Overall metrics
cell_3_code = [
    "models_1v2 = ['4B Zeroshot', '27B Zeroshot']\n",
    "cs_1v2 = [d1['cs_overall'], d2['cs_overall']]\n",
    "cb_1v2 = [d1['codebleu_mean'], d2['codebleu_mean']]\n",
    "\n",
    "models_2v3 = ['27B Zeroshot', '27B Structured']\n",
    "cs_2v3 = [d2['cs_overall'], d3['cs_overall']]\n",
    "cb_2v3 = [d2['codebleu_mean'], d3['codebleu_mean']]\n",
    "\n",
    "print(f\"4B Zeroshot CS: {cs_1v2[0]:.3f}, CodeBLEU: {cb_1v2[0]:.3f}\")\n",
    "print(f\"27B Zeroshot CS: {cs_1v2[1]:.3f}, CodeBLEU: {cb_1v2[1]:.3f}\")\n",
    "print(f\"27B Structured CS: {cs_2v3[1]:.3f}, CodeBLEU: {cb_2v3[1]:.3f}\")\n",
    "\n",
    "fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))\n",
    "width = 0.35\n",
    "\n",
    "x1 = np.arange(len(models_1v2))\n",
    "ax1.bar(x1 - width/2, cs_1v2, width, label='CS Score')\n",
    "ax1.bar(x1 + width/2, cb_1v2, width, label='CodeBLEU Mean')\n",
    "ax1.set_ylabel('Scores')\n",
    "ax1.set_title('4B vs 27B (Zeroshot)')\n",
    "ax1.set_xticks(x1)\n",
    "ax1.set_xticklabels(models_1v2)\n",
    "ax1.tick_params(axis='x', rotation=45)\n",
    "ax1.tick_params(axis='y', rotation=45)\n",
    "ax1.legend()\n",
    "\n",
    "x2 = np.arange(len(models_2v3))\n",
    "ax2.bar(x2 - width/2, cs_2v3, width, label='CS Score')\n",
    "ax2.bar(x2 + width/2, cb_2v3, width, label='CodeBLEU Mean')\n",
    "ax2.set_ylabel('Scores')\n",
    "ax2.set_title('27B Zeroshot vs Structured')\n",
    "ax2.set_xticks(x2)\n",
    "ax2.set_xticklabels(models_2v3)\n",
    "ax2.tick_params(axis='x', rotation=45)\n",
    "ax2.tick_params(axis='y', rotation=45)\n",
    "ax2.legend()\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]
nb['cells'][3]['source'] = cell_3_code

# Remove Cells 11 and 12 (Section 3)
del nb['cells'][11:13]

# Now the original Cell 13 is Cell 11, Cell 14 is 12, Cell 15 is 13, Cell 16 is 14
# Let's fix the numbering in Markdown cells
for cell in nb['cells']:
    if cell['cell_type'] == 'markdown':
        src = cell['source']
        if isinstance(src, list):
            for i in range(len(src)):
                if "## 4. Breakdown" in src[i]:
                    src[i] = src[i].replace("## 4. Breakdown", "## 3. Breakdown")
                if "## 5. Detailed Breakdown" in src[i]:
                    src[i] = src[i].replace("## 5. Detailed Breakdown", "## 4. Detailed Breakdown")
        else:
            if "## 4. Breakdown" in src:
                cell['source'] = src.replace("## 4. Breakdown", "## 3. Breakdown")
            if "## 5. Detailed Breakdown" in src:
                cell['source'] = src.replace("## 5. Detailed Breakdown", "## 4. Detailed Breakdown")

# Find the cell that plots "Language breakdown" and update it
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = "".join(cell['source'])
        if "ax = lang_cs.plot(kind='bar'" in src:
            new_src = src.replace(
                "ax.set_ylabel(\"CS Score\")\nplt.show()",
                "ax.set_ylabel(\"CS Score\")\nax.tick_params(axis='x', rotation=45)\nax.tick_params(axis='y', rotation=45)\nplt.tight_layout()\nplt.show()"
            )
            new_src = new_src.replace(
                "ax2.set_ylabel(\"CS Score\")\nplt.show()",
                "ax2.set_ylabel(\"CS Score\")\nax2.tick_params(axis='x', rotation=45)\nax2.tick_params(axis='y', rotation=45)\nplt.tight_layout()\nplt.show()"
            )
            cell['source'] = [line + "\n" for line in new_src.split("\n")[:-1]]
        elif "df.groupby('language')[['1v2_change', '2v3_change']].mean().plot(" in src:
            new_src = src.replace(
                "axes[0].set_ylabel('Avg CS Score Change')",
                "axes[0].set_ylabel('Avg CS Score Change')\naxes[0].tick_params(axis='x', rotation=45)\naxes[0].tick_params(axis='y', rotation=45)"
            ).replace(
                "axes[1].set_ylabel('Avg CS Score Change')",
                "axes[1].set_ylabel('Avg CS Score Change')\naxes[1].tick_params(axis='x', rotation=45)\naxes[1].tick_params(axis='y', rotation=45)\nplt.tight_layout()"
            )
            cell['source'] = [line + "\n" for line in new_src.split("\n")[:-1]]

with open('results/evaluation_analysis.ipynb', 'w') as f:
    json.dump(nb, f, indent=2)

print('Notebook updated successfully.')
