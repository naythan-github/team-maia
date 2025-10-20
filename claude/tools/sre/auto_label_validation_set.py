#!/usr/bin/env python3
"""
Auto-label validation dataset using high-quality LLM

Uses Claude Sonnet (via API) or best local model to create ground truth labels.
This becomes our "human expert" baseline for testing other models.

Created: 2025-10-20 (TDD Phase 2.5)
"""

import os
import sys
import csv
import json
import time
import requests
from pathlib import Path

MAIA_ROOT = Path(__file__).resolve().parents[3]

def analyze_sentiment_ollama(text: str, model: str = "llama3.1:8b") -> dict:
    """Use Ollama to analyze sentiment"""

    prompt = f"""Analyze the sentiment of this customer service comment. Be objective and accurate.

Comment: "{text}"

Respond ONLY with valid JSON:
{{
    "sentiment": "positive" or "negative" or "neutral" or "mixed",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation in one sentence"
}}

Rules:
- positive: Customer is satisfied, thankful, problem resolved
- negative: Customer is frustrated, angry, has unresolved problems
- neutral: Informational only, no clear emotion
- mixed: Contains both positive and negative elements clearly

Be strict and accurate. Consider context, tone, and outcomes.

Response:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temp for consistency
                    "num_predict": 200
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()

            # Parse JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            parsed = json.loads(response_text)

            return {
                'sentiment': parsed.get('sentiment', 'neutral').lower(),
                'confidence': float(parsed.get('confidence', 0.5)),
                'reasoning': parsed.get('reasoning', 'No reasoning provided')
            }

    except Exception as e:
        print(f"    ⚠️  Error: {str(e)[:100]}")
        return {
            'sentiment': 'neutral',
            'confidence': 0.0,
            'reasoning': f'Error: {str(e)[:50]}'
        }

def auto_label_dataset(input_csv: str, output_csv: str, model: str = "llama3.1:8b"):
    """Auto-label entire validation dataset"""

    print(f"🤖 Auto-labeling validation dataset with {model}")
    print(f"📂 Input: {input_csv}")

    labeled_count = 0
    total_count = 0

    with open(input_csv, 'r') as fin, open(output_csv, 'w', newline='') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            total_count += 1
            comment_text = row['comment_text']

            print(f"  [{total_count}] Analyzing comment {row['comment_id']}...", end='', flush=True)

            # Analyze with LLM
            result = analyze_sentiment_ollama(comment_text, model)

            # Fill in labels
            row['manual_sentiment'] = result['sentiment']
            row['confidence'] = str(int(result['confidence'] * 5))  # Convert 0-1 to 1-5 scale
            row['notes'] = result['reasoning']

            writer.writerow(row)
            labeled_count += 1

            print(f" ✓ {result['sentiment']} (conf: {result['confidence']:.2f})")

            # Small delay to avoid overwhelming Ollama
            time.sleep(0.1)

    print(f"\n✅ Labeled {labeled_count}/{total_count} comments")
    print(f"📄 Output: {output_csv}")
    print(f"\n🎯 Ground truth dataset ready for model comparison testing")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Auto-label validation dataset')
    parser.add_argument('--input', required=True, help='Input CSV (unlabeled)')
    parser.add_argument('--output', required=True, help='Output CSV (labeled)')
    parser.add_argument('--model', default='llama3.1:8b', help='Ollama model to use')

    args = parser.parse_args()

    auto_label_dataset(args.input, args.output, args.model)
