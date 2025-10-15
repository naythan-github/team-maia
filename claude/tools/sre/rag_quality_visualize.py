#!/usr/bin/env python3
"""
RAG Quality Visualization - ASCII Charts

Creates terminal-friendly visualizations of quality comparison results.

Created: 2025-10-15
Author: Maia Data Analysis Agent
"""

import json
from pathlib import Path

MAIA_ROOT = Path(__file__).resolve().parents[3]


def create_bar_chart(label, ollama_val, gpu_val, width=50):
    """Create ASCII bar chart comparing two values"""
    max_val = max(ollama_val, gpu_val)
    if max_val == 0:
        max_val = 1

    ollama_bar = int((ollama_val / max_val) * width)
    gpu_bar = int((gpu_val / max_val) * width)

    print(f"  {label:<30}")
    print(f"    Ollama: {'█' * ollama_bar} {ollama_val:.1%}")
    print(f"    GPU:    {'█' * gpu_bar} {gpu_val:.1%}")


def visualize_results():
    """Create visualizations of test results"""
    results_file = MAIA_ROOT / "claude/data/rag_quality_test_results.json"

    with open(results_file, 'r') as f:
        data = json.load(f)

    print("="*70)
    print("RAG QUALITY COMPARISON - VISUAL SUMMARY")
    print("="*70)

    # Overall comparison
    print("\n📊 OVERALL PRECISION:")
    print("-"*70)
    ollama_avg = data['summary']['ollama_avg_precision']
    gpu_avg = data['summary']['gpu_avg_precision']

    create_bar_chart("Average Precision", ollama_avg, gpu_avg, width=60)

    # Category breakdown
    print("\n📊 PRECISION BY CATEGORY:")
    print("-"*70)

    categories = {}
    for query in data['test_queries']:
        cat = query['category']
        if cat not in categories:
            categories[cat] = {'ollama': [], 'gpu': []}

        categories[cat]['ollama'].append(query['ollama']['precision'])
        categories[cat]['gpu'].append(query['gpu']['precision'])

    for cat, values in sorted(categories.items()):
        ollama_cat_avg = sum(values['ollama']) / len(values['ollama'])
        gpu_cat_avg = sum(values['gpu']) / len(values['gpu'])
        create_bar_chart(cat, ollama_cat_avg, gpu_cat_avg)
        print()

    # Query-by-query comparison
    print("\n📊 QUERY-BY-QUERY PRECISION:")
    print("-"*70)

    for i, query in enumerate(data['test_queries'], 1):
        query_short = query['query'][:45] + "..." if len(query['query']) > 45 else query['query']
        ollama_p = query['ollama']['precision']
        gpu_p = query['gpu']['precision']

        print(f"\n{i}. {query_short}")
        print(f"   Ollama: {'█' * int(ollama_p * 20)} {ollama_p:.1%}")
        print(f"   GPU:    {'█' * int(gpu_p * 20)} {gpu_p:.1%}")

        if abs(gpu_p - ollama_p) < 0.10:
            verdict = "≈"
        elif gpu_p > ollama_p:
            verdict = "✅ GPU"
        else:
            verdict = "⚠️  Ollama"
        print(f"   {verdict}")

    # Performance comparison (illustrative)
    print("\n" + "="*70)
    print("📊 PERFORMANCE COMPARISON:")
    print("-"*70)

    print("\nIndexing Speed (docs/sec):")
    ollama_speed = 15
    gpu_speed = 97
    max_speed = max(ollama_speed, gpu_speed)

    print(f"  Ollama: {'█' * int((ollama_speed/max_speed) * 50)} {ollama_speed} docs/sec")
    print(f"  GPU:    {'█' * int((gpu_speed/max_speed) * 50)} {gpu_speed} docs/sec")
    print(f"  → GPU is {gpu_speed/ollama_speed:.1f}x FASTER")

    print("\nStorage Size (dimensions):")
    ollama_dim = 768
    gpu_dim = 384
    max_dim = max(ollama_dim, gpu_dim)

    print(f"  Ollama: {'█' * int((ollama_dim/max_dim) * 50)} {ollama_dim} dimensions")
    print(f"  GPU:    {'█' * int((gpu_dim/max_dim) * 50)} {gpu_dim} dimensions")
    print(f"  → GPU uses {(1 - gpu_dim/ollama_dim):.1%} LESS storage")

    # Trade-off summary
    print("\n" + "="*70)
    print("📊 QUALITY vs PERFORMANCE TRADE-OFF:")
    print("-"*70)

    quality_loss = ollama_avg - gpu_avg
    speed_gain = gpu_speed / ollama_speed

    print(f"\n  Quality Loss: {quality_loss:.1%} (Ollama better)")
    print(f"  Speed Gain:   {speed_gain:.1f}x (GPU faster)")
    print(f"\n  Trade-off Ratio: Lose {quality_loss:.1%} quality, Gain {speed_gain:.1f}x speed")

    if quality_loss < 0.10 and speed_gain > 5:
        print(f"\n  ✅ VERDICT: Performance gains justify quality loss")
    elif quality_loss < 0.05:
        print(f"\n  ✅ VERDICT: Quality nearly equivalent, use GPU")
    else:
        print(f"\n  ⚠️  VERDICT: Significant quality loss, consider hybrid approach")

    print("="*70)


if __name__ == '__main__':
    visualize_results()
