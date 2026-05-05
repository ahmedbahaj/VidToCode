import json

with open('results/evaluation_analysis.ipynb', 'r') as f:
    nb = json.load(f)

# Find the conclusion markdown and insert before it
conclusion_idx = len(nb["cells"]) - 1
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "markdown" and "## Conclusion" in cell["source"][0]:
        conclusion_idx = i
        break

def add_md(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source
    }

def add_code(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source
    }

new_cells = []

new_cells.append(add_md([
    "## 4. Breakdown by Language and Duration\n",
    "Let's see how performance varies based on programming language and video duration (short, medium, long)."
]))

new_cells.append(add_code([
    "import pandas as pd\n",
    "\n",
    "def get_df(d, name):\n",
    "    records = []\n",
    "    for s in d['per_sample']:\n",
    "        dur = s['id'].split('/')[1] if '/' in s['id'] else 'unknown'\n",
    "        records.append({\n",
    "            'id': s['id'],\n",
    "            'language': s['language'],\n",
    "            'duration': dur,\n",
    "            f'{name}_cs': s.get('cs_score', 0) if s.get('cs_score') is not None else 0,\n",
    "            f'{name}_valid': 1 if s.get('cs_details', {}).get('status') == 'success' else 0\n",
    "        })\n",
    "    return pd.DataFrame(records)\n",
    "\n",
    "df1 = get_df(d1, '4B_zero')\n",
    "df2 = get_df(d2, '27B_zero')\n",
    "df3 = get_df(d3, '27B_struct')\n",
    "\n",
    "df = df1.merge(df2, on=['id', 'language', 'duration']).merge(df3, on=['id', 'language', 'duration'])\n",
    "\n",
    "# Language breakdown\n",
    "lang_cs = df.groupby('language')[['4B_zero_cs', '27B_zero_cs', '27B_struct_cs']].mean()\n",
    "print(\"Mean CS Score by Language:\\n\", lang_cs)\n",
    "\n",
    "ax = lang_cs.plot(kind='bar', figsize=(8, 4), title=\"Average CS Score by Language\")\n",
    "ax.set_ylabel(\"CS Score\")\n",
    "plt.show()\n",
    "\n",
    "# Duration breakdown\n",
    "dur_cs = df.groupby('duration')[['4B_zero_cs', '27B_zero_cs', '27B_struct_cs']].mean()\n",
    "print(\"\\nMean CS Score by Duration:\\n\", dur_cs)\n",
    "\n",
    "ax2 = dur_cs.plot(kind='bar', figsize=(8, 4), title=\"Average CS Score by Duration\")\n",
    "ax2.set_ylabel(\"CS Score\")\n",
    "plt.show()"
]))

new_cells.append(add_md([
    "## 5. Detailed Breakdown of 1 vs 2 and 2 vs 3\n",
    "Let's look at exactly where the improvements and regressions are happening across these dimensions."
]))

new_cells.append(add_code([
    "df['1v2_change'] = df['27B_zero_cs'] - df['4B_zero_cs']\n",
    "df['2v3_change'] = df['27B_struct_cs'] - df['27B_zero_cs']\n",
    "\n",
    "print(\"=== 4B Zero vs 27B Zero (1v2) ===\")\n",
    "print(\"Avg Improvement by Language:\\n\", df.groupby('language')['1v2_change'].mean())\n",
    "print(\"\\nAvg Improvement by Duration:\\n\", df.groupby('duration')['1v2_change'].mean())\n",
    "\n",
    "print(\"\\n=== 27B Zero vs 27B Struct (2v3) ===\")\n",
    "print(\"Avg Change by Language:\\n\", df.groupby('language')['2v3_change'].mean())\n",
    "print(\"\\nAvg Change by Duration:\\n\", df.groupby('duration')['2v3_change'].mean())\n",
    "\n",
    "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
    "df.groupby('language')[['1v2_change', '2v3_change']].mean().plot(kind='bar', ax=axes[0], title='Score Change by Language')\n",
    "axes[0].set_ylabel('Avg CS Score Change')\n",
    "df.groupby('duration')[['1v2_change', '2v3_change']].mean().plot(kind='bar', ax=axes[1], title='Score Change by Duration')\n",
    "axes[1].set_ylabel('Avg CS Score Change')\n",
    "plt.show()"
]))

# Insert new cells before conclusion
nb["cells"] = nb["cells"][:conclusion_idx] + new_cells + nb["cells"][conclusion_idx:]

with open('results/evaluation_analysis.ipynb', 'w') as f:
    json.dump(nb, f, indent=2)

print('Notebook updated successfully.')
