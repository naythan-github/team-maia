#!/usr/bin/env python3
"""
Sentiment Analysis Model Tester (TDD Phase 3)

Tests multiple local LLM models for sentiment analysis accuracy:
- llama3.2:3b (fast)
- llama3.1:8b (balanced)
- gemma2:9b (accuracy)
- mistral:7b (general)

Compares against keyword baseline and generates accuracy metrics.

Usage:
    python3 sentiment_model_tester.py --validation-csv path/to/labeled.csv
    python3 sentiment_model_tester.py --model llama3.2:3b --sample 50

Created: 2025-10-20 (TDD Phase 3 - RED)
"""

import os
import sys
import csv
import json
import time
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

MAIA_ROOT = Path(__file__).resolve().parents[3]

class SentimentModelTester:
    """Test local LLM models for sentiment analysis accuracy"""

    def __init__(self, validation_csv: str, ollama_url: str = "http://localhost:11434"):
        self.validation_csv = validation_csv
        self.ollama_url = ollama_url
        self.validation_data = []
        self.load_validation_data()

    def load_validation_data(self):
        """Load manually labeled validation dataset"""
        print(f"📂 Loading validation data from {self.validation_csv}")

        with open(self.validation_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only include rows with manual labels
                if row['manual_sentiment'].strip():
                    self.validation_data.append({
                        'comment_id': row['comment_id'],
                        'comment_text': row['comment_text'],
                        'keyword_sentiment': row['keyword_sentiment'],
                        'manual_sentiment': row['manual_sentiment'].lower().strip(),
                        'confidence': row.get('confidence', '3'),
                        'notes': row.get('notes', '')
                    })

        print(f"✅ Loaded {len(self.validation_data)} manually labeled comments")

        # Distribution check
        sentiment_dist = defaultdict(int)
        for item in self.validation_data:
            sentiment_dist[item['manual_sentiment']] += 1

        print(f"📊 Distribution: {dict(sentiment_dist)}")

    def test_ollama_model(self, model_name: str, sample_size: int = None) -> Dict:
        """Test a specific Ollama model"""
        print(f"\n🧪 Testing model: {model_name}")

        # Check if model is available
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            available_models = [m['name'] for m in response.json().get('models', [])]
            if model_name not in available_models:
                print(f"❌ Model {model_name} not found. Available: {available_models}")
                print(f"   Run: ollama pull {model_name}")
                return None
        except Exception as e:
            print(f"❌ Failed to connect to Ollama: {e}")
            return None

        # Test on sample
        test_data = self.validation_data[:sample_size] if sample_size else self.validation_data
        print(f"📝 Testing on {len(test_data)} comments")

        results = []
        correct = 0
        total = len(test_data)

        start_time = time.time()

        for i, item in enumerate(test_data, 1):
            print(f"  [{i}/{total}] Processing comment {item['comment_id']}...", end='\r')

            # Generate sentiment with LLM
            predicted_sentiment, confidence, reasoning, latency = self.analyze_sentiment(
                model_name,
                item['comment_text']
            )

            # Compare with manual label
            is_correct = predicted_sentiment == item['manual_sentiment']
            if is_correct:
                correct += 1

            results.append({
                'comment_id': item['comment_id'],
                'comment_text': item['comment_text'][:100] + '...',
                'manual_label': item['manual_sentiment'],
                'predicted_label': predicted_sentiment,
                'confidence': confidence,
                'is_correct': is_correct,
                'latency_ms': latency,
                'reasoning': reasoning
            })

        elapsed = time.time() - start_time
        accuracy = correct / total
        avg_latency = sum(r['latency_ms'] for r in results) / total

        # Calculate precision, recall, F1 for each class
        metrics = self.calculate_metrics(results)

        print(f"\n\n✅ Model: {model_name}")
        print(f"   Accuracy: {accuracy:.1%} ({correct}/{total})")
        print(f"   Avg Latency: {avg_latency:.0f}ms")
        print(f"   Total Time: {elapsed:.1f}s")
        print(f"\n📊 Per-Class Metrics:")
        for sentiment, m in metrics.items():
            print(f"   {sentiment.capitalize()}:")
            print(f"      Precision: {m['precision']:.1%}")
            print(f"      Recall: {m['recall']:.1%}")
            print(f"      F1 Score: {m['f1']:.1%}")

        return {
            'model': model_name,
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'avg_latency_ms': avg_latency,
            'total_time_sec': elapsed,
            'metrics': metrics,
            'results': results
        }

    def analyze_sentiment(self, model: str, text: str) -> Tuple[str, float, str, int]:
        """Analyze sentiment using Ollama model with few-shot prompting"""
        prompt = f"""Analyze the sentiment of this customer support comment.

IMPORTANT INSTRUCTIONS:
1. DEFAULT to positive, negative, or neutral - only use "mixed" when CLEARLY both sentiments exist
2. MIXED requires BOTH: explicit gratitude/appreciation AND explicit frustration/problem
3. "Thanks but [problem still exists]" = mixed
4. "Working on it, please test" = neutral (NOT mixed - just uncertainty)
5. Standard acknowledgments with no emotion = neutral (NOT positive)
6. Respond ONLY with valid JSON (no markdown, no extra text)

EXAMPLES OF EACH SENTIMENT:

POSITIVE - Problem resolved successfully:
Comment: "We successfully reset the password. Please refer to the following link for the credentials."
{{
    "sentiment": "positive",
    "confidence": 0.95,
    "reasoning": "Problem resolved, credentials provided, successful outcome"
}}

NEGATIVE - Complete failure explicitly stated (RARE - only when stating total failure):
Comment: "Thanks for sending through the credentials. Tried all of them, none worked."
{{
    "sentiment": "negative",
    "confidence": 0.85,
    "reasoning": "Despite politeness, complete failure stated - nothing worked at all"
}}

NEUTRAL - Issue not resolved yet, no frustration (NOT negative):
Comment: "Could you please let me know when you're online so that I can look into this? We may be able to rectify the issue with a simple reboot."
{{
    "sentiment": "neutral",
    "confidence": 0.90,
    "reasoning": "Problem exists but no frustration, just coordinating next steps"
}}

NEUTRAL - Standard informational update:
Comment: "This is to acknowledge receiving your request. Ticket has been assigned to the relevant group."
{{
    "sentiment": "neutral",
    "confidence": 0.90,
    "reasoning": "Standard acknowledgment template, no emotion expressed"
}}

MIXED - Appreciation with ongoing concern (RARE - only when BOTH present):
Comment: "Thanks Nish, Sorry I should clarify, we can login to Magento but there is not application setting page."
{{
    "sentiment": "mixed",
    "confidence": 0.80,
    "reasoning": "Gratitude expressed (positive) but issue still exists (negative)"
}}

NOW ANALYZE THIS COMMENT:

Comment: {text}

JSON response:"""

        start = time.time()

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "num_predict": 150
                    }
                },
                timeout=30
            )

            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                # Parse JSON response
                try:
                    # Extract JSON from response (handle markdown code blocks)
                    if '```json' in response_text:
                        response_text = response_text.split('```json')[1].split('```')[0].strip()
                    elif '```' in response_text:
                        response_text = response_text.split('```')[1].split('```')[0].strip()

                    parsed = json.loads(response_text)
                    sentiment = parsed.get('sentiment', 'neutral').lower()
                    confidence = float(parsed.get('confidence', 0.5))
                    reasoning = parsed.get('reasoning', 'No reasoning provided')

                    return sentiment, confidence, reasoning, latency

                except json.JSONDecodeError:
                    print(f"\n⚠️  Failed to parse JSON: {response_text[:100]}")
                    return 'neutral', 0.3, f"Parse error: {response_text[:50]}", latency
            else:
                return 'neutral', 0.0, f"HTTP {response.status_code}", latency

        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return 'neutral', 0.0, f"Error: {str(e)[:50]}", latency

    def calculate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate precision, recall, F1 for each sentiment class"""
        sentiments = ['positive', 'negative', 'neutral', 'mixed']
        metrics = {}

        for sentiment in sentiments:
            tp = sum(1 for r in results if r['manual_label'] == sentiment and r['predicted_label'] == sentiment)
            fp = sum(1 for r in results if r['manual_label'] != sentiment and r['predicted_label'] == sentiment)
            fn = sum(1 for r in results if r['manual_label'] == sentiment and r['predicted_label'] != sentiment)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            metrics[sentiment] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn
            }

        return metrics

    def test_keyword_baseline(self) -> Dict:
        """Test current keyword matching approach (baseline)"""
        print(f"\n🧪 Testing keyword baseline")

        results = []
        correct = 0
        total = len(self.validation_data)

        for item in self.validation_data:
            keyword_sentiment = item['keyword_sentiment']
            manual_sentiment = item['manual_sentiment']

            is_correct = keyword_sentiment == manual_sentiment
            if is_correct:
                correct += 1

            results.append({
                'comment_id': item['comment_id'],
                'comment_text': item['comment_text'][:100] + '...',
                'manual_label': manual_sentiment,
                'predicted_label': keyword_sentiment,
                'is_correct': is_correct
            })

        accuracy = correct / total
        metrics = self.calculate_metrics(results)

        print(f"✅ Keyword Baseline")
        print(f"   Accuracy: {accuracy:.1%} ({correct}/{total})")
        print(f"\n📊 Per-Class Metrics:")
        for sentiment, m in metrics.items():
            print(f"   {sentiment.capitalize()}:")
            print(f"      Precision: {m['precision']:.1%}")
            print(f"      Recall: {m['recall']:.1%}")
            print(f"      F1 Score: {m['f1']:.1%}")

        return {
            'model': 'keyword_baseline',
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'metrics': metrics,
            'results': results
        }

    def compare_all_models(self, models: List[str], sample_size: int = None):
        """Test all models and generate comparison report"""
        print("=" * 80)
        print("SENTIMENT ANALYSIS MODEL COMPARISON")
        print("=" * 80)

        all_results = []

        # Test keyword baseline
        baseline_result = self.test_keyword_baseline()
        all_results.append(baseline_result)

        # Test each LLM model
        for model in models:
            result = self.test_ollama_model(model, sample_size)
            if result:
                all_results.append(result)

        # Generate comparison report
        self.generate_comparison_report(all_results)

    def generate_comparison_report(self, results: List[Dict]):
        """Generate comparison report and save to file"""
        output_file = MAIA_ROOT / f"tests/sentiment_validation/model_comparison_{int(time.time())}.txt"

        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SENTIMENT ANALYSIS MODEL COMPARISON REPORT")
        report_lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Validation Set Size: {results[0]['total']} comments")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Sort by accuracy
        sorted_results = sorted(results, key=lambda x: x['accuracy'], reverse=True)

        report_lines.append("OVERALL RANKING (by accuracy):")
        report_lines.append("-" * 80)
        for i, r in enumerate(sorted_results, 1):
            latency_info = f", Avg Latency: {r['avg_latency_ms']:.0f}ms" if 'avg_latency_ms' in r else ""
            report_lines.append(f"{i}. {r['model']}: {r['accuracy']:.1%} ({r['correct']}/{r['total']}){latency_info}")
        report_lines.append("")

        # Detailed per-model metrics
        report_lines.append("DETAILED METRICS BY MODEL:")
        report_lines.append("=" * 80)
        for r in sorted_results:
            report_lines.append(f"\nModel: {r['model']}")
            report_lines.append(f"Accuracy: {r['accuracy']:.1%}")
            if 'avg_latency_ms' in r:
                report_lines.append(f"Avg Latency: {r['avg_latency_ms']:.0f}ms")
            report_lines.append("\nPer-Class Metrics:")
            for sentiment, m in r['metrics'].items():
                report_lines.append(f"  {sentiment.capitalize()}:")
                report_lines.append(f"    Precision: {m['precision']:.1%} (TP: {m['true_positives']}, FP: {m['false_positives']})")
                report_lines.append(f"    Recall:    {m['recall']:.1%} (FN: {m['false_negatives']})")
                report_lines.append(f"    F1 Score:  {m['f1']:.1%}")
            report_lines.append("-" * 80)

        # Recommendation
        report_lines.append("\nRECOMMENDATION:")
        report_lines.append("=" * 80)
        best_model = sorted_results[0]
        baseline = [r for r in results if r['model'] == 'keyword_baseline'][0]
        improvement = best_model['accuracy'] - baseline['accuracy']

        report_lines.append(f"Best Model: {best_model['model']}")
        report_lines.append(f"Accuracy: {best_model['accuracy']:.1%}")
        report_lines.append(f"Improvement over baseline: {improvement:+.1%}")

        if improvement >= 0.10:
            report_lines.append("\n✅ SIGNIFICANT IMPROVEMENT - Recommend switching to LLM-based sentiment")
        elif improvement >= 0.05:
            report_lines.append("\n⚠️  MODERATE IMPROVEMENT - Consider LLM if latency acceptable")
        else:
            report_lines.append("\n❌ INSUFFICIENT IMPROVEMENT - Stick with keyword baseline or enhance keywords")

        # Write report
        report_text = '\n'.join(report_lines)
        print("\n" + report_text)

        with open(output_file, 'w') as f:
            f.write(report_text)

        print(f"\n📄 Report saved: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Test sentiment analysis models')
    parser.add_argument('--validation-csv', required=True, help='Path to manually labeled validation CSV')
    parser.add_argument('--model', help='Test specific model only')
    parser.add_argument('--sample', type=int, help='Test on sample size (for quick testing)')
    parser.add_argument('--all', action='store_true', help='Test all models')

    args = parser.parse_args()

    tester = SentimentModelTester(args.validation_csv)

    if args.model:
        # Test single model
        tester.test_ollama_model(args.model, args.sample)
    elif args.all:
        # Test all models
        models = ['llama3.2:3b', 'llama3.1:8b', 'gemma2:9b', 'mistral:7b']
        tester.compare_all_models(models, args.sample)
    else:
        print("❌ Specify --model <name> or --all")
        sys.exit(1)

if __name__ == "__main__":
    main()
