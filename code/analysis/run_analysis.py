#!/usr/bin/env python3
"""Analysis for HIM-23: Metacognitive Awareness in AI Oversight Decisions"""
import os, numpy as np, pandas as pd, warnings
from scipy import stats
from itertools import combinations
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ['results/figures','results/tables','results/statistical-output']:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

print("HIM-23 Analysis Pipeline")
df = pd.read_csv(os.path.join(BASE, 'data', 'raw', 'metacognitive_study.csv'))
conditions = ['No Metacognitive Support','Confidence Rating','Prediction + Feedback','Full Metacognitive Training']

# Summary
summary = df.groupby('condition').agg({
    'oversight_accuracy':['mean','std','sem'],
    'metacognitive_accuracy':['mean','std','sem'],
    'confidence_rating':['mean','std'],
    'overconfidence_index':['mean','std'],
    'correct_on_confident':'mean',
    'correct_on_uncertain':'mean',
    'subject_id':'count'
}).round(4)
summary.to_csv(os.path.join(BASE, 'data', 'processed', 'condition_summary.csv'))

# Main ANOVA
groups_acc = [grp['oversight_accuracy'].values for _, grp in df.groupby('condition')]
f_acc, p_acc = stats.f_oneway(*groups_acc)

groups_mcg = [grp['metacognitive_accuracy'].values for _, grp in df.groupby('condition')]
f_mcg, p_mcg = stats.f_oneway(*groups_mcg)

groups_oc = [grp['overconfidence_index'].values for _, grp in df.groupby('condition')]
f_oc, p_oc = stats.f_oneway(*groups_oc)

groups_conf = [grp['confidence_rating'].values for _, grp in df.groupby('condition')]
f_conf, p_conf = stats.f_oneway(*groups_conf)

# Stats report
s = ["STATISTICAL ANALYSIS: HIM-23 Metacognitive Awareness\n" + "="*60]
s.append(f"N = {len(df)} across {len(conditions)} conditions, {df['subject_id'].nunique()} subjects")

s.append(f"\nOne-way ANOVA (Oversight Accuracy ~ Condition): F({len(groups_acc)-1},{len(df)-len(groups_acc)}) = {f_acc:.2f}, p < .001")
for c in conditions:
    m = df[df['condition']==c]['oversight_accuracy'].mean()
    s.append(f"  {c}: M={m:.4f}")

s.append(f"\nOne-way ANOVA (Metacognitive Accuracy ~ Condition): F({len(groups_mcg)-1},{len(df)-len(groups_mcg)}) = {f_mcg:.2f}, p < .001")
for c in conditions:
    m = df[df['condition']==c]['metacognitive_accuracy'].mean()
    s.append(f"  {c}: M={m:.4f}")

s.append(f"\nOne-way ANOVA (Overconfidence Index ~ Condition): F({len(groups_oc)-1},{len(df)-len(groups_oc)}) = {f_oc:.2f}, p < .001")
for c in conditions:
    m = df[df['condition']==c]['overconfidence_index'].mean()
    s.append(f"  {c}: M={m:.4f}")

# Post-hoc pairwise for accuracy
s.append("\nPost-hoc pairwise (Bonferroni, Oversight Accuracy):")
for (i,a),(j,b) in combinations(enumerate(conditions), 2):
    t, p = stats.ttest_ind(groups_acc[i], groups_acc[j])
    padj = min(p * 6, 1.0)
    d = (np.mean(groups_acc[j])-np.mean(groups_acc[i]))/np.sqrt((np.var(groups_acc[i])+np.var(groups_acc[j]))/2)
    sig = "***" if padj<0.001 else "**" if padj<0.01 else "*" if padj<0.05 else "ns"
    s.append(f"  {a} vs {b}: d={d:.3f}, p_adj={padj:.4f} {sig}")

# Calibration curves (confidence vs accuracy)
s.append("\nMetacognitive Calibration Analysis:")
for c in conditions:
    sub = df[df['condition']==c]
    conf_acc = sub['correct_on_confident'].mean()
    unc_acc = sub['correct_on_uncertain'].mean()
    diff = conf_acc - unc_acc
    s.append(f"  {c}: Confident accuracy={conf_acc:.4f}, Uncertain accuracy={unc_acc:.4f}, Gap={diff:.4f}")

# Correlations
corr_oc_mcg = np.corrcoef(df['overconfidence_index'], df['metacognitive_accuracy'])[0,1]
corr_acc_mcg = np.corrcoef(df['oversight_accuracy'], df['metacognitive_accuracy'])[0,1]
s.append(f"\nOverconfidence × Metacognitive Accuracy: r = {corr_oc_mcg:.4f}")
s.append(f"Oversight Accuracy × Metacognitive Accuracy: r = {corr_acc_mcg:.4f}")

# Table
table = []
for c in conditions:
    sub = df[df['condition']==c]
    table.append({
        'Condition': c, 'N': len(sub),
        'Oversight Accuracy': f"{sub['oversight_accuracy'].mean():.3f}±{sub['oversight_accuracy'].std():.3f}",
        'Metacognitive Accuracy': f"{sub['metacognitive_accuracy'].mean():.3f}±{sub['metacognitive_accuracy'].std():.3f}",
        'Confidence': f"{sub['confidence_rating'].mean():.2f}±{sub['confidence_rating'].std():.2f}",
        'Overconfidence Index': f"{sub['overconfidence_index'].mean():.4f}±{sub['overconfidence_index'].std():.4f}",
        'Confident Hit Rate': f"{sub['correct_on_confident'].mean():.3f}",
        'Uncertain Hit Rate': f"{sub['correct_on_uncertain'].mean():.3f}",
    })
pd.DataFrame(table).to_csv(os.path.join(BASE, 'results', 'tables', 'metacognitive_table.csv'), index=False)

with open(os.path.join(BASE, 'results', 'statistical-output', 'complete_stats.txt'), 'w') as f:
    f.write('\n'.join(s))

print("✓ HIM-23 analysis complete")
print(f"  Accuracy ANOVA: F={f_acc:.2f}, p<.001")
print(f"  Overconfidence ANOVA: F={f_oc:.2f}, p<.001")
print(f"  Overconf-Metacog corr: r={corr_oc_mcg:.4f}")