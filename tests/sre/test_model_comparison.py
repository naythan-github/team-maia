#!/usr/bin/env python3
"""
Model Comparison Test: phi3:mini vs llama3.2:3b
Tests consistency, quality, and performance for ServiceDesk quality coaching
"""

import ollama
import time
import statistics
import json
from datetime import datetime

# Test prompt - realistic ServiceDesk comment quality analysis
TEST_PROMPT = """You are a quality coach analyzing ServiceDesk agent comments.

Analyze this comment and provide coaching:

Comment: "vpn is connected"
Agent: brian
Ticket: Customer reported "VPN drops out every 3-5 minutes"

Provide:
1. Quality Assessment (1-5): Professionalism, Clarity, Empathy, Actionability
2. What's Good: Specific positive elements
3. Improvements Needed: Specific issues with examples
4. Best Practice Techniques: How to improve with specific examples

Format as structured JSON."""

def test_model_consistency(model_name: str, iterations: int = 5) -> dict:
    """Test model consistency across multiple runs"""

    print(f"\n{'='*60}")
    print(f"Testing {model_name}")
    print(f"{'='*60}\n")

    results = []

    for i in range(iterations):
        print(f"  Run {i+1}/{iterations}...", end=" ", flush=True)

        start_time = time.time()

        try:
            response = ollama.chat(
                model=model_name,
                messages=[{
                    'role': 'user',
                    'content': TEST_PROMPT
                }],
                options={
                    'temperature': 0.7,
                    'seed': None  # Allow natural variation
                }
            )

            elapsed = time.time() - start_time
            content = response['message']['content']

            # Analyze response
            analysis = {
                'iteration': i + 1,
                'elapsed_time': round(elapsed, 2),
                'response_length': len(content),
                'has_quality_scores': '1-5' in content or 'score' in content.lower(),
                'has_positives': 'good' in content.lower() or 'positive' in content.lower(),
                'has_improvements': 'improvement' in content.lower() or 'issue' in content.lower(),
                'has_techniques': 'technique' in content.lower() or 'practice' in content.lower(),
                'has_examples': 'example' in content.lower() or 'specifically' in content.lower(),
                'response': content
            }

            results.append(analysis)
            print(f"✓ {elapsed:.1f}s, {len(content)} chars")

        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({'error': str(e)})

    return results

def calculate_metrics(results: list, model_name: str) -> dict:
    """Calculate consistency and quality metrics"""

    valid_results = [r for r in results if 'error' not in r]

    if not valid_results:
        return {'error': 'No valid results'}

    # Performance metrics
    times = [r['elapsed_time'] for r in valid_results]
    lengths = [r['response_length'] for r in valid_results]

    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0
    cv_time = (std_time / avg_time * 100) if avg_time > 0 else 0

    avg_length = statistics.mean(lengths)
    std_length = statistics.stdev(lengths) if len(lengths) > 1 else 0
    cv_length = (std_length / avg_length * 100) if avg_length > 0 else 0

    # Quality metrics
    completion_rate = sum([
        r['has_quality_scores'] and
        r['has_positives'] and
        r['has_improvements'] and
        r['has_techniques']
        for r in valid_results
    ]) / len(valid_results) * 100

    # Specificity (examples usage)
    specificity_rate = sum([r['has_examples'] for r in valid_results]) / len(valid_results) * 100

    return {
        'model': model_name,
        'iterations': len(valid_results),
        'avg_time_seconds': round(avg_time, 2),
        'cv_time_percent': round(cv_time, 2),
        'avg_length_chars': round(avg_length, 0),
        'cv_length_percent': round(cv_length, 2),
        'completion_rate_percent': round(completion_rate, 1),
        'specificity_rate_percent': round(specificity_rate, 1),
        'rating': calculate_rating(cv_time, cv_length, completion_rate, specificity_rate)
    }

def calculate_rating(cv_time, cv_length, completion_rate, specificity_rate):
    """Calculate overall rating"""

    # Consistency (50% weight)
    consistency_score = 0
    if cv_time < 5 and cv_length < 5:
        consistency_score = 50  # EXCELLENT
    elif cv_time < 10 and cv_length < 10:
        consistency_score = 40  # GOOD
    elif cv_time < 15 and cv_length < 15:
        consistency_score = 30  # MODERATE
    else:
        consistency_score = 20  # POOR

    # Quality (50% weight)
    quality_score = (completion_rate + specificity_rate) / 4  # Max 50

    total = consistency_score + quality_score

    if total >= 90:
        return "A+ (EXCELLENT - Production Ready)"
    elif total >= 80:
        return "A (VERY GOOD - Production Ready)"
    elif total >= 70:
        return "B+ (GOOD - Acceptable)"
    elif total >= 60:
        return "B (FAIR - Needs Improvement)"
    else:
        return "C (POOR - Not Recommended)"

def main():
    """Run comparison test"""

    print("\n" + "="*60)
    print("SERVICEDESK QUALITY COACHING MODEL COMPARISON")
    print("="*60)
    print(f"\nTest Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Iterations: 5 per model")
    print(f"Temperature: 0.7 (natural variation)")

    # Test both models
    models = ['llama3.2:3b', 'phi3:mini']
    all_results = {}

    for model in models:
        results = test_model_consistency(model, iterations=5)
        metrics = calculate_metrics(results, model)
        all_results[model] = {
            'metrics': metrics,
            'raw_results': results
        }

    # Print comparison
    print("\n" + "="*60)
    print("RESULTS COMPARISON")
    print("="*60)

    for model in models:
        metrics = all_results[model]['metrics']
        print(f"\n{model}:")
        print(f"  Average Time: {metrics['avg_time_seconds']}s")
        print(f"  Time CV: {metrics['cv_time_percent']}% {'✓ EXCELLENT' if metrics['cv_time_percent'] < 5 else '✓ GOOD' if metrics['cv_time_percent'] < 10 else '⚠ MODERATE' if metrics['cv_time_percent'] < 15 else '✗ POOR'}")
        print(f"  Length CV: {metrics['cv_length_percent']}% {'✓ EXCELLENT' if metrics['cv_length_percent'] < 5 else '✓ GOOD' if metrics['cv_length_percent'] < 10 else '⚠ MODERATE' if metrics['cv_length_percent'] < 15 else '✗ POOR'}")
        print(f"  Completion Rate: {metrics['completion_rate_percent']}% {'✓' if metrics['completion_rate_percent'] == 100 else '⚠'}")
        print(f"  Specificity Rate: {metrics['specificity_rate_percent']}% {'✓' if metrics['specificity_rate_percent'] >= 80 else '⚠'}")
        print(f"  Overall Rating: {metrics['rating']}")

    # Recommendation
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)

    llama_rating = all_results['llama3.2:3b']['metrics']['rating']
    phi_rating = all_results['phi3:mini']['metrics']['rating']

    llama_cv_avg = (all_results['llama3.2:3b']['metrics']['cv_time_percent'] +
                    all_results['llama3.2:3b']['metrics']['cv_length_percent']) / 2
    phi_cv_avg = (all_results['phi3:mini']['metrics']['cv_time_percent'] +
                  all_results['phi3:mini']['metrics']['cv_length_percent']) / 2

    llama_quality = (all_results['llama3.2:3b']['metrics']['completion_rate_percent'] +
                     all_results['llama3.2:3b']['metrics']['specificity_rate_percent']) / 2
    phi_quality = (all_results['phi3:mini']['metrics']['completion_rate_percent'] +
                   all_results['phi3:mini']['metrics']['specificity_rate_percent']) / 2

    print(f"\nConsistency Winner: ", end="")
    if llama_cv_avg < phi_cv_avg:
        print(f"llama3.2:3b ({llama_cv_avg:.1f}% CV vs {phi_cv_avg:.1f}% CV)")
    else:
        print(f"phi3:mini ({phi_cv_avg:.1f}% CV vs {llama_cv_avg:.1f}% CV)")

    print(f"Quality Winner: ", end="")
    if llama_quality > phi_quality:
        print(f"llama3.2:3b ({llama_quality:.1f}% vs {phi_quality:.1f}%)")
    else:
        print(f"phi3:mini ({phi_quality:.1f}% vs {llama_quality:.1f}%)")

    print(f"\nSpeed: llama3.2:3b = {all_results['llama3.2:3b']['metrics']['avg_time_seconds']}s, "
          f"phi3:mini = {all_results['phi3:mini']['metrics']['avg_time_seconds']}s")

    # Final recommendation
    if 'A+' in llama_rating or 'A' in llama_rating:
        if 'A+' in phi_rating or 'A' in phi_rating:
            if llama_quality > phi_quality:
                rec = "KEEP llama3.2:3b (both excellent, llama has higher quality)"
            else:
                rec = "SWITCH to phi3:mini (both excellent, phi has higher quality)"
        else:
            rec = "KEEP llama3.2:3b (production-ready, phi not as strong)"
    else:
        if 'A+' in phi_rating or 'A' in phi_rating:
            rec = "SWITCH to phi3:mini (production-ready, llama not as strong)"
        else:
            rec = "NEITHER model is ideal - consider testing larger models"

    print(f"\n🎯 FINAL RECOMMENDATION: {rec}")

    # Save detailed results
    from claude.tools.core.paths import DATA_DIR
    output_file = str(DATA_DIR / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✓ Detailed results saved: {output_file}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
