import json
with open('results/evaluation_analysis.ipynb', 'r') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    source = cell['source']
    if isinstance(source, list):
        text = source[0][:50].strip() if source else ""
    else:
        text = source[:50].strip()
    print(f"Cell {i}: {cell['cell_type']} | {text}")
