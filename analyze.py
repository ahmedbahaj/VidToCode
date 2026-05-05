import json
import pandas as pd
import numpy as np

def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

d1 = load_data('results/4B_zeroshot_results_evaluation.json')
d2 = load_data('results/27B_zeroshot_results_evaluation.json')
d3 = load_data('results/27B_structured_results_evaluation.json')

def extract_metrics(d):
    return {
        'cs_overall': d.get('cs_overall', 0),
        'codebleu_mean': d.get('codebleu_mean', 0),
        'cs_scored': d.get('cs_scored', 0),
        'total_samples': d.get('total_samples', 0)
    }

print("=== OVERALL METRICS ===")
print("4B Zeroshot:", extract_metrics(d1))
print("27B Zeroshot:", extract_metrics(d2))
print("27B Structured:", extract_metrics(d3))

def get_sample_df(d, name):
    records = []
    for s in d['per_sample']:
        records.append({
            'id': s['id'],
            'language': s['language'],
            f'{name}_cs_score': s.get('cs_score'),
            f'{name}_codebleu': s.get('codebleu_score'),
            f'{name}_status': s.get('cs_details', {}).get('status')
        })
    return pd.DataFrame(records)

df1 = get_sample_df(d1, '4B_zero')
df2 = get_sample_df(d2, '27B_zero')
df3 = get_sample_df(d3, '27B_struct')

df = df1.merge(df2, on=['id', 'language']).merge(df3, on=['id', 'language'])

print("\n=== 4B Zero vs 27B Zero ===")
print("CS Score Improvements (27B > 4B):", len(df[df['27B_zero_cs_score'] > df['4B_zero_cs_score']]))
print("CS Score Regressions (27B < 4B):", len(df[df['27B_zero_cs_score'] < df['4B_zero_cs_score']]))
print("CodeBLEU Mean Diff:", (df['27B_zero_codebleu'] - df['4B_zero_codebleu']).mean())

print("\n=== 27B Zero vs 27B Structured ===")
print("CS Score Improvements (Struct > Zero):", len(df[df['27B_struct_cs_score'] > df['27B_zero_cs_score']]))
print("CS Score Regressions (Struct < Zero):", len(df[df['27B_struct_cs_score'] < df['27B_zero_cs_score']]))
print("CodeBLEU Mean Diff:", (df['27B_struct_codebleu'] - df['27B_zero_codebleu']).mean())

# Print some interesting status changes
print("\n=== Status distributions ===")
for col in ['4B_zero_status', '27B_zero_status', '27B_struct_status']:
    print(df[col].value_counts())
    
